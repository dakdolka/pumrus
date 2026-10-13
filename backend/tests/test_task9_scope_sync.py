from types import SimpleNamespace

from app.scripts.practice_scope_sync import (
    _unique_word_exercise_ids,
    infer_topic_code,
)
from app.scripts.publish_practice_expansion import _payload
from app.scripts.curated_task9_practice import TASK9_PRACTICE_SETS


def _version(
    prompt: str,
    answer: str,
    *,
    explanation: str = "",
    curated_key: str | None = None,
):
    return SimpleNamespace(
        prompt_data={"content": prompt},
        feedback_data={"correctAnswer": answer, "correct": explanation},
        answer_config={"acceptedAnswers": [answer]},
        checker_config={"curatedKey": curated_key} if curated_key else {},
    )


def test_task9_legacy_words_are_routed_conservatively():
    assert infer_topic_code(9, _version("ц_рк", "цирк")) == "legacy-theory-11"
    assert infer_topic_code(9, _version("ш_пот", "шёпот")) == "legacy-theory-12"
    assert infer_topic_code(9, _version("пол_гать", "полагать")) == "legacy-theory-9"
    assert infer_topic_code(
        9,
        _version("к_мпания", "кампания", explanation="Словарное написание."),
    ) == "legacy-theory-10"
    assert infer_topic_code(
        9,
        _version("в_дяной", "водяной", explanation="Проверочное слово: воды."),
    ) is None


def test_task9_mixed_scope_keeps_one_exercise_per_word_and_prefers_curated():
    versions = {
        10: _version("ш_пот", "шёпот"),
        20: _version(
            "ш_пот",
            "шёпот",
            curated_key="task9-o-yo-after-sibilants-200:001",
        ),
        30: _version("ж_лтый", "жёлтый"),
    }

    assert _unique_word_exercise_ids(set(versions), versions) == {20, 30}


def test_task9_payload_publishes_exception_marker_and_both_explanations():
    for definition in TASK9_PRACTICE_SETS:
        for index, item in enumerate(definition["items"], start=1):
            if item.get("reuse_curated_key"):
                continue
            payload = _payload(item, f"{definition['code']}:{index:03d}")
            assert payload["checker_config"]["isException"] is bool(
                item.get("is_exception", False)
            )
            assert payload["feedback_data"]["correct"] == item["explanation"]
            assert payload["feedback_data"]["incorrect"] == item["explanation"]
