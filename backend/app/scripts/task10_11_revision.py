"""Reviewable task 10/11 bank packages based on a live practice export."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.scripts.curated_task10_11_practice import FIPI, GRAMOTA_SUFFIX, REVISION, reviewed_cards

EVIDENCE = Path(__file__).with_name("data") / "task10_11_dictionary_evidence.json"


def stable(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(stable(value).encode()).hexdigest()


def snapshot(export: dict, task_numbers=(10, 11)) -> dict:
    catalog = export["catalog"]
    tasks = [task for task in catalog["tasks"] if task["number"] in task_numbers]
    task_ids = {task["id"] for task in tasks}
    topic_ids = {link["topicId"] for link in catalog["taskTopicLinks"] if link["taskId"] in task_ids}
    source = export["practice"]
    sets = [s for s in source["exerciseSets"] if s["taskId"] in task_ids]
    set_ids = {s["id"] for s in sets}
    memberships = [item for item in source["exerciseSetItems"] if item["exerciseSetId"] in set_ids]
    exercise_ids = {item["exerciseId"] for item in memberships} | {link["exerciseId"] for link in source["exerciseTaskLinks"] if link["taskId"] in task_ids}
    exercises = [item for item in source["exercises"] if item["id"] in exercise_ids]
    version_ids = {item["publishedVersionId"] for item in exercises}

    def clean(items):
        # Ignore export timestamps, but include all content, IDs and configuration.
        return sorted([{key: value for key, value in item.items() if key not in {"createdAt", "updatedAt", "publishedAt"}} for item in items], key=stable)

    return {
        "tasks": clean(tasks),
        "topics": clean([topic for topic in catalog["topics"] if topic["id"] in topic_ids]),
        "taskTopicLinks": clean([link for link in catalog["taskTopicLinks"] if link["taskId"] in task_ids]),
        "sets": clean(sets), "memberships": clean(memberships), "exercises": clean(exercises),
        "versions": clean([item for item in source["exerciseVersions"] if item["id"] in version_ids]),
        "taskLinks": clean([item for item in source["exerciseTaskLinks"] if item["exerciseId"] in exercise_ids]),
        "topicLinks": clean([item for item in source["exerciseTopicLinks"] if item["exerciseId"] in exercise_ids]),
    }


def word_key(word: str) -> str:
    return word.casefold().replace("ё", "е").strip()


def legacy_lexeme(version: dict) -> str:
    prompt = str(version.get("promptData", {}).get("content") or "")
    answer = str(version.get("feedbackData", {}).get("correctAnswer") or "")
    if not answer:
        answer = next(iter(version.get("answerConfig", {}).get("acceptedAnswers", [])), "")
    index = prompt.find("_")
    if index >= 0 and len(prompt) == len(answer):
        for match in re.finditer(r"[а-яёА-ЯЁ]+(?:-[а-яёА-ЯЁ]+)*", answer):
            if match.start() <= index < match.end():
                return word_key(match.group())
    return word_key(answer)


def validate_card(card: dict) -> None:
    required = {"lexeme", "answer", "prompt", "explanation", "curated_key", "rule_id", "source_references", "dictionary_evidence", "task_number", "topic_code", "is_exception", "type"}
    if not isinstance(card, dict) or set(card) != required:
        raise ValueError("Неизвестные или пропущенные поля карточки")
    if card["task_number"] not in {10, 11} or card["type"] != "vowel_fill":
        raise ValueError("Этот пакет поддерживает буквенные тренажёры заданий 10 и 11")
    if not all(isinstance(card[key], str) and card[key].strip() for key in ["lexeme", "answer", "prompt", "explanation", "curated_key", "rule_id", "topic_code"]):
        raise ValueError("У карточки должны быть слово, маска, ответ и непустое объяснение")
    prompt, answer = card["prompt"], card["answer"]
    if len(prompt) != len(answer) or "_" not in prompt or any(a != b for a, b in zip(prompt, answer) if a != "_"):
        raise ValueError(f"Маска не соответствует ответу: {prompt}")
    if not re.fullmatch(r"[а-яё]+(?:-[а-яё]+)*", card["lexeme"]) or card["lexeme"] not in answer:
        raise ValueError("Проверяемое слово должно входить в ответ")
    gaps = [i for i, c in enumerate(prompt) if c == "_"]
    occurrences = list(re.finditer(r"(?<![а-яё])" + re.escape(card["lexeme"]) + r"(?![а-яё])", answer))
    if not any(all(match.start() <= i < match.end() for i in gaps) for match in occurrences):
        raise ValueError("Все пропуски должны находиться внутри подтверждённого слова")
    if any(answer[i] not in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя" for i, c in enumerate(prompt) if c == "_"):
        raise ValueError("В пропуске должна быть русская буква")
    record = card["dictionary_evidence"]
    if not isinstance(record, dict) or not isinstance(card["source_references"], list) or not isinstance(card["is_exception"], bool):
        raise ValueError("Проверьте структуру источников и признака исключения")
    if record.get("status") != "verified" or card["lexeme"] not in record.get("headwords", []) or not re.fullmatch(r"[0-9a-f]{64}", record.get("responseSha256", "")):
        raise ValueError(f"Нет подтверждённого словарного написания: {card['lexeme']}")
    from urllib.parse import parse_qs, urlparse
    for reference in card["source_references"]:
        if not isinstance(reference, str) or urlparse(reference).scheme != "https" or urlparse(reference).netloc not in {"orfo.ruslang.ru", "doc.fipi.ru", "gramota.ru"}:
            raise ValueError("Используйте ссылки на проверенные источники: РАН, ФИПИ, Грамота.ру")
    url = urlparse(record.get("url", ""))
    dictionary_match = url.scheme == "https" and url.netloc == "orfo.ruslang.ru" and url.path == "/search/word" and parse_qs(url.query).get("query") == [card["lexeme"]]
    fipi_match = record.get("verificationMethod") == "official_example" and record["url"].split("#")[0] == FIPI and re.fullmatch(r"page=(?:[1-9]|1[0-4])", url.fragment)
    gramota_match = record.get("verificationMethod") == "official_rule_example" and record.get("url") == GRAMOTA_SUFFIX and card["lexeme"] == "асфальтщик"
    if not (dictionary_match or fipi_match or gramota_match):
        raise ValueError("Словарная ссылка должна вести на поиск именно этого слова в Академосе")
    if record["url"] not in card["source_references"]:
        raise ValueError("Добавьте ссылку на словарное подтверждение в источники карточки")


def validate_package(package: dict) -> None:
    if set(package) != {"format", "schemaVersion", "revision", "base", "before", "after"} or package["format"] != "pumrus.practice-edit" or package["schemaVersion"] != 1:
        raise ValueError("Ожидается pumrus.practice-edit, schemaVersion 1")
    if not isinstance(package["base"], dict) or not isinstance(package["before"], dict) or not isinstance(package["after"], dict) or set(package["after"]) != {"topics"} or not isinstance(package["after"]["topics"], list):
        raise ValueError("Ожидаются base, before и after.topics")
    if package["base"].get("fingerprint") != digest(package["before"]):
        raise ValueError("Исходный раздел before изменён. Редактируйте только after")
    task_by_id = {task["id"]: task["number"] for task in package["before"]["tasks"]}
    if set(task_by_id.values()) != {10, 11} or package["base"].get("taskNumbers") != [10, 11]:
        raise ValueError("Пакет должен содержать только задания 10 и 11")
    expected = {(task_by_id[link["taskId"]], link["topicId"]) for link in package["before"]["taskTopicLinks"]}
    topics_by_id = {topic["id"]: topic for topic in package["before"]["topics"]}
    actual = set()
    keys = set()
    for topic in package["after"]["topics"]:
        if not isinstance(topic, dict) or set(topic) != {"taskNumber", "topicId", "topicCode", "title", "cards"} or not isinstance(topic["cards"], list):
            raise ValueError("Тема должна содержать taskNumber, topicId, topicCode, title и cards")
        pair = (topic["taskNumber"], topic["topicId"])
        if pair not in expected or pair in actual or topics_by_id[topic["topicId"]]["code"] != topic["topicCode"]:
            raise ValueError("Тема не соответствует актуальному каталогу либо повторяется")
        actual.add(pair)
        if not topic["cards"]:
            raise ValueError("Не публикуйте пустую тему")
        words, prompts = set(), set()
        for card in topic["cards"]:
            validate_card(card)
            if card["task_number"] != pair[0] or card["topic_code"] != topic["topicCode"]:
                raise ValueError("Карточка привязана к другой теме")
            word = word_key(card["lexeme"])
            if word in words or card["prompt"] in prompts or card["curated_key"] in keys:
                raise ValueError("Внутри темы повторяется слово, маска или ключ карточки")
            words.add(word); prompts.add(card["prompt"]); keys.add(card["curated_key"])
            if len(keys) > 5000:
                raise ValueError("В пакете допускается не более 5000 карточек")
    if actual != expected:
        raise ValueError("В пакете должны быть все темы выбранных заданий")


def make_package(export: dict, evidence: dict) -> dict:
    before = snapshot(export)
    cards_by_topic = defaultdict(list)
    for card in reviewed_cards(evidence):
        cards_by_topic[card["topic_code"]].append(card)
    tasks = {task["id"]: task for task in before["tasks"]}
    topic_tasks = {link["topicId"]: tasks[link["taskId"]]["number"] for link in before["taskTopicLinks"]}
    topics = [{"taskNumber": topic_tasks[topic["id"]], "topicId": topic["id"], "topicCode": topic["code"], "title": topic["title"], "cards": cards_by_topic[topic["code"]]} for topic in before["topics"]]
    package = {"format": "pumrus.practice-edit", "schemaVersion": 1, "revision": REVISION,
               "base": {"taskNumbers": [10, 11], "fingerprint": digest(before)}, "before": before,
               "after": {"topics": sorted(topics, key=lambda topic: (topic["taskNumber"], topic["title"]))}}
    validate_package(package)
    return package


def summary(package: dict) -> dict:
    before = package["before"]
    versions = {item["id"]: item for item in before["versions"]}
    old = [versions[e["publishedVersionId"]] for e in before["exercises"]]
    after = package["after"]["topics"]
    return {
        "before": {"exercises": len(old), "withoutExplanation": sum(not row.get("feedbackData", {}).get("correct") for row in old)},
        "after": {"exercises": sum(len(topic["cards"]) for topic in after), "withoutExplanation": 0,
                  "topics": [{"taskNumber": topic["taskNumber"], "title": topic["title"], "cards": len(topic["cards"])} for topic in after],
                  "mixedUniqueWords": {str(number): len({word_key(c["lexeme"]) for topic in after if topic["taskNumber"] == number for c in topic["cards"]}) for number in [10, 11]}},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    args = parser.parse_args()
    package = make_package(json.loads(args.export.read_text(encoding="utf-8-sig")), json.loads(args.evidence.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary(package), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
