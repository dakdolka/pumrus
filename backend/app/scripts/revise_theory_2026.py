"""Safely publish narrow, source-checked corrections to the live 2026 theory.

Dry run by default. A changed target block is treated as a conflict rather than
overwriting edits made in the owner form. Earlier published versions remain in
the database for comparison and rollback.
"""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.db import async_session_factory
from app.infra.catalog.models import CourseVersionBD, ExamTaskBD, TopicBD
from app.infra.content.models import (
    TheoryBlockV2BD,
    TheoryDocumentBD,
    TheoryDocumentVersionBD,
)


REVISION = "ege-2026-editorial-corrections-v1"
FIPI_GRAMMAR = "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/MR_rus_yaz_ege_2026.pdf"
FIPI_TASK26 = "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-3-grammatika-morfologija.pdf"
GRAMOTA_ROOTS = "https://gramota.ru/biblioteka/spravochniki/pravila-russkoy-orfografii-i-punktuatsii/bezudarnye-glasnye-v-kornyakh"
GRAMOTA_STRESS = "https://gramota.ru/meta/otzyv"


def _replace_markdown(blocks: list[dict], old: str, new: str) -> None:
    matches = [item for item in blocks if item["data"].get("markdown") == old]
    if len(matches) != 1:
        raise ValueError(f"Expected one unchanged markdown block, found {len(matches)}: {old[:70]}")
    matches[0]["data"]["markdown"] = new


