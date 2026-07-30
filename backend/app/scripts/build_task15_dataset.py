"""Build the validated task 15 Н/НН dataset from exported source text."""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path


HEADER_RE = re.compile(
    r"Задание\s+(?P<order>\d+)\s+№\s*(?P<source_id>\d+).*?тип\s+15",
    re.IGNORECASE,
)
MARKER_RE = re.compile(r"\(([1-9])\)")


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


def requested_answer(question: str) -> str:
    instruction = question[: MARKER_RE.search(question).start()]
    if re.search(r"пишется\s+НН", instruction, re.I):
        return "НН"
    if re.search(r"(?:только\s+)?одна\s+(?:буква\s+)?Н\b", instruction, re.I):
        return "Н"
    if re.search(r"пишется\s+Н(?:[.?\s]|$)", instruction, re.I):
        return "Н"
    raise ValueError(f"Не удалось определить условие: {one_line(instruction)}")


def source_prompt(question: str) -> str:
    lines = question.splitlines()
    first = next(
        index for index, line in enumerate(lines) if MARKER_RE.search(line)
    )
    return one_line(" ".join(lines[first:]))


def sentence_for_marker(prompt: str, marker: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", prompt)
    matched = [
        sentence for sentence in sentences if f"({marker})" in sentence
    ]
    if len(matched) != 1:
        raise ValueError(
            f"Маркер ({marker}) должен находиться ровно в одном предложении"
        )
    return matched[0].strip()


def answer_digits(explanation: str) -> set[str]:
    match = re.search(r"\bОтвет:\s*([1-9]+)[^.]*\.", explanation, re.I)
    if not match:
        match = re.search(r"Правильный ответ:\s*([1-9]+)", explanation, re.I)
    if not match:
        raise ValueError("Не удалось извлечь цифровой ответ")
    return set(match.group(1))


def target_word(prompt: str) -> str:
    match = re.search(r"[А-ЯЁа-яё-]*\(Н/НН\)[А-ЯЁа-яё-]*", prompt)
    return match.group(0) if match else "выделенном слове"


def parse_source(source: str) -> list[dict[str, str | int]]:
    source = normalize(source)
    headers = list(HEADER_RE.finditer(source))
    records: list[dict[str, str | int]] = []

    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
        chunk = source[header.end() : end]
        if "Пояснение." not in chunk:
            raise ValueError(f"Задание {header['order']}: нет раздела пояснений")
        question, explanation = chunk.split("Пояснение.", 1)
        prompt = source_prompt(question)
        markers = MARKER_RE.findall(prompt)
        if not markers or len(set(markers)) != len(markers):
            raise ValueError(
                f"Задание {header['order']}: некорректные маркеры {markers}"
            )

        requested = requested_answer(question)
        opposite = "Н" if requested == "НН" else "НН"
        selected = answer_digits(explanation)
        answers = {
            marker: requested if marker in selected else opposite
            for marker in markers
        }

        for active_marker in markers:
            active_sentence = sentence_for_marker(prompt, active_marker)
            rendered = MARKER_RE.sub(
                lambda match: (
                    "(Н/НН)"
                    if match.group(1) == active_marker
                    else answers[match.group(1)].casefold()
                ),
                active_sentence,
            ).replace("|", "—")
            word = target_word(rendered)
            correct_word = word.replace("(Н/НН)", answers[active_marker].casefold())
            records.append(
                {
                    "set": int(header["order"]),
                    "source_id": int(header["source_id"]),
                    "item": int(active_marker),
                    "prompt": rendered,
                    "answer": answers[active_marker],
                    "explanation": f"Правильное написание: {correct_word}.",
                }
            )

    if len(headers) != 100 or len(records) != 408:
        raise ValueError(
            f"Ожидалось 100 заданий и 408 позиций, получено "
            f"{len(headers)} и {len(records)}"
        )
    return records


def render(records: list[dict[str, str | int]]) -> str:
    lines = [
        "# Задание 15: Н и НН",
        "# Формат: предложение | ответ | варианты | пояснение",
        "# Ответы восстановлены по условию и цифровому ключу.",
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
            f"{record['prompt']} | {record['answer']} | Н,НН | "
            f"{record['explanation']}"
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    records = parse_source(args.source.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(records), encoding="utf-8")
    print("source sets: 100")
    print(f"exercises: {len(records)}")
    print(f"single-n: {sum(record['answer'] == 'Н' for record in records)}")
    print(f"double-n: {sum(record['answer'] == 'НН' for record in records)}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
