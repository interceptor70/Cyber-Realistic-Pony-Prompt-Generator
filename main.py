import argparse
import hashlib
import sys
import base64
import json
import zlib
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, simpledialog

import nodes as pony_nodes
from nodes import CR_Pony_Subject, CR_Pony_Master


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
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", new_text)
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
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", new_text)
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
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", new_text)
        bondage_var_obj.set("None")
    except Exception as e:
        print(f"Fehler: {e}")


PREVIEW_NSWF_TAGS = list(dict.fromkeys([
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
]))


def apply_preview_tag_highlights(text_widget, prompt_text):
    if text_widget is None:
        return

    text_widget.configure(state="normal", cursor="arrow", takefocus=0)
    text_widget.delete("1.0", tk.END)
    text_widget.insert("1.0", prompt_text)

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

        self.field_values = {
            "gender": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.GENDERS)), "human"),
            "age": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.AGES)), "25"),
            "ethnicity": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.ETHNICITIES)), "Caucasian"),
            "body_type": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.ALL_BODY_TYPES)), "None"),
            "skin_texture": (sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.SKIN_TYPES)), "pale skin"),
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
            "hair_style", "eye_color", "full_outfit", "top_clothing", "bottom_clothing",
            "headwear", "shoes", "accessories", "pose", "breast_size", "breast_shape",
            "leg_feature", "butt_feature", "face_shape", "expression", "hair_length",
        ]
        self.duo_field_values = {}
        for key in duo_order:
            values, default = self.field_values[key]
            if key == "gender":
                values, default = sort_combo_values(pony_nodes.get_sorted_list(pony_nodes.GENDERS)), "human"
            elif key == "body_type":
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
        self.text = None
        self.prompt_preview = None
        self.settings_path = Path(__file__).with_name("prompt_settings.json")
        self.checksum_store = {}
        self.prompt_checksum_var = tk.StringVar(value="")
        self.prompt_checksum_input_var = tk.StringVar(value="")
        self._preview_refresh_job = None

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
        self.duo_field_widgets["gender"].set("human")
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

        self.scene_frame = scene_frame

        self.load_settings()
        if not self.settings_path.exists():
            self.reset_to_neutral_defaults()
            self.apply_people_setup_defaults()
        else:
            self.update_duo_visibility()
            self.update_mode_visibility()
        self.mode_var.trace_add("write", lambda *_: (self.update_duo_visibility(), self.update_mode_visibility()))
        self.person_count_var.trace_add("write", lambda *_: (self.apply_people_setup_defaults(), self.update_duo_visibility(), self.update_mode_visibility()))
        self.nsfw_var.trace_add("write", lambda *_: self.update_mode_visibility())
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
            "nsfw_modifier": self.nsfw_modifier_var.get(),
            "subject_2_nsfw_modifier": self.subject_2_nsfw_modifier_var.get(),
            "bondage": self.bondage_var.get(),
            "subject_2_bondage": self.subject_2_bondage_var.get(),
            "rating": self.rating_var.get(),
            "score_scheme": self.score_scheme_var.get(),
            "image_quality": self.image_quality_var.get(),
            "location": self.location_var.get(),
            "lighting": self.lighting_var.get(),
            "camera": self.camera_var.get(),
            "sex_act": self.sex_act_var.get(),
            "sex_position": self.sex_position_var.get(),
            "use_break": bool(self.use_break_var.get()),
            "custom_tags": self._read_widget_value(self.custom_tags),
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
            "nsfw_modifier": self.nsfw_modifier_var,
            "subject_2_nsfw_modifier": self.subject_2_nsfw_modifier_var,
            "bondage": self.bondage_var,
            "subject_2_bondage": self.subject_2_bondage_var,
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
                var.set(str(state[key]))

        self.nsfw_var.set(bool(state.get("nsfw", False)))
        self.subject_2_nsfw_var.set(bool(state.get("subject_2_nsfw", False)))
        self.photo_boost_var.set(bool(state.get("photo_boost", False)))
        self.nsfw_modifier_var.set(str(state.get("nsfw_modifier", "None")))
        self.subject_2_nsfw_modifier_var.set(str(state.get("subject_2_nsfw_modifier", "None")))
        self.bondage_var.set(str(state.get("bondage", "None")))
        self.subject_2_bondage_var.set(str(state.get("subject_2_bondage", "None")))
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

        custom_tags = state.get("custom_tags", "")
        extra_clothing_tags = state.get("extra_clothing_tags", "")
        self.custom_tags.delete("1.0", tk.END)
        self.custom_tags.insert("1.0", str(custom_tags))
        self.extra_clothing_tags.delete("1.0", tk.END)
        self.extra_clothing_tags.insert("1.0", str(extra_clothing_tags))

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
        neutral_field_values = {
            "full_outfit": "None",
            "top_clothing": "None",
            "bottom_clothing": "None",
            "headwear": "None",
            "shoes": "None",
            "accessories": "None",
            "hair_style": "Random",
            "eye_color": "Random",
            "pose": "Random",
            "breast_size": "Random",
            "breast_shape": "Random",
        }
        for key, value in neutral_field_values.items():
            if key in self.field_widgets:
                self.field_widgets[key].set(value)

        neutral_duo_values = {
            "pose": "Random",
            "expression": "Random",
            "full_outfit": "None",
            "top_clothing": "None",
            "bottom_clothing": "None",
            "headwear": "None",
            "shoes": "None",
            "accessories": "None",
            "hair_style": "Random",
            "eye_color": "Random",
            "breast_size": "Random",
            "breast_shape": "Random",
        }
        for key, value in neutral_duo_values.items():
            if key in self.duo_field_widgets:
                self.duo_field_widgets[key].set(value)

        self.duo_second_pose_var.set("Random")
        self.duo_second_expression_var.set("Random")

    def load_settings(self):
        if not self.settings_path.exists():
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
            combo = ttk.Combobox(parent, values=values, state="readonly", width=18)
            combo.set(default)
            combo.grid(row=row, column=col * 2 + 1, sticky="ew", padx=(0, 0), pady=0)
            widget_map[key] = combo
            self._bind_widget_preview_refresh(combo)

        if bondage_enabled_var is None:
            bondage_enabled_var = tk.BooleanVar(value=False)

        if include_custom_tags:
            extras = ttk.Frame(parent)
            extras.grid(row=(len(rows) // 2) + 1, column=0, columnspan=4, sticky="ew", pady=(12, 0))

            ttk.Label(extras, text="Custom tags").grid(row=0, column=0, sticky="nw", padx=(0, 4), pady=(2, 0))
            custom_tags_field = tk.Text(extras, height=2, width=42)
            custom_tags_field.grid(row=0, column=1, sticky="ew", pady=(2, 0))
            self._bind_widget_preview_refresh(custom_tags_field)
            widget_map["custom_tags_field"] = custom_tags_field

            ttk.Label(extras, text="Extra clothing tags").grid(row=1, column=0, sticky="nw", padx=(0, 4), pady=(2, 0))
            clothing_tags_field = tk.Text(extras, height=2, width=42)
            clothing_tags_field.grid(row=1, column=1, sticky="ew", pady=(2, 0))
            self._bind_widget_preview_refresh(clothing_tags_field)
            widget_map["clothing_tags_field"] = clothing_tags_field

            if widget_map is self.field_widgets:
                self.custom_tags = custom_tags_field
                self.extra_clothing_tags = clothing_tags_field

            extras.columnconfigure(1, weight=1)
            button_row = (len(rows) // 2) + 3
        else:
            button_row = (len(rows) // 2) + 1

        nsfw_row = ttk.Frame(parent)
        nsfw_row.grid(row=button_row, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        ttk.Checkbutton(nsfw_row, text="NSFW Modifier", variable=nsfw_var).pack(side=tk.LEFT, padx=(0, 10))
        combo = ttk.Combobox(
            nsfw_row,
            textvariable=nsfw_modifier_var,
            values=sort_combo_values(["None", "Random", *pony_nodes.NSFW_MODIFIERS, "detailed anatomy", "accurate anatomy", "correct anatomy", "realistic anatomy", "stylized anatomy", "anatomically correct", "detailed genitals", "realistic genitals", "soft shading", "detailed shading", "wet", "shiny", "glossy", "aroused", "excited", "muscular definition", "muscular chest", "defined abs", "soft belly", "plush thighs"]),
            state="readonly",
            width=26,
        )
        combo.set(nsfw_modifier_var.get())
        combo.pack(side=tk.LEFT)
        combo.bind(
            "<<ComboboxSelected>>",
            lambda e: append_nsfw_modifier_tag_standalone(
                nsfw_modifier_var,
                widget_map.get("custom_tags_field", getattr(self, "custom_tags", None)),
            ),
        )

        bondage_row = ttk.Frame(parent)
        bondage_row.grid(row=button_row + 1, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        ttk.Checkbutton(bondage_row, text="Bondage / Restraint", variable=bondage_enabled_var).pack(side=tk.LEFT, padx=(0, 10))
        bondage_combo = ttk.Combobox(
            bondage_row,
            textvariable=bondage_var,
            values=sort_combo_values(["None", "bound", "tied up", "restrained", "handcuffs", "rope", "bondage", "collar", "leash", "gag", "blindfold", "spread legs", "arms behind back", "legs spread"]),
            state="readonly" if bondage_enabled_var.get() else "disabled",
            width=22,
        )
        bondage_combo.set(bondage_var.get())
        bondage_combo.pack(side=tk.LEFT)

        def _sync_bondage_state(*_):
            custom_text_widget = widget_map.get("custom_tags_field", getattr(self, "custom_tags", None))
            if bondage_enabled_var.get():
                bondage_combo.configure(state="readonly")
            else:
                bondage_var.set("None")
                remove_tags_from_text_widget(custom_text_widget, BONDAGE_TAGS)
                bondage_combo.configure(state="disabled")

        bondage_enabled_var.trace_add("write", _sync_bondage_state)
        bondage_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: (
                append_bondage_tag_standalone(
                    bondage_var,
                    widget_map.get("custom_tags_field", getattr(self, "custom_tags", None)),
                ) if bondage_enabled_var.get() else None
            ),
        )

        _sync_bondage_state()

        if include_custom_tags:
            buttons = ttk.Frame(parent)
            buttons.grid(row=button_row + 2, column=0, columnspan=4, sticky="ew", pady=(10, 6))
            ttk.Button(buttons, text="Generate", command=self.generate).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
            ttk.Button(buttons, text="Copy prompt", command=self.copy_prompt).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
            ttk.Button(buttons, text="Reset defaults", command=lambda: self.reset_person_defaults(person_index)).pack(side=tk.LEFT, fill=tk.X, expand=True)
            preview_row = button_row + 3
        else:
            preview_row = button_row + 2
            buttons = ttk.Frame(parent)
            buttons.grid(row=button_row + 2, column=0, columnspan=4, sticky="ew", pady=(10, 6))
            ttk.Button(buttons, text="Reset defaults", command=lambda: self.reset_person_defaults(person_index)).pack(side=tk.LEFT, fill=tk.X, expand=True)

        preview_frame = ttk.Frame(parent)
        preview_frame.grid(row=preview_row, column=0, columnspan=4, sticky="ew", pady=(6, 6))
        ttk.Label(preview_frame, text="Prompt preview").pack(anchor="w", pady=(0, 4))
        preview = tk.Text(preview_frame, height=4, wrap=tk.WORD, state="disabled", cursor="arrow", takefocus=0, font=("TkDefaultFont", 9))
        preview.pack(fill=tk.BOTH, expand=True)
        for event in ("<Button-1>", "<ButtonRelease-1>", "<B1-Motion>", "<Double-Button-1>"):
            preview.bind(event, lambda event=None, _event=event: "break")
        widget_map["prompt_preview"] = preview
        if widget_map is self.field_widgets:
            self.prompt_preview = preview

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
            "1other": {"gender": "other", "body_type": "human"},
            "2girls": {"gender": "female", "body_type": "human"},
            "2boys": {"gender": "male", "body_type": "human"},
            "2others": {"gender": "other", "body_type": "human"},
            "3girls": {"gender": "female", "body_type": "human"},
            "3boys": {"gender": "male", "body_type": "human"},
            "multiple girls": {"gender": "female", "body_type": "human"},
            "multiple boys": {"gender": "male", "body_type": "human"},
            "multiple others": {"gender": "other", "body_type": "human"},
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
            if hasattr(self, "custom_tags"):
                self.custom_tags.delete("1.0", tk.END)
            if hasattr(self, "extra_clothing_tags"):
                self.extra_clothing_tags.delete("1.0", tk.END)
            self.nsfw_var.set(False)
            self.nsfw_modifier_var.set("None")
            self.bondage_enabled_var.set(False)
            self.bondage_var.set("None")
        elif person_index == 2:
            widget_map = self.duo_field_widgets
            values_map = self.duo_field_values
            self.subject_2_nsfw_var.set(False)
            self.subject_2_nsfw_modifier_var.set("None")
            self.subject_2_bondage_enabled_var.set(False)
            self.subject_2_bondage_var.set("None")
        else:
            widget_map = self.person_tab_widgets.get(person_index, {})
            values_map = self.field_values
            var_map = self.person_tab_var_map.get(person_index, {})
            if var_map:
                var_map.get("nsfw", tk.BooleanVar(value=False)).set(False)
                var_map.get("nsfw_modifier", tk.StringVar(value="None")).set("None")
                var_map.get("bondage_enabled", tk.BooleanVar(value=False)).set(False)
                var_map.get("bondage", tk.StringVar(value="None")).set("None")

        if not widget_map:
            return

        defaults = self._get_people_setup_defaults()
        for key, (values, default) in values_map.items():
            if key in widget_map:
                widget_map[key].set(default)

        self._apply_defaults_to_widget_map(widget_map, defaults)

        custom_widget = widget_map.get("custom_tags_field")
        if custom_widget is not None:
            try:
                custom_widget.delete("1.0", tk.END)
            except Exception:
                pass

        clothing_widget = widget_map.get("clothing_tags_field")
        if clothing_widget is not None:
            try:
                clothing_widget.delete("1.0", tk.END)
            except Exception:
                pass

        self._queue_prompt_preview_refresh()

    def reset_all_person_defaults(self):
        self.reset_to_neutral_defaults()
        defaults = self._get_people_setup_defaults()
        active_count = self._get_person_setup_count()
        for person_index in range(1, active_count + 1):
            self.reset_person_defaults(person_index)
        self.apply_people_setup_defaults()
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

    def _get_widget_text_fields(self, widget_map=None):
        if widget_map is None:
            widget_map = self.field_widgets

        custom_widget = widget_map.get("custom_tags_field")
        clothing_widget = widget_map.get("clothing_tags_field")

        if custom_widget is None:
            custom_widget = getattr(self, "custom_tags", None)
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
            positive_prompt, _, _ = self._build_current_positive_prompt()
            self.update_prompt_preview(positive_prompt)
        except Exception:
            pass
        self._preview_refresh_job = None

    def _bind_widget_preview_refresh(self, widget):
        if widget is None:
            return

        if isinstance(widget, tk.Text):
            widget.bind("<KeyRelease>", self._queue_prompt_preview_refresh)
            widget.bind("<ButtonRelease>", self._queue_prompt_preview_refresh)
            return

        if isinstance(widget, ttk.Combobox):
            widget.bind("<<ComboboxSelected>>", self._queue_prompt_preview_refresh)
            widget.bind("<FocusOut>", self._queue_prompt_preview_refresh)
            return

        if hasattr(widget, "bind"):
            widget.bind("<FocusOut>", self._queue_prompt_preview_refresh)

    def _build_current_positive_prompt(self):
        active_person_count = self._get_person_setup_count()
        subject_prompts = []
        sub1_prompt = None
        sub2_prompt = None

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
                values["nsfw_modifier"] = self.person_tab_var_map.get(person_index, {}).get("nsfw_modifier", tk.StringVar(value="None")).get()
                values["bondage_restraint"] = self.person_tab_var_map.get(person_index, {}).get("bondage", tk.StringVar(value="None")).get()

            prompt_values = dict(values)
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
        custom_tags_text = self._read_widget_value(custom_widget)
        extra_clothing_text = self._read_widget_value(clothing_widget)

        if custom_tags_text:
            prompt_base = f"{prompt_base}, {custom_tags_text}"
        if extra_clothing_text:
            prompt_base = f"{prompt_base}, {extra_clothing_text}"

        sex_act_text = self.sex_act_var.get().strip()
        sex_position_text = self.sex_position_var.get().strip()
        if sex_act_text and sex_act_text not in {"None", "Random"}:
            prompt_base = f"{prompt_base}, {sex_act_text}"
        if sex_position_text and sex_position_text not in {"None", "Random"}:
            prompt_base = f"{prompt_base}, {sex_position_text}"

        final_positive_prompt = attach_scene_metadata(
            prompt_base,
            rating=self.rating_var.get(),
            image_quality=self.image_quality_var.get(),
            location=self.location_var.get(),
            lighting=self.lighting_var.get(),
            camera=self.camera_var.get(),
            photo_boost=self.photo_boost_var.get(),
        )
        return final_positive_prompt, sub1_prompt, sub2_prompt

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
        values["nsfw_modifier"] = self.nsfw_modifier_var.get()
        values["bondage_restraint"] = self.bondage_var.get()
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
        values["nsfw_modifier"] = self.subject_2_nsfw_modifier_var.get()
        values["bondage_restraint"] = self.subject_2_bondage_var.get()
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

    def open_output_window(self, positive_text, negative_text=None):
        if self.output_window is None or not self.output_window.winfo_exists():
            self.output_window = tk.Toplevel(self.root)
            self.output_window.title("Generated Prompt")
            self.output_window.geometry("980x620")
            self.output_window.minsize(760, 420)

            self.output_positive = tk.Text(self.output_window, wrap=tk.WORD, height=16, padx=8, pady=8)
            self.output_positive.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 6))

            ttk.Label(self.output_window, text="Positive prompt").pack(anchor="w", padx=12, pady=(12, 0))
            self.output_positive.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 10))

            ttk.Label(self.output_window, text="Negative prompt").pack(anchor="w", padx=12, pady=(0, 0))
            self.output_negative = tk.Text(self.output_window, wrap=tk.WORD, height=10, padx=8, pady=8)
            self.output_negative.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 12))

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
            self.output_positive.delete("1.0", tk.END)
            self.output_positive.insert(tk.END, positive_text)
        if negative_text is not None:
            self.output_negative.delete("1.0", tk.END)
            self.output_negative.insert(tk.END, negative_text)
        else:
            self.output_negative.delete("1.0", tk.END)
            self.output_negative.insert(tk.END, "-")

    def close_prompt_window(self):
        if self.output_window is None or not self.output_window.winfo_exists():
            return

        positive_text = self.output_positive.get("1.0", tk.END).strip() if self.output_positive is not None else ""
        negative_text = self.output_negative.get("1.0", tk.END).strip() if self.output_negative is not None else "-"
        if positive_text:
            self.output_positive.delete("1.0", tk.END)
            self.output_positive.insert(tk.END, positive_text)
        if negative_text:
            self.output_negative.delete("1.0", tk.END)
            self.output_negative.insert(tk.END, negative_text)
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
                tab_data["nsfw_modifier"] = self.nsfw_modifier_var.get()
                custom_widget, clothing_widget = self._get_widget_text_fields(self.field_widgets)
                tab_data["custom_tags_field"] = self._read_widget_value(custom_widget)
                tab_data["clothing_tags_field"] = self._read_widget_value(clothing_widget)

            elif person_index == 2:
                for key, widget in self.duo_field_widgets.items():
                    tab_data[key] = self._read_widget_value(widget)
                tab_data["nsfw_modifier"] = self.subject_2_nsfw_modifier_var.get()
                custom_widget, clothing_widget = self._get_widget_text_fields(self.duo_field_widgets)
                tab_data["custom_tags_field"] = self._read_widget_value(custom_widget)
                tab_data["clothing_tags_field"] = self._read_widget_value(clothing_widget)
                if hasattr(self, 'subject_2_bondage_var'):
                    tab_data["bondage"] = self.subject_2_bondage_var.get()
                elif hasattr(self, 'duo_second_bondage_var'):
                    tab_data["bondage"] = self.duo_second_bondage_var.get()

            else:
                widget_map = self.person_tab_widgets.get(person_index, {})
                for key, widget in widget_map.items():
                    if key not in {"custom_tags_field", "clothing_tags_field"}:
                        tab_data[key] = self._read_widget_value(widget)

                var_map = self.person_tab_var_map.get(person_index, {})
                if "nsfw_modifier" in var_map:
                    tab_data["nsfw_modifier"] = var_map["nsfw_modifier"].get()
                if "bondage" in var_map:
                    tab_data["bondage"] = var_map["bondage"].get()
                custom_widget, clothing_widget = self._get_widget_text_fields(widget_map)
                tab_data["custom_tags_field"] = self._read_widget_value(custom_widget)
                tab_data["clothing_tags_field"] = self._read_widget_value(clothing_widget)

            state_for_checksum["person_tabs_data"][str(person_index)] = tab_data

        # Berechnet den fertigen, allumfassenden Base64-Teil-Code
        current_checksum = compute_prompt_checksum(state_for_checksum)
        self.checksum_store[current_checksum] = state_for_checksum
        self.prompt_checksum_var.set(current_checksum)
        self.prompt_checksum_input_var.set(current_checksum)
        # -------------------------------------------------------------------


        final_positive_prompt, sub1_prompt, sub2_prompt = self._build_current_positive_prompt()
        self.update_prompt_preview(final_positive_prompt)

        if self.mode_var.get() == "master":
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
                subject_1=sub1_prompt,  # FIXED: Nutzen nun die reparierte Variable
                subject_2=sub2_prompt,  # FIXED: Nutzen nun die reparierte Variable
                subject_3=None,
                subject_4=None,
                photo_boost=False,
            )
            self.open_output_window(final_positive_prompt, negative)
        else:
            self.open_output_window(final_positive_prompt)

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

        self.output_positive.delete("1.0", tk.END)
        self.output_positive.insert(tk.END, positive)
        self.output_negative.delete("1.0", tk.END)
        self.output_negative.insert(tk.END, negative)
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
