from app.scripts.curated_task9_practice import TASK9_PRACTICE_SETS


EXPECTED_TOPICS = {
    "legacy-theory-9",
    "legacy-theory-10",
    "legacy-theory-11",
    "legacy-theory-12",
}


def test_every_task9_topic_has_unique_cards_without_prompt_boilerplate():
    topic_sets = [item for item in TASK9_PRACTICE_SETS if item.get("topic_code")]
    assert {definition["topic_code"] for definition in topic_sets} == EXPECTED_TOPICS
    assert len(TASK9_PRACTICE_SETS) == 5
    for definition in TASK9_PRACTICE_SETS:
        items = definition["items"]
        assert len({item["prompt"] for item in items}) == len(items)
        assert all(item["answer"] and item["explanation"] for item in items)
        assert all(
            not item["prompt"].startswith((
                "Вставьте букву:",
                "Проверьте написание:",
                "Запишите правильно:",
                "Орфографическая разминка",
                "Заполните пропуск",
            ))
            for item in items
        )
        if definition.get("topic_code"):
            assert all(item["topic_code"] == definition["topic_code"] for item in items)


def test_mixed_practice_is_balanced_across_all_topics():
    mixed = next(item for item in TASK9_PRACTICE_SETS if not item.get("topic_code"))
    assert {
        code: sum(item["topic_code"] == code for item in mixed["items"])
        for code in EXPECTED_TOPICS
    } == {code: 50 for code in EXPECTED_TOPICS}
    assert len({item["reuse_curated_key"] for item in mixed["items"]}) == 200


def test_masks_and_answers_have_matching_lengths():
    for definition in TASK9_PRACTICE_SETS:
        for item in definition["items"]:
            assert "_" in item["prompt"]
            assert len(item["prompt"]) == len(item["answer"])
