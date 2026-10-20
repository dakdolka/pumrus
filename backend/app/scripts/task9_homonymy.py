"""Additive task 9 content patch. Pure planning; no database imports or writes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.scripts.curated_theory_data import callout, table, text


REVISION = "task9-homonymy-2026-10-20-v1"
MARKER = "task9Homonymy"
TOPIC_CODE = "legacy-theory-9"
SOURCES = [
    "https://gramota.ru/uchebnik/pravila/korni-s-cheredovaniem-glasnykh-vybor-kotorykh-zavisit-ot-udareniya",
    "https://gramota.ru/uchebnik/pravila/korni-s-cheredovaniem-glasnykh-vybor-kotorykh-zavisit-ot-sleduyushchikh-za-nimi-soglasnykh",
    "https://gramota.ru/biblioteka/spravochniki/pravila-russkoy-orfografii-i-punktuatsii/bezudarnye-glasnye-v-kornyakh",
]


def section(title: str, *children: dict[str, Any]) -> dict[str, Any]:
    return {"type": "section", "data": {"title": title}, "settings": {}, "children": list(children)}


INTRO = [
    callout(
        "**Одинаковые буквы ещё не означают чередование.** Применяйте правило только тогда, "
        "когда совпадают и буквенный состав корня (с учётом чередования), и его значение. "
        "Омонимичные корни одинаково пишутся, но различаются по смыслу. "
        "Сначала определите значение, затем выбирайте правило.",
        "important",
    ),
    table(
        ["Сравните", "Как выбрать гласную"],
        ["**Загорать** — действие солнца", "Чередование **гар/гор**: без ударения пишем **о**"],
        ["**Горевать** — испытывать горе", "Проверяемая гласная: **го́ре**"],
        ["**Гористый** — связанный с горами", "Проверяемая гласная: **го́ры**"],
    ),
    text(
        "**Не только омонимия.** Похожее сочетание букв может входить в другой корень: "
        "*горизонт, ложка, роскошь*. Само по себе оно не даёт основания применять правило чередования. "
        "В таких словах ищите проверку или уточняйте написание по словарю."
    ),
]

SUFFIX = section(
    "Значения корней и омонимы: суффикс -а-",
    table(
        ["Корни", "Значение и примеры"],
        ["**кас/кос**", "Прикосновение, в том числе к теме: *касаться рукой, коснуться вопроса*. Не путайте: *коса, косой*; например, *косить — ко́сит*."],
        ["**бер/бир**", "Брать, собирать, выбирать: *забирать — заберу, собирать — соберу*."],
        ["**дер/дир**", "Драть, снимать слой; также резкое удаление: *выдирать — выдеру, удирать — удеру*."],
        ["**мер/мир**", "Умирание или неподвижность: *умирать — умереть, замирать — замереть*. Не путайте: *примерять — ме́рка, примирять — мир*."],
        ["**пер/пир**", "Закрывать, преграждать путь, опираться: *запирать — запереть, подпирать — подпереть*. Не путайте: *пир, перо*."],
        ["**тер/тир**", "Трение, стирание, растирание: *вытирать — вытереть, растирать — растереть*. Не путайте: *потерять — поте́ря*."],
        ["**блест/блист**", "Блеск, сияние, в том числе переносно: *блестеть — блистать, блистательный*."],
        ["**жег/жиг**", "Жечь, действовать огнём: *выжигать — выжег, зажигать — зажечь*."],
        ["**стел/стил**", "Расстилать по поверхности: *расстилать — расстелить*. Не путайте: *стиль, стильный*."],
        ["**чет/чит**", "Счёт: *вычитать — вычет*; соединение: *сочетать, сочетание* — исключения. Эти слова пишутся с **е**, хотя после корня есть **-а-**."],
    ),
    callout(
        "**А(я) ↔ им/ин** — ещё одно чередование перед суффиксом **-а-**: "
        "*сжать — сжимать, начать — начинать, понять — понимать, принять — принимать*. "
        "Это несколько разных корней: не ищите у всех одно общее значение. "
        "Опознавайте чередование по паре родственных слов.",
        "note",
    ),
)

CONSONANT = section(
    "Значения корней и омонимы: согласная",
    table(
        ["Корни", "Значение и примеры"],
        ["**лаг/лож**", "Класть, размещать; переносно — излагать мысль: *полагать, положить, предложение, изложение*. Не путайте с *ложь*; в слове *ложка* другой корень."],
        ["**раст/ращ/рос**", "Рост, увеличение: *растение, выращивать, заросли, возрастать*. Не путайте: *роса — ро́сы*; слово *роскошь* не относится к этой группе."],
        ["**скак/скоч**", "Прыжок, скачкообразное движение: *скакать, выскочить, подскочить*."],
    ),
    text("Для **лаг/лож** можно ориентироваться и на суффикс **-а-**: *полагать — положить*. Здесь корень оставлен в группе по следующей согласной, как в основной таблице."),
)

STRESS = section(
    "Значения корней и омонимы: ударение и плав/плов",
    table(
        ["Корни", "Значение и примеры"],
        ["**гар/гор**", "Горение, действие высокой температуры или солнца: *подгореть, загорать, нагар*. Не путайте: *горевать — го́ре, гористый — го́ры*. В *горизонте* другое буквосочетание."],
        ["**зар/зор**", "Заря, свет, озарение: *заря, зори, озарение*. Не путайте: *надзирать — надзо́р, позор*."],
        ["**клан/клон**", "Наклон, изгиб, поклон, в том числе переносно: *наклониться, кланяться, поклонение, склоняться к решению*."],
        ["**твар/твор**", "Создание: *творить, творчество, тварь*. **Утварь** — исключение из правила, а не пример омонимии."],
        ["**плав/плов**", "Плавание: *плавать, плавник, пловец*. Это особая группа: обычно **а**, **о** — в *пловец, пловчиха*, **ы** — в *плывун*. Не сводите выбор буквы к ударению."],
    ),
)

MEANING = section(
    "Как различать по смыслу: мак/мок и равн/ровн",
    table(
        ["Сравните", "Смысловое различие"],
        ["**Макать** сухарь / **промокнуть**", "**Мак** — погружать в жидкость; **мок** — становиться мокрым, пропускать или впитывать жидкость: *непромокаемый плащ, промокательная бумага*."],
        ["**Уравнять** права / **выровнять** дорожку", "**Равн** — сделать равным, одинаковым; **ровн** — сделать ровным, гладким. Сохраняйте в памяти исключения из основной таблицы."],
    ),
    callout(
        "**Порядок решения:** значение корня → наличие чередования → условие выбора буквы. "
        "Если значение другое, вернитесь к проверяемой или непроверяемой гласной.",
        "tip",
    ),
)

HEADINGS = [
    "Зависит от суффикса -а-",
    "Зависит от следующей согласной",
    "Зависит от ударения",
    "Зависит от значения",
]
GROUPS = [SUFFIX, CONSONANT, STRESS, MEANING]


def additions() -> list[dict[str, Any]]:
    return deepcopy(INTRO + GROUPS)


def plan_patch(blocks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Preserve all old blocks, parent links and settings; fail if anchors drift.

    Input/output are flat records with id, parent_id, type, data, settings,
    schema_version and sort_order. Added records have temporary string IDs.
    """
    result = deepcopy(blocks)
    by_id = {b["id"]: b for b in result}
    if len(by_id) != len(result):
        raise ValueError("Duplicate block IDs; inspect the current document")
    for block in result:
        ancestors = {block["id"]}
        parent_id = block.get("parent_id")
        while parent_id is not None:
            if parent_id not in by_id:
                raise ValueError(f"Missing parent {parent_id!r}; inspect the current nesting")
            if parent_id in ancestors:
                raise ValueError("Cyclic block nesting; inspect the current document")
            ancestors.add(parent_id)
            parent_id = by_id[parent_id].get("parent_id")
    marked = [b for b in result if b.get("settings", {}).get(MARKER) == REVISION]
    expected_count = len(INTRO) + sum(1 + len(g["children"]) for g in GROUPS)
    if marked:
        if len(marked) != expected_count:
            raise ValueError("Incomplete homonymy patch; inspect the document before retrying")
        return result, []

    def one(matches: list[dict[str, Any]], label: str) -> dict[str, Any]:
        if len(matches) != 1:
            raise ValueError(f"Expected one anchor {label!r}, found {len(matches)}")
        return matches[0]

    headings = [one([b for b in result if b["type"] == "rich_text" and b["data"].get("markdown") == h], h) for h in HEADINGS]
    parent = headings[0].get("parent_id")
    if any(b.get("parent_id") != parent for b in headings):
        raise ValueError("Group headings must share a parent; inspect the current nesting")
    siblings = sorted([b for b in result if b.get("parent_id") == parent], key=lambda b: (b["sort_order"], b["id"]))
    positions = [siblings.index(h) for h in headings]
    if positions != sorted(positions):
        raise ValueError("Unexpected group heading order")
    rule = one([b for b in siblings[:positions[0]] if b["type"] == "callout" and b["data"].get("variant") == "rule" and "чередующ" in b["data"].get("markdown", "")], "alternation rule")

    insert_before: dict[Any, list[dict[str, Any]]] = {
        headings[i + 1]["id"]: [GROUPS[i]] for i in range(3)
    }
    # Keep any practice links at the end of the topic.
    after_meaning = siblings[positions[3] + 1:]
    practice = next((b for b in after_meaning if b["type"] == "practice_link"), None)
    if practice:
        insert_before[practice["id"]] = [MEANING]

    new_records: list[dict[str, Any]] = []
    def emit(definition: dict[str, Any], parent_id: Any) -> dict[str, Any]:
        definition = deepcopy(definition)
        children = definition.pop("children", [])
        record = {
            **definition, "id": f"{REVISION}:{len(new_records)}", "parent_id": parent_id,
            "schema_version": 1, "sort_order": 0,
            "settings": {**definition.get("settings", {}), MARKER: REVISION, "sources": SOURCES},
        }
        new_records.append(record)
        for index, child in enumerate(children):
            emit(child, record["id"])["sort_order"] = index
        return record

    ordered = []
    for sibling in siblings:
        ordered.extend(emit(d, parent) for d in insert_before.get(sibling["id"], []))
        ordered.append(sibling)
        if sibling["id"] == rule["id"]:
            ordered.extend(emit(d, parent) for d in INTRO)
    if not practice:
        ordered.append(emit(MEANING, parent))
    for index, record in enumerate(ordered):
        record["sort_order"] = index
    result.extend(new_records)
    return result, ["После правила: предупреждение, сравнение трёх слов, пояснение о похожих буквосочетаниях", *[f"После группы «{h}»: {g['data']['title']}" for h, g in zip(HEADINGS, GROUPS)]]
