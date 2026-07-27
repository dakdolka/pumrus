from __future__ import annotations

import re
from typing import Any


PARSER_TYPES = {"single_choice", "stress_selection", "vowel_fill", "text_input"}
VOWELS = set("аеёиоуыэюя")


def _parts(line: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(r"\s*(?:\||=>|\t)\s*", line)
    ]


def parse_exercises(raw_text: str, parser_type: str) -> dict[str, Any]:
    if parser_type not in PARSER_TYPES:
        return {"rows": [], "errors": [{"line": 0, "message": "Неизвестный формат"}]}

    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_number, source in enumerate(raw_text.splitlines(), start=1):
        line = source.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = _parts(line)
            if parser_type == "stress_selection":
                marked = parts[-1]
                positions = [
                    index
                    for index, character in enumerate(marked)
                    if character.isupper() and character.casefold() in VOWELS
                ]
                if len(positions) != 1:
                    raise ValueError("выделите одну ударную гласную заглавной буквой")
                position = positions[0]
                word = "".join(
                    character.casefold() if index == position else character
                    for index, character in enumerate(marked)
                )
                rows.append({
                    "line": line_number,
                    "source": source,
                    "prompt": word,
                    "answer": marked,
                    "correctPosition": position,
                })
            elif parser_type == "vowel_fill":
                if len(parts) >= 2:
                    mask, answer = parts[0], parts[1]
                else:
                    answer = parts[0].casefold()
                    marked_positions = {
                        index
                        for index, character in enumerate(parts[0])
                        if character.isupper() and character.casefold() in VOWELS
                    }
                    if not marked_positions:
                        raise ValueError(
                            "выделите пропущенные гласные заглавными или укажите маску | ответ"
                        )
                    mask = "".join(
                        "_" if index in marked_positions else character.casefold()
                        for index, character in enumerate(parts[0])
                    )
                if len(mask) != len(answer):
                    raise ValueError("маска и ответ должны иметь одинаковую длину")
                gaps = [index for index, character in enumerate(mask) if character in {"_", "…"}]
                if not gaps:
                    raise ValueError("в маске нет пропусков")
                if any(answer[index].casefold() not in VOWELS for index in gaps):
                    raise ValueError("в пропусках должны находиться гласные")
                rows.append({
                    "line": line_number,
                    "source": source,
                    "prompt": mask,
                    "mask": mask,
                    "answer": answer.casefold(),
                })
            else:
                if len(parts) < 2 or not parts[0] or not parts[1]:
                    raise ValueError("используйте формат «условие | ответ»")
                row = {
                    "line": line_number,
                    "source": source,
                    "prompt": parts[0],
                    "answer": parts[1],
                }
                if parser_type == "single_choice":
                    row["options"] = (
                        [value.strip() for value in parts[2].split(",") if value.strip()]
                        if len(parts) > 2
                        else []
                    )
                rows.append(row)
        except ValueError as error:
            errors.append({"line": line_number, "source": source, "message": str(error)})

    if parser_type == "single_choice" and rows:
        shared_options = sorted({
            value
            for row in rows
            for value in [row["answer"], *row.get("options", [])]
        })
        for row in rows:
            row["options"] = shared_options
    return {"rows": rows, "errors": errors}
