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
