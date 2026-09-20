import json
from pathlib import Path

import main


def test_save_and_load_prompt_round_trip(tmp_path):
    file_path = tmp_path / "prompt.txt"
    positive = "positive prompt text"
    negative = "negative prompt text"

    main.save_prompt_to_file(file_path, positive, negative)
    loaded_positive, loaded_negative = main.load_prompt_from_file(file_path)

    assert loaded_positive == positive
    assert loaded_negative == negative


def test_load_prompt_from_file_handles_missing_negative(tmp_path):
    file_path = tmp_path / "prompt_only.txt"
    file_path.write_text("only positive text\n", encoding="utf-8")

    loaded_positive, loaded_negative = main.load_prompt_from_file(file_path)

    assert loaded_positive == "only positive text"
    assert loaded_negative == "-"


def test_load_checksum_state_from_settings_recovers_stored_checksum(tmp_path):
    settings_path = tmp_path / "prompt_settings.json"
    state = {
        "mode": "subject",
        "seed": "42",
        "person_count": "solo",
        "nsfw": False,
        "custom_tags": "test tag",
    }
    checksum = main.compute_prompt_checksum(state)
    settings_path.write_text(
        json.dumps({"checksum_store": {checksum: state}}, ensure_ascii=False),
        encoding="utf-8",
    )

    loaded_state = main.load_checksum_state_from_settings(settings_path, checksum)

    assert loaded_state == state
