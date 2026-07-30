from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path


HEADER_RE = re.compile(
    r"Задание\s+(?P<order>\d+)\s+№\s*(?P<source_id>\d+).*?тип\s+13",
    re.IGNORECASE,
)
ITEM_RE = re.compile(
    r"(?ms)^\s*(?P<number>[1-5])\s*[.)]\s*(?P<content>.*?)"
    r"(?=^\s*[1-5]\s*[.)]\s*|\Z)"
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = "".join(
        character
        for character in text
        if unicodedata.category(character) != "Cf"
    )
    return text.replace("\u202f", " ").replace("\xa0", " ")


def one_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def canonicalize_prompt(text: str) -> str:
    text = one_line(text).replace("|", "—")
    text = re.sub(r"\((?:HE|НE|HЕ)\)", "(НЕ)", text)
    text = re.sub(r"\bНЕ\(([А-ЯЁ-]+)\)", r"(НЕ)\1", text)
    return text


def clean_explanation(text: str) -> str:
    text = re.split(r"\s+Ответ:\s*", text, maxsplit=1)[0]
    if "—" in text:
        text = text.split("—", 1)[1]
    text = one_line(text).rstrip(".")
    text = re.sub(
        r"\s*(?:Ваш ответ|Правильный ответ|В избранное|Дополнительно).*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text.replace("|", "—").strip() + "."


def parse_source(source: str) -> list[dict[str, str | int]]:
    source = normalize(source)
    headers = list(HEADER_RE.finditer(source))
    records: list[dict[str, str | int]] = []

    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
        chunk = source[header.end() : end]
        if "Пояснение." not in chunk:
            raise ValueError(f"Задание {header['order']}: отсутствует раздел пояснений")

        question, explanation = chunk.split("Пояснение.", 1)
        question_items = dict(
            (match["number"], one_line(match["content"]))
            for match in ITEM_RE.finditer(question)
        )
        explanation_items = dict(
            (match["number"], match["content"])
            for match in ITEM_RE.finditer(explanation)
        )
        if set(question_items) != set("12345"):
            raise ValueError(
                f"Задание {header['order']}: извлечено "
                f"{len(question_items)} пунктов вместо 5"
            )

        condition_match = re.search(
            r"пишется\s+(СЛИТНО|РАЗДЕЛЬНО)",
            question,
            re.IGNORECASE,
        )
        answer_match = re.search(
            r"\bОтвет:\s*([1-5]+)[^.]*\.",
            explanation,
            re.IGNORECASE,
        )
        if not answer_match:
            answer_match = re.search(
                r"Правильный ответ:\s*([1-5]+)",
                explanation,
                re.IGNORECASE,
            )
        if not condition_match or not answer_match:
            raise ValueError(
                f"Задание {header['order']}: не удалось извлечь условие или ответ"
            )

        requested = condition_match.group(1).casefold()
        selected = set(answer_match.group(1))
        opposite = "раздельно" if requested == "слитно" else "слитно"

        for item_number in "12345":
            answer = requested if item_number in selected else opposite
            explanation_text = clean_explanation(
                explanation_items.get(item_number, "")
            )
            if not explanation_text or explanation_text == ".":
                explanation_text = (
                    f"В этом контексте написание должно быть {answer}."
                )
            records.append(
                {
                    "set": int(header["order"]),
                    "source_id": int(header["source_id"]),
                    "item": int(item_number),
                    "prompt": canonicalize_prompt(question_items[item_number]),
                    "answer": answer,
                    "explanation": explanation_text,
                }
            )

    if len(headers) != 84 or len(records) != 420:
        raise ValueError(
            f"Ожидалось 84 задания и 420 пунктов, получено "
            f"{len(headers)} и {len(records)}"
        )
    return records


def render(records: list[dict[str, str | int]]) -> str:
    lines = [
        "# Задание 13: НЕ/НИ со словами",
        "# Формат: предложение | ответ | варианты | пояснение",
        "# Ответы восстановлены по условию и официальному цифровому ответу каждого комплекта.",
        "",
    ]
    current_set = None
    for record in records:
        if record["set"] != current_set:
            current_set = record["set"]
            lines.extend(
                [
                    "",
                    f"# Комплект {record['set']}; источник № {record['source_id']}",
                ]
            )
        lines.append(
            f"{record['prompt']} | {record['answer']} | "
            f"слитно,раздельно | {record['explanation']}"
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a validated bulk-import TXT for EGE task 13."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    records = parse_source(args.source.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(records), encoding="utf-8")

    joined = sum(record["answer"] == "слитно" for record in records)
    separate = len(records) - joined
    print(f"sets: 84")
    print(f"exercises: {len(records)}")
    print(f"joined: {joined}")
    print(f"separate: {separate}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
