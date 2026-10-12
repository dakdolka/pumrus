from app.scripts.curated_task9_practice import TASK9_PRACTICE_SETS


EXPECTED_TOPICS = {
    "task-9-checkable",
    "task-9-alternating",
    "task-9-dictionary",
    "task-9-root-groups",
    "task-9-e-o",
}


def test_every_task9_topic_has_200_unique_cards():
    assert {definition["topic_code"] for definition in TASK9_PRACTICE_SETS} == EXPECTED_TOPICS
    for definition in TASK9_PRACTICE_SETS:
        items = definition["items"]
        assert len(items) == 200
        assert len({item["prompt"] for item in items}) == 200
        assert all(item["answer"] and item["explanation"] for item in items)
        assert all(item["topic_code"] == definition["topic_code"] for item in items)


def test_masks_and_answers_have_matching_lengths():
    for definition in TASK9_PRACTICE_SETS:
        for item in definition["items"]:
            assert "_" in item["prompt"]
            assert len(item["prompt"]) == len(item["answer"])
