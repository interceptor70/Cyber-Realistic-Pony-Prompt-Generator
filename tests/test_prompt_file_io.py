import json
from pathlib import Path
from types import SimpleNamespace

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


def test_compose_negative_prompt_appends_watermark_blockers_after_feral_tags():
    negative = main.compose_negative_prompt("blurry, low quality", main.FERAL_NEGATIVE_TAGS)

    assert "blurry" in negative
    assert "human" in negative
    assert negative.endswith(", ".join(main.NEGATIVE_WATERMARK_BLOCKERS))


def test_generate_master_always_includes_watermark_blockers():
    node = main.CR_Pony_Master()
    _, negative = node.generate_master(
        seed=42,
        rating="rating_safe",
        location="luxury penthouse",
        lighting="cinematic lighting",
        camera="85mm portrait lens",
        use_break=True,
        nsfw_mode=False,
        score_scheme="default high",
        source_bias="None",
        strong_anime_bias=False,
        style_preset="None",
        subject_1="1girl",
        photo_boost=False,
    )

    assert negative.endswith(", ".join(main.NEGATIVE_WATERMARK_BLOCKERS))


def test_should_auto_enable_canvas_detail_only_for_non_ignored_values():
    assert main.should_auto_enable_canvas_detail("female") is True
    assert main.should_auto_enable_canvas_detail("feral female") is True
    assert main.should_auto_enable_canvas_detail("None") is False
    assert main.should_auto_enable_canvas_detail("Random") is False
    assert main.should_auto_enable_canvas_detail("") is False


def test_filter_blocked_canvas_character_tags_removes_scene_values():
    filtered_tags = main.filter_blocked_canvas_character_tags(
        ["female", "jungle temple ruins", "volumetric lighting", "anthro"],
        ["jungle temple ruins", "volumetric lighting"],
    )

    assert filtered_tags == ["female", "anthro"]


def test_sanitize_gui_text_replaces_bad_ti_character():
    assert main.sanitize_gui_text("lighƟng and cinemaƟc") == "lighting and cinematic"


def test_get_neutral_reset_value_prefers_none_over_random():
    assert main.get_neutral_reset_value(["Random", "None", "female"], "female") == "None"


def test_get_neutral_reset_value_uses_random_when_none_is_missing():
    assert main.get_neutral_reset_value(["female", "Random", "male"], "female") == "Random"


def test_get_neutral_reset_value_falls_back_when_neutral_values_are_missing():
    assert main.get_neutral_reset_value(["female", "male"], "female") == "female"


def test_compose_canvas_positive_prompt_uses_fixed_quality_prefix_and_weighted_bracket():
    result = main.compose_canvas_positive_prompt(
        ["female", "anthro", "striped fur", "panther anatomy"],
        "1.15",
    )

    assert result == "score_9, score_8_up, score_7_up, rating_explicit, source_photography, raw photo, hyperrealistic, (female, anthro, striped fur, panther anatomy:1.15)"


def test_update_canvas_prompts_builds_fixed_prefix_and_filters_scene_values():
    class DummyText:
        def __init__(self):
            self.value = ""

        def delete(self, *args):
            self.value = ""

        def insert(self, *args):
            self.value = args[-1]

        def get(self, *args):
            return self.value

    class DummyNode:
        def generate_master(self, **_kwargs):
            return "-", "negative prompt"

    fake = SimpleNamespace()
    fake.field_widgets = {
        "gender": SimpleNamespace(value="female"),
        "body_type": SimpleNamespace(value="anthro"),
        "special_skin_type": SimpleNamespace(value="striped fur"),
    }
    fake.canvas_include_options = [
        ("gender", "Gender"),
        ("body_type", "Body Type"),
        ("special_skin_type", "Special Skin Type"),
    ]
    fake.canvas_include_vars = {key: SimpleNamespace(get=lambda: True) for key in fake.field_widgets}
    fake.location_var = SimpleNamespace(get=lambda: "night background")
    fake.lighting_var = SimpleNamespace(get=lambda: "dark cinematic lighting")
    fake.camera_var = SimpleNamespace(get=lambda: "abandoned_building")
    fake.canvas_weight_var = SimpleNamespace(get=lambda: "1.15")
    fake.seed_var = SimpleNamespace(get=lambda: "42")
    fake.rating_var = SimpleNamespace(get=lambda: "rating_explicit")
    fake.score_scheme_var = SimpleNamespace(get=lambda: "default high")
    fake.nsfw_var = SimpleNamespace(get=lambda: False)
    fake.sex_act_var = SimpleNamespace(get=lambda: "None")
    fake.sex_position_var = SimpleNamespace(get=lambda: "None")
    fake.use_break_var = SimpleNamespace(get=lambda: True)
    fake.canvas_positive_text = DummyText()
    fake.canvas_negative_text = DummyText()
    custom_widget = SimpleNamespace(value="score_9, striped fur, dark cinematic lighting, night background, panther anatomy, lighƟng")
    fake._get_widget_text_fields = lambda widgets: (custom_widget, None)
    fake._read_widget_value = lambda widget: getattr(widget, "value", "")
    fake._is_feral_gender = lambda value: False
    fake._get_base_gender_from_value = lambda value: value

    original_node = main.CR_Pony_Master
    main.CR_Pony_Master = DummyNode
    try:
        main.PromptGui.update_canvas_prompts(fake)
    finally:
        main.CR_Pony_Master = original_node

    assert fake.canvas_positive_text.value == "score_9, score_8_up, score_7_up, rating_explicit, source_photography, raw photo, hyperrealistic, (female, anthro, striped fur, panther anatomy:1.15)"
    assert "night background" not in fake.canvas_positive_text.value
    assert "dark cinematic lighting" not in fake.canvas_positive_text.value
    assert "abandoned_building" not in fake.canvas_positive_text.value
    assert "lighting" not in fake.canvas_positive_text.value


