import argparse
import hashlib
import sys
import base64
import json
import zlib
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

import nodes as pony_nodes
from nodes import CR_Pony_Subject, CR_Pony_Master


def save_prompt_to_file(file_path, positive_text, negative_text=None):
    path = Path(file_path)
    if negative_text is None:
        negative_text = "-"
    content = (
        "[POSITIVE]\n"
        f"{positive_text.strip()}\n\n"
        "[NEGATIVE]\n"
        f"{negative_text.strip()}\n"
    )
    path.write_text(content, encoding="utf-8")


def load_prompt_from_file(file_path):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    text = path.read_text(encoding="utf-8")
    text = text.strip()
    if not text:
        return "", "-"

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

        positive = "\n".join(sections.get("POSITIVE", [])).strip()
        negative = "\n".join(sections.get("NEGATIVE", [])).strip() or "-"
        return positive, negative

    return text, "-"


def compute_prompt_checksum(state):
    """
    Kompprimiert und verschlüsselt den gesamten UI-Zustand 
    in einen autarken, teilbaren Text-Code.
    """
    try:
        # 1. Den Zustand in einen kompakten JSON-String ohne Leerzeichen umwandeln
        payload = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        
        # 2. Den Text komprimieren (zlib halbiert die Länge des Codes!)
        compressed_data = zlib.compress(payload.encode("utf-8"))
        
        # 3. In einen internet- und textfreundlichen Base64-String umwandeln
        b64_bytes = base64.urlsafe_b64encode(compressed_data)
        return b64_bytes.decode("utf-8")
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
        root.geometry("1020x660")
        root.minsize(860, 540)

        self.mode_var = tk.StringVar(value="subject")
        self.seed_var = tk.StringVar(value="42")
        self.person_count_var = tk.StringVar(value="solo")
        self.duo_second_gender_var = tk.StringVar(value="male")
        self.duo_second_pose_var = tk.StringVar(value="standing elegantly")
        self.duo_second_expression_var = tk.StringVar(value="Random")
        self.nsfw_var = tk.BooleanVar(value=False)
        self.subject_2_nsfw_var = tk.BooleanVar(value=False)
        self.photo_boost_var = tk.BooleanVar(value=False)
        self.nsfw_modifier_var = tk.StringVar(value="None")
        self.subject_2_nsfw_modifier_var = tk.StringVar(value="None")
        self.bondage_var = tk.StringVar(value="None")
        self.subject_2_bondage_var = tk.StringVar(value="None")
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
            "gender": (pony_nodes.get_sorted_list(pony_nodes.GENDERS), "human"),
            "age": (pony_nodes.get_sorted_list(pony_nodes.AGES), "25"),
            "ethnicity": (pony_nodes.get_sorted_list(pony_nodes.ETHNICITIES), "Caucasian"),
            "body_type": (pony_nodes.get_sorted_list(pony_nodes.ALL_BODY_TYPES), "None"),
            "skin_texture": (pony_nodes.get_sorted_list(pony_nodes.SKIN_TYPES), "pale skin"),
            "hair_color": (pony_nodes.get_sorted_list(pony_nodes.HAIR_COLORS), "platinum blonde"),
            "hair_style": (pony_nodes.get_sorted_list(pony_nodes.ALL_HAIRSTYLES), "Random"),
            "eye_color": (pony_nodes.get_sorted_list(pony_nodes.EYE_COLORS), "Random"),
            "full_outfit": (pony_nodes.get_sorted_list(pony_nodes.FULL_OUTFITS), "None"),
            "top_clothing": (pony_nodes.get_sorted_list(pony_nodes.TOP_CLOTHING), "None"),
            "bottom_clothing": (pony_nodes.get_sorted_list(pony_nodes.BOTTOM_CLOTHING), "None"),
            "headwear": (pony_nodes.get_sorted_list(pony_nodes.HEADWEAR), "None"),
            "shoes": (pony_nodes.get_sorted_list(pony_nodes.FOOTWEAR), "None"),
            "accessories": (pony_nodes.get_sorted_list(pony_nodes.ACCESSORIES), "None"),
            "pose": (pony_nodes.get_sorted_list(pony_nodes.ALL_POSES), "Random"),
            "breast_size": (pony_nodes.get_sorted_list(pony_nodes.BREAST_SIZES), "Random"),
            "breast_shape": (pony_nodes.get_sorted_list(pony_nodes.BREAST_SHAPES), "Random"),
            "leg_feature": (pony_nodes.get_sorted_list(pony_nodes.LEG_FEATURES), "Random"),
            "butt_feature": (pony_nodes.get_sorted_list(pony_nodes.BUTT_FEATURES), "Random"),
            "face_shape": (pony_nodes.get_sorted_list(pony_nodes.FACE_SHAPES), "Random"),
            "expression": (pony_nodes.get_sorted_list(pony_nodes.EXPRESSIONS), "Random"),
            "hair_length": (pony_nodes.get_sorted_list(pony_nodes.HAIR_LENGTHS), "Random"),
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
                values, default = pony_nodes.get_sorted_list(pony_nodes.GENDERS), "human"
            elif key == "body_type":
                values, default = pony_nodes.get_sorted_list(pony_nodes.ALL_BODY_TYPES), "None"
            elif key == "pose":
                values, default = pony_nodes.get_sorted_list(pony_nodes.ALL_POSES), "Random"
            elif key == "expression":
                values, default = pony_nodes.get_sorted_list(pony_nodes.EXPRESSIONS), "Random"
            self.duo_field_values[key] = (values, default)

        self.field_widgets = {}
        self.duo_field_widgets = {}
        self.output_window = None
        self.output_positive = None
        self.output_negative = None
        self.text = None
        self.settings_path = Path(__file__).with_name("prompt_settings.json")
        self.checksum_store = {}
        self.prompt_checksum_var = tk.StringVar(value="")
        self.prompt_checksum_input_var = tk.StringVar(value="")

        main = ttk.Frame(root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        top_bar = ttk.Frame(main)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_bar, text="Generator").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Combobox(top_bar, textvariable=self.mode_var, values=["subject", "master"], state="readonly", width=14).grid(row=0, column=1, sticky="w")

        ttk.Label(top_bar, text="People / Setup").grid(row=0, column=2, sticky="w", padx=(12, 8))
        ttk.Combobox(
            top_bar,
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
        ).grid(row=0, column=3, sticky="w")

        ttk.Label(top_bar, text="Seed").grid(row=0, column=4, sticky="w", padx=(12, 8))
        ttk.Entry(top_bar, textvariable=self.seed_var, width=12).grid(row=0, column=5, sticky="w")
        ttk.Checkbutton(top_bar, text="Photo boost", variable=self.photo_boost_var).grid(row=0, column=6, sticky="w", padx=(12, 0))
        ttk.Label(top_bar, text="Checksum").grid(row=0, column=7, sticky="w", padx=(12, 0))
        ttk.Entry(top_bar, textvariable=self.prompt_checksum_var, state="readonly", width=18).grid(row=0, column=8, sticky="w")
        ttk.Entry(top_bar, textvariable=self.prompt_checksum_input_var, width=18).grid(row=0, column=9, sticky="w", padx=(6, 0))
        ttk.Button(top_bar, text="Apply", command=self.apply_saved_checksum).grid(row=0, column=10, sticky="w", padx=(6, 0))
        ttk.Checkbutton(top_bar, text="Use BREAK between subjects", variable=self.use_break_var).grid(row=0, column=11, sticky="w", padx=(12, 0))
        ttk.Button(top_bar, text="Open", command=self.open_prompt_window_if_available).grid(row=0, column=12, sticky="w", padx=(12, 0))
        ttk.Button(top_bar, text="Load", command=self.load_prompt_file).grid(row=0, column=13, sticky="w", padx=(8, 0))

        top_bar.columnconfigure(5, weight=1)

        self.duo_second_gender_var = tk.StringVar(value="human")
        self.duo_second_pose_var = tk.StringVar(value="Random")
        self.duo_second_expression_var = tk.StringVar(value="Random")
        self.duo_second_body_type_var = tk.StringVar(value="None")

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
            ("Rating", pony_nodes.get_sorted_list(pony_nodes.RATINGS), self.rating_var),
            ("Score scheme", pony_nodes.get_sorted_list(pony_nodes.SCORE_SCHEMES), self.score_scheme_var),
            ("Image Quality", pony_nodes.get_sorted_list(["None", "score_9", "score_8_up", "score_7_up", "masterpiece", "best quality", "highly detailed", "intricate details"]), self.image_quality_var),
            ("Location", pony_nodes.get_sorted_list(pony_nodes.LOCATIONS), self.location_var),
            ("Lighting", pony_nodes.get_sorted_list(pony_nodes.LIGHTING), self.lighting_var),
            ("Camera", pony_nodes.get_sorted_list(pony_nodes.CAMERAS), self.camera_var),
            ("Sex act", pony_nodes.get_sorted_list(pony_nodes.SEX_ACTS), self.sex_act_var),
            ("Sex position", pony_nodes.get_sorted_list(pony_nodes.SEX_POSITIONS), self.sex_position_var),
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
        self.reset_to_neutral_defaults()
        self.update_duo_visibility()
        self.update_mode_visibility()
        self.mode_var.trace_add("write", lambda *_: (self.update_duo_visibility(), self.update_mode_visibility()))
        self.person_count_var.trace_add("write", lambda *_: (self.update_duo_visibility(), self.update_mode_visibility()))
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
            "custom_tags": self.custom_tags.get("1.0", tk.END).strip(),
            "extra_clothing_tags": self.extra_clothing_tags.get("1.0", tk.END).strip(),
        }
        for key, widget in self.field_widgets.items():
            state[f"field_{key}"] = widget.get()
        for key, widget in self.duo_field_widgets.items():
            state[f"duo_{key}"] = widget.get()
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
        if checksum not in self.checksum_store:
            messagebox.showwarning("Checksum not found", "No saved prompt settings were found for this checksum.")
            return
        self.apply_settings_state(self.checksum_store[checksum])
        self.prompt_checksum_input_var.set(checksum)
        self.prompt_checksum_var.set(checksum)

    def on_close(self):
        self.save_settings()
        self.root.destroy()

    def _build_subject_panel(self, parent, widget_map, values_map, nsfw_var, nsfw_modifier_var, bondage_var, include_custom_tags=True):
        rows = []
        for key, (values, default) in values_map.items():
            label = key.replace("_", " ").title()
            rows.append((key, label, values, default))

        for index, (key, label, values, default) in enumerate(rows):
            row = index // 2
            col = index % 2
            ttk.Label(parent, text=label).grid(row=row, column=col * 2, sticky="w", padx=(0, 10), pady=5)
            combo = ttk.Combobox(parent, values=values, state="readonly", width=26)
            combo.set(default)
            combo.grid(row=row, column=col * 2 + 1, sticky="ew", padx=(0, 12), pady=5)
            widget_map[key] = combo

        if include_custom_tags:
            extras = ttk.Frame(parent)
            extras.grid(row=(len(rows) // 2) + 1, column=0, columnspan=4, sticky="ew", pady=(12, 0))

            ttk.Label(extras, text="Custom tags").grid(row=0, column=0, sticky="nw", padx=(0, 10), pady=(8, 0))
            self.custom_tags = tk.Text(extras, height=3, width=46)
            self.custom_tags.grid(row=0, column=1, sticky="ew", pady=(8, 0))

            ttk.Label(extras, text="Extra clothing tags").grid(row=1, column=0, sticky="nw", padx=(0, 10), pady=(8, 0))
            self.extra_clothing_tags = tk.Text(extras, height=3, width=46)
            self.extra_clothing_tags.grid(row=1, column=1, sticky="ew", pady=(8, 0))
            extras.columnconfigure(1, weight=1)
            button_row = (len(rows) // 2) + 3
        else:
            button_row = (len(rows) // 2) + 1

        nsfw_row = ttk.Frame(parent)
        nsfw_row.grid(row=button_row, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        ttk.Checkbutton(nsfw_row, text="NSFW Modifier", variable=nsfw_var).pack(side=tk.LEFT, padx=(0, 10))
        combo = ttk.Combobox(
            nsfw_row,
            textvariable=nsfw_modifier_var,
            values=["None", "Random", *pony_nodes.NSFW_MODIFIERS, "detailed anatomy", "accurate anatomy", "correct anatomy", "realistic anatomy", "stylized anatomy", "anatomically correct", "detailed genitals", "realistic genitals", "soft shading", "detailed shading", "wet", "shiny", "glossy", "aroused", "excited", "muscular definition", "muscular chest", "defined abs", "soft belly", "plush thighs"],
            state="readonly",
            width=26,
        )
        combo.set(nsfw_modifier_var.get())
        combo.pack(side=tk.LEFT)

        bondage_row = ttk.Frame(parent)
        bondage_row.grid(row=button_row + 1, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        ttk.Label(bondage_row, text="Bondage / Restraint").pack(side=tk.LEFT, padx=(0, 10))
        bondage_combo = ttk.Combobox(
            bondage_row,
            textvariable=bondage_var,
            values=["None", "bound", "tied up", "restrained", "handcuffs", "rope", "bondage", "collar", "leash", "gag", "blindfold", "spread legs", "arms behind back", "legs spread"],
            state="readonly",
            width=22,
        )
        bondage_combo.set(bondage_var.get())
        bondage_combo.pack(side=tk.LEFT)

        if include_custom_tags:
            buttons = ttk.Frame(parent)
            buttons.grid(row=button_row + 2, column=0, columnspan=4, sticky="ew", pady=(16, 8))
            ttk.Button(buttons, text="Generate", command=self.generate).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
            ttk.Button(buttons, text="Copy prompt", command=self.copy_prompt).pack(side=tk.LEFT, fill=tk.X, expand=True)

        for i in range(4):
            parent.columnconfigure(i, weight=1)

    def _create_person_tab(self, person_index, title, widget_map, values_map, nsfw_var, nsfw_modifier_var, bondage_var, include_custom_tags):
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
            include_custom_tags=include_custom_tags,
        )
        self.person_notebook.add(frame, text=title)
        self.person_tabs[person_index] = frame
        self.person_tab_widgets[person_index] = widget_map
        self.person_tab_var_map[person_index] = {
            "nsfw": nsfw_var,
            "nsfw_modifier": nsfw_modifier_var,
            "bondage": bondage_var,
        }

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
                        include_custom_tags = True
                    elif index == 2:
                        widget_map = self.duo_field_widgets
                        values_map = self.duo_field_values
                        nsfw_var = self.subject_2_nsfw_var
                        nsfw_modifier_var = self.subject_2_nsfw_modifier_var
                        bondage_var = self.subject_2_bondage_var
                        include_custom_tags = False
                    else:
                        widget_map = {}
                        values_map = self.field_values
                        nsfw_var = tk.BooleanVar(value=False)
                        nsfw_modifier_var = tk.StringVar(value="None")
                        bondage_var = tk.StringVar(value="None")
                        include_custom_tags = False
                    self._create_person_tab(index, f"Person {index}", widget_map, values_map, nsfw_var, nsfw_modifier_var, bondage_var, include_custom_tags)
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
        show_scene = self.mode_var.get() == "master" or self.person_count_var.get() == "duo" or self.nsfw_var.get()
        if show_scene:
            self.scene_frame.pack(fill=tk.X, pady=(0, 8))
        else:
            self.scene_frame.pack_forget()

    def get_subject_values(self):
        values = {}
        for key in self.field_values:
            values[key] = self.field_widgets[key].get()
        values["custom_tags"] = self.custom_tags.get("1.0", tk.END).strip()
        values["extra_clothing_tags"] = self.extra_clothing_tags.get("1.0", tk.END).strip()
        values["nsfw_modifier"] = self.nsfw_modifier_var.get()
        values["bondage_restraint"] = self.bondage_var.get()
        return values

    def get_duo_second_values(self):
        values = {}
        for key in self.field_values:
            if key in self.duo_field_widgets:
                values[key] = self.duo_field_widgets[key].get()
            else:
                values[key] = self.field_values[key][1]
        values["custom_tags"] = self.custom_tags.get("1.0", tk.END).strip()
        values["extra_clothing_tags"] = self.extra_clothing_tags.get("1.0", tk.END).strip()
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
            "custom_tags": self.custom_tags.get("1.0", tk.END).strip(),
            "extra_clothing_tags": self.extra_clothing_tags.get("1.0", tk.END).strip(),
            "person_tabs_data": {}  # Speichert alle Karteikarten-Reiter dynamisch
        }

        # Wir lesen alle aktiven Tabs nacheinander aus
        active_person_count = self._get_person_setup_count()
        for person_index in range(1, active_person_count + 1):
            tab_data = {}
            
            if person_index == 1:
                for key, widget in self.field_widgets.items():
                    tab_data[key] = widget.get()
                tab_data["nsfw_modifier"] = self.nsfw_modifier_var.get()
                    
            elif person_index == 2:
                for key, widget in self.duo_field_widgets.items():
                    tab_data[key] = widget.get()
                tab_data["nsfw_modifier"] = self.subject_2_nsfw_modifier_var.get()
                # Falls Bondage bei Person 2 aktiv ist, mitspeichern
                if hasattr(self, 'subject_2_bondage_var'):
                    tab_data["bondage"] = self.subject_2_bondage_var.get()
                elif hasattr(self, 'duo_second_bondage_var'):
                    tab_data["bondage"] = self.duo_second_bondage_var.get()
                    
            else:
                # Holt die Werte für Person 3, 4 etc. dynamisch aus den Tab-Strukturen
                widget_map = self.person_tab_widgets.get(person_index, {})
                for key, widget in widget_map.items():
                    tab_data[key] = widget.get()
                
                var_map = self.person_tab_var_map.get(person_index, {})
                if "nsfw_modifier" in var_map:
                    tab_data["nsfw_modifier"] = var_map["nsfw_modifier"].get()
                if "bondage" in var_map:
                    tab_data["bondage"] = var_map["bondage"].get()

            # Ordne die gesammelten Daten dem jeweiligen Tab-Index zu
            state_for_checksum["person_tabs_data"][str(person_index)] = tab_data

        # Berechnet den fertigen, allumfassenden Base64-Teil-Code
        current_checksum = compute_prompt_checksum(state_for_checksum)
        self.checksum_store[current_checksum] = state_for_checksum
        self.prompt_checksum_var.set(current_checksum)
        self.prompt_checksum_input_var.set(current_checksum)
        # -------------------------------------------------------------------


        active_person_count = self._get_person_setup_count()
        subject_prompts = []

        # Wir sichern uns Variablen für das spätere generate_master-Node
        sub1_prompt = None
        sub2_prompt = None

        for person_index in range(1, active_person_count + 1):
            if person_index == 1:
                widget_map = self.field_widgets
                values = self.get_subject_values()
            elif person_index == 2:
                widget_map = self.duo_field_widgets
                values = self.get_duo_second_values()
            else:
                widget_map = self.person_tab_widgets.get(person_index, {})
                if not widget_map:
                    continue
                values = {}
                for key in self.field_values:
                    values[key] = widget_map[key].get()
                values["custom_tags"] = self.custom_tags.get("1.0", tk.END).strip()
                values["extra_clothing_tags"] = self.extra_clothing_tags.get("1.0", tk.END).strip()
                values["nsfw_modifier"] = self.person_tab_var_map.get(person_index, {}).get("nsfw_modifier", tk.StringVar(value="None")).get()
                values["bondage_restraint"] = self.person_tab_var_map.get(person_index, {}).get("bondage", tk.StringVar(value="None")).get()

            prompt_values = dict(values)

            gender_value = (prompt_values.get("gender") or "").strip()
            if gender_value in {"", "None", "Random"}:
                prompt_values["lead_token"] = "person"
            else:
                prompt_values["lead_token"] = gender_value

            #prompt_values["setup_group"] = self.person_count_var.get()
            if prompt_values.get("body_type") in {"", "None", "Random"}:
                prompt_values["body_type"] = ""

            built_prompt = pony_nodes.build_subject_prompt_from_ui(prompt_values)
            subject_prompts.append(built_prompt)

            # Für das master-Node zwischenspeichern
            if person_index == 1:
                sub1_prompt = built_prompt
            elif person_index == 2:
                sub2_prompt = built_prompt

        if not subject_prompts:
            default_p = pony_nodes.build_subject_prompt_from_ui({"lead_token": "person", "gender": "human"})
            subject_prompts = [default_p]
            sub1_prompt = default_p

        # Wir holen uns einfach exakt den Text, der im Dropdown ausgewählt ist
        setup_val = (self.person_count_var.get() or "").strip()
        
        # Wenn ein Wert da ist, hängen wir ein Komma ran, sonst bleibt es leer
        if setup_val and setup_val != "None":
            global_tag = f"{setup_val}, "
        else:
            global_tag = ""

        # Verbinde die einzelnen Personen-Klammern sauber miteinander
        subjects_str = " BREAK ".join(subject_prompts) if self.use_break_var.get() else ", ".join(subject_prompts)
        
        # Setze den ausgewählten Setup-Wert ganz an den Anfang VOR die Personen
        prompt_base = f"{global_tag}{subjects_str}"


        custom_tags_text = self.custom_tags.get("1.0", tk.END).strip()
        extra_clothing_text = self.extra_clothing_tags.get("1.0", tk.END).strip()

        if custom_tags_text:
            prompt_base = f"{prompt_base}, {custom_tags_text}"
        if extra_clothing_text:
            prompt_base = f"{prompt_base}, {extra_clothing_text}"

        # --- REPARATUR: SEX ACT & POSITION EINFÜGEN ---
        sex_act_text = self.sex_act_var.get().strip()
        sex_position_text = self.sex_position_var.get().strip()

        if sex_act_text and sex_act_text not in {"None", "Random"}:
            prompt_base = f"{prompt_base}, {sex_act_text}"
        if sex_position_text and sex_position_text not in {"None", "Random"}:
            prompt_base = f"{prompt_base}, {sex_position_text}"
        # ----------------------------------------------


        final_positive_prompt = attach_scene_metadata(
            prompt_base,
            rating=self.rating_var.get(),
            image_quality=self.image_quality_var.get(),
            location=self.location_var.get(),
            lighting=self.lighting_var.get(),
            camera=self.camera_var.get(),
            photo_boost=self.photo_boost_var.get(),
        )

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

        file_path = filedialog.asksaveasfilename(
            title="Save prompt",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path:
            return

        save_prompt_to_file(file_path, positive, negative)
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
