import argparse
import copy
import hashlib
import re
import sys
import base64
import json
import os
import zlib
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, simpledialog

import nodes as pony_nodes
from nodes import CR_Pony_Subject, CR_Pony_Master


NEGATIVE_WATERMARK_BLOCKERS = pony_nodes.NEGATIVE_WATERMARK_BLOCKERS


def sort_combo_values(values):
    if values is None:
        return []

    ordered = []
    seen = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)

    priority = {"None": 0, "Random": 1}
    return sorted(ordered, key=lambda item: (priority.get(item, 2), item.lower()))


def sanitize_gui_text(value):
    text = str(value or "")
    return text.replace("\u019F", "ti").replace("\u0275", "ti")


def get_neutral_reset_value(values, fallback_default=""):
    ordered_values = [str(value).strip() for value in (values or []) if str(value).strip()]
    for preferred in ("None", "Random"):
        if preferred in ordered_values:
            return preferred
    return fallback_default


def build_default_settings_template():
    return {
        "mode": "subject",
        "seed": "42",
        "person_count": "solo",
        "duo_second_gender": "None",
        "duo_second_pose": "Random",
        "duo_second_expression": "Random",
        "duo_second_body_type": "None",
        "nsfw": False,
        "subject_2_nsfw": False,
        "photo_boost": False,
        "nsfw_modifier": "",
        "subject_2_nsfw_modifier": "",
        "bondage": "",
        "subject_2_bondage": "",
        "bondage_enabled": False,
        "subject_2_bondage_enabled": False,
        "rating": "rating_safe",
        "score_scheme": "default high",
        "image_quality": "None",
        "location": "Random",
        "lighting": "Random",
        "camera": "Random",
        "sex_act": "None",
        "sex_position": "None",
        "use_break": True,
        "custom_tags": "",
        "extra_clothing_tags": "",
        "checksum_store": {},
    }


def set_text_widget_text(text_widget, value):
    if text_widget is None:
        return
    text_widget.delete("1.0", tk.END)
    text_widget.insert("1.0", sanitize_gui_text(value))
    auto_grow_callback = getattr(text_widget, "_auto_grow_callback", None)
    if callable(auto_grow_callback):
        try:
            text_widget.after_idle(auto_grow_callback)
        except Exception:
            pass
    tag_sync_callback = getattr(text_widget, "_tag_sync_callback", None)
    if callable(tag_sync_callback):
        try:
            text_widget.after_idle(tag_sync_callback)
        except Exception:
            pass


def split_tag_text(value):
    tags = []
    seen = set()
    for part in str(value or "").split(","):
        text = sanitize_gui_text(part).strip()
        if not text or text in {"None", "Random"}:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        tags.append(text)
    return tags


def compose_tag_text(tags):
    return ", ".join(split_tag_text(", ".join(str(tag or "") for tag in (tags or []))))


CANVAS_PROMPT_PREFIX = "score_9, score_8_up, score_7_up, rating_explicit, source_photography, raw photo, hyperrealistic"


def compose_canvas_positive_prompt(bracket_tags, weight_value):
    clean_tags = []
    seen = set()
    for tag in bracket_tags or []:
        text = sanitize_gui_text(tag).strip()
        if not text:
            continue

        lowered = text.lower()
        if lowered in seen:
            continue

        seen.add(lowered)
        clean_tags.append(text)

    clean_weight = sanitize_gui_text(weight_value or "1.15").strip()
    if not clean_weight:
        clean_weight = "1.15"

    final_prompt = f"{CANVAS_PROMPT_PREFIX}, ({', '.join(clean_tags)}:{clean_weight})"
    final_prompt = re.sub(r"\s{2,}", " ", final_prompt)
    final_prompt = re.sub(r"\s*,\s*", ", ", final_prompt)
    final_prompt = re.sub(r",\s*,+", ", ", final_prompt)
    final_prompt = re.sub(r"\(\s+", "(", final_prompt)
    final_prompt = re.sub(r"\s+\)", ")", final_prompt)
    return final_prompt.strip(" ,")


def filter_blocked_canvas_character_tags(tags, blocked_values):
    blocked_lower = {
        sanitize_gui_text(value).strip().lower()
        for value in blocked_values
        if value is not None and not pony_nodes._is_ignored_value(value)
    }

    filtered_tags = []
    seen = set()
    for tag in tags or []:
        text = sanitize_gui_text(tag).strip()
        if not text:
            continue

        lowered = text.lower()
        if lowered in blocked_lower or lowered in seen:
            continue

        seen.add(lowered)
        filtered_tags.append(text)

    return filtered_tags


def append_nsfw_modifier_tag_standalone(nsfw_var_obj, text_widget):
    try:
        selected_tag = nsfw_var_obj.get().strip()
        if selected_tag in {"None", "Random", ""}:
            return
        current_text = text_widget.get("1.0", "end-1c").strip()
        if current_text:
            if selected_tag not in current_text:
                new_text = f"{current_text}, {selected_tag}"
            else:
                new_text = current_text
        else:
            new_text = selected_tag
        set_text_widget_text(text_widget, new_text)
        nsfw_var_obj.set("None")
    except Exception as e:
        print(f"Fehler: {e}")


BONDAGE_TAGS = [
    "bound",
    "tied up",
    "restrained",
    "handcuffs",
    "rope",
    "bondage",
    "collar",
    "leash",
    "gag",
    "blindfold",
    "spread legs",
    "arms behind back",
    "legs spread",
]


def remove_tags_from_text_widget(text_widget, tags_to_remove):
    if text_widget is None:
        return
    try:
        current_text = text_widget.get("1.0", "end-1c").strip()
        if not current_text:
            return
        current_tags = [part.strip() for part in current_text.split(",") if part.strip()]
        remove_set = {tag.strip().lower() for tag in tags_to_remove if tag and tag != "None"}
        filtered_tags = [tag for tag in current_tags if tag.lower() not in remove_set]
        new_text = ", ".join(filtered_tags)
        set_text_widget_text(text_widget, new_text)
    except Exception as e:
        print(f"Fehler: {e}")


def append_bondage_tag_standalone(bondage_var_obj, text_widget):
    try:
        selected_tag = bondage_var_obj.get().strip()
        if selected_tag in {"None", "", "Random"}:
            return
        current_text = text_widget.get("1.0", "end-1c").strip()
        if current_text:
            if selected_tag not in current_text:
                new_text = f"{current_text}, {selected_tag}"
            else:
                new_text = current_text
        else:
            new_text = selected_tag
        set_text_widget_text(text_widget, new_text)
        bondage_var_obj.set("None")
    except Exception as e:
        print(f"Fehler: {e}")


PREVIEW_NSWF_TAGS = [
    tag
    for tag in dict.fromkeys([
        *pony_nodes.NSFW_MODIFIERS,
        "detailed anatomy",
        "accurate anatomy",
        "correct anatomy",
        "realistic anatomy",
        "stylized anatomy",
        "anatomically correct",
        "detailed genitals",
        "realistic genitals",
        "soft shading",
        "detailed shading",
        "wet",
        "shiny",
        "glossy",
        "aroused",
        "excited",
        "muscular definition",
        "muscular chest",
        "defined abs",
        "soft belly",
        "plush thighs",
    ])
    if "fur" not in str(tag).lower()
]

DEFAULT_NSWF_MASTER_LIST = sort_combo_values(["None", "Random", *PREVIEW_NSWF_TAGS])
DEFAULT_BONDAGE_MASTER_LIST = sort_combo_values(["None", *BONDAGE_TAGS])

_custom_tag_source_values = list(PREVIEW_NSWF_TAGS)
for _section_values in getattr(pony_nodes, "NSFW_MODIFIER_SECTIONS", {}).values():
    if isinstance(_section_values, (list, tuple, set)):
        _custom_tag_source_values.extend(_section_values)
_custom_tag_source_values.extend(BONDAGE_TAGS)
DEFAULT_CUSTOM_TAG_MASTER_LIST = sort_combo_values(["None", "Random", *_custom_tag_source_values])

FERAL_POSITIVE_TAGS = [
    "detailed animal fur",
    "thick fur texture",
    "individual fur strands",
    "no human",
    "no anthro",
    "no person",
]

FERAL_NEGATIVE_TAGS = [
    "human",
    "person",
    "man",
    "woman",
    "anthro",
    "anthropomorphic",
    "furry",
    "humanoid",
    "face",
    "hands",
    "fingers",
    "bipedal",
    "standing upright",
]


def compose_negative_prompt(base_prompt="-", *extra_tag_groups):
    return pony_nodes.merge_negative_prompt_tags(base_prompt, *extra_tag_groups)


def should_auto_enable_canvas_detail(value):
    return not pony_nodes._is_ignored_value(value)


FELL_KREATUREN = ["anthro", "were", "bipedal wolf", "kitsune", "lycanthrope", "tanuki", "minotaur", "taur", "centaur", "faun", "satyr", "incubus", "succubus", "catgirl", "bunnygirl"]
SCHUPPEN_KREATUREN = ["alligator", "crocodile", "draconic", "dragon", "drake", "lizardman", "reptilian", "serpent", "snake", "lamia", "naga", "fish", "mermaid", "merfolk", "merman", "shark", "amphibian", "kappa"]
FEDER_KREATUREN = ["angel", "avian", "bird", "celestial", "griffin", "gryphon", "harpy", "tengu"]
INSEKTEN_KREATUREN = ["arachnid", "arthropod", "insect", "ant", "bee", "wasp", "spider"]
GLATTE_KREATUREN = ["slime", "gelatinous", "amorphous", "plant", "flora", "alraune", "octopus", "cephalopod", "tentacle"]
METALL_KREATUREN = ["robot", "mecha", "mechanical", "cyborg"]
KNOCHEN_KREATUREN = ["skeleton", "undead", "zombie"]

PONY_LOGIC_GROUPS = {
    "fur": FELL_KREATUREN,
    "scales": SCHUPPEN_KREATUREN,
    "feathers": FEDER_KREATUREN,
    "insects": INSEKTEN_KREATUREN,
    "smooth": GLATTE_KREATUREN,
    "metal": METALL_KREATUREN,
    "bones": KNOCHEN_KREATUREN,
}


def _build_pony_logic_search_text(values):
    body_type = str(values.get("body_type") or "").strip().lower()
    species = str(values.get("species") or "").strip().lower()
    return " ".join(part for part in (body_type, species) if part)


def _matches_pony_logic_group(search_text, keywords):
    for keyword in keywords:
        pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
        if re.search(pattern, search_text):
            return True
    return False


def _get_special_skin_family(value):
    skin_text = str(value or "").strip().lower()
    if pony_nodes._is_ignored_value(value):
        return None
    if "fur" in skin_text:
        return "fur"
    if "scale" in skin_text:
        return "scales"
    if "feather" in skin_text:
        return "feathers"
    return None


def verify_pony_logic(values):
    search_text = _build_pony_logic_search_text(values)
    body_type = str(values.get("body_type") or "").strip()
    special_skin_type = str(values.get("special_skin_type") or "").strip()
    body_type_lower = body_type.lower()
    skin_family = _get_special_skin_family(special_skin_type)

    if skin_family is None:
        return None

    group_matches = {
        name: _matches_pony_logic_group(search_text, keywords)
        for name, keywords in PONY_LOGIC_GROUPS.items()
    }
    belongs_to_creature_group = any(group_matches.values())

    if body_type_lower == "human":
        return f"❌ Konflikt: Der Body Type '{body_type}' verträgt sich nicht mit dem Special Skin Type '{special_skin_type}'!"

    if not belongs_to_creature_group:
        return f"❌ Konflikt: Du hast '{special_skin_type}' ausgewählt, aber der Body Type '{body_type}' liefert dem Modell keine passende Kreatur (z. B. draconic, anthro)!"

    if group_matches["insects"] and skin_family in {"fur", "feathers"}:
        return f"❌ Konflikt: Der Body Type '{body_type}' verträgt sich nicht mit dem Special Skin Type '{special_skin_type}'!"

    if group_matches["scales"] and skin_family in {"fur", "feathers"}:
        return f"❌ Konflikt: Der Body Type '{body_type}' verträgt sich nicht mit dem Special Skin Type '{special_skin_type}'!"

    if group_matches["feathers"] and skin_family == "scales":
        return f"❌ Konflikt: Der Body Type '{body_type}' verträgt sich nicht mit dem Special Skin Type '{special_skin_type}'!"

    if group_matches["metal"] and skin_family in {"fur", "feathers"}:
        return f"❌ Konflikt: Der Body Type '{body_type}' verträgt sich nicht mit dem Special Skin Type '{special_skin_type}'!"

    return None


def evaluate_pony_model_status(values):
    body_type = str(values.get("body_type") or "").strip()
    gender = str(values.get("gender") or "").strip()
    camera = str(values.get("camera") or "").strip()
    location = str(values.get("location") or "").strip()

    body_type_lower = body_type.lower()
    gender_lower = gender.lower()
    camera_lower = camera.lower()

    human_body_selected = body_type_lower == "human"
    feral_gender_selected = gender_lower.startswith("feral")
    close_up_camera_selected = "close-up" in camera_lower or "macro" in camera_lower
    location_selected = not pony_nodes._is_ignored_value(location)
    clothing_selected = any(
        not pony_nodes._is_ignored_value(values.get(key))
        for key in ("full_outfit", "top_clothing", "bottom_clothing", "headwear", "shoes", "accessories")
    )

    logic_error = verify_pony_logic(values)
    if logic_error:
        return {
            "level": "red",
            "signal_color": "#c62828",
            "text_color": "#c62828",
            "message": logic_error,
        }

    if feral_gender_selected and clothing_selected:
        return {
            "level": "red",
            "signal_color": "#c62828",
            "text_color": "#c62828",
            "message": "🔴 Prompt-Status: Logischer Widerspruch erkannt!",
        }

    if close_up_camera_selected and location_selected:
        return {
            "level": "yellow",
            "signal_color": "#d97706",
            "text_color": "#b45309",
            "message": "🟡 Prompt-Status: Kamera/Location-Beschnitt möglich",
        }

    if human_body_selected or (feral_gender_selected and not clothing_selected):
        return {
            "level": "green",
            "signal_color": "#2e7d32",
            "text_color": "#2e7d32",
            "message": "🟢 Prompt-Status: Optimal für Pony",
        }

    return {
        "level": "green",
        "signal_color": "#2e7d32",
        "text_color": "#2e7d32",
        "message": "🟢 Prompt-Status: Optimal für Pony",
    }


def apply_preview_tag_highlights(text_widget, prompt_text):
    if text_widget is None:
        return

    text_widget.configure(state="normal", cursor="arrow", takefocus=0)
    set_text_widget_text(text_widget, prompt_text)

    text_widget.tag_configure("nsfw_highlight", background="#ffe0ea", foreground="#7a1f3f", font=("TkDefaultFont", 9, "bold"))
    text_widget.tag_configure("bondage_highlight", background="#e8e0ff", foreground="#3f2d73", font=("TkDefaultFont", 9, "bold"))

    for tag_name, tags in {
        "nsfw_highlight": PREVIEW_NSWF_TAGS,
        "bondage_highlight": BONDAGE_TAGS,
    }.items():
        text_widget.tag_remove(tag_name, "1.0", tk.END)
        for tag in sorted(tags, key=len, reverse=True):
            if not tag:
                continue
            start = "1.0"
            lower_tag = tag.lower()
            while True:
                idx = text_widget.search(lower_tag, start, nocase=True, stopindex=tk.END)
                if not idx:
                    break
                end = f"{idx}+{len(tag)}c"
                text_widget.tag_add(tag_name, idx, end)
                start = end

    text_widget.configure(state="disabled", cursor="arrow")
    for event in ("<Button-1>", "<ButtonRelease-1>", "<B1-Motion>", "<Double-Button-1>"):
        text_widget.bind(event, lambda event=None, _event=event: "break")