def test_verify_pony_logic_blocks_human_with_special_skin():
    result = main.verify_pony_logic({
        "body_type": "human",
        "species": "",
        "special_skin_type": "thick fur",
    })

    assert result == "❌ Konflikt: Der Body Type 'human' verträgt sich nicht mit dem Special Skin Type 'thick fur'!"


def test_verify_pony_logic_blocks_insect_with_fur():
    result = main.verify_pony_logic({
        "body_type": "arachnid",
        "species": "bee girl",
        "special_skin_type": "fluffy fur",
    })

    assert result == "❌ Konflikt: Der Body Type 'arachnid' verträgt sich nicht mit dem Special Skin Type 'fluffy fur'!"


def test_verify_pony_logic_blocks_reptile_with_feathers():
    result = main.verify_pony_logic({
        "body_type": "dragon anthro",
        "species": "drake",
        "special_skin_type": "soft feathers",
    })

    assert result == "❌ Konflikt: Der Body Type 'dragon anthro' verträgt sich nicht mit dem Special Skin Type 'soft feathers'!"


def test_verify_pony_logic_blocks_bird_with_scales():
    result = main.verify_pony_logic({
        "body_type": "harpy",
        "species": "avian",
        "special_skin_type": "smooth scales",
    })

    assert result == "❌ Konflikt: Der Body Type 'harpy' verträgt sich nicht mit dem Special Skin Type 'smooth scales'!"


def test_verify_pony_logic_blocks_mechanical_with_fur():
    result = main.verify_pony_logic({
        "body_type": "cyborg",
        "species": "robot",
        "special_skin_type": "thick fur",
    })

    assert result == "❌ Konflikt: Der Body Type 'cyborg' verträgt sich nicht mit dem Special Skin Type 'thick fur'!"


def test_verify_pony_logic_reports_missing_creature_signal_for_generic_body_type():
    result = main.verify_pony_logic({
        "body_type": "lean_muscular",
        "species": "",
        "special_skin_type": "fluffy fur",
    })

    assert result == "❌ Konflikt: Du hast 'fluffy fur' ausgewählt, aber der Body Type 'lean_muscular' liefert dem Modell keine passende Kreatur (z. B. draconic, anthro)!"


def test_verify_pony_logic_allows_matching_fur_creature_skin_combo():
    result = main.verify_pony_logic({
        "body_type": "anthro wolf",
        "species": "werewolf",
        "special_skin_type": "shaggy fur",
    })

    assert result is None


def test_evaluate_pony_model_status_returns_green_for_human_without_special_skin():
    status = main.evaluate_pony_model_status({
        "gender": "female",
        "body_type": "human",
        "special_skin_type": "None",
        "camera": "85mm portrait lens",
        "location": "luxury penthouse",
        "full_outfit": "None",
        "top_clothing": "None",
        "bottom_clothing": "None",
        "headwear": "None",
        "shoes": "None",
        "accessories": "None",
    })

    assert status["level"] == "green"


def test_evaluate_pony_model_status_returns_yellow_for_close_up_with_location():
    status = main.evaluate_pony_model_status({
        "gender": "female",
        "body_type": "human",
        "special_skin_type": "None",
        "camera": "close-up",
        "location": "luxury penthouse",
        "full_outfit": "None",
        "top_clothing": "None",
        "bottom_clothing": "None",
        "headwear": "None",
        "shoes": "None",
        "accessories": "None",
    })

    assert status["level"] == "yellow"


def test_evaluate_pony_model_status_returns_red_for_feral_with_clothing():
    status = main.evaluate_pony_model_status({
        "gender": "feral female",
        "body_type": "anthro wolf",
        "species": "werewolf",
        "special_skin_type": "thick fur",
        "camera": "85mm portrait lens",
        "location": "luxury penthouse",
        "full_outfit": "dress",
        "top_clothing": "None",
        "bottom_clothing": "None",
        "headwear": "None",
        "shoes": "None",
        "accessories": "None",
    })

    assert status["level"] == "red"


def test_evaluate_pony_model_status_returns_red_for_species_skin_logic_conflict():
    status = main.evaluate_pony_model_status({
        "gender": "female",
        "body_type": "human",
        "species": "",
        "special_skin_type": "thick fur",
        "camera": "85mm portrait lens",
        "location": "luxury penthouse",
        "full_outfit": "None",
        "top_clothing": "None",
        "bottom_clothing": "None",
        "headwear": "None",
        "shoes": "None",
        "accessories": "None",
    })

    assert status["level"] == "red"
    assert status["message"] == "❌ Konflikt: Der Body Type 'human' verträgt sich nicht mit dem Special Skin Type 'thick fur'!"
