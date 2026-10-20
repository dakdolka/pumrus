"""Portable, editable theory pages and optimistic concurrency stamps."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

BLOCK_TYPES = ("rich_text", "section", "callout", "example", "list", "table", "image", "video_embed", "practice_link", "theory_link")
ANCHOR = re.compile(r"[a-z][a-z0-9-]{0,63}")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EditBlock(StrictModel):
    id: str | None = Field(default=None, min_length=1, max_length=96)
    type: Literal["rich_text", "section", "callout", "example", "list", "table", "image", "video_embed", "practice_link", "theory_link"]
    data: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    children: list[EditBlock] = Field(default_factory=list, max_length=2000)


class EditPage(StrictModel):
    title: str = Field(min_length=1, max_length=256)
    ownerTitle: str = Field(min_length=1, max_length=256)
    description: str = Field(default="", max_length=1024)
    blocks: list[EditBlock] = Field(max_length=2000)


class EditBase(StrictModel):
    documentId: int = Field(gt=0)
    publishedVersionId: int | None
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class TheoryEditPackage(StrictModel):
    format: Literal["pumrus.theory-edit"]
    schemaVersion: Literal[1]
    base: EditBase
    before: EditPage
    after: EditPage


def validate_data(block_type: str, data: dict[str, Any]) -> None:
    if block_type == "theory_link":
        for key in ("taskNumber", "topicId"):
            if type(data.get(key)) is not int or not 0 < data[key] <= 2**53 - 1:
                raise ValueError(f"data.{key}: укажите положительное целое число")
        anchor = data.get("anchor")
        if anchor is not None and (not isinstance(anchor, str) or (anchor and not ANCHOR.fullmatch(anchor))):
            raise ValueError("data.anchor: некорректная метка раздела")
    for key in ("markdown", "title", "url", "alt", "caption", "svg", "buttonLabel"):
        if key in data and not isinstance(data[key], str):
            raise ValueError(f"data.{key}: ожидается текст")
    if block_type == "callout" and data.get("variant", "note") not in {"note", "rule", "warning", "important", "tip"}:
        raise ValueError("Неизвестный вид выноски: data.variant")
    if block_type == "list":
        if data.get("style", "unordered") not in {"ordered", "unordered"}:
            raise ValueError("data.style: ordered или unordered")
        values = data.get("items", [])
        if not isinstance(values, list) or any(not isinstance(v, str) and not (isinstance(v, dict) and isinstance(v.get("text"), str)) for v in values):
            raise ValueError("data.items: ожидается список строк")
    if block_type == "table":
        rows = data.get("rows", [])
        if not isinstance(rows, list):
            raise ValueError("data.rows: ожидается список строк таблицы")
        for row in rows:
            cells = row.get("cells") if isinstance(row, dict) else row
            if not isinstance(cells, list) or any(not isinstance(c, (str, int, float)) and not (isinstance(c, dict) and isinstance(c.get("text"), str)) for c in cells):
                raise ValueError("Каждая строка таблицы должна содержать cells: [текст, ...]")


def validate_anchor(settings: dict[str, Any], used: set[str]) -> None:
    anchor = settings.get("anchor")
    if anchor is None or anchor == "":
        return
    if not isinstance(anchor, str) or not ANCHOR.fullmatch(anchor):
        raise ValueError("settings.anchor: латинские строчные буквы, цифры и дефис; начните с буквы (до 64 символов)")
    if anchor in used:
        raise ValueError("settings.anchor: повторяется метка раздела")
    used.add(anchor)


def flatten_page(page: EditPage) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    used: set[str] = set()
    anchors: set[str] = set()

    def walk(blocks: list[EditBlock], parent: str | None, depth: int) -> None:
        if depth > 32:
            raise ValueError("Вложенность блоков не должна превышать 32 уровня")
        for order, block in enumerate(blocks):
            if len(flat) >= 2000:
                raise ValueError("В одной теме допускается не более 2000 блоков")
            block_id = block.id or f"new:auto:{len(flat) + 1}"
            if block_id in used:
                raise ValueError(f"Повторяется id блока: {block_id}")
            used.add(block_id)
            validate_data(block.type, block.data)
            validate_anchor(block.settings, anchors)
            flat.append({
                "client_id": block_id, "parent_client_id": parent, "block_type": block.type,
                "data": deepcopy(block.data), "settings": deepcopy(block.settings), "sort_order": order,
            })
            walk(block.children, block_id, depth + 1)

    walk(page.blocks, None, 0)
    return flat


def tree_blocks(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert DB-style records; reject damaged graphs rather than dropping blocks."""
    by_id = {str(b["id"]): b for b in records}
    if len(by_id) != len(records):
        raise ValueError("Повторяются идентификаторы исходных блоков")
    groups: dict[str | None, list[dict[str, Any]]] = {}
    for record in records:
        parent = str(record["parent_id"]) if record.get("parent_id") is not None else None
        if parent is not None and parent not in by_id:
            raise ValueError("Родительский блок отсутствует в исходной теме")
        groups.setdefault(parent, []).append(record)
    visited = set()

    def walk(parent: str | None, depth: int = 0) -> list[dict[str, Any]]:
        if depth > 32:
            raise ValueError("Слишком большая вложенность исходной темы")
        result = []
        for b in sorted(groups.get(parent, []), key=lambda b: (b["sort_order"], str(b["id"]))):
            key = str(b["id"])
            if key in visited:
                raise ValueError("В исходной теме обнаружен цикл")
            visited.add(key)
            node = {"id": key, "type": b["type"], "data": deepcopy(b["data"]), "settings": deepcopy(b.get("settings") or {})}
            children = walk(key, depth + 1)
            if children:
                node["children"] = children
            result.append(node)
        return result

    result = walk(None)
    if len(visited) != len(records):
        raise ValueError("В исходной теме обнаружена замкнутая вложенность")
    return result


def canonical_page(page: dict[str, Any] | EditPage) -> dict[str, Any]:
    parsed = page if isinstance(page, EditPage) else EditPage.model_validate(page)
    flatten_page(parsed)
    return parsed.model_dump()


def fingerprint(page: dict[str, Any] | EditPage) -> str:
    data = json.dumps(canonical_page(page), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def make_package(document_id: int, version_id: int | None, page: dict[str, Any]) -> dict[str, Any]:
    canonical_page(page)
    return {
        "format": "pumrus.theory-edit", "schemaVersion": 1,
        "base": {"documentId": document_id, "publishedVersionId": version_id, "fingerprint": fingerprint(page)},
        "before": deepcopy(page), "after": deepcopy(page),
    }


def check_base(package: TheoryEditPackage, document_id: int, version_id: int | None, page: dict[str, Any]) -> None:
    if package.base.documentId != document_id:
        raise ValueError("Пакет предназначен для другой темы")
    if package.base.publishedVersionId != version_id or package.base.fingerprint != fingerprint(page):
        raise ValueError("Тема изменилась после экспорта. Экспортируйте её заново и перенесите правки")
    if fingerprint(package.before) != package.base.fingerprint:
        raise ValueError("Раздел before изменён. Редактируйте только after")