def save_prompt_to_file(file_path, positive_text, negative_text=None, checksum=None, comment=None):
    path = Path(file_path)
    if negative_text is None:
        negative_text = "-"

    sections = [
        "[POSITIVE]",
        positive_text.strip(),
        "",
        "[NEGATIVE]",
        negative_text.strip(),
    ]

    checksum_text = (str(checksum or "")).strip()
    if checksum_text:
        sections.extend(["", "[CHECKSUM]", checksum_text])

    comment_text = (str(comment or "")).strip()
    if comment_text:
        sections.extend(["", "[COMMENT]", comment_text])

    content = "\n".join(sections) + "\n"
    path.write_text(content, encoding="utf-8")


def load_prompt_from_file(file_path, include_metadata=False):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    text = path.read_text(encoding="utf-8")
    text = text.strip()
    if not text:
        if include_metadata:
            return "", "-", "", ""
        return "", "-"

    metadata = {"checksum": "", "comment": ""}
    if "[POSITIVE]" in text or "[NEGATIVE]" in text:
        sections = {}
        current = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                current = stripped[1:-1].upper()
                sections[current] = []
            elif current is not None:
                sections[current].append(stripped)

        if "CHECKSUM" in sections:
            metadata["checksum"] = "\n".join(sections["CHECKSUM"]).strip()
        if "COMMENT" in sections:
            metadata["comment"] = "\n".join(sections["COMMENT"]).strip()

        positive = "\n".join(sections.get("POSITIVE", [])).strip()
        negative = "\n".join(sections.get("NEGATIVE", [])).strip() or "-"
        if include_metadata:
            return positive, negative, metadata["checksum"], metadata["comment"]
        return positive, negative

    if include_metadata:
        return text, "-", "", ""
    return text, "-"


def load_checksum_state_from_settings(settings_path, checksum):
    path = Path(settings_path)
    if not path.exists() or not checksum:
        return None

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    checksum_store = data.get("checksum_store")
    if not isinstance(checksum_store, dict):
        return None

    state = checksum_store.get(checksum)
    return state if isinstance(state, dict) else None


def compute_prompt_checksum(state):
    """Create a compact, deterministic checksum key for the current UI state."""
    try:
        payload = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    except Exception:
        return ""

    def apply_settings_state_from_base64(self, base64_code):
        if not base64_code or not base64_code.strip():
            return False
            
        try:
            b64_bytes = base64_code.strip().encode('utf-8')
            compressed_data = base64.urlsafe_b64decode(b64_bytes)
            json_str = zlib.decompress(compressed_data).decode('utf-8')
            state = json.loads(json_str)
            
            # 1. Zuerst lädt dein funktionierender Original-Code Person 1, 2 und die Szene
            self.apply_settings_state(state)
            
            # 2. Direkt danach lädt unser neuer, sicherer Helfer Person 3 und 4 nach!
            self.restore_additional_tabs_safely(state)
            
            return True
        except Exception:
            from tkinter import messagebox
            messagebox.showerror("Code ungültig", "Dieser Checksummen-Code ist beschädigt.")
            return False




def generate_default_subject(seed=0, gender="female"):
    node = CR_Pony_Subject()
    return node.generate_subject(
        seed=seed,
        gender=gender,
        age="25",
        ethnicity="Caucasian",
        body_type="slim body",
        skin_texture="pale skin",
        hair_color="platinum blonde",
        hair_style="Random",
        eye_color="Random",
        full_outfit="None",
        top_clothing="None",
        bottom_clothing="None",
        headwear="None",
        shoes="None",
        accessories="None",
        pose="Random",
        breast_size="Random",
        breast_shape="Random",
        custom_tags="",
        nsfw_modifiers=False,
        leg_feature="Random",
        butt_feature="Random",
        face_shape="Random",
        expression="Random",
        hair_length="Random",
        extra_clothing_tags="",
    )[0]


def build_subject_prompt(seed, values, gender_override=None, nsfw=False, nsfw_modifier="Random", lead_token=None):
    node = CR_Pony_Subject()
    gender = gender_override or values["gender"]
    if nsfw_modifier not in ["Random", "None"]:
        values = dict(values)
        values["custom_tags"] = f"{values.get('custom_tags', '').strip()}, {nsfw_modifier}".strip(", ")
    return node.generate_subject(
        seed=seed,
        gender=gender,
        age=values["age"],
        ethnicity=values["ethnicity"],
        body_type=values["body_type"],
        skin_texture=values["skin_texture"],
        hair_color=values["hair_color"],
        hair_style=values["hair_style"],
        eye_color=values["eye_color"],
        full_outfit=values["full_outfit"],
        top_clothing=values["top_clothing"],
        bottom_clothing=values["bottom_clothing"],
        headwear=values["headwear"],
        shoes=values["shoes"],
        accessories=values["accessories"],
        pose=values["pose"],
        breast_size=values["breast_size"],
        breast_shape=values["breast_shape"],
        custom_tags=values["custom_tags"],
        nsfw_modifiers=nsfw,
        leg_feature=values["leg_feature"],
        butt_feature=values["butt_feature"],
        face_shape=values["face_shape"],
        expression=values["expression"],
        hair_length=values["hair_length"],
        extra_clothing_tags=values["extra_clothing_tags"],
        lead_token=lead_token,
    )[0]


def build_scene_prompt_metadata(rating=None, image_quality=None, location=None, lighting=None, camera=None, photo_boost=False):
    prefix_parts = []
    suffix_parts = []

    for value in [rating, image_quality]:
        if pony_nodes._is_ignored_value(value):
            continue
        text = str(value).strip()
        if text:
            prefix_parts.append(text)

    if photo_boost:
        prefix_parts.append("source_photography, raw photo, hyperrealistic, 8k uhd, film grain")

    for value in [location, lighting, camera]:
        if pony_nodes._is_ignored_value(value):
            continue
        text = str(value).strip()
        if text:
            suffix_parts.append(text)

    if photo_boost:
        suffix_parts.append("photorealistic")

    return ", ".join(prefix_parts), ", ".join(suffix_parts)


def attach_scene_metadata(prompt, rating=None, image_quality=None, location=None, lighting=None, camera=None, photo_boost=False):
    prefix, suffix = build_scene_prompt_metadata(
        rating=rating,
        image_quality=image_quality,
        location=location,
        lighting=lighting,
        camera=camera,
        photo_boost=photo_boost,
    )
    parts = []
    if prefix:
        parts.append(prefix)
    if prompt and str(prompt).strip():
        parts.append(str(prompt).strip())
    if suffix:
        parts.append(suffix)
    return ", ".join(parts)


def build_subject_parser(subparsers):
    parser = subparsers.add_parser("subject", help="Generate a single subject prompt")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--gender", choices=["female", "male", "futa", "other", "Random"], default="female")
    parser.add_argument("--age", default="25")
    parser.add_argument("--ethnicity", default="Caucasian")
    parser.add_argument("--body-type", default="slim body")
    parser.add_argument("--skin", dest="skin_texture", default="pale skin")
    parser.add_argument("--hair-color", default="platinum blonde")
    parser.add_argument("--hair-style", default="messy bun")
    parser.add_argument("--eye-color", default="blue")
    parser.add_argument("--full-outfit", default="None")
    parser.add_argument("--top", default="None")
    parser.add_argument("--bottom", default="None")
    parser.add_argument("--headwear", default="None")
    parser.add_argument("--shoes", default="None")
    parser.add_argument("--accessories", default="None")
    parser.add_argument("--pose", default="standing elegantly")
    parser.add_argument("--breast-size", default="medium breasts")
    parser.add_argument("--breast-shape", default="natural breasts")
    parser.add_argument("--custom-tags", default="")
    parser.add_argument("--extra-clothing-tags", default="")
    parser.add_argument("--person-count", choices=["single", "duo"], default="single")
    parser.add_argument("--duo-gender", choices=["female", "male", "futa", "other", "Random"], default="male")
    parser.add_argument("--nsfw", action="store_true")
    parser.add_argument("--leg-feature", default="Random")
    parser.add_argument("--butt-feature", default="Random")
    parser.add_argument("--face-shape", default="Random")
    parser.add_argument("--expression", default="Random")
    parser.add_argument("--hair-length", default="Random")
    return parser


def build_master_parser(subparsers):
    parser = subparsers.add_parser("master", help="Generate a full positive/negative master prompt")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rating", default="rating_safe")
    parser.add_argument("--location", default="luxury penthouse")
    parser.add_argument("--lighting", default="cinematic lighting")
    parser.add_argument("--camera", default="85mm portrait lens")
    parser.add_argument("--use-break", action="store_true", default=True)
    parser.add_argument("--no-break", dest="use_break", action="store_false")
    parser.add_argument("--nsfw-mode", action="store_true")
    parser.add_argument("--sex-act", default="None")
    parser.add_argument("--sex-position", default="None")
    parser.add_argument("--score-scheme", default="default high")
    parser.add_argument("--source-bias", default="None")
    parser.add_argument("--strong-anime-bias", action="store_true")
    parser.add_argument("--style-preset", default="None")
    parser.add_argument("--subject-1", default=None)
    parser.add_argument("--subject-2", default=None)
    parser.add_argument("--subject-3", default=None)
    parser.add_argument("--subject-4", default=None)
    return parser


def run_subject(args):
    values = {
        "gender": args.gender,
        "age": args.age,
        "ethnicity": args.ethnicity,
        "body_type": args.body_type,
        "skin_texture": args.skin_texture,
        "hair_color": args.hair_color,
        "hair_style": args.hair_style,
        "eye_color": args.eye_color,
        "full_outfit": args.full_outfit,
        "top_clothing": args.top,
        "bottom_clothing": args.bottom,
        "headwear": args.headwear,
        "shoes": args.shoes,
        "accessories": args.accessories,
        "pose": args.pose,
        "breast_size": args.breast_size,
        "breast_shape": args.breast_shape,
        "custom_tags": args.custom_tags,
        "leg_feature": args.leg_feature,
        "butt_feature": args.butt_feature,
        "face_shape": args.face_shape,
        "expression": args.expression,
        "hair_length": args.hair_length,
        "extra_clothing_tags": args.extra_clothing_tags,
    }

    if args.person_count == "duo":
        first = build_subject_prompt(args.seed, values, nsfw=args.nsfw)
        second_values = dict(values)
        second_values["gender"] = args.duo_gender
        second_values["expression"] = args.expression
        second = build_subject_prompt(args.seed + 1, second_values, gender_override=args.duo_gender, nsfw=args.nsfw)
        prompt = f"{first} BREAK {second}"
    else:
        prompt = build_subject_prompt(args.seed, values, nsfw=args.nsfw)

    print(prompt)
    return prompt


def run_master(args):
    subject_1 = subject_2 = subject_3 = subject_4 = None

    if not any([args.subject_1, args.subject_2, args.subject_3, args.subject_4]):
        subject_1 = generate_default_subject(seed=args.seed, gender="female")
        subject_2 = generate_default_subject(seed=args.seed + 1, gender="male")
    else:
        subject_1, subject_2, subject_3, subject_4 = (
            args.subject_1,
            args.subject_2,
            args.subject_3,
            args.subject_4,
        )
        subject_1 = subject_1 if subject_1 else None
        subject_2 = subject_2 if subject_2 else None
        subject_3 = subject_3 if subject_3 else None
        subject_4 = subject_4 if subject_4 else None

    node = CR_Pony_Master()
    positive, negative = node.generate_master(
        seed=args.seed,
        rating=args.rating,
        location=args.location,
        lighting=args.lighting,
        camera=args.camera,
        use_break=args.use_break,
        nsfw_mode=args.nsfw_mode,
        sex_act=args.sex_act,
        sex_position=args.sex_position,
        score_scheme=args.score_scheme,
        source_bias=args.source_bias,
        strong_anime_bias=args.strong_anime_bias,
        style_preset=args.style_preset,
        subject_1=subject_1 if not any([args.subject_1, args.subject_2, args.subject_3, args.subject_4]) else args.subject_1,
        subject_2=subject_2 if not any([args.subject_1, args.subject_2, args.subject_3, args.subject_4]) else args.subject_2,
        subject_3=subject_3 if not any([args.subject_1, args.subject_2, args.subject_3, args.subject_4]) else args.subject_3,
        subject_4=subject_4 if not any([args.subject_1, args.subject_2, args.subject_3, args.subject_4]) else args.subject_4,
    )
    print("POSITIVE:")
    print(positive)
    print("\nNEGATIVE:")
    print(negative)
    return positive, negative