def _replace_table(blocks: list[dict], marker: str, rows: list[list[str]]) -> None:
    matches = [
        item for item in blocks
        if item["type"] == "table"
        and any(marker in " ".join(map(str, row.get("cells", []))) for row in item["data"].get("rows", []))
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one unchanged table containing {marker!r}, found {len(matches)}")
    matches[0]["data"]["rows"] = [{"cells": row} for row in rows]


def revise(owner: str, key: str | int, blocks: list[dict]) -> list[str]:
    """Apply only corrections whose outdated published wording is still present."""
    changes: list[str] = []
    if (owner, key) == ("topic", "topic-957e89c99be8"):
        _replace_markdown(
            blocks,
            "Здесь нет никаких подсказок, нужно просто **чувствовать** контекст!",
            "Не угадывайте по звучанию. Определите, что нужно связать: причину с результатом, "
            "событие со временем или предмет с местом. Затем проверьте, подходит ли наречие "
            "по смыслу и по грамматической форме: *потому* указывает на причину, "
            "*поэтому* — на следствие.",
        )
        changes.append("task 1: remove advice to guess by intuition")
    elif (owner, key) == ("topic", "task-3-styles-v2"):
        matches = [item for item in blocks if item["type"] == "rich_text" and not item["data"].get("markdown", "").strip()]
        if len(matches) != 1 or any(item["parent_id"] == matches[0]["id"] for item in blocks):
            raise ValueError("Task 3 blank block has changed; refusing to remove it")
        blocks.remove(matches[0])
        changes.append("task 3: remove an empty visible block")
    elif (owner, key) == ("topic", "task-4-nouns"):
        _replace_markdown(
            blocks,
            "**ОтзЫв** посла — действие *отозвать*; **Отзыв** о книге — мнение. Значение различает ударение.",
            "**отзы́в** посла — действие *отозвать*; **о́тзыв** о книге — мнение. "
            "Здесь ударение меняет значение слова.",
        )
        changes.append("task 4: clarify stress in the pair отзыв/отзыв")
    elif (owner, key) == ("task", 7):
        _replace_markdown(
            blocks,
            "Ошибка находится внутри формы слова: неверны окончание, суффикс, основа или модель образования. Синтаксические связи проверяются уже в задании 8.",
            "В 2026 году задание 7 проверяет **грамматическую ошибку**, а не только "
            "ошибку в форме слова. Проверяйте образование слова, его форму и связь с соседними "
            "словами. В ответ записывайте только исправленное слово.",
        )
        old_items = [
            "Определите часть речи и начальную форму.",
            "Назовите грамматическое значение: род, падеж, число, степень, лицо или наклонение.",
            "Постройте форму по нормативной модели и проверьте словарные исключения.",
            "Запишите исправленную форму без изменения остальных слов.",
        ]
        matches = [item for item in blocks if item["type"] == "list" and item["data"].get("items") == old_items]
        if len(matches) != 1:
            raise ValueError("Task 7 algorithm has changed; refusing to overwrite it")
        matches[0]["data"]["items"] = [
            "Прочитайте выделенное слово буквально: ошибка может быть уже в образовании слова.",
            "Проверьте три зоны: словообразование, форму слова, согласование или управление.",
            "Сравните подозрительный вариант с нормой; необычная форма не всегда ошибочна.",
            "Запишите только исправленное слово в нужной форме.",
        ]
        changes.append("task 7: align algorithm with expanded 2026 format")
    elif (owner, key) == ("topic", "task-7-adjectives-pronouns"):
        matches = [item for item in blocks if item["type"] == "table" and any(
            "вокруг него (после наречия)" in cell
            for row in item["data"].get("rows", []) for cell in row.get("cells", [])
        )]
        if len(matches) != 1:
            raise ValueError("Task 7 pronoun table has changed; refusing to overwrite it")
        matches[0]["data"]["rows"] = [
            row for row in matches[0]["data"]["rows"]
            if "вокруг него (после наречия)" not in row.get("cells", [])
        ]
        changes.append("task 7: remove a correct expression from the 'incorrect' column")
    elif (owner, key) == ("topic", "legacy-theory-9"):
        matches = [item for item in blocks if item["type"] == "table" and any(
            "что слышится: *загар, горы*" in cell
            for row in item["data"].get("rows", []) for cell in row.get("cells", [])
        )]
        if len(matches) != 1:
            raise ValueError("Task 9 alternating-root table has changed; refusing to overwrite it")
        rows = matches[0]["data"]["rows"]
        for row in rows:
            cells = row.get("cells", [])
            if cells and cells[0] == "гар/гор":
                cells[2] = "а: *загар, нагар*. Запомните безударные исключения: *пригарь, выгарки*"
            elif cells and cells[0] == "зар/зор":
                cells[1] = "а: *зарница, заревать*"
                cells[2] = "а или о по произношению: *зарево, зори*. Написание *зоревать* устарело"
        changes.append("task 9: remove false root and obsolete spelling")
    elif (owner, key) == ("topic", "legacy-theory-11"):
        matches = [item for item in blocks if item["type"] == "callout" and 'цыц""' in item["data"].get("markdown", "")]
        if len(matches) != 1:
            raise ValueError("Task 9 Ц quotation has changed; refusing to overwrite it")
        matches[0]["data"]["markdown"] = matches[0]["data"]["markdown"].replace('цыц""', 'цыц"')
        changes.append("task 9: remove duplicated quotation mark")
    elif (owner, key) == ("task", 13):
        _replace_markdown(
            blocks,
            "Сначала определите часть речи. Затем проверьте сильные условия раздельного написания: **противопоставление с а**, слова **далеко не / вовсе не / отнюдь не**, отрицательные местоимения и наречия с **ни**. Только после этого ищите условие для слитного написания.",
            "Сначала определите часть речи. Для **НЕ** проверьте условия раздельного написания "
            "(*не высокий, а низкий; вовсе не высокий*), затем — слитного. "
            "**НЕ/НИ** в местоимениях и наречиях разбирайте отдельно: проверьте ударение и наличие предлога.",
        )
        changes.append("task 13: separate НЕ spelling from НЕ/НИ choice")
    elif (owner, key) == ("task", 26):
        old_items = [
            "Определите границы поиска и направление связи.",
            "Во втором предложении найдите элементы, непонятные без первого.",
            "Проверьте именно те средства, которые названы в условии.",
            "Назовите конкретное слово, форму или конструкцию и её опору.",
            "Если средств несколько, убедитесь, что выполнено всё условие.",
        ]
        matches = [item for item in blocks if item["type"] == "list" and item["data"].get("items") == old_items]
        if len(matches) != 1:
            raise ValueError("Task 26 algorithm has changed; refusing to overwrite it")
        matches[0]["data"]["items"] = [
            "Первое предложение указанного диапазона используйте только как опору: в ответ оно не входит.",
            "Читайте точную формулировку: связь с предыдущим или с предыдущими предложениями.",
            "Для каждого названного средства найдите отдельное слово в проверяемом предложении и его опору.",
            "Если названы два средства, нужны оба; лишнее средство может исключить вариант.",
            "Запишите только номер предложения, в котором обнаружена требуемая связь.",
        ]
        changes.append("task 26: clarify FIPI answer boundaries and exact evidence")
    elif (owner, key) == ("topic", "task-26-lexical"):
        _replace_table(blocks, "Родо-видовая связь", [
            ["Средство", "Как проверить"],
            ["Лексический повтор", "Одно и то же слово в той же форме: *дом — дом*"],
            ["Форма слова", "То же слово в другой форме: *дом — дому*"],
            ["Однокоренные слова", "Разные слова с общим корнем: *дом — домашний*"],
            ["Синоним", "Одинаковое или близкое значение: *метель — буран*"],
            ["Контекстный синоним", "Равнозначность возникает именно в данном тексте"],
            ["Антоним", "Слова противопоставлены по значению в контексте"],
        ])
        changes.append("task 26: remove excluded genus/species example and separate word forms")
    elif (owner, key) == ("topic", "task-26-grammar"):
        _replace_table(blocks, "Единство вида и времени", [
            ["Не засчитывается в задании 26", "Почему"],
            ["Единство вида и времени глаголов", "Общий временной план не доказывает названное средство"],
            ["Слова одной тематической группы и родо-видовая связь", "Смысловой близости недостаточно"],
            ["Синтаксический параллелизм, анафора, эпифора", "ФИПИ не учитывает эти приёмы в этой линии"],
        ])
        _replace_markdown(
            blocks,
            "**Один выбрал дорогу к реке. Другой — тропу через лес.** Во втором предложении пропущено *выбрал*: связь поддерживает неполнота и параллелизм.",
            "**Дом опустел. К дому больше никто не подходил.** *Дом — дому* — формы "
            "одного слова; именно эту пару можно назвать и проверить по условию.",
        )
        _replace_markdown(blocks, "Цепная и параллельная связь", "Чем полезны схемы связи")
        _replace_markdown(
            blocks,
            "Тип связи помогает увидеть направление, но в ответе ищите конкретное средство, названное в условии.",
            "Цепная или параллельная организация помогает читать текст, но не заменяет "
            "точное слово — средство связи из формулировки задания.",
        )
        changes.append("task 26: remove means explicitly excluded by FIPI")
    return changes


TARGETS = [
    ("topic", "topic-957e89c99be8"),
    ("topic", "task-3-styles-v2"),
    ("topic", "task-4-nouns"),
    ("task", 7),
    ("topic", "task-7-adjectives-pronouns"),
    ("topic", "legacy-theory-9"),
    ("topic", "legacy-theory-11"),
    ("task", 13),
    ("task", 26),
    ("topic", "task-26-lexical"),
    ("topic", "task-26-grammar"),
]


async def run(execute: bool) -> None:
    async with async_session_factory() as db:
        version = await db.scalar(select(CourseVersionBD).where(CourseVersionBD.is_active.is_(True)))
        if version is None:
            raise RuntimeError("No active course version")
        plans = []
        for owner, key in TARGETS:
            if owner == "task":
                entity = await db.scalar(select(ExamTaskBD).where(
                    ExamTaskBD.course_version_id == version.id, ExamTaskBD.number == key,
                ))
                document_query = select(TheoryDocumentBD).where(TheoryDocumentBD.exam_task_id == entity.id) if entity else None
            else:
                entity = await db.scalar(select(TopicBD).where(
                    TopicBD.course_version_id == version.id, TopicBD.code == key,
                ))
                document_query = select(TheoryDocumentBD).where(TheoryDocumentBD.topic_id == entity.id) if entity else None
            if document_query is None:
                raise RuntimeError(f"Missing {owner} {key!r}")
            document = await db.scalar(document_query.with_for_update())
            if document is None or document.published_version_id is None:
                raise RuntimeError(f"Missing published theory for {owner} {key!r}")
            current = await db.get(TheoryDocumentVersionBD, document.published_version_id)
            source_blocks = list((await db.scalars(select(TheoryBlockV2BD).where(
                TheoryBlockV2BD.document_version_id == current.id,
            ).order_by(TheoryBlockV2BD.sort_order, TheoryBlockV2BD.id))).all())
            if source_blocks and all(
                (block.settings or {}).get("editorialRevision") == REVISION
                for block in source_blocks
            ):
                print(f"unchanged {owner} {key}")
                continue
            blocks = [{
                "id": block.id,
                "parent_id": block.parent_block_id,
                "type": block.block_type,
                "schema_version": block.schema_version,
                "data": deepcopy(block.data),
                "original_data": deepcopy(block.data),
                "settings": deepcopy(block.settings or {}),
                "sort_order": block.sort_order,
            } for block in source_blocks]
            changes = revise(owner, key, blocks)
            if not changes:
                raise RuntimeError(f"No editorial changes defined for {owner} {key!r}")
            if (owner, key) == ("task", 7) and (
                entity.title != "Задание 7. Морфологические нормы"
                or entity.short_description != "Нормативное образование форм слов"
            ):
                raise ValueError("Task 7 catalog title changed; refusing to overwrite it")
            if (owner, key) == ("topic", "task-26-grammar") and (
                entity.title != "Грамматические и синтаксические средства"
                or entity.short_description != "Единство форм, параллелизм и неполнота"
                or document.title != "Грамматические и синтаксические средства"
            ):
                raise ValueError("Task 26 topic metadata changed; refusing to overwrite it")
            plans.append((document, current, blocks, changes, entity, (owner, key)))
            for change in changes:
                print(f"would publish: {change} (current version {current.version_number})")
        if not execute:
            print(f"Dry run: {len(plans)} documents; no records written")
            return
        for document, current, blocks, changes, entity, target in plans:
            next_number = await db.scalar(select(func.max(TheoryDocumentVersionBD.version_number)).where(
                TheoryDocumentVersionBD.document_id == document.id,
            ))
            published = TheoryDocumentVersionBD(
                document_id=document.id,
                version_number=(next_number or 0) + 1,
                status="published",
                published_at=datetime.now(timezone.utc),
            )
            db.add(published)
            await db.flush()
            cloned = {}
            for block in blocks:
                settings = {**block["settings"], "editorialRevision": REVISION}
                if block["data"] != block["original_data"]:
                    if target in (("task", 7), ("topic", "task-7-adjectives-pronouns")):
                        settings["editorialSources"] = [FIPI_GRAMMAR]
                    elif target == ("topic", "task-4-nouns"):
                        settings["editorialSources"] = [GRAMOTA_STRESS]
                    elif target == ("topic", "legacy-theory-9"):
                        settings["editorialSources"] = [GRAMOTA_ROOTS]
                    elif "task 26:" in changes[0]:
                        settings["editorialSources"] = [FIPI_TASK26]
                copy = TheoryBlockV2BD(
                    document_version_id=published.id,
                    block_type=block["type"],
                    schema_version=block["schema_version"],
                    data=block["data"],
                    settings=settings,
                    sort_order=block["sort_order"],
                )
                db.add(copy)
                await db.flush()
                cloned[block["id"]] = copy
            for block in blocks:
                if block["parent_id"] is not None:
                    cloned[block["id"]].parent_block_id = cloned[block["parent_id"]].id
            document.published_version_id = published.id
            if target == ("task", 7):
                entity.title = "Задание 7. Грамматические нормы"
                entity.short_description = "Словообразование, формы слов и грамматическая связь слов"
            elif target == ("topic", "task-26-grammar"):
                entity.title = "Что не засчитывается в задании 26"
                entity.short_description = "Отличайте общую связность текста от проверяемого средства связи"
                document.title = entity.title
            print(f"published document {document.id}: version {published.version_number}; {', '.join(changes)}")
        await db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Publish reviewed changes")
    args = parser.parse_args()
    asyncio.run(run(args.execute))


if __name__ == "__main__":
    main()
