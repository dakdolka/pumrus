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
        if definition.get("topic_code"):
            assert len(items) == 200
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


def test_mixed_practice_is_the_union_of_all_topic_words():
    mixed = next(item for item in TASK9_PRACTICE_SETS if not item.get("topic_code"))
    topic_items = [
        item
        for definition in TASK9_PRACTICE_SETS
        if definition.get("topic_code")
        for item in definition["items"]
    ]
    expected_answers = {item["answer"].strip().casefold() for item in topic_items}
    mixed_answers = [item["answer"].strip().casefold() for item in mixed["items"]]

    assert set(mixed_answers) == expected_answers
    assert len(mixed_answers) == len(set(mixed_answers))
    assert len({item["reuse_curated_key"] for item in mixed["items"]}) == len(
        mixed["items"]
    )


def test_masks_and_answers_have_matching_lengths():
    for definition in TASK9_PRACTICE_SETS:
        for item in definition["items"]:
            assert "_" in item["prompt"]
            assert len(item["prompt"]) == len(item["answer"])
