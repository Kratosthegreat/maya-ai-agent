#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מייצר את web/data.js מתוך חבילת football_manager.

הפייתון הוא מקור האמת. כל שינוי בטבלאות נעשה שם, ואז מריצים:

    python3 web/gen_data.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from football_manager import data as D          # noqa: E402
from football_manager import engine as E        # noqa: E402
from football_manager import models as M        # noqa: E402
from football_manager import progression as P   # noqa: E402
from football_manager import story_pack as SP  # noqa: E402

# (שם בפלט, המודול שממנו לוקחים)
SOURCES = [
    ("POSITIONS", D), ("POSITION_NAMES_HE", D), ("ATTRIBUTES", D),
    ("ATTRIBUTE_NAMES_HE", D), ("POSITION_WEIGHTS", D), ("POSITION_ROLE_SHARE", D),
    ("FORMATIONS", D), ("LEAGUES", D), ("CLUBS", D), ("FIRST_NAMES", D),
    ("LAST_NAMES", D), ("NATIONALITIES", D), ("MANAGER_NAMES", D), ("TRAITS", D),
    ("CAREER_STAGES_HE", D), ("TRAINING_FOCUS_HE", D),
    ("STADIUM_WORDS", D), ("STADIUM_SUFFIX", D), ("TICKET_BASE", D),
    ("FACILITIES", D), ("STAFF_ROLES", D), ("STAFF_NAMES", D),
    ("PHYSIQUE", D), ("BMI_RANGE", D),
    ("TRAINING_SPILL", D), ("SPILL_SHARE", D), ("GENERAL_SHARE", D),
    ("SPONSOR_TIERS", D), ("DEAL_KINDS", D), ("MEDIA_JOBS", D),
    ("AGENT_NAMES", D),
    ("INJURY_TYPES", E), ("MENTALITIES", E), ("PRESSING", E),
    ("AGE_CURVE", P), ("DECLINE_SENSITIVITY", P),
    ("SQUAD_TEMPLATE", M),
    ("PACK", SP),
]


# טבלאות שהערכים בתוכן נצרכים ישירות בקוד ה-JS, ולכן עוברות ל-camelCase
CAMEL_TABLES = {"FACILITIES", "STAFF_ROLES"}


def camel(text: str) -> str:
    head, *rest = text.split("_")
    return head + "".join(part.title() for part in rest)


def camelise(table: dict) -> dict:
    """ממיר מפתחות פנימיים ל-camelCase, כולל שמות שדות של Club."""
    out = {}
    for key, spec in table.items():
        converted = {camel(k): v for k, v in spec.items()}
        if "field" in converted:
            converted["field"] = camel(converted["field"])
        out[key] = converted
    return out


def main() -> None:
    out = {}
    for name, module in SOURCES:
        if not hasattr(module, name):
            raise SystemExit(f"חסר {name} ב-{module.__name__}")
        value = getattr(module, name)
        out[name] = camelise(value) if name in CAMEL_TABLES else value

    out["STORY_PACK"] = out.pop("PACK")     # שם ברור יותר בצד ה-JS

    path = os.path.join(HERE, "data.js")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("// נוצר אוטומטית מ-football_manager/data.py — אין לערוך ידנית.\n")
        fh.write("// מריצים מחדש: python3 web/gen_data.py\n")
        fh.write("const D = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")
    print(f"נכתב {path} ({os.path.getsize(path) // 1024}KB, {len(out)} טבלאות)")


if __name__ == "__main__":
    main()