class PromptGui:
    def __init__(self, root):
        self.root = root
        root.title("CyberRealistic Pony Prompt Generator")
        root.geometry("1280x860")
        root.minsize(1100, 780)

        self.mode_var = tk.StringVar(value="subject")
        self.seed_var = tk.StringVar(value="42")
        self.person_count_var = tk.StringVar(value="solo")
        self.duo_second_gender_var = tk.StringVar(value="male")
        self.duo_second_pose_var = tk.StringVar(value="standing elegantly")
        self.duo_second_expression_var = tk.StringVar(value="Random")
        self.duo_second_body_type_var = tk.StringVar(value="None")
        self.nsfw_var = tk.BooleanVar(value=False)
        self.subject_2_nsfw_var = tk.BooleanVar(value=False)
        self.photo_boost_var = tk.BooleanVar(value=False)
        self.nsfw_modifier_var = tk.StringVar(value="None")
        self.subject_2_nsfw_modifier_var = tk.StringVar(value="None")
        self.bondage_var = tk.StringVar(value="None")
        self.subject_2_bondage_var = tk.StringVar(value="None")
        self.bondage_enabled_var = tk.BooleanVar(value=False)
        self.subject_2_bondage_enabled_var = tk.BooleanVar(value=False)
        self.rating_var = tk.StringVar(value="rating_safe")
        self.score_scheme_var = tk.StringVar(value="default high")
        self.image_quality_var = tk.StringVar(value="None")
        self.location_var = tk.StringVar(value="luxury penthouse")
        self.lighting_var = tk.StringVar(value="cinematic lighting")
        self.camera_var = tk.StringVar(value="85mm portrait lens")
        self.sex_act_var = tk.StringVar(value="None")
        self.sex_position_var = tk.StringVar(value="None")
        self.use_break_var = tk.BooleanVar(value=True)

        self.special_skin_type_options = [
            "None",
            # --- Texturen & Längen ---
            "fluffy fur", "thick fur", "short fur", "rough fur", "shaggy fur", "soft fur", "sleek fur", "silky fur", "long fur", "dense fur",
            # --- Ganzkörper-Modifikatoren (Anthro / Full Body) ---
            "full body fur", "covered in fur", "furry body", "anthropomorphic fur", "seamless fur texture",
            # --- Muster & Zeichnungen ---
            "spotted fur", "striped fur", "patched fur", "brindle fur", "mottled fur", "leopard print fur", "tiger stripe fur", "bi-color fur",
            # --- Spezial-Zustände ---
            "wet fur", "damp fur", "matted fur", "dirty fur", "glowing fur", "magic-infused fur",
            # --- Schuppen & Federn (Fabelwesen) ---
            "smooth scales", "reptilian scales", "dragon scales", "glowing scales", "soft feathers", "glossy feathers", "angelic feathers"
        ]
        self.gender_options = [
            "None",
            "androgynous",
            "female",
            "hermaphrodite",
            "male",
            "feral female",
            "feral male",
        ]

        self.field_values = {
            "gender": (list(self.gender_options), "female"),
            "age": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.AGES)), "25"),
            "ethnicity": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.ETHNICITIES)), "Caucasian"),
            "body_type": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.ALL_BODY_TYPES)), "None"),
            "skin_texture": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.SKIN_TYPES)), "pale skin"),
            "special_skin_type": (list(self.special_skin_type_options), "None"),
            "hair_color": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.HAIR_COLORS)), "platinum blonde"),
            "hair_style": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.ALL_HAIRSTYLES)), "Random"),
            "eye_color": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.EYE_COLORS)), "Random"),
            "full_outfit": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.FULL_OUTFITS)), "None"),
            "top_clothing": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.TOP_CLOTHING)), "None"),
            "bottom_clothing": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.BOTTOM_CLOTHING)), "None"),
            "headwear": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.HEADWEAR)), "None"),
            "shoes": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.FOOTWEAR)), "None"),
            "accessories": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.ACCESSORIES)), "None"),
            "pose": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.ALL_POSES)), "Random"),
            "breast_size": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.BREAST_SIZES)), "Random"),
            "breast_shape": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.BREAST_SHAPES)), "Random"),
            "leg_feature": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.LEG_FEATURES)), "Random"),
            "butt_feature": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.BUTT_FEATURES)), "Random"),
            "face_shape": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.FACE_SHAPES)), "Random"),
            "expression": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.EXPRESSIONS)), "Random"),
            "hair_length": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.HAIR_LENGTHS)), "Random"),
        }
        duo_order = [
            "gender", "age", "ethnicity", "body_type", "skin_texture", "hair_color",
            "special_skin_type",
            "hair_style", "eye_color", "full_outfit", "top_clothing", "bottom_clothing",
            "headwear", "shoes", "accessories", "pose", "breast_size", "breast_shape",
            "leg_feature", "butt_feature", "face_shape", "expression", "hair_length",
        ]
        self.duo_field_values = {}
        for key in duo_order:
            values, default = self.field_values[key]
            if key == "body_type":
                values, default = sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.ALL_BODY_TYPES)), "None"
            elif key == "pose":
                values, default = sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.ALL_POSES)), "Random"
            elif key == "expression":
                values, default = sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.EXPRESSIONS)), "Random"
            self.duo_field_values[key] = (values, default)

        self.field_widgets = {}
        self.duo_field_widgets = {}
        self.output_window = None
        self.output_positive = None
        self.output_negative = None
        self.canvas_window = None
        self.canvas_positive_text = None
        self.canvas_negative_text = None
        self.canvas_include_options = [
            ("gender", "Gender"),
            ("body_type", "Body Type"),
            ("skin_texture", "Skin Texture"),
            ("special_skin_type", "Special Skin Type"),
            ("hair_style", "Hair Style"),
            ("hair_color", "Hair Color"),
            ("expression", "Expression"),
            ("age", "Age"),
            ("ethnicity", "Ethnicity"),
            ("eye_color", "Eye Color"),
            ("hair_length", "Hair Length"),
            ("face_shape", "Face Shape"),
            ("pose", "Pose"),
            ("full_outfit", "Full Outfit"),
            ("top_clothing", "Top Clothing"),
            ("bottom_clothing", "Bottom Clothing"),
            ("accessories", "Accessories"),
            ("headwear", "Headwear"),
            ("shoes", "Shoes"),
            ("breast_size", "Breast Size"),
            ("breast_shape", "Breast Shape"),
            ("leg_feature", "Leg Feature"),
            ("butt_feature", "Butt Feature"),
        ]
        self.canvas_include_vars = {}
        default_canvas_enabled = {"gender", "body_type"}
        for key, _label in self.canvas_include_options:
            self.canvas_include_vars[key] = tk.BooleanVar(value=key in default_canvas_enabled)
        self.canvas_weight_var = tk.StringVar(value="1.15")
        self.canvas_denoise_var = tk.DoubleVar(value=0.65)
        self.canvas_denoise_recommendation_label = None
        self.pony_status_signal = None
        self.pony_status_message = None
        self.status_text_label = None
        self.text = None
        self.prompt_preview = None
        self.settings_template_path = Path(__file__).with_name("prompt_settings.example.json")
        self.settings_path = Path(__file__).with_name("prompt_settings.local.json")
        self.checksum_store = {}
        self.prompt_checksum_var = tk.StringVar(value="")
        self.prompt_checksum_input_var = tk.StringVar(value="")
        self._preview_refresh_job = None
        self.preset_combo = None
        self.preset_info_text = None
        self.nsfw_master_list = list(DEFAULT_NSWF_MASTER_LIST)
        self.bondage_master_list = list(DEFAULT_BONDAGE_MASTER_LIST)
        self.custom_tags_master_list = list(DEFAULT_CUSTOM_TAG_MASTER_LIST)
        self.active_nsfw_tags = []
        self.active_bondage_tags = []
        self.active_custom_tags = []
        self.nsfw_tags_container = None
        self.bondage_tags_container = None
        self.custom_tags_container = None

        try:
            # Sicherheitscheck für PyInstaller: Wenn als EXE verpackt, nutze den temporären Pfad (_MEIPASS)
            import sys
            import os
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                json_path = os.path.join(sys._MEIPASS, "presets.json")
            else:
                json_path = "presets.json"

            with open(json_path, "r", encoding="utf-8") as f:
                self.INPAINT_PRESET_DB = json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der presets.json: {e}")
            self.INPAINT_PRESET_DB = {}


        for var in (
            self.mode_var,
            self.seed_var,
            self.person_count_var,
            self.duo_second_gender_var,
            self.duo_second_pose_var,
            self.duo_second_expression_var,
            self.duo_second_body_type_var,
            self.nsfw_var,
            self.subject_2_nsfw_var,
            self.photo_boost_var,
            self.nsfw_modifier_var,
            self.subject_2_nsfw_modifier_var,
            self.bondage_var,
            self.subject_2_bondage_var,
            self.bondage_enabled_var,
            self.subject_2_bondage_enabled_var,
            self.rating_var,
            self.score_scheme_var,
            self.image_quality_var,
            self.location_var,
            self.lighting_var,
            self.camera_var,
            self.sex_act_var,
            self.sex_position_var,
            self.use_break_var,
        ):
            var.trace_add("write", self._queue_prompt_preview_refresh)
        self.canvas_weight_var.trace_add("write", lambda *_: self.update_canvas_prompts())

        main = ttk.Frame(root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        top_bar = ttk.Frame(main)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        header_row = ttk.Frame(top_bar)
        header_row.grid(row=0, column=0, sticky="ew")

        ttk.Label(header_row, text="Generator").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Combobox(header_row, textvariable=self.mode_var, values=["subject", "master"], state="readonly", width=14).pack(side=tk.LEFT)

        ttk.Label(header_row, text="People / Setup").pack(side=tk.LEFT, padx=(12, 8))
        ttk.Combobox(
            header_row,
            textvariable=self.person_count_var,
            values=[
                "solo",
                "1girl",
                "1boy",
                "1other",
                "2girls",
                "2boys",
                "2others",
                "3girls",
                "3boys",
                "multiple girls",
                "multiple boys",
                "multiple others",
                "group",
                "crowd",
                "orgy",
                "gangbang",
            ],
            state="readonly",
            width=18,
        ).pack(side=tk.LEFT)

        ttk.Label(header_row, text="Seed").pack(side=tk.LEFT, padx=(12, 8))
        ttk.Entry(header_row, textvariable=self.seed_var, width=12).pack(side=tk.LEFT)

        ttk.Label(header_row, text="Checksum").pack(side=tk.LEFT, padx=(12, 0))
        ttk.Entry(header_row, textvariable=self.prompt_checksum_var, state="readonly", width=18).pack(side=tk.LEFT)
        ttk.Entry(header_row, textvariable=self.prompt_checksum_input_var, width=18).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(header_row, text="Apply", command=self.apply_saved_checksum).pack(side=tk.LEFT, padx=(6, 0))

        top_bar.columnconfigure(0, weight=1)

        controls_row = ttk.Frame(top_bar)
        controls_row.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Checkbutton(controls_row, text="Photo boost", variable=self.photo_boost_var).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(controls_row, text="Use BREAK between subjects", variable=self.use_break_var).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Button(controls_row, text="Open", command=self.open_prompt_window_if_available).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(controls_row, text="Load", command=self.load_prompt_file).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(controls_row, text="Reset all defaults", command=self.reset_all_person_defaults).pack(side=tk.LEFT)
        self.invoke_canvas_button = ttk.Button(controls_row, text="Invoke Canvas", command=self.open_canvas_window)
        self.invoke_canvas_button.pack(side=tk.LEFT, padx=(8, 0))

        top_bar.columnconfigure(0, weight=1)

        self.person_tabs = {}
        self.person_tab_widgets = {}
        self.person_tab_var_map = {}

        self.person_notebook = ttk.Notebook(main)
        self.person_notebook.pack(fill=tk.BOTH, expand=True, padx=(0, 12))

        self._create_person_tab(
            1,
            "Person 1",
            self.field_widgets,
            self.field_values,
            self.nsfw_var,
            self.nsfw_modifier_var,
            self.bondage_var,
            self.bondage_enabled_var,
            include_custom_tags=True,
        )

        self._create_person_tab(
            2,
            "Person 2",
            self.duo_field_widgets,
            self.duo_field_values,
            self.subject_2_nsfw_var,
            self.subject_2_nsfw_modifier_var,
            self.subject_2_bondage_var,
            self.subject_2_bondage_enabled_var,
            include_custom_tags=False,
        )
        self.duo_field_widgets["gender"].configure(textvariable=self.duo_second_gender_var)
        self.duo_field_widgets["pose"].configure(textvariable=self.duo_second_pose_var)
        self.duo_field_widgets["expression"].configure(textvariable=self.duo_second_expression_var)
        self.duo_field_widgets["body_type"].configure(textvariable=self.duo_second_body_type_var)
        self.duo_field_widgets["gender"].set("female")
        self.duo_field_widgets["pose"].set("Random")
        self.duo_field_widgets["expression"].set("Random")
        self.duo_field_widgets["body_type"].set("None")

        self._refresh_person_tabs()

        scene_frame = ttk.LabelFrame(main, text="Scene / Master controls")
        scene_frame.pack(fill=tk.X, pady=(0, 10))

        scene_rows = [
            ("Rating", sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.RATINGS)), self.rating_var),
            ("Score scheme", sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.SCORE_SCHEMES)), self.score_scheme_var),
            ("Image Quality", sort_combo_values(["None", "score_9", "score_8_up", "score_7_up", "masterpiece", "best quality", "highly detailed", "intricate details"]), self.image_quality_var),
            ("Location", sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.LOCATIONS)), self.location_var),
            ("Lighting", sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.LIGHTING)), self.lighting_var),
            ("Camera", sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.CAMERAS)), self.camera_var),
            ("Sex act", sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.SEX_ACTS)), self.sex_act_var),
            ("Sex position", sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.SEX_POSITIONS)), self.sex_position_var),
        ]

        for idx, (label_text, values, var) in enumerate(scene_rows):
            row = idx // 2
            col = idx % 2
            ttk.Label(scene_frame, text=label_text).grid(row=row, column=col * 2, sticky="w", padx=(10, 8), pady=7)
            combo = ttk.Combobox(scene_frame, textvariable=var, values=values, state="readonly", width=30)
            combo.set(var.get())
            combo.grid(row=row, column=col * 2 + 1, sticky="ew", padx=(0, 12), pady=7)

        scene_bg = self.root.cget("bg")
        self.validator_frame = ttk.LabelFrame(scene_frame, text="Inpaint Cheat Sheet / Preset")
        self.validator_frame.grid(row=0, column=4, rowspan=4, sticky="nsew", padx=20, pady=10)

        validator_content = tk.Frame(self.validator_frame, bg=scene_bg)
        validator_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(validator_content, text="Inpaint Presets:", bg=scene_bg, anchor="w", justify=tk.LEFT).pack(
            fill="x",
            pady=(5, 5),
        )

        self.preset_combo = ttk.Combobox(validator_content, state="readonly", width=45)
        self.preset_combo.pack(fill="x", pady=(5, 5))
        self.preset_combo["values"] = ["None", *sorted(list(self.INPAINT_PRESET_DB.keys()))]
        self.preset_combo.set("None")
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_change)

        self.preset_info_text = tk.Text(
            validator_content,
            height=5,
            width=45,
            wrap="word",
            bg="#f5f5f5",
            state="disabled",
            cursor="arrow",
            takefocus=0,
        )
        self.preset_info_text.pack(fill="x", pady=(5, 5))

        status_frame = tk.Frame(validator_content, bg=scene_bg)
        status_frame.pack(fill="x", pady=(5, 5), side=tk.BOTTOM)

        self.pony_status_signal = tk.Label(status_frame, width=2, height=1, bg="#2e7d32", relief=tk.SOLID, bd=1)
        self.pony_status_signal.pack(side=tk.LEFT, anchor="n", padx=(0, 10))
        self.pony_status_message = tk.Label(
            status_frame,
            text="🟢 Prompt-Status: Optimal für Pony",
            fg="#2e7d32",
            bg=scene_bg,
            anchor="w",
            justify=tk.LEFT,
            wraplength=360,
            width=42,
        )
        self.pony_status_message.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_text_label = self.pony_status_message

        scene_frame.columnconfigure(1, weight=1)
        scene_frame.columnconfigure(3, weight=1)
        scene_frame.columnconfigure(4, weight=1, minsize=420)

        self.scene_frame = scene_frame

        self.load_settings()
        if not self.settings_path.exists():
            self.reset_to_neutral_defaults()
            self.apply_people_setup_defaults()
        else:
            self.update_duo_visibility()
            self.update_mode_visibility()
        self.mode_var.trace_add("write", lambda *_: (self.update_duo_visibility(), self.update_mode_visibility()))
        self.person_count_var.trace_add("write", self._sync_person_count_state)
        self.nsfw_var.trace_add("write", lambda *_: self.update_mode_visibility())
        self._update_invoke_canvas_button_state()
        self._refresh_pony_status_indicator()
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_settings_state(self):
        state = {
            "mode": self.mode_var.get(),
            "seed": self.seed_var.get(),
            "person_count": self.person_count_var.get(),
            "duo_second_gender": self.duo_second_gender_var.get(),
            "duo_second_pose": self.duo_second_pose_var.get(),
            "duo_second_expression": self.duo_second_expression_var.get(),
            "duo_second_body_type": self.duo_second_body_type_var.get(),
            "nsfw": bool(self.nsfw_var.get()),
            "subject_2_nsfw": bool(self.subject_2_nsfw_var.get()),
            "photo_boost": bool(self.photo_boost_var.get()),
            "nsfw_modifier": self._get_active_tags_text(self.field_widgets, "nsfw"),
            "subject_2_nsfw_modifier": self._get_active_tags_text(self.duo_field_widgets, "nsfw"),
            "bondage": self._get_active_tags_text(self.field_widgets, "bondage"),
            "subject_2_bondage": self._get_active_tags_text(self.duo_field_widgets, "bondage"),
            "bondage_enabled": bool(self.bondage_enabled_var.get()),
            "subject_2_bondage_enabled": bool(self.subject_2_bondage_enabled_var.get()),
            "rating": self.rating_var.get(),
            "score_scheme": self.score_scheme_var.get(),
            "image_quality": self.image_quality_var.get(),
            "location": self.location_var.get(),
            "lighting": self.lighting_var.get(),
            "camera": self.camera_var.get(),
            "sex_act": self.sex_act_var.get(),
            "sex_position": self.sex_position_var.get(),
            "use_break": bool(self.use_break_var.get()),
            "custom_tags": self._read_widget_value(self.field_widgets.get("custom_tags_field")),
            "extra_clothing_tags": self._read_widget_value(self.extra_clothing_tags),
        }
        for key, widget in self.field_widgets.items():
            state[f"field_{key}"] = self._read_widget_value(widget)
        for key, widget in self.duo_field_widgets.items():
            state[f"duo_{key}"] = self._read_widget_value(widget)
        state["checksum_store"] = self.checksum_store
        return state

    def apply_settings_state(self, state):
        if not isinstance(state, dict):
            return

        value_mapping = {
            "mode": self.mode_var,
            "seed": self.seed_var,
            "person_count": self.person_count_var,
            "duo_second_gender": self.duo_second_gender_var,
            "duo_second_pose": self.duo_second_pose_var,
            "duo_second_expression": self.duo_second_expression_var,
            "duo_second_body_type": self.duo_second_body_type_var,
            "rating": self.rating_var,
            "score_scheme": self.score_scheme_var,
            "image_quality": self.image_quality_var,
            "location": self.location_var,
            "lighting": self.lighting_var,
            "camera": self.camera_var,
            "sex_act": self.sex_act_var,
            "sex_position": self.sex_position_var,
        }
        for key, var in value_mapping.items():
            if key in state and state[key] is not None:
                var.set(sanitize_gui_text(state[key]))

        self.nsfw_var.set(bool(state.get("nsfw", False)))
        self.subject_2_nsfw_var.set(bool(state.get("subject_2_nsfw", False)))
        self.photo_boost_var.set(bool(state.get("photo_boost", False)))
        bondage_tags = state.get("bondage", "")
        subject_2_bondage_tags = state.get("subject_2_bondage", "")
        self.bondage_enabled_var.set(bool(state.get("bondage_enabled", bool(split_tag_text(bondage_tags)))))
        self.subject_2_bondage_enabled_var.set(bool(state.get("subject_2_bondage_enabled", bool(split_tag_text(subject_2_bondage_tags)))))
        self.image_quality_var.set(str(state.get("image_quality", "None")))
        self.use_break_var.set(bool(state.get("use_break", True)))

        for key, widget in self.field_widgets.items():
            saved_value = state.get(f"field_{key}")
            if saved_value is not None:
                widget.set(str(saved_value))

        for key, widget in self.duo_field_widgets.items():
            saved_value = state.get(f"duo_{key}")
            if saved_value is not None:
                widget.set(str(saved_value))

        custom_tags = state.get("custom_tags", state.get("field_custom_tags_field", ""))
        duo_custom_tags = state.get("duo_custom_tags_field", "")
        extra_clothing_tags = state.get("extra_clothing_tags", "")
        custom_widget, _ = self._get_widget_text_fields(self.field_widgets)
        duo_custom_widget, _ = self._get_widget_text_fields(self.duo_field_widgets)
        set_text_widget_text(custom_widget, custom_tags)
        set_text_widget_text(duo_custom_widget, duo_custom_tags)
        set_text_widget_text(self.extra_clothing_tags, extra_clothing_tags)
        self._apply_widget_tag_state(
            self.field_widgets,
            nsfw_tags=state.get("nsfw_modifier", ""),
            bondage_tags=bondage_tags,
        )
        self._apply_widget_tag_state(
            self.duo_field_widgets,
            nsfw_tags=state.get("subject_2_nsfw_modifier", ""),
            bondage_tags=subject_2_bondage_tags,
        )

        checksum_store = state.get("checksum_store")
        if isinstance(checksum_store, dict):
            self.checksum_store = checksum_store

    def save_settings(self):
        try:
            payload = self.get_settings_state()
            self.settings_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def reset_to_neutral_defaults(self):
        for widget_map, values_map in (
            (self.field_widgets, self.field_values),
            (self.duo_field_widgets, self.duo_field_values),
        ):
            for key, (values, default) in values_map.items():
                widget = widget_map.get(key)
                if widget is None:
                    continue
                widget.set(get_neutral_reset_value(values, default))

        neutral_var_values = [
            (self.mode_var, "subject"),
            (self.seed_var, "42"),
            (self.person_count_var, "solo"),
            (self.duo_second_gender_var, get_neutral_reset_value(self.gender_options, "female")),
            (self.duo_second_pose_var, get_neutral_reset_value(self.duo_field_values.get("pose", ([], "Random"))[0], "Random")),
            (self.duo_second_expression_var, get_neutral_reset_value(self.duo_field_values.get("expression", ([], "Random"))[0], "Random")),
            (self.duo_second_body_type_var, get_neutral_reset_value(self.duo_field_values.get("body_type", ([], "None"))[0], "None")),
            (self.rating_var, get_neutral_reset_value(pony_nodes.get_sorted_list(pony_nodes.RATINGS), self.rating_var.get())),
            (self.score_scheme_var, get_neutral_reset_value(pony_nodes.get_sorted_list(pony_nodes.SCORE_SCHEMES), self.score_scheme_var.get())),
            (self.image_quality_var, "None"),
            (self.location_var, get_neutral_reset_value(pony_nodes.get_sorted_list(pony_nodes.LOCATIONS), self.location_var.get())),
            (self.lighting_var, get_neutral_reset_value(pony_nodes.get_sorted_list(pony_nodes.LIGHTING), self.lighting_var.get())),
            (self.camera_var, get_neutral_reset_value(pony_nodes.get_sorted_list(pony_nodes.CAMERAS), self.camera_var.get())),
            (self.sex_act_var, get_neutral_reset_value(pony_nodes.get_sorted_list(pony_nodes.SEX_ACTS), "None")),
            (self.sex_position_var, get_neutral_reset_value(pony_nodes.get_sorted_list(pony_nodes.SEX_POSITIONS), "None")),
        ]
        for var, value in neutral_var_values:
            var.set(value)

        self.nsfw_var.set(False)
        self.subject_2_nsfw_var.set(False)
        self.photo_boost_var.set(False)
        self.nsfw_modifier_var.set("None")
        self.subject_2_nsfw_modifier_var.set("None")
        self.bondage_var.set("None")
        self.subject_2_bondage_var.set("None")
        self.bondage_enabled_var.set(False)
        self.subject_2_bondage_enabled_var.set(False)
        self.use_break_var.set(True)
        self.prompt_checksum_var.set("")
        self.prompt_checksum_input_var.set("")

        custom_widget, clothing_widget = self._get_widget_text_fields(self.field_widgets)
        duo_custom_widget, duo_clothing_widget = self._get_widget_text_fields(self.duo_field_widgets)
        for text_widget in (custom_widget, clothing_widget, duo_custom_widget, duo_clothing_widget):
            set_text_widget_text(text_widget, "")

        self._apply_widget_tag_state(self.field_widgets, nsfw_tags="", bondage_tags="")
        self._apply_widget_tag_state(self.duo_field_widgets, nsfw_tags="", bondage_tags="")

    def load_settings(self):
        if not self.settings_path.exists():
            if self.settings_template_path.exists():
                try:
                    state = json.loads(self.settings_template_path.read_text(encoding="utf-8"))
                    self.settings_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception:
                    return
            else:
                return
        try:
            with self.settings_path.open("r", encoding="utf-8") as fh:
                state = json.load(fh)
            self.apply_settings_state(state)
        except Exception:
            return

    def apply_saved_checksum(self):
        checksum = (self.prompt_checksum_input_var.get() or "").strip()
        if not checksum:
            return

        state = self.checksum_store.get(checksum)
        if state is None:
            state = load_checksum_state_from_settings(self.settings_path, checksum)
            if state is not None:
                self.checksum_store[checksum] = state

        if state is None:
            messagebox.showwarning("Checksum not found", "No saved prompt settings were found for this checksum.")
            return

        self.apply_settings_state(state)
        self.prompt_checksum_input_var.set(checksum)
        self.prompt_checksum_var.set(checksum)

    def on_close(self):
        self.save_settings()
        self.root.destroy()

    def _build_subject_panel(self, parent, widget_map, values_map, nsfw_var, nsfw_modifier_var, bondage_var, bondage_enabled_var=None, include_custom_tags=True, person_index=None):
        rows = []
        for key, (values, default) in values_map.items():
            label = key.replace("_", " ").title()
            rows.append((key, label, values, default))

        for index, (key, label, values, default) in enumerate(rows):
            row = index // 2
            col = index % 2
            ttk.Label(parent, text=label).grid(row=row, column=col * 2, sticky="w", padx=(0, 0), pady=0)
            combo_var = tk.StringVar(value=default)
            combo = ttk.Combobox(parent, values=values, state="readonly", width=18, textvariable=combo_var)
            combo.grid(row=row, column=col * 2 + 1, sticky="ew", padx=(0, 0), pady=0)
            widget_map[key] = combo
            self._bind_widget_preview_refresh(combo)

        content_row_start = (len(rows) // 2) + 1

        widget_map["nsfw_master_list"] = list(self.nsfw_master_list)
        widget_map["bondage_master_list"] = list(self.bondage_master_list)
        widget_map["custom_tags_master_list"] = list(self.custom_tags_master_list)
        active_nsfw_tags = widget_map.setdefault("active_nsfw_tags", [])
        active_bondage_tags = widget_map.setdefault("active_bondage_tags", [])
        active_custom_tags = widget_map.setdefault("active_custom_tags", [])

        if widget_map is self.field_widgets:
            self.active_nsfw_tags = active_nsfw_tags
            self.active_bondage_tags = active_bondage_tags
            self.active_custom_tags = active_custom_tags

        if bondage_enabled_var is None:
            bondage_enabled_var = tk.BooleanVar(value=False)

        if include_custom_tags:
            extras = ttk.Frame(parent)
            extras.grid(row=content_row_start, column=0, columnspan=4, sticky="ew", pady=(12, 0))

            ttk.Label(extras, text="Custom tags").grid(row=0, column=0, sticky="nw", padx=(0, 4), pady=(2, 0))
            custom_tags_field = tk.Text(extras, height=3, width=42)
            custom_tags_field.grid(row=0, column=1, sticky="ew", pady=(2, 0))
            self._configure_auto_grow_text_widget(custom_tags_field, min_lines=3, max_lines=8)
            self._configure_custom_tag_mirroring(widget_map, custom_tags_field)
            self._bind_widget_preview_refresh(custom_tags_field)
            widget_map["custom_tags_field"] = custom_tags_field

            ttk.Label(extras, text="Extra clothing tags").grid(row=1, column=0, sticky="nw", padx=(0, 4), pady=(8, 0))
            clothing_tags_field = tk.Text(extras, height=2, width=42)
            clothing_tags_field.grid(row=1, column=1, sticky="ew", pady=(8, 0))
            self._bind_widget_preview_refresh(clothing_tags_field)
            widget_map["clothing_tags_field"] = clothing_tags_field

            if widget_map is self.field_widgets:
                self.custom_tags = custom_tags_field
                self.extra_clothing_tags = clothing_tags_field

            extras.columnconfigure(1, weight=1)
            button_row = content_row_start + 2
        else:
            button_row = content_row_start

        nsfw_row = ttk.Frame(parent)
        nsfw_row.grid(row=button_row, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        ttk.Checkbutton(nsfw_row, text="NSFW Modifier", variable=nsfw_var).pack(side=tk.LEFT, padx=(0, 10))
        combo = ttk.Combobox(
            nsfw_row,
            textvariable=nsfw_modifier_var,
            values=self._get_available_tag_values(widget_map, "nsfw"),
            state="readonly",
            width=26,
        )
        combo.set(nsfw_modifier_var.get())
        combo.pack(side=tk.LEFT)
        combo.bind("<<ComboboxSelected>>", lambda _event, wm=widget_map: self._handle_tag_selection(wm, "nsfw"))
        widget_map["nsfw_modifier_var"] = nsfw_modifier_var
        widget_map["nsfw_tags_combo"] = combo

        nsfw_tags_container = ttk.Frame(parent)
        nsfw_tags_container.grid(row=button_row + 1, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        widget_map["nsfw_tags_container"] = nsfw_tags_container
        if widget_map is self.field_widgets:
            self.nsfw_tags_container = nsfw_tags_container

        bondage_row = ttk.Frame(parent)
        bondage_row.grid(row=button_row + 2, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        ttk.Checkbutton(bondage_row, text="Bondage / Restraint", variable=bondage_enabled_var).pack(side=tk.LEFT, padx=(0, 10))
        bondage_combo = ttk.Combobox(
            bondage_row,
            textvariable=bondage_var,
            values=self._get_available_tag_values(widget_map, "bondage"),
            state="readonly" if bondage_enabled_var.get() else "disabled",
            width=22,
        )
        bondage_combo.set(bondage_var.get())
        bondage_combo.pack(side=tk.LEFT)
        widget_map["bondage_var"] = bondage_var
        widget_map["bondage_tags_combo"] = bondage_combo

        bondage_tags_container = ttk.Frame(parent)
        bondage_tags_container.grid(row=button_row + 3, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        widget_map["bondage_tags_container"] = bondage_tags_container
        if widget_map is self.field_widgets:
            self.bondage_tags_container = bondage_tags_container

        def _sync_bondage_state(*_):
            if bondage_enabled_var.get():
                bondage_combo.configure(state="readonly")
            else:
                bondage_var.set("None")
                self._get_widget_tag_list(widget_map, "bondage")[:] = []
                self._sync_tag_controls(widget_map, "bondage")
                bondage_combo.configure(state="disabled")

        bondage_enabled_var.trace_add("write", _sync_bondage_state)
        bondage_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event, wm=widget_map: self._handle_tag_selection(wm, "bondage"),
        )

        _sync_bondage_state()
        self._sync_tag_controls(widget_map, "nsfw")
        self._sync_tag_controls(widget_map, "bondage")

        if include_custom_tags:
            buttons = ttk.Frame(parent)
            buttons.grid(row=button_row + 4, column=0, columnspan=4, sticky="ew", pady=(10, 6))
            ttk.Button(buttons, text="Generate", command=self.generate).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
            ttk.Button(buttons, text="Copy prompt", command=self.copy_prompt).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
            ttk.Button(buttons, text="Reset defaults", command=lambda: self.reset_person_defaults(person_index)).pack(side=tk.LEFT, fill=tk.X, expand=True)
            preview_row = button_row + 5
        else:
            preview_row = button_row + 4
            buttons = ttk.Frame(parent)
            buttons.grid(row=button_row + 4, column=0, columnspan=4, sticky="ew", pady=(10, 6))
            ttk.Button(buttons, text="Reset defaults", command=lambda: self.reset_person_defaults(person_index)).pack(side=tk.LEFT, fill=tk.X, expand=True)

        if widget_map is not self.field_widgets:
            preview_frame = ttk.Frame(parent)
            preview_frame.grid(row=preview_row, column=0, columnspan=4, sticky="ew", pady=(6, 6))
            ttk.Label(preview_frame, text="Prompt preview").pack(anchor="w", pady=(0, 4))
            preview = tk.Text(preview_frame, height=4, wrap=tk.WORD, state="disabled", cursor="arrow", takefocus=0, font=("TkDefaultFont", 9))
            preview.pack(fill=tk.BOTH, expand=True)
            for event in ("<Button-1>", "<ButtonRelease-1>", "<B1-Motion>", "<Double-Button-1>"):
                preview.bind(event, lambda event=None, _event=event: "break")
            widget_map["prompt_preview"] = preview

        for i in range(4):
            parent.columnconfigure(i, weight=1)

    def _create_person_tab(self, person_index, title, widget_map, values_map, nsfw_var, nsfw_modifier_var, bondage_var, bondage_enabled_var=None, include_custom_tags=True):
        frame = ttk.Frame(self.person_notebook)
        form = ttk.Frame(frame, padding=(8, 0, 8, 0))
        form.pack(fill=tk.BOTH, expand=True)
        self._build_subject_panel(
            form,
            widget_map,
            values_map,
            nsfw_var=nsfw_var,
            nsfw_modifier_var=nsfw_modifier_var,
            bondage_var=bondage_var,
            bondage_enabled_var=bondage_enabled_var,
            include_custom_tags=include_custom_tags,
            person_index=person_index,
        )
        self.person_notebook.add(frame, text=title)
        self.person_tabs[person_index] = frame
        self.person_tab_widgets[person_index] = widget_map
        self.person_tab_var_map[person_index] = {
            "nsfw": nsfw_var,
            "nsfw_modifier": nsfw_modifier_var,
            "bondage": bondage_var,
            "bondage_enabled": bondage_enabled_var,
        }
        self._apply_defaults_to_widget_map(widget_map, self._get_people_setup_defaults())

    def _get_person_setup_count(self):
        value = (self.person_count_var.get() or "solo").strip().lower()
        single_values = {"solo", "1girl", "1boy", "1other"}
        if value in single_values:
            return 1

        if value in {"2girls", "2boys", "2others"}:
            return 2
        if value in {"3girls", "3boys", "multiple girls", "multiple boys", "multiple others"}:
            return 3
        if value in {"group", "crowd", "orgy", "gangbang"}:
            return 4

        for token in value.split():
            if token.isdigit():
                return max(1, min(int(token), 4))
        return 1

    def _refresh_person_tabs(self):
        if not hasattr(self, "person_notebook"):
            return

        count = self._get_person_setup_count()
        maximum_tabs = 4

        for index in range(1, maximum_tabs + 1):
            frame = self.person_tabs.get(index)
            if index <= count:
                if frame is None:
                    if index == 1:
                        widget_map = self.field_widgets
                        values_map = self.field_values
                        nsfw_var = self.nsfw_var
                        nsfw_modifier_var = self.nsfw_modifier_var
                        bondage_var = self.bondage_var
                        bondage_enabled_var = self.bondage_enabled_var
                        include_custom_tags = True
                    elif index == 2:
                        widget_map = self.duo_field_widgets
                        values_map = self.duo_field_values
                        nsfw_var = self.subject_2_nsfw_var
                        nsfw_modifier_var = self.subject_2_nsfw_modifier_var
                        bondage_var = self.subject_2_bondage_var
                        bondage_enabled_var = self.subject_2_bondage_enabled_var
                        include_custom_tags = True
                    else:
                        widget_map = {}
                        values_map = self.field_values
                        nsfw_var = tk.BooleanVar(value=False)
                        nsfw_modifier_var = tk.StringVar(value="None")
                        bondage_var = tk.StringVar(value="None")
                        bondage_enabled_var = tk.BooleanVar(value=False)
                        include_custom_tags = True
                    self._create_person_tab(index, f"Person {index}", widget_map, values_map, nsfw_var, nsfw_modifier_var, bondage_var, bondage_enabled_var, include_custom_tags)
                else:
                    try:
                        self.person_notebook.index(frame)
                    except tk.TclError:
                        self.person_notebook.add(frame, text=f"Person {index}")
            else:
                if frame is not None:
                    try:
                        self.person_notebook.forget(frame)
                    except Exception:
                        pass
                    self.person_tabs.pop(index, None)
                    self.person_tab_widgets.pop(index, None)
                    self.person_tab_var_map.pop(index, None)

        for idx in (1, 2):
            if idx in self.person_tabs:
                self.person_notebook.select(self.person_tabs[idx])
                break

    def _hide_person_tabs(self):
        self._refresh_person_tabs()

    def _get_people_setup_defaults(self):
        setup_name = (self.person_count_var.get() or "solo").strip().lower()

        setup_defaults = {
            "solo": {"gender": "female", "body_type": "human"},
            "1girl": {"gender": "female", "body_type": "human"},
            "1boy": {"gender": "male", "body_type": "human"},
            "1other": {"gender": "androgynous", "body_type": "human"},
            "2girls": {"gender": "female", "body_type": "human"},
            "2boys": {"gender": "male", "body_type": "human"},
            "2others": {"gender": "androgynous", "body_type": "human"},
            "3girls": {"gender": "female", "body_type": "human"},
            "3boys": {"gender": "male", "body_type": "human"},
            "multiple girls": {"gender": "female", "body_type": "human"},
            "multiple boys": {"gender": "male", "body_type": "human"},
            "multiple others": {"gender": "androgynous", "body_type": "human"},
            "group": {"gender": "female", "body_type": "human"},
            "crowd": {"gender": "female", "body_type": "human"},
            "orgy": {"gender": "female", "body_type": "human"},
            "gangbang": {"gender": "female", "body_type": "human"},
        }

        return setup_defaults.get(setup_name, {"gender": "female", "body_type": "human"})

    def _apply_defaults_to_widget_map(self, widget_map, defaults):
        if not isinstance(widget_map, dict):
            return
        if "gender" in widget_map and widget_map["gender"].instate(["!disabled"]):
            widget_map["gender"].set(defaults["gender"])
        if "body_type" in widget_map and widget_map["body_type"].instate(["!disabled"]):
            widget_map["body_type"].set(defaults["body_type"])

    def reset_person_defaults(self, person_index):
        if person_index is None:
            person_index = 1

        if person_index == 1:
            widget_map = self.field_widgets
            values_map = self.field_values
            custom_widget = widget_map.get("custom_tags_field")
            if custom_widget is not None:
                custom_widget.delete("1.0", tk.END)
            if hasattr(self, "extra_clothing_tags"):
                self.extra_clothing_tags.delete("1.0", tk.END)
            self.nsfw_var.set(False)
            self.bondage_enabled_var.set(False)
            self.bondage_var.set("None")
        elif person_index == 2:
            widget_map = self.duo_field_widgets
            values_map = self.duo_field_values
            custom_widget = widget_map.get("custom_tags_field")
            if custom_widget is not None:
                custom_widget.delete("1.0", tk.END)
            self.subject_2_nsfw_var.set(False)
            self.subject_2_bondage_enabled_var.set(False)
            self.subject_2_bondage_var.set("None")
        else:
            widget_map = self.person_tab_widgets.get(person_index, {})
            values_map = self.field_values
            var_map = self.person_tab_var_map.get(person_index, {})
            if var_map:
                var_map.get("nsfw", tk.BooleanVar(value=False)).set(False)
                var_map.get("bondage_enabled", tk.BooleanVar(value=False)).set(False)
                var_map.get("bondage", tk.StringVar(value="None")).set("None")

        if not widget_map:
            return

        for key, (values, default) in values_map.items():
            if key in widget_map:
                widget_map[key].set(get_neutral_reset_value(values, default))

        self._apply_widget_tag_state(widget_map, nsfw_tags="", bondage_tags="")

        clothing_widget = widget_map.get("clothing_tags_field")
        if clothing_widget is not None:
            try:
                clothing_widget.delete("1.0", tk.END)
            except Exception:
                pass

        self._queue_prompt_preview_refresh()

    def reset_all_person_defaults(self):
        self.reset_to_neutral_defaults()
        active_count = self._get_person_setup_count()
        for person_index in range(1, active_count + 1):
            self.reset_person_defaults(person_index)

        for person_index in range(3, 5):
            widget_map = self.person_tab_widgets.get(person_index, {})
            for key, (values, default) in self.field_values.items():
                if key in widget_map:
                    widget_map[key].set(get_neutral_reset_value(values, default))
            custom_widget, clothing_widget = self._get_widget_text_fields(widget_map)
            set_text_widget_text(custom_widget, "")
            set_text_widget_text(clothing_widget, "")
            self._apply_widget_tag_state(widget_map, nsfw_tags="", bondage_tags="")

        if self.preset_combo is not None:
            self.preset_combo.set("None")
        self._set_readonly_info_text(self.preset_info_text, "")
        self.canvas_denoise_var.set(0.65)
        self._queue_prompt_preview_refresh()

    def apply_people_setup_defaults(self):
        defaults = self._get_people_setup_defaults()

        if "gender" in self.field_widgets and self.field_widgets["gender"].instate(["!disabled"]):
            self.field_widgets["gender"].set(defaults["gender"])
        if "body_type" in self.field_widgets and self.field_widgets["body_type"].instate(["!disabled"]):
            self.field_widgets["body_type"].set(defaults["body_type"])

        if "gender" in self.duo_field_widgets and self.duo_field_widgets["gender"].instate(["!disabled"]):
            self.duo_field_widgets["gender"].set(defaults["gender"])
            self.duo_second_gender_var.set(defaults["gender"])
        if "body_type" in self.duo_field_widgets and self.duo_field_widgets["body_type"].instate(["!disabled"]):
            self.duo_field_widgets["body_type"].set(defaults["body_type"])
            self.duo_second_body_type_var.set(defaults["body_type"])

        for person_index in range(3, 5):
            self._apply_defaults_to_widget_map(self.person_tab_widgets.get(person_index, {}), defaults)

    def _is_multi_person_setup(self):
        value = (self.person_count_var.get() or "solo").strip().lower()
        single_values = {"solo", "1girl", "1boy", "1other"}
        return value not in single_values

    def update_duo_visibility(self):
        if hasattr(self, "person_notebook"):
            self._hide_person_tabs()
            return
        if self._is_multi_person_setup():
            self.right_subject_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            self.subject_2_nsfw_var.set(self.subject_2_nsfw_var.get())
        else:
            self.right_subject_frame.pack_forget()

    def update_mode_visibility(self):
        self.scene_frame.pack(fill=tk.X, pady=(0, 8))

    def _update_invoke_canvas_button_state(self):
        if getattr(self, "invoke_canvas_button", None) is None:
            return

        state = "normal" if (self.person_count_var.get() or "").strip().lower() == "solo" else "disabled"
        self.invoke_canvas_button.configure(state=state)

    def _sync_person_count_state(self, *_):
        self.apply_people_setup_defaults()
        self.update_duo_visibility()
        self.update_mode_visibility()
        self._update_invoke_canvas_button_state()

    def _get_tag_control_config(self, tag_kind):
        if tag_kind == "nsfw":
            return {
                "active_key": "active_nsfw_tags",
                "master_key": "nsfw_master_list",
                "master_attr": "nsfw_master_list",
                "combo_key": "nsfw_tags_combo",
                "container_key": "nsfw_tags_container",
                "var_key": "nsfw_modifier_var",
            }
        if tag_kind == "bondage":
            return {
                "active_key": "active_bondage_tags",
                "master_key": "bondage_master_list",
                "master_attr": "bondage_master_list",
                "combo_key": "bondage_tags_combo",
                "container_key": "bondage_tags_container",
                "var_key": "bondage_var",
            }
        return {
            "active_key": "active_custom_tags",
            "master_key": "custom_tags_master_list",
            "master_attr": "custom_tags_master_list",
            "combo_key": "custom_tags_combo",
            "container_key": "custom_tags_container",
            "var_key": "custom_tags_var",
        }

    def _get_widget_tag_list(self, widget_map, tag_kind):
        if widget_map is None:
            widget_map = self.field_widgets
        config = self._get_tag_control_config(tag_kind)
        return widget_map.setdefault(config["active_key"], [])

    def _get_active_tags_text(self, widget_map, tag_kind):
        return compose_tag_text(self._get_widget_tag_list(widget_map, tag_kind))

    def _get_available_tag_values(self, widget_map, tag_kind):
        if widget_map is None:
            widget_map = self.field_widgets

        config = self._get_tag_control_config(tag_kind)
        master_list = widget_map.get(config["master_key"], getattr(self, config["master_attr"], []))
        active_lower = {tag.lower() for tag in self._get_widget_tag_list(widget_map, tag_kind)}
        available_values = []
        for value in master_list:
            if value in {"None", "Random"} or value.lower() not in active_lower:
                available_values.append(value)
        return available_values

    def update_tags_ui(self, widget_map, tag_kind):
        config = self._get_tag_control_config(tag_kind)
        container = widget_map.get(config["container_key"])
        if container is None:
            return

        for child in container.winfo_children():
            child.destroy()

        max_columns = 10
        pill_bg = "#f5f5f5"
        pill_border = "#d9d9d9"

        for column in range(max_columns):
            container.grid_columnconfigure(column, weight=0)

        active_tags = self._get_widget_tag_list(widget_map, tag_kind)
        for index, tag in enumerate(active_tags):
            row = index // max_columns
            column = index % max_columns

            pill = tk.Frame(
                container,
                bg=pill_bg,
                highlightbackground=pill_border,
                highlightthickness=1,
                bd=0,
            )
            pill.grid(row=row, column=column, padx=2, pady=2, sticky="w")

            tk.Label(
                pill,
                text=tag,
                bg=pill_bg,
                relief="flat",
                padx=0,
                pady=0,
            ).pack(side=tk.LEFT, padx=(5, 2), pady=3)
            tk.Button(
                pill,
                text="X",
                width=2,
                bg=pill_bg,
                activebackground=pill_bg,
                relief="flat",
                bd=0,
                padx=0,
                pady=0,
                command=lambda selected_tag=tag, wm=widget_map, kind=tag_kind: self._remove_active_tag(wm, kind, selected_tag),
            ).pack(side=tk.LEFT, padx=(0, 5), pady=2)

    def _render_tag_pills(self, widget_map, tag_kind):
        self.update_tags_ui(widget_map, tag_kind)

    def _sync_tag_controls(self, widget_map, tag_kind):
        config = self._get_tag_control_config(tag_kind)
        combo = widget_map.get(config["combo_key"])
        combo_var = widget_map.get(config["var_key"])
        if combo is not None:
            combo.configure(values=self._get_available_tag_values(widget_map, tag_kind))
        if combo_var is not None:
            combo_var.set("None")
        self._render_tag_pills(widget_map, tag_kind)

    def _handle_tag_selection(self, widget_map, tag_kind):
        config = self._get_tag_control_config(tag_kind)
        combo_var = widget_map.get(config["var_key"])
        if combo_var is None:
            return

        selected_tag = sanitize_gui_text(combo_var.get()).strip()
        if selected_tag in {"", "None", "Random"}:
            combo_var.set("None")
            return

        active_tags = self._get_widget_tag_list(widget_map, tag_kind)
        if selected_tag.lower() not in {tag.lower() for tag in active_tags}:
            active_tags.append(selected_tag)

        self._sync_tag_controls(widget_map, tag_kind)
        self._queue_prompt_preview_refresh()

    def _remove_active_tag(self, widget_map, tag_kind, tag_to_remove):
        active_tags = self._get_widget_tag_list(widget_map, tag_kind)
        active_tags[:] = [tag for tag in active_tags if tag.lower() != tag_to_remove.lower()]
        if tag_kind in {"nsfw", "bondage"}:
            auto_key = f"auto_{tag_kind}_tags"
            auto_tags = widget_map.get(auto_key, [])
            if tag_to_remove.lower() in {tag.lower() for tag in auto_tags}:
                custom_widget = widget_map.get("custom_tags_field")
                remove_tags_from_text_widget(custom_widget, [tag_to_remove])
                self._sync_special_tag_controls_from_custom_text(widget_map)
        self._sync_tag_controls(widget_map, tag_kind)
        self._queue_prompt_preview_refresh()

    def _apply_widget_tag_state(self, widget_map, nsfw_tags="", bondage_tags=""):
        self._get_widget_tag_list(widget_map, "nsfw")[:] = split_tag_text(nsfw_tags)
        self._get_widget_tag_list(widget_map, "bondage")[:] = split_tag_text(bondage_tags)
        self._sync_tag_controls(widget_map, "nsfw")
        self._sync_tag_controls(widget_map, "bondage")

    def _adjust_auto_grow_text_widget_height(self, widget, min_lines=3, max_lines=8):
        if widget is None or not widget.winfo_exists():
            return

        try:
            chars_per_line = max(20, int(widget.cget("width")))
        except Exception:
            chars_per_line = 42

        text = widget.get("1.0", "end-1c")
        logical_lines = text.splitlines() or [""]
        display_lines = 0
        for logical_line in logical_lines:
            expanded_line = logical_line.expandtabs(4)
            display_lines += max(1, (len(expanded_line) + chars_per_line - 1) // chars_per_line)

        target_height = max(min_lines, min(max_lines, display_lines))
        if int(widget.cget("height")) != target_height:
            widget.configure(height=target_height)

    def _configure_auto_grow_text_widget(self, widget, min_lines=3, max_lines=8):
        if widget is None:
            return

        widget.configure(wrap=tk.WORD)

        def _auto_grow_callback(_event=None, text_widget=widget, min_height=min_lines, max_height=max_lines):
            self._adjust_auto_grow_text_widget_height(text_widget, min_height, max_height)

        widget._auto_grow_callback = _auto_grow_callback
        widget.bind("<KeyRelease>", _auto_grow_callback, add="+")
        widget.bind("<Configure>", _auto_grow_callback, add="+")
        widget.bind("<FocusOut>", _auto_grow_callback, add="+")
        widget.after_idle(_auto_grow_callback)

    def _extract_matching_master_tags(self, tags, master_list):
        normalized_master = {}
        for value in master_list or []:
            if value in {"None", "Random"}:
                continue
            normalized_master[str(value).strip().lower()] = str(value).strip()

        matches = []
        seen = set()
        for tag in tags:
            normalized = normalized_master.get(tag.lower())
            if not normalized:
                continue
            lowered = normalized.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            matches.append(normalized)
        return matches

    def _sync_special_tag_controls_from_custom_text(self, widget_map):
        custom_widget = widget_map.get("custom_tags_field")
        if custom_widget is None:
            return

        custom_tags = split_tag_text(self._read_widget_value(custom_widget))
        for tag_kind in ("nsfw", "bondage"):
            config = self._get_tag_control_config(tag_kind)
            master_list = widget_map.get(config["master_key"], getattr(self, config["master_attr"], []))
            auto_key = f"auto_{tag_kind}_tags"
            previous_auto_tags = widget_map.get(auto_key, [])
            previous_auto_lower = {tag.lower() for tag in previous_auto_tags}
            active_tags = self._get_widget_tag_list(widget_map, tag_kind)
            manual_tags = [tag for tag in active_tags if tag.lower() not in previous_auto_lower]
            auto_tags = self._extract_matching_master_tags(custom_tags, master_list)
            widget_map[auto_key] = auto_tags

            merged_tags = list(manual_tags)
            merged_lower = {tag.lower() for tag in merged_tags}
            for tag in auto_tags:
                if tag.lower() in merged_lower:
                    continue
                merged_tags.append(tag)
                merged_lower.add(tag.lower())

            active_tags[:] = merged_tags
            self._sync_tag_controls(widget_map, tag_kind)

    def _configure_custom_tag_mirroring(self, widget_map, widget):
        if widget is None:
            return

        def _tag_sync_callback(_event=None, wm=widget_map):
            self._sync_special_tag_controls_from_custom_text(wm)

        widget._tag_sync_callback = _tag_sync_callback
        widget.bind("<KeyRelease>", _tag_sync_callback, add="+")
        widget.bind("<ButtonRelease>", _tag_sync_callback, add="+")
        widget.bind("<FocusOut>", _tag_sync_callback, add="+")
        widget.after_idle(_tag_sync_callback)

    def _get_widget_text_fields(self, widget_map=None):
        if widget_map is None:
            widget_map = self.field_widgets

        custom_widget = widget_map.get("custom_tags_field")
        clothing_widget = widget_map.get("clothing_tags_field")

        if clothing_widget is None:
            clothing_widget = getattr(self, "extra_clothing_tags", None)

        return custom_widget, clothing_widget

    def _read_widget_value(self, widget):
        if widget is None:
            return ""

        if isinstance(widget, tk.Text):
            return widget.get("1.0", tk.END).strip()

        if hasattr(widget, "get"):
            try:
                return widget.get()
            except TypeError:
                return ""

        return ""

    def _queue_prompt_preview_refresh(self, *_):
        if self.root is None or not self.root.winfo_exists():
            return
        if self._preview_refresh_job is not None:
            try:
                self.root.after_cancel(self._preview_refresh_job)
            except Exception:
                pass
        self._preview_refresh_job = self.root.after(80, self._refresh_live_preview)

    def _refresh_live_preview(self, *_):
        try:
            positive_prompt, _, _, _ = self._build_current_positive_prompt()
            self.update_prompt_preview(positive_prompt)
        except Exception:
            pass
        try:
            self._refresh_pony_status_indicator()
        except Exception:
            pass
        self._preview_refresh_job = None

    def _get_pony_status_values(self):
        values = {
            "location": self.location_var.get(),
            "camera": self.camera_var.get(),
        }
        for key in ("gender", "body_type", "special_skin_type", "full_outfit", "top_clothing", "bottom_clothing", "headwear", "shoes", "accessories"):
            values[key] = self._read_widget_value(self.field_widgets.get(key))
        return values

    def _refresh_pony_status_indicator(self):
        if self.pony_status_signal is None or self.pony_status_message is None:
            return

        status = evaluate_pony_model_status(self._get_pony_status_values())
        self.pony_status_signal.configure(bg=status["signal_color"])
        self.pony_status_message.configure(text=status["message"], fg=status["text_color"])

    def _bind_widget_preview_refresh(self, widget):
        if widget is None:
            return

        if isinstance(widget, tk.Text):
            widget.bind("<KeyRelease>", self._queue_prompt_preview_refresh, add="+")
            widget.bind("<ButtonRelease>", self._queue_prompt_preview_refresh, add="+")
            return

        if isinstance(widget, ttk.Combobox):
            widget.bind("<<ComboboxSelected>>", self._queue_prompt_preview_refresh)
            widget.bind("<FocusOut>", self._queue_prompt_preview_refresh)
            return

        if hasattr(widget, "bind"):
            widget.bind("<FocusOut>", self._queue_prompt_preview_refresh)

    def _is_feral_gender(self, value):
        return str(value or "").strip().lower().startswith("feral")

    def _get_base_gender_from_value(self, value):
        text = str(value or "").strip().lower()
        if text == "feral female":
            return "female"
        if text == "feral male":
            return "male"
        return str(value or "").strip()

    def _build_current_positive_prompt(self):
        active_person_count = self._get_person_setup_count()
        subject_prompts = []
        sub1_prompt = None
        sub2_prompt = None
        feral_mode_enabled = False

        for person_index in range(1, active_person_count + 1):
            if person_index == 1:
                values = self.get_subject_values()
            elif person_index == 2:
                values = self.get_duo_second_values()
            else:
                widget_map = self.person_tab_widgets.get(person_index, {})
                if not widget_map:
                    continue
                values = {}
                for key in self.field_values:
                    values[key] = self._read_widget_value(widget_map.get(key))
                custom_widget, clothing_widget = self._get_widget_text_fields(widget_map)
                values["custom_tags"] = self._read_widget_value(custom_widget)
                values["extra_clothing_tags"] = self._read_widget_value(clothing_widget)
                values["nsfw_modifier"] = self._get_active_tags_text(widget_map, "nsfw")
                values["bondage_restraint"] = self._get_active_tags_text(widget_map, "bondage")

            raw_gender = values.get("gender", "")
            if self._is_feral_gender(raw_gender):
                feral_mode_enabled = True

            values[f"person_{person_index}_special_skin"] = values.get("special_skin_type", "None")

            prompt_values = dict(values)
            prompt_values["person_index"] = str(person_index)
            prompt_values["gender"] = self._get_base_gender_from_value(raw_gender)
            gender_value = (prompt_values.get("gender") or "").strip()
            if gender_value in {"", "None", "Random"}:
                prompt_values["lead_token"] = "person"
            else:
                prompt_values["lead_token"] = gender_value

            if prompt_values.get("body_type") in {"", "None", "Random"}:
                prompt_values["body_type"] = ""

            built_prompt = pony_nodes.build_subject_prompt_from_ui(prompt_values)
            subject_prompts.append(built_prompt)

            if person_index == 1:
                sub1_prompt = built_prompt
            elif person_index == 2:
                sub2_prompt = built_prompt

        if not subject_prompts:
            default_p = pony_nodes.build_subject_prompt_from_ui({"lead_token": "person", "gender": "human"})
            subject_prompts = [default_p]
            sub1_prompt = default_p

        setup_val = (self.person_count_var.get() or "").strip()
        if setup_val and setup_val != "None":
            global_tag = f"{setup_val}, "
        else:
            global_tag = ""

        subjects_str = " BREAK ".join(subject_prompts) if self.use_break_var.get() else ", ".join(subject_prompts)
        prompt_base = f"{global_tag}{subjects_str}"

        custom_widget, clothing_widget = self._get_widget_text_fields(self.field_widgets)
        extra_clothing_text = self._read_widget_value(clothing_widget)

        if extra_clothing_text:
            prompt_base = f"{prompt_base}, {extra_clothing_text}"

        sex_act_text = self.sex_act_var.get().strip()
        sex_position_text = self.sex_position_var.get().strip()
        if sex_act_text and sex_act_text not in {"None", "Random"}:
            prompt_base = f"{prompt_base}, {sex_act_text}"
        if sex_position_text and sex_position_text not in {"None", "Random"}:
            prompt_base = f"{prompt_base}, {sex_position_text}"

        if feral_mode_enabled:
            prompt_base = f"{prompt_base}, {', '.join(FERAL_POSITIVE_TAGS)}"

        final_positive_prompt = attach_scene_metadata(
            prompt_base,
            rating=self.rating_var.get(),
            image_quality=self.image_quality_var.get(),
            location=self.location_var.get(),
            lighting=self.lighting_var.get(),
            camera=self.camera_var.get(),
            photo_boost=self.photo_boost_var.get(),
        )
        return final_positive_prompt, sub1_prompt, sub2_prompt, feral_mode_enabled

    def _build_current_master_negative_prompt(self, seed, sub1_prompt, sub2_prompt):
        if self.mode_var.get() != "master":
            return compose_negative_prompt("-")

        node = CR_Pony_Master()
        _, negative = node.generate_master(
            seed=seed,
            rating=self.rating_var.get(),
            location=self.location_var.get(),
            lighting=self.lighting_var.get(),
            camera=self.camera_var.get(),
            use_break=self.use_break_var.get(),
            nsfw_mode=self.nsfw_var.get(),
            sex_act=self.sex_act_var.get(),
            sex_position=self.sex_position_var.get(),
            score_scheme=self.score_scheme_var.get(),
            source_bias="None",
            strong_anime_bias=False,
            style_preset="None",
            subject_1=sub1_prompt,
            subject_2=sub2_prompt,
            subject_3=None,
            subject_4=None,
            photo_boost=False,
        )
        return compose_negative_prompt(negative)

    def _build_canvas_inpaint_text(self):
        try:
            seed = int(self.seed_var.get())
        except ValueError:
            messagebox.showerror("Invalid seed", "Seed must be an integer.")
            return None

        feral_mode_enabled = self._is_feral_gender(self._read_widget_value(self.field_widgets.get("gender")))

        selected_character_tags = self._get_canvas_selected_character_tags()
        custom_character_tags = self._get_canvas_custom_tags()

        node = CR_Pony_Master()
        positive_prompt, negative_prompt = node.generate_master(
            seed=seed,
            rating=self.rating_var.get(),
            location=self.location_var.get(),
            lighting=self.lighting_var.get(),
            camera=self.camera_var.get(),
            use_break=self.use_break_var.get(),
            nsfw_mode=self.nsfw_var.get(),
            sex_act=self.sex_act_var.get(),
            sex_position=self.sex_position_var.get(),
            score_scheme=self.score_scheme_var.get(),
            source_bias="None",
            strong_anime_bias=False,
            style_preset="None",
            subject_1=None,
            subject_2=None,
            subject_3=None,
            subject_4=None,
            photo_boost=False,
        )
        positive = self._sanitize_canvas_positive_prompt(
            positive_prompt,
            selected_character_tags=selected_character_tags,
            custom_character_tags=custom_character_tags,
            seed=seed,
            feral_mode=feral_mode_enabled,
        )

        extra_negatives = [FERAL_NEGATIVE_TAGS] if feral_mode_enabled else []
        negative = compose_negative_prompt(negative_prompt or "-", *extra_negatives)

        return positive, negative

    def _get_canvas_selected_character_tags(self):
        tags = []
        seen = set()
        blocked_keys = {"location", "lighting"}

        for key, _label in self.canvas_include_options:
            if key in blocked_keys:
                continue

            include_var = self.canvas_include_vars.get(key)
            if include_var is None or not include_var.get():
                continue

            widget = self.field_widgets.get(key) if isinstance(self.field_widgets, dict) else None
            value = self._read_widget_value(widget)
            if pony_nodes._is_ignored_value(value):
                continue

            text = str(value).strip()
            if key == "gender":
                text = self._get_base_gender_from_value(text)
            if not text:
                continue

            lowered = text.lower()
            if lowered in seen:
                continue

            seen.add(lowered)
            tags.append(text)

        return tags

    def _sync_canvas_include_defaults_from_main_fields(self):
        for key, _label in self.canvas_include_options:
            include_var = self.canvas_include_vars.get(key)
            if include_var is None:
                continue

            widget = self.field_widgets.get(key) if isinstance(self.field_widgets, dict) else None
            value = self._read_widget_value(widget)
            include_var.set(should_auto_enable_canvas_detail(value))

    def _get_canvas_custom_tags(self):
        custom_widget, _clothing_widget = self._get_widget_text_fields(self.field_widgets)
        raw_text = self._read_widget_value(custom_widget)
        if not raw_text:
            return []

        tags = []
        seen = set()
        for part in raw_text.split(","):
            text = re.sub(r"\s{2,}", " ", part).strip()
            if not text:
                continue
            lowered = text.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            tags.append(text)
        return tags

    def _sanitize_canvas_positive_prompt(self, prompt_text, selected_character_tags=None, custom_character_tags=None, seed=0, feral_mode=False):
        prefix_parts = []
        for value in (self.rating_var.get(), self.image_quality_var.get()):
            text = sanitize_gui_text(value).strip()
            if text and not pony_nodes._is_ignored_value(text):
                prefix_parts.append(text)

        if self.photo_boost_var.get():
            prefix_parts.append("source_photography, raw photo, hyperrealistic, 8k uhd, film grain")

        allowed_tags = [sanitize_gui_text(tag).strip() for tag in (selected_character_tags or []) if sanitize_gui_text(tag).strip()]
        custom_tags = [sanitize_gui_text(tag).strip() for tag in (custom_character_tags or []) if sanitize_gui_text(tag).strip()]
        if custom_tags:
            allowed_tags.extend(custom_tags)

        blocked_scene_tags = {self.location_var.get(), self.lighting_var.get(), self.camera_var.get()}
        allowed_tags = filter_blocked_canvas_character_tags(allowed_tags, blocked_scene_tags)

        if feral_mode:
            allowed_tags.extend(FERAL_POSITIVE_TAGS)

        if not allowed_tags:
            return ", ".join(prefix_parts)

        weight_value = sanitize_gui_text(self.canvas_weight_var.get() or "1.15").strip()
        if not weight_value:
            weight_value = "1.15"

        weighted_block = f"({', '.join(allowed_tags)}:{weight_value})"
        parts = [part for part in prefix_parts if part]
        parts.append(weighted_block)
        return ", ".join(parts)

    def update_canvas_prompts(self):
        feral_mode_enabled = self._is_feral_gender(self._read_widget_value(self.field_widgets.get("gender")))

        blocked_scene_values = {
            sanitize_gui_text(self.location_var.get()).strip().lower(),
            sanitize_gui_text(self.lighting_var.get()).strip().lower(),
            sanitize_gui_text(self.camera_var.get()).strip().lower(),
        }
        blocked_scene_values = {value for value in blocked_scene_values if value}

        bracket_tags = []
        seen = set()

        for key, _label in self.canvas_include_options:
            include_var = self.canvas_include_vars.get(key)
            if include_var is None or not include_var.get():
                continue

            widget = self.field_widgets.get(key) if isinstance(self.field_widgets, dict) else None
            value = sanitize_gui_text(self._read_widget_value(widget)).strip()
            if pony_nodes._is_ignored_value(value):
                continue

            if key == "gender":
                value = sanitize_gui_text(self._get_base_gender_from_value(value)).strip()

            lowered = value.lower()
            if not value or lowered in seen or lowered in blocked_scene_values:
                continue

            seen.add(lowered)
            bracket_tags.append(value)

        custom_widget, _clothing_widget = self._get_widget_text_fields(self.field_widgets)
        raw_custom_tags = sanitize_gui_text(self._read_widget_value(custom_widget)).replace("(", "").replace(")", "")
        blocked_custom_tags = {
            "score_9",
            "score_8_up",
            "score_7_up",
            "rating_explicit",
            "source_photography",
            "raw photo",
            "hyperrealistic",
            "masterpiece",
            "location",
            "lighting",
            "camera",
            "background",
            "snowy mountain background",
            "bright rim lighting",
            "dark cinematic lighting",
            "night background",
            "sci-fi lighting",
            "dark misty forest background",
            "volcanic background",
            "dramatic lighting",
            "volumetric lighting",
            "dynamic high-contrast studio lighting",
            "dynamic dramatic lighting",
            "underwater lighting",
            "jungle temple ruins background",
            *blocked_scene_values,
        }

        if raw_custom_tags:
            for part in raw_custom_tags.split(","):
                part = part.strip()
                text = sanitize_gui_text(re.sub(r"\s{2,}", " ", part)).strip()
                if not text:
                    continue

                lowered = text.lower()
                if lowered in seen or lowered in blocked_custom_tags:
                    continue

                seen.add(lowered)
                bracket_tags.append(text)

        if feral_mode_enabled:
            for tag in FERAL_POSITIVE_TAGS:
                text = sanitize_gui_text(tag).strip()
                if not text:
                    continue
                lowered = text.lower()
                if lowered in seen:
                    continue
                seen.add(lowered)
                bracket_tags.append(text)

        weight_value = sanitize_gui_text(self.canvas_weight_var.get() or "1.15").strip()
        final_positive_prompt = compose_canvas_positive_prompt(bracket_tags, weight_value)

        # Safety scrub: remove blocked lighting/background phrases from the final canvas prompt as well.
        blocked_canvas_phrases = {phrase.lower() for phrase in blocked_custom_tags}
        cleaned_final_parts = []
        for part in final_positive_prompt.split(","):
            cleaned_part = sanitize_gui_text(re.sub(r"\s{2,}", " ", part)).strip()
            if not cleaned_part:
                continue
            if cleaned_part.lower() in blocked_canvas_phrases:
                continue
            cleaned_final_parts.append(cleaned_part)
        final_positive_prompt = ", ".join(cleaned_final_parts)

        if self.canvas_positive_text is not None:
            set_text_widget_text(self.canvas_positive_text, final_positive_prompt)

        try:
            seed = int(self.seed_var.get())
        except ValueError:
            seed = 0

        node = CR_Pony_Master()
        _, negative_prompt = node.generate_master(
            seed=seed,
            rating=self.rating_var.get(),
            location=self.location_var.get(),
            lighting=self.lighting_var.get(),
            camera=self.camera_var.get(),
            use_break=self.use_break_var.get(),
            nsfw_mode=self.nsfw_var.get(),
            sex_act=self.sex_act_var.get(),
            sex_position=self.sex_position_var.get(),
            score_scheme=self.score_scheme_var.get(),
            source_bias="None",
            strong_anime_bias=False,
            style_preset="None",
            subject_1=None,
            subject_2=None,
            subject_3=None,
            subject_4=None,
            photo_boost=False,
        )

        extra_negatives = [FERAL_NEGATIVE_TAGS] if feral_mode_enabled else []
        negative = compose_negative_prompt(negative_prompt or "-", *extra_negatives)

        if self.canvas_negative_text is not None:
            set_text_widget_text(self.canvas_negative_text, negative)

    def refresh_canvas_prompt_fields(self):
        self.update_canvas_prompts()

    def update_preview_text(self):
        self._queue_prompt_preview_refresh()

    def _set_readonly_info_text(self, text_widget, value):
        if text_widget is None:
            return
        text_widget.configure(state="normal")
        set_text_widget_text(text_widget, value)
        text_widget.configure(state="disabled")

    def _get_preset_value(self, preset, keys, default_value):
        for key in keys:
            if key in preset:
                return preset.get(key)
        return default_value

    def on_preset_change(self, event):
        if self.preset_combo is None:
            return

        preset_key = (self.preset_combo.get() or "").strip()
        if preset_key in {"", "None"}:
            self._set_readonly_info_text(self.preset_info_text, "")
            self.update_preview_text()
            return

        preset = self.INPAINT_PRESET_DB.get(preset_key, {})
        if not isinstance(preset, dict):
            return

        body_type_value = sanitize_gui_text(self._get_preset_value(preset, ["body_type", "Body Type", "bodyType"], "None"))
        special_skin_value = sanitize_gui_text(self._get_preset_value(preset, ["special_skin_type", "special_skin", "Special Skin Type", "specialSkinType"], "None"))
        positive_prompt_value = sanitize_gui_text(self._get_preset_value(preset, ["positive", "positive_prompt", "Positive Prompt", "positivePrompt"], ""))
        custom_tags_value = sanitize_gui_text(self._get_preset_value(preset, ["custom_tags", "Custom Tags", "customTags"], positive_prompt_value))
        negative_prompt_value = sanitize_gui_text(self._get_preset_value(preset, ["negative", "negative_prompt", "Negative Prompt", "negativePrompt"], "-"))
        info_value = sanitize_gui_text(self._get_preset_value(preset, ["info", "Info"], ""))

        denoise_raw = self._get_preset_value(
            preset,
            ["denoise", "denoise_strength", "denoising", "denoising_strength", "Denoising Strength"],
            0.65,
        )
        try:
            denoise_value = float(denoise_raw)
        except (TypeError, ValueError):
            denoise_value = 0.65

        if "body_type" in self.field_widgets:
            self.field_widgets["body_type"].set(body_type_value)
        if "special_skin_type" in self.field_widgets:
            self.field_widgets["special_skin_type"].set(special_skin_value)

        self.canvas_denoise_var.set(denoise_value)
        self.update_denoising_recommendation(denoise_value)

        custom_tags_widget, _ = self._get_widget_text_fields(self.field_widgets)
        set_text_widget_text(custom_tags_widget, custom_tags_value)

        if self.canvas_negative_text is not None:
            set_text_widget_text(self.canvas_negative_text, negative_prompt_value if negative_prompt_value else "-")

        self._set_readonly_info_text(self.preset_info_text, info_value)
        self.update_preview_text()
        self.update_canvas_prompts()

    def update_denoising_recommendation(self, val):
        try:
            value = float(val)
        except (TypeError, ValueError):
            value = 0.65

        if value <= 0.15:
            message = "🔍 [0.0 - 0.15] Minimal: Nur leichte Fehlerkorrektur (Stil & Textur bleiben identisch)"
            color = "#4d4d4d"
            font = None
        elif value <= 0.35:
            message = "✨ [0.16 - 0.35] Soft-Inpaint: Perfekt für Haut-Strukturen, Poren & sanfte Texturanpassungen"
            color = "#1f7a1f"
            font = None
        elif value <= 0.59:
            message = "🎨 [0.36 - 0.59] Modifikation: Formänderung bei bestehender Anatomie"
            color = "#d97706"
            font = None
        elif value <= 0.80:
            message = "🔥 [0.60 - 0.80] OPTIMAL: Komplette anatomische Neugenerierung (z.B. Lykaner/Anatomie-Details)"
            color = "#8b0000"
            font = ("TkDefaultFont", 9, "bold")
        else:
            message = "⚠️ [0.81 - 1.00] Extrem: Ignoriert das Originalbild fast komplett (Gefahr von Bildfehlern)"
            color = "#7b2cbf"
            font = None

        if self.canvas_denoise_recommendation_label is not None:
            self.canvas_denoise_recommendation_label.configure(text=message, fg=color)
            if font is not None:
                self.canvas_denoise_recommendation_label.configure(font=font)
            else:
                self.canvas_denoise_recommendation_label.configure(font=("TkDefaultFont", 9))

        return message

    def update_prompt_preview(self, prompt_text):
        preview_text = (prompt_text or "").strip()
        if not preview_text:
            preview_text = "Generate a prompt to preview it here."

        preview_widgets = []
        if self.prompt_preview is not None:
            preview_widgets.append(self.prompt_preview)
        for widget_map in self.person_tab_widgets.values():
            preview_widget = widget_map.get("prompt_preview")
            if preview_widget is not None:
                preview_widgets.append(preview_widget)

        for preview_widget in preview_widgets:
            apply_preview_tag_highlights(preview_widget, preview_text)

    def get_subject_values(self):
        values = {}
        for key in self.field_values:
            values[key] = self._read_widget_value(self.field_widgets[key])

        custom_widget, clothing_widget = self._get_widget_text_fields(self.field_widgets)
        values["custom_tags"] = self._read_widget_value(custom_widget)
        values["extra_clothing_tags"] = self._read_widget_value(clothing_widget)
        values["nsfw_modifier"] = self._get_active_tags_text(self.field_widgets, "nsfw")
        values["bondage_restraint"] = self._get_active_tags_text(self.field_widgets, "bondage")
        return values

    def get_duo_second_values(self):
        values = {}
        for key in self.field_values:
            if key in self.duo_field_widgets:
                values[key] = self._read_widget_value(self.duo_field_widgets[key])
            else:
                values[key] = self.field_values[key][1]

        custom_widget, clothing_widget = self._get_widget_text_fields(self.duo_field_widgets)
        values["custom_tags"] = self._read_widget_value(custom_widget)
        values["extra_clothing_tags"] = self._read_widget_value(clothing_widget)
        values["nsfw_modifier"] = self._get_active_tags_text(self.duo_field_widgets, "nsfw")
        values["bondage_restraint"] = self._get_active_tags_text(self.duo_field_widgets, "bondage")
        return values

    def apply_selected_category_tags(self):
        return

    def open_prompt_window_if_available(self):
        if self.output_window is not None and self.output_window.winfo_exists():
            self.output_window.deiconify()
            self.output_window.lift()
            return

        if self.output_positive is None:
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return

        positive_text = self.output_positive.get("1.0", tk.END).strip()
        negative_text = self.output_negative.get("1.0", tk.END).strip() if self.output_negative is not None else "-"
        if not positive_text:
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return

        self.open_output_window(positive_text, negative_text if negative_text else "-")

    def open_canvas_window(self):
        if (self.person_count_var.get() or "").strip().lower() != "solo":
            return

        if self.canvas_window is None or not self.canvas_window.winfo_exists():
            self.canvas_window = tk.Toplevel(self.root)
            self.canvas_window.title("Canvas Inpaint")
            self.canvas_window.geometry("900x820")
            self.canvas_window.minsize(850, 780)
            self.canvas_window.protocol("WM_DELETE_WINDOW", self.close_canvas_window)

            params_frame = ttk.LabelFrame(self.canvas_window, text="Canvas parameters")
            params_frame.pack(fill=tk.X, padx=12, pady=(12, 8))

            ttk.Label(params_frame, text="Denoising Strength").pack(anchor="w", padx=12, pady=(10, 4))
            denoise_scale = tk.Scale(
                params_frame,
                from_=0.0,
                to=1.0,
                resolution=0.01,
                orient=tk.HORIZONTAL,
                variable=self.canvas_denoise_var,
                command=self.update_denoising_recommendation,
                length=320,
            )
            denoise_scale.pack(fill=tk.X, padx=12, pady=(0, 4))
            self.canvas_denoise_recommendation_label = tk.Label(
                params_frame,
                text="",
                anchor="w",
                justify=tk.LEFT,
                wraplength=280,
                padx=2,
            )
            self.canvas_denoise_recommendation_label.pack(fill=tk.X, padx=12, pady=(0, 10))
            self.update_denoising_recommendation(self.canvas_denoise_var.get())

            include_frame = ttk.LabelFrame(self.canvas_window, text="Include Character Details")
            include_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
            weight_row = ttk.Frame(include_frame)
            weight_row.grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(8, 4))
            ttk.Label(weight_row, text="Klammer-Gewichtung:").pack(side=tk.LEFT)
            weight_entry = ttk.Entry(weight_row, textvariable=self.canvas_weight_var, width=8)
            weight_entry.pack(side=tk.LEFT, padx=(8, 0))

            include_columns = 4
            for idx, (key, label_text) in enumerate(self.canvas_include_options):
                include_var = self.canvas_include_vars.get(key)
                if include_var is None:
                    continue
                row = (idx // include_columns) + 1
                col = idx % include_columns
                ttk.Checkbutton(
                    include_frame,
                    text=label_text,
                    variable=include_var,
                    command=self.update_canvas_prompts,
                ).grid(row=row, column=col, sticky="w", padx=(10, 10), pady=(6, 4))
            for col in range(include_columns):
                include_frame.columnconfigure(col, weight=1)

            prompts_frame = ttk.Frame(self.canvas_window, padding=10)
            prompts_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

            prompts_pane = ttk.Panedwindow(prompts_frame, orient=tk.VERTICAL)
            prompts_pane.pack(fill=tk.BOTH, expand=True)

            positive_frame = ttk.Frame(prompts_pane)
            ttk.Label(positive_frame, text="Positive prompt:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(5, 2))
            positive_text_frame = ttk.Frame(positive_frame)
            positive_text_frame.pack(fill=tk.BOTH, expand=True)
            self.canvas_positive_text = tk.Text(positive_text_frame, wrap=tk.WORD, height=8, padx=10, pady=10)
            positive_scrollbar = ttk.Scrollbar(positive_text_frame, orient=tk.VERTICAL, command=self.canvas_positive_text.yview)
            self.canvas_positive_text.configure(yscrollcommand=positive_scrollbar.set)
            self.canvas_positive_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            positive_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            prompts_pane.add(positive_frame, weight=1)

            negative_frame = ttk.Frame(prompts_pane)
            ttk.Label(negative_frame, text="Negative prompt:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(5, 2))
            negative_text_frame = ttk.Frame(negative_frame)
            negative_text_frame.pack(fill=tk.BOTH, expand=True)
            self.canvas_negative_text = tk.Text(negative_text_frame, wrap=tk.WORD, height=6, padx=10, pady=10)
            negative_scrollbar = ttk.Scrollbar(negative_text_frame, orient=tk.VERTICAL, command=self.canvas_negative_text.yview)
            self.canvas_negative_text.configure(yscrollcommand=negative_scrollbar.set)
            self.canvas_negative_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            negative_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            prompts_pane.add(negative_frame, weight=1)

            button_bar = ttk.Frame(self.canvas_window)
            button_bar.pack(fill=tk.X, padx=12, pady=(0, 12))
            ttk.Button(button_bar, text="Copy positive", command=self.copy_canvas_prompt).pack(side=tk.LEFT, padx=(0, 8))
            ttk.Button(button_bar, text="Copy negative", command=self.copy_canvas_negative_prompt).pack(side=tk.LEFT, padx=(0, 8))
            ttk.Button(button_bar, text="Close", command=self.close_canvas_window).pack(side=tk.RIGHT)
        else:
            self.canvas_window.deiconify()
            self.canvas_window.lift()

        self._sync_canvas_include_defaults_from_main_fields()
        self.update_canvas_prompts()

    def close_canvas_window(self):
        if self.canvas_window is None or not self.canvas_window.winfo_exists():
            return
        self.canvas_window.withdraw()

    def copy_canvas_prompt(self):
        if self.canvas_positive_text is None:
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return

        text = self.canvas_positive_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Positive prompt copied to clipboard.")

    def copy_canvas_negative_prompt(self):
        if self.canvas_negative_text is None:
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return

        text = self.canvas_negative_text.get("1.0", tk.END).strip()
        if not text or text == "-":
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Negative prompt copied to clipboard.")

    def open_output_window(self, positive_text, negative_text=None):
        if self.output_window is None or not self.output_window.winfo_exists():
            self.output_window = tk.Toplevel(self.root)
            self.output_window.title("Generated Prompt")
            self.output_window.geometry("980x620")
            self.output_window.minsize(760, 420)

            positive_frame = ttk.Frame(self.output_window)
            positive_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 8))

            ttk.Label(positive_frame, text="Positiver Prompt:", anchor="w").pack(fill=tk.X, anchor="w", pady=(0, 2))
            self.output_positive = tk.Text(positive_frame, wrap=tk.WORD, height=16, padx=8, pady=8)
            positive_scrollbar = ttk.Scrollbar(positive_frame, orient=tk.VERTICAL, command=self.output_positive.yview)
            self.output_positive.configure(yscrollcommand=positive_scrollbar.set)
            self.output_positive.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            positive_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            negative_frame = ttk.Frame(self.output_window)
            negative_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

            ttk.Label(negative_frame, text="Negativer Prompt:", anchor="w").pack(fill=tk.X, anchor="w", pady=(0, 2))
            self.output_negative = tk.Text(negative_frame, wrap=tk.WORD, height=10, padx=8, pady=8)
            negative_scrollbar = ttk.Scrollbar(negative_frame, orient=tk.VERTICAL, command=self.output_negative.yview)
            self.output_negative.configure(yscrollcommand=negative_scrollbar.set)
            self.output_negative.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            negative_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            button_bar = ttk.Frame(self.output_window)
            button_bar.pack(fill=tk.X, padx=12, pady=(0, 12))
            ttk.Button(button_bar, text="Load", command=self.load_prompt_file).pack(side=tk.LEFT)
            ttk.Button(button_bar, text="Save", command=self.save_prompt_file).pack(side=tk.LEFT, padx=(8, 0))
            ttk.Button(button_bar, text="Copy positive", command=self.copy_prompt).pack(side=tk.LEFT, padx=(8, 0))
            ttk.Button(button_bar, text="Copy negative", command=self.copy_negative_prompt).pack(side=tk.LEFT, padx=(8, 0))
            ttk.Button(button_bar, text="Close", command=self.close_prompt_window).pack(side=tk.RIGHT)

            self.text = self.output_positive
        else:
            self.output_window.deiconify()
            self.output_window.lift()

        if positive_text is not None:
            set_text_widget_text(self.output_positive, positive_text)
        if negative_text is not None:
            set_text_widget_text(self.output_negative, negative_text)
        else:
            set_text_widget_text(self.output_negative, "-")

    def close_prompt_window(self):
        if self.output_window is None or not self.output_window.winfo_exists():
            return

        positive_text = self.output_positive.get("1.0", tk.END).strip() if self.output_positive is not None else ""
        negative_text = self.output_negative.get("1.0", tk.END).strip() if self.output_negative is not None else "-"
        if positive_text:
            set_text_widget_text(self.output_positive, positive_text)
        if negative_text:
            set_text_widget_text(self.output_negative, negative_text)
        self.output_window.withdraw()

    def generate(self):
        checksum_value = (self.prompt_checksum_input_var.get() or "").strip()
        current_checksum = self.prompt_checksum_var.get().strip()
        if checksum_value and checksum_value in self.checksum_store and checksum_value != current_checksum:
            self.apply_settings_state(self.checksum_store[checksum_value])

        try:
            seed = int(self.seed_var.get())
        except ValueError:
            messagebox.showerror("Invalid seed", "Seed must be an integer.")
            return

          # --- GLOBALER CHECKSUMMEN-BLOCK (SPEICHERT ALLE TABS & OPTIONEN) ---
        person1_custom_widget, person1_clothing_widget = self._get_widget_text_fields(self.field_widgets)
        state_for_checksum = {
            "mode": self.mode_var.get(),
            "seed": self.seed_var.get(),
            "person_count": self.person_count_var.get(),
            "nsfw": bool(self.nsfw_var.get()),
            "photo_boost": bool(self.photo_boost_var.get()),
            "rating": self.rating_var.get(),
            "score_scheme": self.score_scheme_var.get(),
            "location": self.location_var.get(),
            "lighting": self.lighting_var.get(),
            "camera": self.camera_var.get(),
            "sex_act": self.sex_act_var.get(),
            "sex_position": self.sex_position_var.get(),
            "use_break": bool(self.use_break_var.get()),
            "custom_tags": self._read_widget_value(person1_custom_widget),
            "extra_clothing_tags": self._read_widget_value(person1_clothing_widget),
            "person_tabs_data": {}  # Speichert alle Karteikarten-Reiter dynamisch
        }

        # Wir lesen alle aktiven Tabs nacheinander aus
        active_person_count = self._get_person_setup_count()
        for person_index in range(1, active_person_count + 1):
            tab_data = {}

            if person_index == 1:
                for key, widget in self.field_widgets.items():
                    tab_data[key] = self._read_widget_value(widget)
                tab_data["nsfw_modifier"] = self._get_active_tags_text(self.field_widgets, "nsfw")
                tab_data["bondage"] = self._get_active_tags_text(self.field_widgets, "bondage")
                custom_widget, clothing_widget = self._get_widget_text_fields(self.field_widgets)
                tab_data["custom_tags_field"] = self._read_widget_value(custom_widget)
                tab_data["clothing_tags_field"] = self._read_widget_value(clothing_widget)

            elif person_index == 2:
                for key, widget in self.duo_field_widgets.items():
                    tab_data[key] = self._read_widget_value(widget)
                tab_data["nsfw_modifier"] = self._get_active_tags_text(self.duo_field_widgets, "nsfw")
                tab_data["bondage"] = self._get_active_tags_text(self.duo_field_widgets, "bondage")
                custom_widget, clothing_widget = self._get_widget_text_fields(self.duo_field_widgets)
                tab_data["custom_tags_field"] = self._read_widget_value(custom_widget)
                tab_data["clothing_tags_field"] = self._read_widget_value(clothing_widget)

            else:
                widget_map = self.person_tab_widgets.get(person_index, {})
                for key, widget in widget_map.items():
                    if key not in {"custom_tags_field", "clothing_tags_field"}:
                        tab_data[key] = self._read_widget_value(widget)

                var_map = self.person_tab_var_map.get(person_index, {})
                if "nsfw_modifier" in var_map:
                    tab_data["nsfw_modifier"] = self._get_active_tags_text(widget_map, "nsfw")
                if "bondage" in var_map:
                    tab_data["bondage"] = self._get_active_tags_text(widget_map, "bondage")
                custom_widget, clothing_widget = self._get_widget_text_fields(widget_map)
                tab_data["custom_tags_field"] = self._read_widget_value(custom_widget)
                tab_data["clothing_tags_field"] = self._read_widget_value(clothing_widget)

            state_for_checksum["person_tabs_data"][str(person_index)] = tab_data
            state_for_checksum[f"person_{person_index}_special_skin"] = tab_data.get("special_skin_type", "None")

        # Berechnet den fertigen, allumfassenden Base64-Teil-Code
        current_checksum = compute_prompt_checksum(state_for_checksum)
        self.checksum_store[current_checksum] = state_for_checksum
        self.prompt_checksum_var.set(current_checksum)
        self.prompt_checksum_input_var.set(current_checksum)
        # -------------------------------------------------------------------


        final_positive_prompt, sub1_prompt, sub2_prompt, feral_mode_enabled = self._build_current_positive_prompt()
        self.update_prompt_preview(final_positive_prompt)

        if self.mode_var.get() == "master":
            negative = self._build_current_master_negative_prompt(seed, sub1_prompt, sub2_prompt)
            if feral_mode_enabled:
                negative = compose_negative_prompt(negative, FERAL_NEGATIVE_TAGS)
            self.open_output_window(final_positive_prompt, negative)
        else:
            if feral_mode_enabled:
                self.open_output_window(final_positive_prompt, compose_negative_prompt("-", FERAL_NEGATIVE_TAGS))
            else:
                self.open_output_window(final_positive_prompt, compose_negative_prompt("-"))

    def save_prompt_file(self):
        if self.output_positive is None:
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return

        positive = self.output_positive.get("1.0", tk.END).strip()
        if not positive:
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return

        negative = self.output_negative.get("1.0", tk.END).strip() if self.output_negative is not None else "-"
        if not negative:
            negative = "-"

        checksum_value = (self.prompt_checksum_var.get() or self.prompt_checksum_input_var.get() or "").strip()
        comment_value = simpledialog.askstring(
            "Optional comment",
            "Add an optional comment for this saved prompt (leave empty for none):",
            initialvalue="",
        )

        file_path = filedialog.asksaveasfilename(
            title="Save prompt",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path:
            return

        save_prompt_to_file(file_path, positive, negative, checksum=checksum_value, comment=comment_value)
        messagebox.showinfo("Saved", f"Prompt saved to {file_path}.")

    def load_prompt_file(self):
        file_path = filedialog.askopenfilename(
            title="Load prompt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            positive, negative = load_prompt_from_file(file_path)
        except FileNotFoundError:
            messagebox.showerror("Load failed", "The selected file could not be found.")
            return

        if self.output_window is None or not self.output_window.winfo_exists():
            self.open_output_window(positive, negative)
            return

        set_text_widget_text(self.output_positive, positive)
        set_text_widget_text(self.output_negative, negative)
        self.output_window.deiconify()
        self.output_window.lift()

    def copy_prompt(self):
        if self.output_positive is None:
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return

        text = self.output_positive.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Positive prompt copied to clipboard.")

    def copy_negative_prompt(self):
        if self.output_negative is None:
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return

        text = self.output_negative.get("1.0", tk.END).strip()
        if not text or text == "-":
            messagebox.showwarning("No prompt", "Generate a prompt first.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Negative prompt copied to clipboard.")


def main():
    parser = argparse.ArgumentParser(description="Standalone generator for CyberRealistic Pony prompts")
    subparsers = parser.add_subparsers(dest="mode")
    build_subject_parser(subparsers)
    build_master_parser(subparsers)

    if len(sys.argv) == 1:
        root = tk.Tk()
        PromptGui(root)
        root.mainloop()
        return 0

    args = parser.parse_args()
    if args.mode == "subject":
        return 0 if run_subject(args) else 0
    elif args.mode == "master":
        run_master(args)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


    def restore_additional_tabs_safely(self, state):
        """
        Diese Funktion läuft völlig unabhängig und lädt die Daten 
        für Person 3 und 4, ohne die Hauptfunktion zu gefährden.
        """
        try:
            if not isinstance(state, dict):
                return
                
            tabs_data = state.get("person_tabs_data", {})
            if isinstance(tabs_data, dict) and tabs_data:
                for idx_str, data in tabs_data.items():
                    person_index = int(idx_str)
                    
                    # Person 1 und 2 wurden bereits geladen, wir füllen nur 3 und 4 auf
                    if person_index > 2:
                        if hasattr(self, 'person_tab_widgets'):
                            widget_map = self.person_tab_widgets.get(person_index, {})
                            for key, val in data.items():
                                if key in widget_map:
                                    widget_map[key].set(str(val))
                        
                        if hasattr(self, 'person_tab_var_map'):
                            var_map = self.person_tab_var_map.get(person_index, {})
                            if "nsfw_modifier" in data and "nsfw_modifier" in var_map:
                                var_map["nsfw_modifier"].set(str(data["nsfw_modifier"]))
                            if "bondage" in data and "bondage" in var_map:
                                var_map["bondage"].set(str(data["bondage"]))
        except Exception:
            pass
