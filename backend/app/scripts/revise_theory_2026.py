"""Safely publish narrow, source-checked corrections to the live 2026 theory.

Dry run by default. A changed target block is treated as a conflict rather than
overwriting edits made in the owner form. Earlier published versions remain in
the database for comparison and rollback.
"""

from __future__ import annotations

import argparse
import asyncio
import difflib
import json
from copy import deepcopy
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.db import async_session_factory
from app.infra.catalog.models import CourseVersionBD, ExamTaskBD, ExamTaskTopicBD, TopicBD
from app.infra.content.models import (
    TheoryBlockV2BD,
    TheoryDocumentBD,
    TheoryDocumentVersionBD,
)
from app.infra.exercises.models import ExerciseSetBD, ExerciseTopicLinkBD
from app.infra.monetization.models import AccessPolicyResourceBD


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

VISIBLE_STATUSES = frozenset({"published", "published_manual"})


async def report_cleanup(show_content: bool = False) -> None:
    """Read-only inventory before any proposal to physically delete stale topics.

    Removing a topic cascades to its theory and exercise-topic links. It can
    also cascade to exercise sets and their items, or be blocked by sessions.
    This report deliberately does not perform that deletion or restore topics.
    """
    async with async_session_factory() as db:
        active = await db.scalar(select(CourseVersionBD).where(CourseVersionBD.is_active.is_(True)))
        if active is None:
            raise RuntimeError("No active course version")
        tasks = list((await db.scalars(select(ExamTaskBD).where(
            ExamTaskBD.course_version_id == active.id
        ).order_by(ExamTaskBD.number))).all())
        topics = list((await db.scalars(select(TopicBD).where(
            TopicBD.course_version_id == active.id
        ).order_by(TopicBD.id))).all())
        task_ids = {task.id for task in tasks}
        topic_ids = {topic.id for topic in topics}
        links = list((await db.scalars(select(ExamTaskTopicBD).where(
            ExamTaskTopicBD.exam_task_id.in_(task_ids)
        ))).all())
        docs = list((await db.scalars(select(TheoryDocumentBD).where(
            (TheoryDocumentBD.exam_task_id.in_(task_ids))
            | (TheoryDocumentBD.topic_id.in_(topic_ids))
        ))).all())
        doc_by_task = {doc.exam_task_id: doc for doc in docs if doc.exam_task_id is not None}
        doc_by_topic = {doc.topic_id: doc for doc in docs if doc.topic_id is not None}
        document_ids = {doc.id for doc in docs}
        version_counts = dict((await db.execute(select(
            TheoryDocumentVersionBD.document_id, func.count(TheoryDocumentVersionBD.id)
        ).where(TheoryDocumentVersionBD.document_id.in_(document_ids))
            .group_by(TheoryDocumentVersionBD.document_id))).all())
        published_version_ids = {
            doc.published_version_id for doc in docs if doc.published_version_id is not None
        }
        block_counts = dict((await db.execute(select(
            TheoryBlockV2BD.document_version_id, func.count(TheoryBlockV2BD.id)
        ).where(TheoryBlockV2BD.document_version_id.in_(published_version_ids))
            .group_by(TheoryBlockV2BD.document_version_id))).all())
        blocks_by_version: dict[int, list[TheoryBlockV2BD]] = {}
        if show_content:
            block_rows = (await db.scalars(select(TheoryBlockV2BD).where(
                TheoryBlockV2BD.document_version_id.in_(published_version_ids)
            ).order_by(TheoryBlockV2BD.document_version_id,
                       TheoryBlockV2BD.sort_order, TheoryBlockV2BD.id))).all()
            for block in block_rows:
                blocks_by_version.setdefault(block.document_version_id, []).append(block)
        exercise_link_counts = dict((await db.execute(select(
            ExerciseTopicLinkBD.topic_id, func.count(ExerciseTopicLinkBD.exercise_id)
        ).where(ExerciseTopicLinkBD.topic_id.in_(topic_ids))
            .group_by(ExerciseTopicLinkBD.topic_id))).all())
        set_rows = list((await db.scalars(select(ExerciseSetBD).where(
            ExerciseSetBD.topic_id.in_(topic_ids)
        ).order_by(ExerciseSetBD.topic_id, ExerciseSetBD.id))).all())
        sets_by_topic: dict[int, list[ExerciseSetBD]] = {}
        for exercise_set in set_rows:
            sets_by_topic.setdefault(exercise_set.topic_id, []).append(exercise_set)
        policy_counts = dict((await db.execute(select(
            AccessPolicyResourceBD.resource_id, func.count(AccessPolicyResourceBD.id)
        ).where(
            AccessPolicyResourceBD.resource_type == "topic",
            AccessPolicyResourceBD.resource_id.in_(topic_ids),
        ).group_by(AccessPolicyResourceBD.resource_id))).all())
        topics_by_id = {topic.id: topic for topic in topics}
        links_by_task: dict[int, list[int]] = {}
        task_numbers_by_topic: dict[int, list[int]] = {}
        task_number_by_id = {task.id: task.number for task in tasks}
        for link in links:
            links_by_task.setdefault(link.exam_task_id, []).append(link.topic_id)
            task_numbers_by_topic.setdefault(link.topic_id, []).append(
                task_number_by_id[link.exam_task_id]
            )

        print(f"Активная версия курса: {active.code}")
        print("Покрытие заданий — опубликованный вводный документ и видимые темы:")
        for task in tasks:
            doc = doc_by_task.get(task.id)
            intro_blocks = block_counts.get(doc.published_version_id, 0) if doc else 0
            visible = [topic for id in links_by_task.get(task.id, [])
                       if (topic := topics_by_id.get(id)) is not None
                       and topic.status in VISIBLE_STATUSES]
            flag = "  ← НУЖНА ВИДИМАЯ ТЕМА" if not visible else ""
            print(f"  {task.number:02d}: вводных блоков {intro_blocks}, "
                  f"видимых тем {len(visible)}{flag}")
        stale = [topic for topic in topics if topic.status not in VISIBLE_STATUSES]
        status_counts: dict[str, int] = {}
        for topic in stale:
            status_counts[topic.status] = status_counts.get(topic.status, 0) + 1
        print(f"\nНевидимых тем: {len(stale)}; по статусам: {status_counts}")
        safe_count = 0
        blocked_count = 0
        for topic in stale:
            exercise_links = exercise_link_counts.get(topic.id, 0)
            exercise_sets = sets_by_topic.get(topic.id, [])
            policy_links = policy_counts.get(topic.id, 0)
            has_live_links = bool(exercise_links or exercise_sets or policy_links)
            blocked_count += int(has_live_links)
            safe_count += int(not has_live_links)
            task_numbers = sorted(set(task_numbers_by_topic.get(topic.id, [])))
            doc = doc_by_topic.get(topic.id)
            blocks = block_counts.get(doc.published_version_id, 0) if doc else 0
            same_title = sorted({candidate.id for task in tasks if task.number in task_numbers
                for id in links_by_task.get(task.id, [])
                if (candidate := topics_by_id.get(id)) is not None
                and candidate.status in VISIBLE_STATUSES
                and candidate.title.casefold().strip() == topic.title.casefold().strip()})
            if not has_live_links:
                action = "ПРЕДЛОЖЕНИЕ: удалить вместе с историей теории"
            elif len(same_title) == 1:
                action = (f"ПРЕДЛОЖЕНИЕ: проверить перенос практики на тему "
                          f"#{same_title[0]}, затем удалить старую")
            else:
                action = ("ТРЕБУЕТ РЕШЕНИЯ: новая актуальная тема либо точное "
                          "соответствие; удаление пока запрещено")
            print(f"  #{topic.id} [{topic.status}] {topic.title!r}; "
                f"задания={task_numbers}, блоков={blocks}, "
                  f"версий={version_counts.get(doc.id, 0) if doc else 0}, "
                  f"связей упражнений={exercise_links}, "
                  f"наборов={len(exercise_sets)}, политик={policy_links}; "
                  f"одноимённая видимая тема={same_title or 'нет'}; {action}")
            for exercise_set in exercise_sets:
                print(f"      набор #{exercise_set.id} {exercise_set.title!r} "
                      f"[{exercise_set.status}], задание #{exercise_set.exam_task_id}")
            if show_content and doc and doc.published_version_id:
                for block in blocks_by_version.get(doc.published_version_id, []):
                    data = json.dumps(block.data, ensure_ascii=False, sort_keys=True)
                    print(f"      блок #{block.id} {block.block_type} "
                          f"(родитель={block.parent_block_id}, порядок={block.sort_order}): {data}")
        print(f"\nИтог: {safe_count} тем без ссылок практики/доступа; "
              f"{blocked_count} тем нельзя удалять до переноса связей.")
        print("Это только предпросмотр. Темы, документы и практика не изменены.")


