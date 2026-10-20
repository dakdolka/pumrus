"""Prepare reviewable edit packages from live exports; never connect to/write a DB.

Usage: python -m app.scripts.split_task9_suffix_rules EXPORT_DIRECTORY OUTPUT_DIRECTORY
Input: topic-{9,10,17,18,19,20}-live-export.json (API responses with `package`).
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

from app.api.v2.theory_edit import TheoryEditPackage, check_base, flatten_page

SOURCES = {
    "i-y": "https://gramota.ru/uchebnik/pravila/bukvy-y-i-i-posle-ts%20",
    "o-yo": "https://gramota.ru/biblioteka/spravochniki/pravila-russkoy-orfografii-i-punktuatsii/bukvy-o-e-e-posle-shipyashchikh",
}


def block(kind, data, *, anchor=None, children=None, source=None):
    settings = {"editorialRevision": "task9-task11-root-suffix-split-v1"}
    if anchor:
        settings["anchor"] = anchor
    if source:
        settings["sources"] = [SOURCES[source]]
    node = {"type": kind, "data": data, "settings": settings}
    if children:
        node["children"] = children
    return node


def note(text, variant="rule", **kwargs):
    return block("callout", {"variant": variant, "markdown": text}, **kwargs)


def table(rows):
    return block("table", {"rows": [{"cells": row} for row in rows]})


def link(task, topic, text, label, anchor):
    return block("theory_link", {"taskNumber": task, "topicId": topic, "anchor": anchor, "markdown": text, "buttonLabel": label})


def section(title, anchor, children, source):
    return block("section", {"title": title}, anchor=anchor, children=children, source=source)


def insert_before_practice(page, additions):
    position = next((i for i, b in enumerate(page["blocks"]) if b["type"] == "practice_link"), len(page["blocks"]))
    page["blocks"][position:position] = additions


def prepare_packages(exports: dict[int, dict]) -> dict[int, dict]:
    packages = {topic: deepcopy(value["package"]) for topic, value in exports.items()}
    if set(packages) != {9, 10, 17, 18, 19, 20}:
        raise ValueError("Нужны актуальные экспорты шести тем: 9, 10, 17, 18, 19, 20")
    pages = {topic: value["after"] for topic, value in packages.items()}

    # Existing IDs/metadata survive; only the explicitly identified mixed content changes.
    page = pages[9]
    page["title"] = page["ownerTitle"] = "И/Ы после Ц в корне"
    page["description"] = "И в корне после Ц и слова-исключения с Ы"
    original_table = next(b for b in page["blocks"] if b["type"] == "table" and any(row["cells"][0] == "Корень" for row in b["data"]["rows"]))
    original_table["data"]["rows"] = [
        {"cells": ["Написание в корне", "Примеры"]},
        {"cells": ["Обычно **И**", "цирк, цифра, цитата, цилиндр, панцирь"]},
    ]
    warning = next(b for b in page["blocks"] if b["type"] == "callout" and "Исключения в корне" in b["data"].get("markdown", ""))
    warning["data"]["markdown"] = '**Исключения с Ы:** *цыган на цыпочках подошёл к цыплёнку и цыкнул: «Цыц!»*\n\nСохраняйте **ы** в однокоренных словах: *цыганский, цыплячий, цыкать*. Также запомните *цыркать* и производные.'
    example = next(b for b in page["blocks"] if b["type"] == "example" and "куцый" in b["data"].get("markdown", ""))
    example["data"]["markdown"] = "**Цирковой** — гласная в корне **-цирк-**, пишем **и**. **Цыганский** — корень **-цыган-** относится к исключениям, пишем **ы**. Сначала определите границы корня."
    page["blocks"].insert(0, note("В **корне** после **ц** обычно пишется **и**. Написание **ы** в словах-исключениях нужно запомнить вместе с однокоренными словами.", anchor="i-y-root", source="i-y"))
    page["blocks"].extend([
        link(11, 19, "**Продолжим правило в суффиксах.** Суффикс принадлежности **-ын-** после Ц разбираем в задании 11.", "И/Ы в суффиксах прилагательных", "i-y-suffix"),
        link(11, 17, "В глагольном суффиксе **-ыва-** после Ц также пишется **ы**. Это отдельная суффиксальная орфограмма.", "И/Ы в суффиксах глаголов", "i-y-verb-suffix"),
    ])

    page = pages[10]
    page["blocks"][0].setdefault("settings", {})["anchor"] = "o-yo-root"
    for b in page["blocks"]:
        if b["type"] == "table":
            for row in b["data"].get("rows", []):
                row["cells"] = ["шомпол" if cell == "трущоба" else cell for cell in row["cells"]]
        if b["type"] == "callout" and b["data"].get("variant") == "tip":
            b["data"]["markdown"] = b["data"]["markdown"].replace("трещ**о**тка, ", "").replace("трущ**о**ба, ", "")
    page["blocks"].extend([
        link(11, 20, "**Продолжим тему за пределами корня.** О/Е/Ё в суффиксах существительных выбираются по другим условиям. Здесь же — *трещотка* и *трущоба*.", "О/Е/Ё в суффиксах существительных", "o-e-yo-noun-suffix"),
        link(11, 19, "В прилагательных важно различать суффиксы отыменных и отглагольных образований.", "О/Е/Ё в суффиксах прилагательных", "o-e-yo-adjective-suffix"),
        link(11, 18, "Для наречий на **-о/-е** после шипящих действует правило ударения.", "О/Е в суффиксах наречий", "o-e-adverb-suffix"),
    ])

    page = pages[19]
    page["description"] += "; И/Ы после Ц и О/Е/Ё после шипящих в суффиксах"
    insert_before_practice(page, [
        section("И/Ы после Ц в суффиксе прилагательных", "i-y-suffix", [
            note("В притяжательном суффиксе **-ын-** после **ц** пишется **ы**: *сестрицын, лисицын, синицын*. Суффикс обозначает принадлежность: *сестрицын платок* — платок сестрицы.", source="i-y"),
            block("example", {"markdown": "**Сестриц-ын**: **ы** входит в суффикс **-ын-**, а не в корень. Правило «в корне после Ц обычно И» здесь не применяется."}),
            note("Не смешивайте суффикс и окончание: *сестрицын* — **-ын-** суффикс; *куцый, улицы, бойцы* — **ы** в окончании. В окончаниях после Ц пишется **ы**; это отдельная орфограмма, не суффикс задания 11.", "important"),
        ], "i-y"),
        section("О/Е/Ё после шипящих в суффиксах прилагательных", "o-e-yo-adjective-suffix", [
            note("В суффиксах **отыменных прилагательных** после шипящих под ударением пишется **о**, без ударения — **е**. Сначала убедитесь, что гласная находится в суффиксе.", source="o-yo"),
            table([["Под ударением — О", "Без ударения — Е"], ["ежо́вый, парчо́вый, холщо́вый", "гру́шевый, плю́шевый, плащево́й"]]),
            note("В **отглагольных прилагательных** с ударным суффиксом **-ён-** пишется **ё**: *жжёный, печёный, тушёный*. Буква **ё** также пишется в ударном суффиксе страдательных причастий **-ённ-/-ён-**: *решённый, решён*. Правило «под ударением О» на эти суффиксы не переносится.", "important", source="o-yo"),
            block("example", {"markdown": "**Парчо́вый** — от существительного *парча*, суффикс **-ов-**. **Тушёный** — от глагола *тушить*, суффикс **-ён-**. Одинаковое ударение не означает одинаковое правило."}),
        ], "o-yo"),
    ])
    page["blocks"].extend([
        link(9, 9, "**Другая часть правила И/Ы:** выбор буквы после Ц в корне и корневые исключения.", "И/Ы после Ц в корне · задание 9", "i-y-root"),
        link(9, 10, "**Другая часть правила О/Ё:** чередование с Е и словарные написания в корне.", "О/Ё в корне · задание 9", "o-yo-root"),
    ])

    page = pages[20]
    page["description"] += "; О/Е/Ё после шипящих в суффиксах"
    insert_before_practice(page, [section("О/Е/Ё после шипящих в суффиксах существительных", "o-e-yo-noun-suffix", [
        note("После шипящих в суффиксах **-ок-, -онок-, -онк-** под ударением пишется **о**: *пирожо́к, медвежо́нок, девчо́нка*. В безударных суффиксах **-ек-, -еньк-** пишется **е**: *оре́шек, ре́ченька*. Проверяйте ударение именно на гласной суффикса. Случаи с **ё** рассмотрим отдельно ниже.", source="o-yo"),
        table([["Суффикс с О после шипящей", "Примеры"], ["-ок-, -онок-, -онк-", "крючо́к, медвежо́нок, рубашо́нка"], ["-овк- в отыменных существительных", "речо́вка, плащо́вка, грушо́вка, ножо́вка"], ["-отк-", "трещо́тка"], ["-об- (в академическом правиле)", "чащо́ба, трущо́ба"]]),
        note("**Трещотка** относится к правилу о суффиксе **-отк-**, а не к корневым исключениям. *Чащоба, трущоба* в академическом правиле приводятся с **-об-**; морфемный разбор *трущобы* может различаться в словарях. Написание **о** сохраняется.", "note"),
        note("Не заменяйте **ё** на **о** в отглагольных существительных: *ночёвка* ← *ночевать*, *корчёвка* ← *корчевать*. В словах *тушёнка, сгущёнка* сохраняется **ё** производящих форм *тушёный, сгущённый*. Суффикс **-ёр-** также пишется с **ё**: *дирижёр, стажёр*.", "important", source="o-yo"),
        block("example", {"markdown": "**Речовка** ← *речевой*: отыменное образование, **о** в суффиксальной части. **Ночёвка** ← *ночевать*: отглагольное образование, **ё**. **Бечёвка** ← *бечева*: **ё** находится в корне, поэтому это материал задания 9."}),
    ], "o-yo")])
    page["blocks"].extend([
        link(9, 10, "**Вернуться к первой части темы:** О/Ё после шипящих в корне. Там другой способ выбора буквы.", "О/Ё в корне · задание 9", "o-yo-root"),
        link(11, 19, "**Продолжить тему:** выбор О/Е/Ё в суффиксах прилагательных.", "Суффиксы прилагательных · задание 11", "o-e-yo-adjective-suffix"),
    ])

    page = pages[17]
    insert_before_practice(page, [section("И/Ы после Ц в глагольном суффиксе", "i-y-verb-suffix", [
        note("В суффиксе **-ыва-** после **ц** пишется **ы**: *поклацывать, побряцывать*. Это суффикс, поэтому правило о букве И в корне после Ц не применяется.", source="i-y"),
        block("example", {"markdown": "*Побряц-ыва-ть*: **ы** входит в суффикс **-ыва-**. Выбор **-ова-/-ева-** или **-ыва-/-ива-** проверяйте по форме **я**, как показано выше."}),
    ], "i-y")])
    page["blocks"].append(link(9, 9, "**Первая часть правила:** И/Ы после Ц в корне и слова-исключения.", "И/Ы в корне · задание 9", "i-y-root"))

    page = pages[18]
    # The rule is already present: mark and link it, without duplicating it.
    page["blocks"][0].setdefault("settings", {})["anchor"] = "o-e-adverb-suffix"
    page["blocks"].extend([
        link(9, 10, "**Не смешивайте корень и суффикс:** О/Ё в корне разбираем в задании 9.", "О/Ё в корне · задание 9", "o-yo-root"),
        link(11, 20, "**Продолжить тему:** О/Е/Ё в суффиксах существительных, включая отглагольные образования.", "Суффиксы существительных · задание 11", "o-e-yo-noun-suffix"),
    ])

    for topic, package in packages.items():
        parsed = TheoryEditPackage.model_validate(package)
        check_base(parsed, package["base"]["documentId"], package["base"]["publishedVersionId"], exports[topic]["package"]["before"])
        flatten_page(parsed.after)
        if package["base"] != exports[topic]["package"]["base"] or package["before"] != exports[topic]["package"]["before"]:
            raise ValueError("Исходная выгрузка была изменена")
    return packages


FILENAMES = {
    9: "task9-i-y-roots.json", 10: "task9-o-yo-roots.json",
    17: "task11-verb-suffixes.json", 18: "task11-adverb-suffixes.json",
    19: "task11-adjective-suffixes.json", 20: "task11-noun-suffixes.json",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    exports = {topic: json.loads((args.export_directory / f"topic-{topic}-live-export.json").read_text(encoding="utf-8-sig")) for topic in FILENAMES}
    packages = prepare_packages(exports)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    for topic, package in packages.items():
        target = args.output_directory / FILENAMES[topic]
        target.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{target.name}: document {package['base']['documentId']}, version {package['base']['publishedVersionId']}")


if __name__ == "__main__":
    main()