def _show_difference(before: dict, after: dict | None, label: str) -> None:
    old_lines = json.dumps(before, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    new_lines = (
        json.dumps(after, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
        if after is not None else []
    )
    print(f"  {label}")
    for line in difflib.unified_diff(
        old_lines, new_lines, fromfile="сейчас", tofile="после", lineterm=""
    ):
        print(f"    {line}")


def _show_plan(owner: str, key: str | int, document: TheoryDocumentBD,
               current: TheoryDocumentVersionBD, entity: ExamTaskBD | TopicBD,
               source_blocks: list[TheoryBlockV2BD], blocks: list[dict],
               changes: list[str]) -> None:
    print(f"\n=== {owner} {key!r}: {entity.title} ===")
    print(f"Документ #{document.id}, опубликованная версия {current.version_number}")
    for change in changes:
        print(f"Причина: {change}")
    updated = {block["id"]: block for block in blocks}
    altered = 0
    removed = 0
    for source in source_blocks:
        replacement = updated.get(source.id)
        if replacement is None:
            removed += 1
            _show_difference(source.data, None, f"УДАЛИТЬ блок #{source.id} ({source.block_type})")
        elif source.data != replacement["data"]:
            altered += 1
            _show_difference(
                source.data, replacement["data"],
                f"ИЗМЕНИТЬ блок #{source.id} ({source.block_type})",
            )
    if (owner, key) == ("task", 7):
        print(f"  ПЕРЕИМЕНОВАТЬ задание: {entity.title!r} → 'Задание 7. Грамматические нормы'")
        print(f"  ИЗМЕНИТЬ описание: {entity.short_description!r} → "
              "'Словообразование, формы слов и грамматическая связь слов'")
    elif (owner, key) == ("topic", "task-26-grammar"):
        print(f"  ПЕРЕИМЕНОВАТЬ тему и документ: {entity.title!r} → "
              "'Что не засчитывается в задании 26'")
        print(f"  ИЗМЕНИТЬ описание: {entity.short_description!r} → "
              "'Отличайте общую связность текста от проверяемого средства связи'")
    if not altered and not removed:
        raise RuntimeError(f"No actual block changes for {owner} {key!r}")
    print(f"Итого: изменится {altered}, удалится {removed}, "
          f"без изменений {len(source_blocks) - altered - removed} блоков")


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
            _show_plan(owner, key, document, current, entity, source_blocks, blocks, changes)
            plans.append((document, current, blocks, changes, entity, (owner, key)))
        if not execute:
            print(f"\nПредпросмотр: {len(plans)} документов. Ничего не записано и не опубликовано.")
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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true", help="Publish reviewed editorial changes")
    mode.add_argument("--cleanup-report", action="store_true", help="Audit stale topics and practice references without changing data")
    parser.add_argument("--show-content", action="store_true", help="With --cleanup-report, include current block contents of stale topics")
    args = parser.parse_args()
    if args.show_content and not args.cleanup_report:
        parser.error("--show-content requires --cleanup-report")
    if args.cleanup_report:
        asyncio.run(report_cleanup(args.show_content))
    else:
        asyncio.run(run(args.execute))


if __name__ == "__main__":
    main()
