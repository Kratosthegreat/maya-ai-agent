# -*- coding: utf-8 -*-
"""
football_manager.data
=====================
נתוני הבסיס של המשחק: ליגות, מועדונים, שמות, עמדות ומשקלי תכונות.
כל הנתונים כאן סטטיים וללא תלות במצב המשחק.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# עמדות
# ---------------------------------------------------------------------------

POSITIONS = ["GK", "CB", "LB", "RB", "DM", "CM", "AM", "LW", "RW", "ST"]

POSITION_NAMES_HE = {
    "GK": "שוער",
    "CB": "בלם",
    "LB": "מגן שמאלי",
    "RB": "מגן ימני",
    "DM": "קשר הגנתי",
    "CM": "קשר מרכזי",
    "AM": "קשר התקפי",
    "LW": "כנף שמאלית",
    "RW": "כנף ימנית",
    "ST": "חלוץ",
}

ATTRIBUTES = [
    "pace",       # מהירות
    "shooting",   # בעיטות
    "passing",    # מסירות
    "dribbling",  # כדרור
    "defending",  # הגנה
    "physical",   # פיזי
    "mental",     # ראש / קריאת משחק
]

ATTRIBUTE_NAMES_HE = {
    "pace": "מהירות",
    "shooting": "בעיטה",
    "passing": "מסירה",
    "dribbling": "כדרור",
    "defending": "הגנה",
    "physical": "כוח פיזי",
    "mental": "קריאת משחק",
}

# משקל כל תכונה בחישוב הדירוג הכללי, לפי עמדה
POSITION_WEIGHTS = {
    "GK": {"pace": 0.05, "shooting": 0.02, "passing": 0.10, "dribbling": 0.03,
           "defending": 0.45, "physical": 0.15, "mental": 0.20},
    "CB": {"pace": 0.10, "shooting": 0.03, "passing": 0.10, "dribbling": 0.05,
           "defending": 0.40, "physical": 0.20, "mental": 0.12},
    "LB": {"pace": 0.22, "shooting": 0.04, "passing": 0.15, "dribbling": 0.12,
           "defending": 0.27, "physical": 0.12, "mental": 0.08},
    "RB": {"pace": 0.22, "shooting": 0.04, "passing": 0.15, "dribbling": 0.12,
           "defending": 0.27, "physical": 0.12, "mental": 0.08},
    "DM": {"pace": 0.08, "shooting": 0.05, "passing": 0.22, "dribbling": 0.08,
           "defending": 0.28, "physical": 0.15, "mental": 0.14},
    "CM": {"pace": 0.10, "shooting": 0.10, "passing": 0.28, "dribbling": 0.15,
           "defending": 0.12, "physical": 0.10, "mental": 0.15},
    "AM": {"pace": 0.13, "shooting": 0.18, "passing": 0.25, "dribbling": 0.22,
           "defending": 0.03, "physical": 0.05, "mental": 0.14},
    "LW": {"pace": 0.25, "shooting": 0.16, "passing": 0.14, "dribbling": 0.28,
           "defending": 0.03, "physical": 0.05, "mental": 0.09},
    "RW": {"pace": 0.25, "shooting": 0.16, "passing": 0.14, "dribbling": 0.28,
           "defending": 0.03, "physical": 0.05, "mental": 0.09},
    "ST": {"pace": 0.20, "shooting": 0.34, "passing": 0.08, "dribbling": 0.15,
           "defending": 0.02, "physical": 0.13, "mental": 0.08},
}

# תפקיד השחקן במערך: כמה הוא תורם להגנה / קישור / התקפה
POSITION_ROLE_SHARE = {
    "GK": {"def": 1.00, "mid": 0.00, "att": 0.00},
    "CB": {"def": 0.90, "mid": 0.10, "att": 0.00},
    "LB": {"def": 0.65, "mid": 0.30, "att": 0.05},
    "RB": {"def": 0.65, "mid": 0.30, "att": 0.05},
    "DM": {"def": 0.45, "mid": 0.50, "att": 0.05},
    "CM": {"def": 0.20, "mid": 0.60, "att": 0.20},
    "AM": {"def": 0.05, "mid": 0.45, "att": 0.50},
    "LW": {"def": 0.05, "mid": 0.25, "att": 0.70},
    "RW": {"def": 0.05, "mid": 0.25, "att": 0.70},
    "ST": {"def": 0.00, "mid": 0.10, "att": 0.90},
}

# מערך פורמציות: כמה שחקנים מכל עמדה
FORMATIONS = {
    "4-4-2": ["GK", "RB", "CB", "CB", "LB", "RW", "CM", "CM", "LW", "ST", "ST"],
    "4-3-3": ["GK", "RB", "CB", "CB", "LB", "DM", "CM", "CM", "RW", "ST", "LW"],
    "4-2-3-1": ["GK", "RB", "CB", "CB", "LB", "DM", "DM", "RW", "AM", "LW", "ST"],
    "3-5-2": ["GK", "CB", "CB", "CB", "RB", "DM", "CM", "CM", "LB", "ST", "ST"],
    "5-3-2": ["GK", "RB", "CB", "CB", "CB", "LB", "DM", "CM", "CM", "ST", "ST"],
}

# ---------------------------------------------------------------------------
# ליגות ומועדונים
# ---------------------------------------------------------------------------
# tier 1 = ליגת העל, tier 2 = הליגה הלאומית, tier 0 = ליגת העילית האירופית

LEAGUES = [
    {"id": "top", "name": "ליגת העל", "tier": 1, "country": "ישראל", "size": 20},
    {"id": "national", "name": "הליגה הלאומית", "tier": 2, "country": "ישראל", "size": 20},
    {"id": "euro", "name": "ליגת האלופות האירופית", "tier": 0, "country": "אירופה", "size": 16},
]

# (מזהה, שם, כינוי, מוניטין 1-100, תקציב במיליונים)
CLUBS = [
    # --- ליגת העל (20 קבוצות) ---
    ("maccabi_harel", "מכבי הראל", "הצהובים", "top", 82, 42.0),
    ("hapoel_yam", "הפועל ים התיכון", "היַמָּאים", "top", 78, 34.0),
    ("beitar_zion", "בית\"ר ציון", "השחורים־צהובים", "top", 74, 26.0),
    ("bnei_negev", "בני הנגב", "בני המדבר", "top", 71, 21.0),
    ("maccabi_sharon", "מכבי השרון", "הירוקים", "top", 69, 18.5),
    ("hapoel_carmel", "הפועל הכרמל", "האריות", "top", 67, 16.0),
    ("ironi_moriah", "עירוני מוריה", "אנשי ההר", "top", 65, 14.5),
    ("maccabi_yarden", "מכבי ירדן", "הנהר", "top", 63, 13.0),
    ("hapoel_ayalon", "הפועל איילון", "הפועלים", "top", 61, 11.5),
    ("ironi_galil", "עירוני גליל עליון", "ההרים", "top", 59, 10.5),
    ("shimshon_ashdod", "שמשון אשדוד", "אנשי החוף", "top", 57, 9.5),
    ("maccabi_lachish", "מכבי לכיש", "השדות", "top", 55, 8.5),
    ("hapoel_shfela", "הפועל השפלה", "העמק", "top", 53, 7.5),
    ("ironi_kinneret", "עירוני כנרת", "הגלים", "top", 51, 7.0),
    ("hakoah_arava", "הכוח ערבה", "הסופה", "top", 49, 6.2),
    ("bnei_tavor", "בני תבור", "הפסגה", "top", 47, 5.6),
    ("maccabi_ofek", "מכבי אופק", "האופק", "top", 45, 5.0),
    ("hapoel_zvulun", "הפועל זבולון", "העוגן", "top", 43, 4.4),
    ("ironi_shomron", "עירוני שומרון", "הגבעות", "top", 41, 4.0),
    ("shimshon_dan", "שמשון דן", "הגוש", "top", 39, 3.6),

    # --- הליגה הלאומית (20 קבוצות) ---
    ("maccabi_modiin", "מכבי מודיעין", "המכבים", "national", 38, 3.4),
    ("hapoel_ramla", "הפועל רמלה", "הצריחים", "national", 37, 3.2),
    ("bnei_hasharon", "בני השרון", "התפוזים", "national", 36, 3.0),
    ("ironi_besor", "עירוני הבשור", "הנחל", "national", 35, 2.8),
    ("maccabi_arad", "מכבי ערד", "המצוק", "national", 34, 2.6),
    ("hapoel_negba", "הפועל נגבה", "החומה", "national", 33, 2.4),
    ("ironi_hermon", "עירוני חרמון", "השלג", "national", 32, 2.3),
    ("maccabi_ofakim", "מכבי אופקים", "המדבר", "national", 31, 2.2),
    ("bnei_gilboa", "בני גלבוע", "הרכס", "national", 30, 2.0),
    ("hapoel_alexander", "הפועל נחל אלכסנדר", "הזרם", "national", 29, 1.9),
    ("ironi_masada", "עירוני מצדה", "המצודה", "national", 28, 1.8),
    ("maccabi_eshkol", "מכבי אשכול", "הכרמים", "national", 27, 1.7),
    ("hapoel_hula", "הפועל החולה", "האגם", "national", 26, 1.6),
    ("bnei_ela", "בני האלה", "העמק", "national", 25, 1.5),
    ("ironi_ramon", "עירוני רמון", "המכתש", "national", 24, 1.4),
    ("maccabi_yehuda", "מכבי הרי יהודה", "ההרים", "national", 23, 1.3),
    ("hapoel_taninim", "הפועל תנינים", "הנחל", "national", 22, 1.2),
    ("bnei_zin", "בני צין", "הערבה", "national", 21, 1.1),
    ("ironi_habsor", "עירוני הבשור ב'", "הגדה", "national", 20, 1.0),
    ("maccabi_shikma", "מכבי שקמה", "העצים", "national", 19, 0.9),

    # --- ליגת האלופות האירופית (16 קבוצות) ---
    ("real_castilla", "ריאל קסטיליה", "המלכותיים", "euro", 94, 260.0),
    ("olympia_munchen", "אולימפיה מינכן", "הבווארים", "euro", 93, 240.0),
    ("thames_united", "תמז יונייטד", "השדים", "euro", 91, 230.0),
    ("paris_luxe", "פארי לוקס", "הבירה", "euro", 90, 220.0),
    ("inter_lazio", "אינטר לאציו", "הנחשים", "euro", 88, 190.0),
    ("catalunya_fc", "קטלוניה", "הבלאוגרנה", "euro", 89, 200.0),
    ("mersey_athletic", "מרסי אתלטיק", "האדומים", "euro", 87, 185.0),
    ("saxon_dortmund", "סקסון דורטמונד", "הצהוב־שחור", "euro", 84, 150.0),
    ("ajax_noord", "אייאקס נורד", "בית הספר", "euro", 82, 120.0),
    ("porto_atlantico", "פורטו אטלנטיקו", "הדרקונים", "euro", 80, 100.0),
    ("galata_bosphorus", "גלאטה בוספורוס", "האריות", "euro", 79, 95.0),
    ("milano_nord", "מילאנו נורד", "הרוסונרי", "euro", 85, 165.0),
    ("albion_north", "אלביון נורת'", "הפועלים", "euro", 83, 140.0),
    ("sevilla_sur", "סביליה סור", "האדומים־לבנים", "euro", 78, 88.0),
    ("wien_donau", "וינה דונאו", "הסגולים", "euro", 74, 62.0),
    ("brugge_west", "ברוז' ווסט", "הכחולים", "euro", 72, 55.0),
]

# ---------------------------------------------------------------------------
# שמות לייצור שחקנים
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "איתי", "עומר", "יובל", "נועם", "אורי", "רועי", "דור", "גיא", "אלון", "עידו",
    "שגיא", "ליאור", "עמית", "בר", "ניר", "טל", "אסף", "עדן", "מתן", "יונתן",
    "אריאל", "שחר", "רון", "נדב", "איל", "עומרי", "יהב", "אביב", "חן", "ספיר",
    "מרקו", "לוקאס", "דייגו", "אנזו", "רפאל", "בילאל", "אמארה", "יוסוף", "טיאגו", "פאבלו",
]

LAST_NAMES = [
    "כהן", "לוי", "מזרחי", "פרץ", "ביטון", "דהן", "אברהם", "פרידמן", "שרון", "אזולאי",
    "בן־חיים", "גולן", "אשכנזי", "טוויטו", "זהבי", "רפאלוב", "חמד", "מלמד", "סבן", "אוחיון",
    "סילבה", "מנדס", "קוסטה", "פרננדס", "מולר", "יאנסן", "נובאק", "פטרוב", "אוקונקוו", "דיאלו",
]

NATIONALITIES = [
    ("ישראל", 0.62), ("ברזיל", 0.06), ("ניגריה", 0.05), ("צרפת", 0.04),
    ("ספרד", 0.04), ("סרביה", 0.04), ("ארגנטינה", 0.03), ("פורטוגל", 0.03),
    ("גאנה", 0.03), ("קרואטיה", 0.03), ("הולנד", 0.03),
]

MANAGER_NAMES = [
    "ז'וזה ריברו", "אריק לוינסון", "פאולו מנדס", "יאן דה־בור", "משה אלגרבלי",
    "רוברטו סנטיני", "דייויד קלארק", "אמיר בן־שושן", "טומאס נובאק", "ניקולא פטרוביץ'",
    "שלומי דגן", "פרנק אוליביירה", "מרקוס שטיין", "עידן ברקוביץ'", "קרלוס אלמדה",
]

# ---------------------------------------------------------------------------
# אימון: מה מתפתח יחד עם מה
# ---------------------------------------------------------------------------

# אף אימון לא נוגע בתכונה אחת בלבד. מי שרץ ספרינטים מחזק גם רגליים,
# ומי שעובד על סיומות משפר גם את הנגיעה הראשונה ואת קריאת המצב.
TRAINING_SPILL = {
    "pace":      ("physical", "dribbling"),
    "shooting":  ("dribbling", "mental"),
    "passing":   ("mental", "dribbling"),
    "dribbling": ("pace", "passing"),
    "defending": ("mental", "physical"),
    "physical":  ("pace", "defending"),
    "mental":    ("passing", "defending"),
}
SPILL_SHARE = 0.30      # כמה מקבלת כל תכונה נלווית, יחסית לעיקרית
GENERAL_SHARE = 0.15    # התפתחות רוחבית שקורית גם בלי כוונה

# ---------------------------------------------------------------------------
# חסויות, תקשורת וסוכנים
# ---------------------------------------------------------------------------

# מותגים לפי דרג. כל דרג נפתח במוניטין אחר, וכל אחד משלם אחרת.
# (שם, מוניטין מינימלי, בסיס תשלום שנתי, מכפיל דרישות תקשורת)
SPONSOR_TIERS = [
    ("local", "מקומי", 12, 22_000, 0.4, [
        "מוסך אלוני", "פלאפל הבורסה", "רהיטי בן־ארי", "חדר כושר אולימפוס",
        "סופרמרקט השכונה", "מכללת הנגב",
    ]),
    ("national", "ארצי", 34, 105_000, 0.8, [
        "בנק הראשון", "סלקום ספורט", "שופרסל", "אלקטרה", "טמפו", "יס פלוס",
    ]),
    ("continental", "יבשתי", 58, 450_000, 1.1, [
        "אאודי אירופה", "לופטהנזה", "סנטנדר", "אמסטל", "בוקינג",
    ]),
    ("global", "עולמי", 76, 1_600_000, 1.5, [
        "נייקי", "אדידס", "פומה", "רד בול", "ג'ילט", "רולקס", "אמירייטס",
    ]),
]

# סוגי חוזה מסחרי — לכל אחד אופי משלו
DEAL_KINDS = {
    "boots": {"name": "חוזה נעליים", "pay": 1.0, "media": 3, "days": 2},
    "apparel": {"name": "חוזה ביגוד", "pay": 1.25, "media": 5, "days": 3},
    "drink": {"name": "משקה אנרגיה", "pay": 0.85, "media": 4, "days": 2},
    "bank": {"name": "קמפיין בנק", "pay": 1.4, "media": 7, "days": 4},
    "car": {"name": "יבואן רכב", "pay": 1.15, "media": 5, "days": 3},
    "watch": {"name": "מותג שעונים", "pay": 1.6, "media": 6, "days": 2},
}

# עבודות תקשורת — נפתחות לפי כריזמה ומוניטין
MEDIA_JOBS = [
    ("column", "טור שבועי בעיתון ספורט", 22, 30, 45_000),
    ("panel", "פאנל אולפן אחרי משחקים", 40, 45, 120_000),
    ("doc", "סרט תיעודי על העונה שלך", 55, 55, 340_000),
    ("boot_launch", "השקה בינלאומית של דגם נעל", 70, 70, 900_000),
]

# שמות סוכנים
AGENT_NAMES = [
    "ז'ורז' מנדוזה", "רפי אלמוג", "סימונה בלאנקו", "טוני קרסטיץ'",
    "עידו שרעבי", "מארק דיוויס", "לואיז פררה", "יוסי בן־דוד",
]

# ---------------------------------------------------------------------------
# מבנה גוף לפי עמדה
# ---------------------------------------------------------------------------

# (גובה ממוצע בס"מ, סטיית תקן) — שוערים ובלמים גבוהים, כנפיים נמוכים
PHYSIQUE = {
    "GK": (189, 4.5),
    "CB": (187, 4.5),
    "LB": (178, 4.0),
    "RB": (178, 4.0),
    "DM": (183, 5.0),
    "CM": (179, 5.0),
    "AM": (176, 5.0),
    "LW": (175, 5.0),
    "RW": (175, 5.0),
    "ST": (183, 6.0),
}

# מדד מסת גוף אופייני לכדורגלן מקצועי
BMI_RANGE = (21.8, 24.2)

# ---------------------------------------------------------------------------
# אצטדיון, מתקנים וצוות מקצועי
# ---------------------------------------------------------------------------

# שמות אצטדיונים — נבחרים לפי מזהה המועדון, כך שהם קבועים לאורך המשחק
STADIUM_WORDS = [
    "האצטדיון העירוני", "היכל", "אצטדיון", "פארק", "הזירה",
]
STADIUM_SUFFIX = [
    "הצפון", "הדרום", "העמק", "החוף", "הגבעה", "המושבה", "הנמל",
    "הכרמל", "השפלה", "המדבר", "הבירה", "הגליל",
]

# מחיר כרטיס בסיסי לפי דרג הליגה (₪). מוכפל לפי מוניטין המועדון.
TICKET_BASE = {0: 140, 1: 78, 2: 46, 3: 28}

# מתקני המועדון: כל אחד משפיע על משהו אחר בסימולציה
FACILITIES = {
    "training": {
        "field": "training_facilities",
        "name": "מתקני אימון",
        "effect": "קצב ההתפתחות של כל שחקני הסגל, כולל שלך.",
        "unit": 9.0,          # כמה נקודות מוסיף שדרוג אחד
        "weeks": 6,           # כמה שבועות בנייה
        "cost": 7_000_000,    # מחיר בסיס, עולה עם הרמה הקיימת
    },
    "youth": {
        "field": "youth_academy",
        "name": "מחלקת נוער",
        "effect": "איכות השחקנים שעולים מהנוער ורמת היריבים בשנות הנוער.",
        "unit": 8.0,
        "weeks": 8,
        "cost": 5_500_000,
    },
    "medical": {
        "field": "medical_centre",
        "name": "מרכז רפואי",
        "effect": "משך הפציעות בסגל — מרכז טוב מקצר שיקום.",
        "unit": 10.0,
        "weeks": 5,
        "cost": 4_500_000,
    },
    "stadium": {
        "field": "capacity",
        "name": "הרחבת האצטדיון",
        "effect": "כמה כרטיסים אפשר למכור במשחק בית.",
        "unit": 0.18,         # תוספת של 18% מהקיבולת
        "weeks": 20,
        "cost": 7_500_000,    # מחיר לכל 1,000 מקומות שנוספים
    },
}

# בעלי תפקיד. לכל תפקיד השפעה מדידה אחת, ושכר שבועי לפי האיכות.
STAFF_ROLES = {
    "assistant": {
        "name": "עוזר מאמן",
        "effect": "מוסיף לקצב האימון של כל הסגל.",
        "wage_per_point": 62,
    },
    "fitness": {
        "name": "מאמן כושר",
        "effect": "התאוששות מהירה יותר, ופחות פציעות מעומס אימון.",
        "wage_per_point": 48,
    },
    "physio": {
        "name": "פיזיותרפיסט",
        "effect": "מקצר את משך הפציעות.",
        "wage_per_point": 44,
    },
    "scout": {
        "name": "ראש סקאוטינג",
        "effect": "משפר את איכות השחקנים שעולים מהנוער.",
        "wage_per_point": 40,
    },
    "analyst": {
        "name": "אנליסט",
        "effect": "יתרון טקטי קטן בכל משחק.",
        "wage_per_point": 52,
    },
}

STAFF_NAMES = [
    "רון אלקיים", "ז'אן פוליה", "דניאל אשכנזי", "מירי שגב", "אנדראס קלוזה",
    "יוסי דהן", "לורה בנקס", "פבלו אורטגה", "נועם ברזילי", "טל אבידן",
    "סרחיו מולינה", "אורית כהן", "מרקו יאנסן", "עדי פרץ", "חנא סרוג'י",
    "דין מקנזי", "רותם לביא", "אלכס דוברוב", "שרון מזרחי", "פייר לובלן",
]

# ---------------------------------------------------------------------------
# תכונות אופי (traits) שמשפיעות על התפתחות ועל העלילה
# ---------------------------------------------------------------------------

TRAITS = {
    "leader": {"name": "מנהיג טבעי", "desc": "מרים את הקבוצה ברגעים קשים."},
    "hothead": {"name": "חם מזג", "desc": "מקבל כרטיסים, אבל משחק עם אש."},
    "workhorse": {"name": "סוס עבודה", "desc": "מתאמן יותר מכולם ומתפתח מהר."},
    "glass": {"name": "שביר", "desc": "נוטה להיפצע."},
    "clutch": {"name": "שחקן של רגעים", "desc": "זורח במשחקים גדולים."},
    "loyal": {"name": "נאמן", "desc": "האוהדים מעריצים אותו, קשה לו לעזוב."},
    "media_darling": {"name": "חביב התקשורת", "desc": "יודע לדבר למצלמות."},
    "student": {"name": "תלמיד של המשחק", "desc": "לומד אימון מהר יותר."},
}

# ---------------------------------------------------------------------------
# שלבי קריירה
# ---------------------------------------------------------------------------

CAREER_STAGES_HE = {
    "youth": "כדורגל נוער",
    "academy": "נערי הנוער",
    "player": "שחקן מקצוען",
    "veteran": "שחקן ותיק",
    "retired": "פרישה",
    "coach": "מאמן עוזר",
    "manager": "מנג'ר ראשי",
    "director": "מנהל ספורטיבי",
    "pundit": "פרשן טלוויזיה",
    "agent": "סוכן שחקנים",
    "owner": "בעלים של מועדון",
    "legend": "אגדה",
}

TRAINING_FOCUS_HE = {
    "pace": "ספרינטים ומהירות",
    "shooting": "סיומות מול השער",
    "passing": "מסירות ומשחק קצר",
    "dribbling": "כדרור אחד על אחד",
    "defending": "עבודה הגנתית",
    "physical": "חדר כושר",
    "mental": "וידאו וטקטיקה",
    "rest": "מנוחה והתאוששות",
    "badges": "לימודי אימון (תעודות)",
    "media": "סדנת תקשורת",
    "business": "לימודי ניהול ועסקים",
    "school": "בית ספר ושיעורי בית",
    "street": "כדורגל במגרש השכונתי",
}

# ---------------------------------------------------------------------------
# מדינות המועדונים באירופה — בשביל דוחות סקאוטינג וסוכנים מחו"ל
# ---------------------------------------------------------------------------

CLUB_COUNTRY = {
    "real_castilla": "ספרד", "catalunya_fc": "ספרד", "sevilla_sur": "ספרד",
    "olympia_munchen": "גרמניה", "saxon_dortmund": "גרמניה",
    "thames_united": "אנגליה", "mersey_athletic": "אנגליה", "albion_north": "אנגליה",
    "paris_luxe": "צרפת",
    "inter_lazio": "איטליה", "milano_nord": "איטליה",
    "ajax_noord": "הולנד", "brugge_west": "בלגיה",
    "porto_atlantico": "פורטוגל", "galata_bosphorus": "טורקיה",
    "wien_donau": "אוסטריה",
}


# דגל לכל מדינה. זה לא קישוט: כשמועדון מופיע ברשימה ליד מועדון אחר,
# הדגל הוא מה שאומר במבט אחד "זה מחו\"ל" בלי לקרוא מילה.
COUNTRY_FLAGS = {
    "ישראל": "🇮🇱", "ספרד": "🇪🇸", "גרמניה": "🇩🇪", "אנגליה": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "צרפת": "🇫🇷", "איטליה": "🇮🇹", "הולנד": "🇳🇱", "בלגיה": "🇧🇪",
    "פורטוגל": "🇵🇹", "טורקיה": "🇹🇷", "אוסטריה": "🇦🇹",
}

HOME_COUNTRY = "ישראל"


def club_country(cid: str, league_id: str = "") -> str:
    """המדינה של המועדון. מועדונים ישראלים מוחזרים כ'ישראל'."""
    return CLUB_COUNTRY.get(cid, HOME_COUNTRY)


def country_flag(country: str) -> str:
    return COUNTRY_FLAGS.get(country, "🏳")


def is_foreign(cid: str) -> bool:
    return club_country(cid) != HOME_COUNTRY


def league_name(league_id: str) -> str:
    for row in LEAGUES:
        if row["id"] == league_id:
            return row["name"]
    return ""


def club_tag(cid: str, league_id: str = "") -> str:
    """שורת הזהות של מועדון: דגל, מדינה, וליגה.

    התלונה שהולידה את זה: "עירבבת מועדונים מקומיים עם מועדונים מחו\"ל".
    הנתונים תמיד היו נכונים — שלוש ליגות נפרדות — אבל בממשק שם של
    מועדון אירופי הופיע בדיוק כמו שם של מועדון מקומי, בלי שום סימן.
    זו הפונקציה שאמורה להופיע בכל מקום שבו שם מועדון מוצג.
    """
    country = club_country(cid)
    flag = country_flag(country)
    league = league_name(league_id)
    if country == HOME_COUNTRY:
        return f"{flag} {league}" if league else flag
    return f"{flag} {country}" + (f" · {league}" if league else "")


# ---------------------------------------------------------------------------
# סטטיסטיקת משחק אישית
# ---------------------------------------------------------------------------
# כל שורה: (מפתח, שם בעברית, האם "יותר זה טוב", התכונה שמייצרת אותה)
# זה החוט שמחבר בין האימון לבין מה שקרה במגרש: כל שורה נגזרת מתכונה,
# והמאמן קורא בדיוק את השורות האלה כשהוא מחליט מה לדרוש ממך בשבוע הבא.

STAT_LINES = [
    ("shots",     "בעיטות",          True,  "shooting"),
    ("on_target", "בעיטות למסגרת",   True,  "shooting"),
    ("key_passes", "מסירות מפתח",    True,  "passing"),
    ("pass_pct",  "אחוז מסירה",      True,  "passing"),
    ("dribbles",  "כדרורים שהצליחו", True,  "dribbling"),
    ("duels_pct", "אחוז דו־קרב",     True,  "physical"),
    ("tackles",   "חטיפות",          True,  "defending"),
    ("losses",    "איבודי כדור",     False, "passing"),
    ("sprints",   "ספרינטים",        True,  "pace"),
    ("distance",  'ק"מ ריצה',        True,  "physical"),
    ("reads",     "קריאות נכונות",   True,  "mental"),
]

STAT_LABELS = {key: label for key, label, _, _ in STAT_LINES}

# מה המאמן אומר כשהשורה הזאת היא הגרועה שלך במשחק,
# ומה הוא מבטיח שיקרה אם תעבוד עליה
DIRECTIVE_REASON = {
    "shooting": ("בעטת {shots} פעמים ורק {on_target} הלכו למסגרת.",
                 "אם הסיומות ישתפרו, המצבים שאתה כבר מייצר יהפכו לשערים."),
    "passing": ("איבדת {losses} כדורים ואחוז המסירה שלך היה {pass_pct}%.",
                "פחות איבודים זה יותר זמן עם הכדור — וקו הקישור יזרום דרכך."),
    "dribbling": ("ניסית לעבור אחד על אחד ויצאת מזה {dribbles} פעמים בלבד.",
                  "כדרור טוב יותר יפתח לך מסירות מפתח שהיום לא קיימות."),
    "defending": ("חטפת {tackles} כדורים. בעמדה שלך זה מעט.",
                  "עבודה הגנתית תקנה לך דקות גם במשחקים שאתה לא זורח בהם."),
    "physical": ("הפסדת את רוב הדו־קרבים — {duels_pct}% בלבד.",
                 "גוף חזק יותר גם שובר פחות: פחות פציעות, יותר דקות."),
    "pace": ("{sprints} ספרינטים. בכל פעם שהיה צריך להגיע ראשון, לא הגעת.",
             "חמישה המטרים הראשונים הם ההבדל בין מצב לבין כלום."),
    "mental": ("היית במקום הלא נכון יותר מדי פעמים — {reads} קריאות נכונות.",
               "קריאת משחק טובה חוסכת לך ריצות ומכניסה אותך למצבים."),
    "rest": ("נכנסת למשחק על {fitness}% כושר, ובדקה 60 זה נראה.",
             "שבוע קליל עכשיו מחזיר אותך שלם למשחק הבא."),
}

# מה מקבלים על כל אבן דרך שנעברת בזמן
MILESTONE_REWARD = {"potential": 2.2, "rep": 1.6, "morale": 8, "trust": 5}

# ---------------------------------------------------------------------------
# נכסים והשקעות
# ---------------------------------------------------------------------------
# (מפתח, שם, קטגוריה, מחיר, תשואה שנתית, תנודתיות, גיל/מוניטין מינימלי, תיאור)

ASSETS = [
    ("studio_flat", "דירת סטודיו להשכרה", "נדל\"ן", 1_400_000, 0.036, 0.10, 0,
     "שתי חדרים ליד המגרש. לא מרגש, ומשלם כל חודש."),
    ("family_flat", "דירת ארבעה חדרים", "נדל\"ן", 3_200_000, 0.033, 0.11, 0,
     "הדירה שההורים שלך תמיד רצו. גם שוכר טוב יושב בה."),
    ("penthouse", "פנטהאוז על הים", "נדל\"ן", 14_000_000, 0.026, 0.16, 30,
     "יותר סטייטמנט מהשקעה — אבל הוא עולה בערכו בזמן שאתה ישן בו."),
    ("shops", "שתי חנויות ברחוב ראשי", "נדל\"ן מסחרי", 6_500_000, 0.061, 0.20, 20,
     "שכירות מסחרית משלמת יותר, וגם מתפנה בלי להודיע."),
    ("office_floor", "קומת משרדים", "נדל\"ן מסחרי", 22_000_000, 0.058, 0.22, 45,
     "חוזה ארוך עם חברת הייטק. עד שהם מתכווצים."),
    ("restaurant", "מסעדה בשם שלך", "עסק", 5_000_000, 0.085, 0.45, 35,
     "השם שלך על השלט. זה מביא אנשים — כל עוד השם שווה משהו."),
    ("padel", "מתחם פאדל", "עסק", 9_000_000, 0.095, 0.34, 30,
     "שמונה מגרשים ותורים בערב. ספורט שמוכר את עצמו."),
    ("academy", "אקדמיית כדורגל לילדים", "עסק", 7_500_000, 0.072, 0.28, 40,
     "מאתיים ילדים בשנה. גם עסק, וגם משהו שנשאר אחריך."),
    ("agency_stake", "אחזקה בסוכנות שחקנים", "פיננסי", 18_000_000, 0.110, 0.50, 55,
     "עמלות של אחרים נכנסות אליך. תלוי לגמרי בעסקאות שייסגרו."),
    ("index_fund", "קרן מדד עולמית", "פיננסי", 1_000_000, 0.068, 0.30, 0,
     "משעמם, נזיל, ובטווח ארוך מנצח כמעט הכול."),
    ("club_shares", "מניות מיעוט במועדון", "פיננסי", 55_000_000, 0.045, 0.55, 70,
     "אחוזים במועדון בליגה. הערך שלהן זז עם הטבלה."),
]

ASSET_EVENTS = [
    ("נדל\"ן", "השוכר עזב באמצע החוזה. חודשיים בלי הכנסה.", -0.35),
    ("נדל\"ן", "התחדשות עירונית בשכונה — השווי קפץ.", 0.22),
    ("נדל\"ן מסחרי", "רשת גדולה חתמה על החנות. השכירות עלתה.", 0.28),
    ("נדל\"ן מסחרי", "הרחוב נסגר לשיפוצים לחצי שנה.", -0.30),
    ("עסק", "ביקורת מצוינת במוסף הסופ\"ש. תורים בכניסה.", 0.40),
    ("עסק", "מנהל התחלף וחצי מהצוות הלך. חודש גרוע.", -0.38),
    ("פיננסי", "רבעון חזק בשווקים.", 0.33),
    ("פיננסי", "תיקון חד בשווקים. על הנייר, בינתיים.", -0.36),
]

# ---------------------------------------------------------------------------
# סעיפי בונוס בחוזי חסות
# ---------------------------------------------------------------------------
# (מפתח, תיאור, מה נמדד, סכום ליחידה כאחוז מהחוזה השנתי)

BONUS_CLAUSES = [
    ("per_goal", "בונוס לכל שער בעונה", "goals", 0.030),
    ("per_assist", "בונוס לכל בישול בעונה", "assists", 0.018),
    ("trophy", "בונוס על תואר", "trophies", 0.320),
    ("caps", "בונוס על משחקי נבחרת", "caps", 0.055),
    ("rating", "בונוס על ציון עונה מעל 7.0", "rating", 0.240),
]

# ---------------------------------------------------------------------------
# תכונות מפורטות — המבנה של המשחק המקורי
# ---------------------------------------------------------------------------
# שבע התכונות שהיו כאן קודם הן קיבוץ גס. במקור יש ארבע קבוצות ועשרות
# תכונות, כל אחת בסולם 1-20, וזה מה שהופך שחקן לשחקן ולא למספר אחד.
# מכאן ואילך: התכונות המפורטות הן האמת, ושבע הקבוצות נגזרות מהן.

# הסולם של התכונות המפורטות. 1-20 כמו במקור: 20 הוא לא "מצוין" אלא
# הטוב בעולם, ומעטים מגיעים לשם ביותר מתכונה אחת בכל הקריירה.
MIN_DETAIL = 1
MAX_DETAIL = 20

TECHNICAL = [
    ("corners", "קרנות"),
    ("crossing", "הרמות"),
    ("dribbling", "כדרור"),
    ("finishing", "סיום"),
    ("first_touch", "נגיעה ראשונה"),
    ("free_kick", "בעיטות חופשיות"),
    ("heading", "נגיחות"),
    ("long_shots", "בעיטות מרחוק"),
    ("long_throws", "זריקות ארוכות"),
    ("marking", "צמידות"),
    ("passing", "מסירה"),
    ("penalty_taking", "פנדלים"),
    ("tackling", "חטיפה"),
    ("technique", "טכניקה"),
]

MENTAL = [
    ("aggression", "אגרסיביות"),
    ("anticipation", "חיזוי"),
    ("bravery", "אומץ"),
    ("composure", "קור רוח"),
    ("concentration", "ריכוז"),
    ("decisions", "קבלת החלטות"),
    ("determination", "נחישות"),
    ("flair", "ברק"),
    ("leadership", "מנהיגות"),
    ("off_the_ball", "תנועה בלי כדור"),
    ("positioning", "מיקום"),
    ("teamwork", "עבודת צוות"),
    ("vision", "ראיית משחק"),
    ("work_rate", "קצב עבודה"),
]

PHYSICAL = [
    ("acceleration", "האצה"),
    ("agility", "זריזות"),
    ("balance", "שיווי משקל"),
    ("jumping_reach", "קפיצה"),
    ("natural_fitness", "כושר טבעי"),
    ("pace", "מהירות"),
    ("stamina", "סיבולת"),
    ("strength", "כוח"),
]

GOALKEEPING = [
    ("aerial_reach", "הגעה באוויר"),
    ("command_of_area", "שליטה ברחבה"),
    ("communication", "תקשורת"),
    ("eccentricity", "אקסצנטריות"),
    ("handling", "אחיזה"),
    ("kicking", "בעיטה"),
    ("one_on_ones", "אחד על אחד"),
    ("reflexes", "רפלקסים"),
    ("rushing_out", "יציאה מהשער"),
    ("tendency_to_punch", "נטייה לאגרוף"),
    ("throwing", "זריקה"),
]

ATTR_GROUPS = [
    ("technical", "טכניות", TECHNICAL),
    ("mental", "מנטליות", MENTAL),
    ("physical", "פיזיות", PHYSICAL),
    ("goalkeeping", "שוערים", GOALKEEPING),
]

DETAIL_NAMES_HE = {}
DETAIL_GROUP = {}
for _key, _label, _rows in ATTR_GROUPS:
    for _attr, _he in _rows:
        DETAIL_NAMES_HE[_attr] = _he
        DETAIL_GROUP[_attr] = _key

OUTFIELD_ATTRS = [a for a, _ in TECHNICAL] + [a for a, _ in MENTAL] + [a for a, _ in PHYSICAL]
KEEPER_ATTRS = [a for a, _ in GOALKEEPING] + [a for a, _ in MENTAL] + [a for a, _ in PHYSICAL] + [
    "first_touch", "passing", "technique"]

# תכונות שאין להן משמעות אמיתית לשחקן שדה או לשוער — לא מוצגות ולא מתאמנות
def attrs_for(position: str):
    return KEEPER_ATTRS if position == "GK" else OUTFIELD_ATTRS


# ---------------------------------------------------------------------------
# הגזירה: שבע הקבוצות מתוך התכונות המפורטות
# ---------------------------------------------------------------------------
# כל קבוצה היא ממוצע משוקלל של התכונות שבאמת מרכיבות אותה. ככה אימון
# על "סיום" מזיז את קבוצת הבעיטה, ומנוע המשחקים הקיים ממשיך לעבוד
# בדיוק כמו קודם — רק שמתחתיו יש עכשיו עולם שלם.

GROUP_MAP = {
    "pace": {"acceleration": 1.0, "pace": 1.0, "agility": 0.45, "balance": 0.30},
    "shooting": {"finishing": 1.0, "long_shots": 0.55, "technique": 0.45,
                 "composure": 0.45, "heading": 0.30},
    "passing": {"passing": 1.0, "vision": 0.70, "technique": 0.45,
                "first_touch": 0.40, "crossing": 0.30},
    "dribbling": {"dribbling": 1.0, "first_touch": 0.50, "agility": 0.45,
                  "flair": 0.40, "balance": 0.30, "technique": 0.35},
    "defending": {"tackling": 1.0, "marking": 0.95, "positioning": 0.70,
                  "anticipation": 0.45, "concentration": 0.35, "aggression": 0.20},
    "physical": {"strength": 1.0, "stamina": 0.80, "jumping_reach": 0.55,
                 "natural_fitness": 0.45, "work_rate": 0.55, "bravery": 0.30},
    "mental": {"decisions": 1.0, "anticipation": 0.70, "off_the_ball": 0.60,
               "teamwork": 0.55, "concentration": 0.55, "composure": 0.50,
               "vision": 0.45, "determination": 0.40, "positioning": 0.35},
}

GROUP_MAP_GK = {
    "pace": {"acceleration": 1.0, "agility": 0.80, "pace": 0.55},
    "shooting": {"kicking": 1.0, "technique": 0.45, "throwing": 0.35},
    "passing": {"kicking": 1.0, "passing": 0.70, "vision": 0.55, "throwing": 0.45},
    "dribbling": {"first_touch": 1.0, "technique": 0.65, "rushing_out": 0.45,
                  "composure": 0.40},
    "defending": {"reflexes": 1.0, "handling": 0.95, "one_on_ones": 0.75,
                  "positioning": 0.70, "command_of_area": 0.60, "aerial_reach": 0.55},
    "physical": {"strength": 1.0, "jumping_reach": 0.85, "natural_fitness": 0.55,
                 "agility": 0.55, "stamina": 0.30},
    "mental": {"decisions": 1.0, "concentration": 0.85, "communication": 0.65,
               "anticipation": 0.60, "composure": 0.55},
}

# ---------------------------------------------------------------------------
# תכונות נסתרות ואישיות
# ---------------------------------------------------------------------------
# האישיות במקור אינה שדה — היא נגזרת מתכונות שאתה לא רואה. שחקן עם
# מקצוענות 18 ונחישות 17 יתפתח אחרת מזה שיש לו 6, ואף מספר במסך לא
# יסביר לך למה.

HIDDEN_ATTRS = [
    ("ambition", "שאפתנות"),
    ("loyalty", "נאמנות"),
    ("pressure", "עמידות בלחץ"),
    ("professionalism", "מקצוענות"),
    ("sportsmanship", "רוח ספורטיבית"),
    ("temperament", "מזג"),
    ("controversy", "נטייה לסערות"),
]

# (שם, תיאור, תנאים) — נבדק לפי הסדר, הראשון שמתאים זוכה
PERSONALITIES = [
    ("model_citizen", "אזרח מופת",
     "מקצוען עד הסוף, בלי רעש, ומרים את כל מי שסביבו.",
     {"professionalism": 18, "determination": 15, "sportsmanship": 15, "temperament": 15}),
    ("model_professional", "מקצוען מודל",
     "ראשון באימון, אחרון בחדר הכושר. מתפתח מהר יותר מכולם.",
     {"professionalism": 18, "determination": 15, "ambition": 12}),
    ("perfectionist", "פרפקציוניסט",
     "לא מרוצה גם אחרי שער. זה מה שדוחף אותו, וזה גם מה ששוחק אותו.",
     {"professionalism": 17, "determination": 18, "ambition": 17}),
    ("resolute", "נחוש",
     "לא נשבר. משחקים גדולים הם המקום שלו.",
     {"determination": 18, "pressure": 15}),
    ("driven", "מונע מבפנים",
     "רוצה להגיע רחוק, ומוכן לשלם על זה.",
     {"ambition": 17, "determination": 14, "professionalism": 12}),
    ("professional", "מקצוען",
     "עושה את העבודה, בלי דרמות.",
     {"professionalism": 15, "determination": 12}),
    ("fairly_professional", "מקצוען למדי",
     "לרוב עושה את הדבר הנכון.",
     {"professionalism": 12, "determination": 10}),
    ("loyal", "נאמן",
     "המועדון שגידל אותו הוא הבית, וקשה לו לעזוב.",
     {"loyalty": 17, "professionalism": 10}),
    ("temperamental", "מזגזג",
     "יום אחד הוא מכריע, יום אחר הוא לא שם.",
     {"temperament": -7}),
    ("casual", "מזלזל",
     "כישרון יש. את השעה הנוספת באימון אין.",
     {"professionalism": -7}),
    ("unambitious", "חסר שאיפה",
     "מרוצה ממה שיש. זה לא בהכרח רע — זה פשוט לא ייקח אותו רחוק.",
     {"ambition": -6}),
    ("balanced", "מאוזן",
     "בלי קצוות. עובד, משחק, הולך הביתה.",
     {}),
]

# ערך שלילי בתנאי פירושו "לכל היותר": {"temperament": -7} = מזג 7 ומטה

PERSONALITY_EFFECT = {
    # (מכפיל התפתחות, תנודתיות מורל, השפעה על אמון המאמן)
    "model_citizen": (1.30, 0.70, 1.25),
    "model_professional": (1.28, 0.72, 1.20),
    "perfectionist": (1.26, 1.15, 1.05),
    "resolute": (1.18, 0.80, 1.10),
    "driven": (1.16, 0.95, 1.05),
    "professional": (1.10, 0.90, 1.10),
    "fairly_professional": (1.02, 1.00, 1.00),
    "loyal": (1.00, 0.90, 1.15),
    "balanced": (0.96, 1.00, 1.00),
    "temperamental": (0.82, 1.45, 0.80),
    "casual": (0.80, 1.10, 0.85),
    "unambitious": (0.88, 0.95, 1.00),
}

# ---------------------------------------------------------------------------
# תפקידים וחובות
# ---------------------------------------------------------------------------
# עמדה היא לא תפקיד. "חלוץ" אומר איפה אתה עומד; "חלוץ בור" אומר מה
# העבודה שלך, אילו תכונות באמת נמדדות אצלך, ומה המאמן יצפה לראות.
# (מפתח, שם, עמדות, חובות, תכונות מפתח, תכונות משניות, תיאור)

ROLES = [
    # --- שוער ---
    ("gk", "שוער", ["GK"], ["defend"],
     ["reflexes", "handling", "one_on_ones", "positioning", "concentration"],
     ["aerial_reach", "command_of_area", "communication", "decisions"],
     "נשאר על הקו, שומר על הרחבה, ולא מחפש הרפתקאות."),
    ("sweeper_keeper", "שוער־מנקה", ["GK"], ["defend", "support", "attack"],
     ["rushing_out", "one_on_ones", "first_touch", "passing", "decisions"],
     ["reflexes", "handling", "composure", "anticipation", "acceleration"],
     "יוצא מהרחבה, מוסר ראשונה, ומשחק כמו שחקן אחד־עשר."),

    # --- בלמים ---
    ("cd_defend", "בלם", ["CB"], ["defend", "stopper", "cover"],
     ["marking", "tackling", "positioning", "heading", "jumping_reach"],
     ["strength", "concentration", "bravery", "anticipation"],
     "לא נותן לכדור לעבור. פשוט, ובלי סיבוכים."),
    ("bpd", "בלם שמוציא", ["CB"], ["defend", "stopper", "cover"],
     ["passing", "vision", "first_touch", "composure", "technique"],
     ["marking", "tackling", "positioning", "decisions"],
     "לא רק הורס — פותח. המסירה הראשונה שלו היא ההתקפה."),
    ("ncb", "בלם בלי שטויות", ["CB"], ["defend", "stopper", "cover"],
     ["heading", "jumping_reach", "strength", "bravery", "marking"],
     ["tackling", "aggression", "positioning"],
     "כדור באוויר, כדור לצד השני. אין בעיות."),
    ("libero", "ליברו", ["CB"], ["defend", "support"],
     ["passing", "vision", "technique", "decisions", "off_the_ball"],
     ["marking", "tackling", "first_touch", "composure", "stamina"],
     "יוצא מהקו האחורי עם הכדור ומייצר עודף במרכז."),

    # --- מגנים ---
    ("fb", "מגן", ["LB", "RB"], ["defend", "support", "automatic"],
     ["marking", "tackling", "positioning", "anticipation", "concentration"],
     ["crossing", "stamina", "teamwork", "work_rate"],
     "מגן קודם כול. עולה רק כשבטוח."),
    ("wb", "מגן מתקדם", ["LB", "RB"], ["defend", "support", "attack", "automatic"],
     ["crossing", "dribbling", "stamina", "work_rate", "acceleration"],
     ["marking", "tackling", "teamwork", "off_the_ball"],
     "עולה ויורד תשעים דקות בקו. שני תפקידים בגוף אחד."),
    ("cwb", "מגן מתקדם מלא", ["LB", "RB"], ["support", "attack"],
     ["crossing", "dribbling", "flair", "stamina", "acceleration", "technique"],
     ["off_the_ball", "work_rate", "agility", "passing"],
     "כמעט כנף. הקו כולו שלו, וההגנה תסתדר."),
    ("iwb", "מגן מתהפך", ["LB", "RB"], ["defend", "support", "attack"],
     ["passing", "vision", "first_touch", "decisions", "positioning"],
     ["tackling", "marking", "composure", "teamwork"],
     "נכנס פנימה לקו הקישור ומייצר עודף במרכז, לא בקו."),
    ("nfb", "מגן בלי שטויות", ["LB", "RB"], ["defend"],
     ["marking", "tackling", "positioning", "strength", "bravery"],
     ["concentration", "anticipation", "aggression"],
     "לא מרים ראש. מרחיק, וממשיך לעבוד."),

    # --- קשרים הגנתיים ---
    ("dm", "קשר הגנתי", ["DM"], ["defend", "support"],
     ["positioning", "tackling", "anticipation", "concentration", "teamwork"],
     ["marking", "strength", "decisions", "passing"],
     "לפני ההגנה, אחרי הקישור. השקט של הקבוצה."),
    ("anchor", "עוגן", ["DM"], ["defend"],
     ["positioning", "marking", "tackling", "concentration", "decisions"],
     ["anticipation", "strength", "teamwork"],
     "לא זז מהמקום. סותם את החור שבין הקווים."),
    ("half_back", "מגן־קשר", ["DM"], ["defend"],
     ["positioning", "marking", "tackling", "anticipation", "teamwork"],
     ["passing", "first_touch", "composure", "stamina"],
     "יורד בין הבלמים בבנייה, ועולה בהגנה. שלושה נגד שניים, תמיד."),
    ("bwm", "קשר חוטף", ["DM", "CM"], ["defend", "support"],
     ["tackling", "aggression", "work_rate", "stamina", "bravery"],
     ["anticipation", "positioning", "teamwork", "determination"],
     "רודף את הכדור עד שהוא מקבל אותו. או עד שהשופט שורק."),
    ("dlp", "קשר בונה עמוק", ["DM", "CM"], ["defend", "support"],
     ["passing", "vision", "technique", "composure", "decisions"],
     ["first_touch", "teamwork", "anticipation", "positioning"],
     "המשחק עובר דרכו. רואה את המסירה שלושה מהלכים לפני כולם."),
    ("regista", "רג'יסטה", ["DM"], ["support"],
     ["vision", "passing", "flair", "technique", "composure", "decisions"],
     ["first_touch", "off_the_ball", "dribbling", "anticipation"],
     "בונה עמוק אבל בלי רסן — מחפש את המסירה שתשבור את הכל."),
    ("volante", "סגונדו וולנטה", ["DM"], ["support", "attack"],
     ["stamina", "work_rate", "long_shots", "off_the_ball", "tackling"],
     ["passing", "positioning", "strength", "acceleration"],
     "מתחיל אחורה ומסיים ברחבה. ריאות של שניים."),

    # --- קשרים מרכזיים ---
    ("cm", "קשר מרכזי", ["CM"], ["defend", "support", "attack", "automatic"],
     ["passing", "teamwork", "decisions", "work_rate", "positioning"],
     ["first_touch", "tackling", "stamina", "composure"],
     "הדבק. עושה את מה שהמשחק צריך באותו רגע."),
    ("b2b", "קשר ריאות", ["CM"], ["support"],
     ["stamina", "work_rate", "teamwork", "off_the_ball", "passing"],
     ["tackling", "long_shots", "strength", "determination"],
     "רץ שנים־עשר קילומטר וגם מוסר. מרגישים כשהוא לא שם."),
    ("mezzala", "מצאלה", ["CM"], ["support", "attack"],
     ["dribbling", "passing", "off_the_ball", "flair", "vision"],
     ["technique", "acceleration", "long_shots", "work_rate"],
     "נפתח לחצי־חלל בין המגן לבלם, ומשם שובר."),
    ("carrilero", "קארילרו", ["CM"], ["support"],
     ["teamwork", "work_rate", "positioning", "stamina", "passing"],
     ["tackling", "decisions", "anticipation"],
     "מכסה את הרצועה שבין המרכז לקו. עבודה שאף אחד לא מריע לה."),
    ("rpm", "בונה נודד", ["CM"], ["support"],
     ["passing", "vision", "technique", "off_the_ball", "stamina"],
     ["dribbling", "first_touch", "work_rate", "composure"],
     "אין לו עמדה. הוא הולך לאן שהכדור, והכדור הולך אליו."),
    ("ap", "בונה מתקדם", ["CM", "AM"], ["support", "attack"],
     ["passing", "vision", "technique", "flair", "first_touch"],
     ["dribbling", "composure", "off_the_ball", "decisions"],
     "עובד גבוה, בין הקווים, ומחפש את הכדור האחרון."),

    # --- קשרים התקפיים ---
    ("am", "קשר התקפי", ["AM"], ["support", "attack"],
     ["passing", "off_the_ball", "technique", "vision", "long_shots"],
     ["first_touch", "dribbling", "composure", "flair"],
     "בין הקישור להתקפה, במקום שקשה לשמור עליו."),
    ("enganche", "אנגנצ'ה",  ["AM"], ["support"],
     ["vision", "passing", "technique", "composure", "flair"],
     ["first_touch", "decisions", "anticipation"],
     "העשר הקלאסי. לא רץ אחורה, ולא צריך — הכדור מגיע אליו."),
    ("shadow", "חלוץ צל", ["AM"], ["attack"],
     ["off_the_ball", "finishing", "acceleration", "anticipation", "composure"],
     ["dribbling", "first_touch", "long_shots", "work_rate"],
     "נכנס מאחורי החלוץ בדיוק כשההגנה מסתכלת עליו."),
    ("trequartista", "טרקוורטיסטה", ["AM", "ST"], ["attack"],
     ["flair", "vision", "technique", "dribbling", "off_the_ball"],
     ["passing", "finishing", "first_touch", "composure"],
     "משוחרר מכל חובה הגנתית. או שהוא מכריע, או שהוא נעלם."),

    # --- כנפיים ---
    ("winger", "כנף", ["LW", "RW"], ["support", "attack"],
     ["crossing", "dribbling", "acceleration", "pace", "technique"],
     ["agility", "flair", "off_the_ball", "balance"],
     "אחד על אחד, ואז הרמה. הקהל קם כשהכדור מגיע אליו."),
    ("if", "חלוץ פנימי", ["LW", "RW"], ["support", "attack"],
     ["dribbling", "finishing", "off_the_ball", "acceleration", "first_touch"],
     ["long_shots", "agility", "flair", "composure"],
     "חותך פנימה מהקו על הרגל החזקה ומחפש שער."),
    ("iw", "כנף מתהפכת", ["LW", "RW"], ["support", "attack"],
     ["passing", "crossing", "dribbling", "vision", "technique"],
     ["off_the_ball", "agility", "first_touch", "decisions"],
     "חותך פנימה, אבל כדי לבשל — לא כדי לבעוט."),
    ("wp", "בונה מהקו", ["LW", "RW"], ["support", "attack"],
     ["passing", "vision", "technique", "crossing", "first_touch"],
     ["dribbling", "composure", "decisions", "flair"],
     "מקבל את הכדור בקו ומנהל ממנו את ההתקפה."),
    ("raumdeuter", "ראומדויטר", ["LW", "RW"], ["attack"],
     ["off_the_ball", "anticipation", "finishing", "concentration", "composure"],
     ["decisions", "acceleration", "first_touch", "teamwork"],
     "לא מכדרר ולא מרים. פשוט נמצא במקום שאף אחד לא שמר עליו."),
    ("wtf", "כנף מטרה", ["LW", "RW"], ["support", "attack"],
     ["heading", "jumping_reach", "strength", "bravery", "first_touch"],
     ["crossing", "teamwork", "off_the_ball"],
     "מחזיק את הכדור בקו ומושך אליו את המגן."),
    ("dw", "כנף הגנתית", ["LW", "RW"], ["defend", "support"],
     ["work_rate", "stamina", "teamwork", "tackling", "positioning"],
     ["crossing", "dribbling", "anticipation", "marking"],
     "רץ אחורה עם המגן שלהם. לא זוהר, אבל בלעדיו הקו נשבר."),

    # --- חלוצים ---
    ("af", "חלוץ מתקדם", ["ST"], ["attack"],
     ["finishing", "off_the_ball", "acceleration", "composure", "dribbling"],
     ["first_touch", "anticipation", "pace", "technique"],
     "רץ לעומק בכל הזדמנות, ומחפש את הכדור מאחורי ההגנה."),
    ("poacher", "חלוץ בור", ["ST"], ["attack"],
     ["finishing", "off_the_ball", "anticipation", "composure", "concentration"],
     ["first_touch", "acceleration", "heading", "decisions"],
     "לא נוגע בכדור תשעים דקות, ומכריע ברגע הנכון."),
    ("tf", "חלוץ מטרה", ["ST"], ["support", "attack"],
     ["heading", "jumping_reach", "strength", "bravery", "first_touch"],
     ["finishing", "teamwork", "balance", "composure"],
     "מחזיק עם הגב לשער עד שכל הקבוצה עולה."),
    ("cf", "חלוץ מושלם", ["ST"], ["support", "attack"],
     ["finishing", "dribbling", "passing", "first_touch", "technique", "off_the_ball"],
     ["composure", "vision", "strength", "acceleration", "flair"],
     "כובש, מבשל, מחזיק, פותח. עושה הכול, וטוב בהכול."),
    ("dlf", "חלוץ נסוג", ["ST"], ["support", "attack"],
     ["first_touch", "passing", "technique", "composure", "vision"],
     ["finishing", "off_the_ball", "strength", "teamwork"],
     "יורד לקבל בין הקווים ומושך את הבלם אחריו."),
    ("pf", "חלוץ לוחץ", ["ST"], ["defend", "support", "attack"],
     ["work_rate", "stamina", "aggression", "bravery", "teamwork"],
     ["finishing", "off_the_ball", "anticipation", "acceleration"],
     "הלחיצה מתחילה ממנו. ההגנה שלהם לא נחה רגע."),
    ("f9", "תשע מדומה", ["ST"], ["support"],
     ["passing", "vision", "first_touch", "technique", "off_the_ball", "flair"],
     ["dribbling", "finishing", "composure", "decisions"],
     "יורד לקישור ומשאיר את הרחבה ריקה — למישהו אחר."),
]

DUTY_NAMES_HE = {
    "defend": "הגנה", "support": "תמיכה", "attack": "התקפה",
    "stopper": "בולם", "cover": "מכסה", "automatic": "אוטומטי",
}

ROLE_BY_KEY = {row[0]: row for row in ROLES}


def roles_for(position: str):
    """התפקידים שאפשר למלא בעמדה נתונה."""
    return [row for row in ROLES if position in row[2]]


# כמה כל חובה מזיזה את אופי התפקיד: (נטייה הגנתית, נטייה התקפית, ריצה)
DUTY_SHIFT = {
    "defend": (0.28, -0.22, -0.05),
    "cover": (0.30, -0.24, -0.02),
    "stopper": (0.24, -0.16, 0.06),
    "support": (0.0, 0.0, 0.08),
    "automatic": (0.05, 0.05, 0.04),
    "attack": (-0.22, 0.30, 0.05),
}

# ---------------------------------------------------------------------------
# הוראות קבוצתיות
# ---------------------------------------------------------------------------
# עד עכשיו הטקטיקה הייתה משהו שקרה מעליך. במקור היא מה שקובע מה אתה
# עושה תשעים דקות: כמה תיגע בכדור, כמה תרוץ, כמה תאבד. המאמן בוחר,
# ואתה מרגיש. (מפתח, שם, ערך -2..2)

TEAM_INSTRUCTIONS = {
    "mentality": ("מנטליות", [
        ("very_defensive", "הגנתית מאוד", -2), ("defensive", "הגנתית", -1),
        ("balanced", "מאוזנת", 0),
        ("positive", "חיובית", 1), ("attacking", "התקפית", 2),
    ]),
    "tempo": ("קצב", [
        ("much_lower", "איטי מאוד", -2), ("lower", "איטי", -1),
        ("standard", "רגיל", 0),
        ("higher", "מהיר", 1), ("much_higher", "מהיר מאוד", 2),
    ]),
    "width": ("רוחב", [
        ("very_narrow", "צר מאוד", -2), ("narrow", "צר", -1),
        ("standard", "רגיל", 0),
        ("wide", "רחב", 1), ("very_wide", "רחב מאוד", 2),
    ]),
    "passing": ("אורך מסירה", [
        ("much_shorter", "קצר מאוד", -2), ("shorter", "קצר", -1),
        ("standard", "רגיל", 0),
        ("direct", "ישיר", 1), ("much_direct", "ישיר מאוד", 2),
    ]),
    "pressing": ("עוצמת לחיצה", [
        ("much_less", "נמוכה מאוד", -2), ("less", "נמוכה", -1),
        ("standard", "רגילה", 0),
        ("more", "גבוהה", 1), ("much_more", "גבוהה מאוד", 2),
    ]),
    "engagement": ("קו לחיצה", [
        ("much_deeper", "עמוק מאוד", -2), ("deeper", "עמוק", -1),
        ("standard", "רגיל", 0),
        ("higher", "גבוה", 1), ("much_higher", "גבוה מאוד", 2),
    ]),
    "d_line": ("קו הגנה", [
        ("much_deeper", "עמוק מאוד", -2), ("deeper", "עמוק", -1),
        ("standard", "רגיל", 0),
        ("higher", "גבוה", 1), ("much_higher", "גבוה מאוד", 2),
    ]),
}

INSTRUCTION_KEYS = list(TEAM_INSTRUCTIONS)

# סגנונות מוכנים — כל מאמן משחק לפי אחד מהם, ואתה יכול לקרוא אותו
TACTICAL_STYLES = [
    ("gegenpress", "גגנפרסינג",
     {"mentality": 2, "tempo": 2, "width": 1, "passing": 0,
      "pressing": 2, "engagement": 2, "d_line": 2},
     "מאבדים את הכדור? מחזירים אותו תוך שש שניות. תשעים דקות של ריצה."),
    ("tiki_taka", "טיקי־טאקה",
     {"mentality": 1, "tempo": -1, "width": -1, "passing": -2,
      "pressing": 1, "engagement": 1, "d_line": 1},
     "החזקה כשיטת הגנה. מאות מסירות, וסבלנות עד שנפתח חור."),
    ("counter", "מעברים מהירים",
     {"mentality": -1, "tempo": 2, "width": 0, "passing": 2,
      "pressing": -1, "engagement": -1, "d_line": -1},
     "נותנים להם את הכדור, ואז רצים שישים מטר בשלוש מסירות."),
    ("control", "שליטה",
     {"mentality": 1, "tempo": 0, "width": 1, "passing": -1,
      "pressing": 0, "engagement": 0, "d_line": 1},
     "מנהלים את הקצב, מחזיקים גבוה, ולא ממהרים לשום מקום."),
    ("direct", "כדורגל ישיר",
     {"mentality": 1, "tempo": 1, "width": 1, "passing": 2,
      "pressing": 0, "engagement": 0, "d_line": 0},
     "קדימה מהר, שנייה, ולחפש את הראש של החלוץ."),
    ("catenaccio", "בטון",
     {"mentality": -2, "tempo": -1, "width": -2, "passing": -1,
      "pressing": -2, "engagement": -2, "d_line": -2},
     "אחד־אפס זה ניצחון מושלם. שני קווים של ארבעה, ובהצלחה."),
    ("wing_play", "משחק קו",
     {"mentality": 1, "tempo": 1, "width": 2, "passing": 1,
      "pressing": 0, "engagement": 0, "d_line": 0},
     "הכול דרך הקווים. הרמות, קרנות, ועוד הרמות."),
    ("balanced_style", "מאוזן",
     {"mentality": 0, "tempo": 0, "width": 0, "passing": 0,
      "pressing": 0, "engagement": 0, "d_line": 0},
     "בלי אג'נדה. מגיבים למה שהמשחק נותן."),
]

STYLE_BY_KEY = {row[0]: row for row in TACTICAL_STYLES}


def instruction_label(key: str, value: int) -> str:
    """השם בעברית של ערך ההוראה."""
    rows = TEAM_INSTRUCTIONS.get(key)
    if not rows:
        return ""
    for _slug, label, level in rows[1]:
        if level == value:
            return label
    return ""

# ---------------------------------------------------------------------------
# מה כל תכונה עושה בפועל
# ---------------------------------------------------------------------------
# "מה זה צמידות? במה הוא מועיל?" — שאלה טובה שלא הייתה לה תשובה בשום
# מקום במשחק. לכל תכונה: מה היא, מה היא עושה על הדשא, ומי צריך אותה.
# (מפתח: (הסבר קצר, מה זה עושה במשחק, מי צריך))

ATTR_INFO = {
    # --- טכניות ---
    "corners": ("בעיטת קרן מדויקת.",
                "קובע כמה מהקרנות שלך מגיעות לראש הנכון ברחבה.",
                "מי שבועט קרנות — לרוב קשר או כנף עם רגל טובה."),
    "crossing": ("הרמה מהאגף לרחבה.",
                 "מעלה את מסירות המפתח שלך כשאתה מגיע לקו הרוחב.",
                 "כנפיים ומגנים מתקדמים. חסר ערך לבלם."),
    "dribbling": ("לרוץ עם הכדור בשליטה צמודה.",
                  "קובע כמה יריבים תעבור אחד על אחד, ופחות איבודי כדור.",
                  "כנפיים, קשרים התקפיים וחלוצים שמקבלים עם הפנים לשער."),
    "finishing": ("להכניס את הכדור לרשת ממצב.",
                  "הקובע הישיר בכמה מהבעיטות שלך הולכות למסגרת ונכנסות.",
                  "כל מי שנמצא ברחבה. התכונה החשובה ביותר לחלוץ."),
    "first_touch": ("הנגיעה הראשונה בכדור.",
                    "נגיעה טובה חוסכת חצי שנייה, וחצי שנייה זה מצב.",
                    "כולם, וקריטית למי שמקבל עם הגב לשער."),
    "free_kick": ("בעיטה חופשית מדויקת.",
                  "מכריעה משחקים צמודים. משתפרת רק באימון ישיר.",
                  "בועט הכדורים הנייחים של הקבוצה."),
    "heading": ("לכוון נגיחה, לא רק להגיע לכדור.",
                "שערים מקרנות והרחקות מהרחבה שלך.",
                "בלמים, חלוצי מטרה, וכל מי שגבוה."),
    "long_shots": ("בעיטה מחוץ לרחבה.",
                   "פותחת הגנות שמסתגרות, כשאין דרך פנימה.",
                   "קשרים התקפיים וקשרי ריאות שמגיעים לקצה הרחבה."),
    "long_throws": ("זריקת חוץ ארוכה.",
                    "הופכת זריקה לקרן. נישתי, אבל אמיתי.",
                    "מגנים בקבוצות שמשחקות ישיר."),
    "marking": ("להישאר צמוד ליריב שלך.",
                "שומר שהיריב שאתה אחראי עליו לא יקבל כדור בכלל.",
                "בלמים ומגנים. קשר הגנתי גם צריך."),
    "passing": ("להעביר את הכדור למקום הנכון.",
                "מעלה את אחוז המסירה ומוריד איבודי כדור.",
                "כולם. הבסיס של כל תפקיד בקישור."),
    "penalty_taking": ("לבעוט מ-11 מטר.",
                       "אחד־עשר מטר, ותשעים דקות תלויות בזה.",
                       "בועט הפנדלים. משתפר רק באימון ישיר."),
    "tackling": ("לחטוף כדור בלי לעשות עבירה.",
                 "כל חטיפה נקייה היא התקפה שנעצרה ואחת שמתחילה.",
                 "בלמים, מגנים וקשרים הגנתיים."),
    "technique": ("האיכות הכללית שלך עם הכדור.",
                  "מכפיל שקט: משפר בעיטה, מסירה, הרמה וכדרור יחד.",
                  "כולם. במיוחד מי שהתפקיד שלו הוא לבנות."),
    # --- מנטליות ---
    "aggression": ("כמה אתה נכנס לכל אירוע.",
                   "יותר לחיצה ויותר חטיפות — וגם יותר כרטיסים.",
                   "קשרים חוטפים וחלוצים לוחצים. פחות לבנאים."),
    "anticipation": ("לקרוא מה עומד לקרות רגע לפני.",
                     "מגיע ראשון לכדור בלי לרוץ מהר יותר.",
                     "כולם. לחלוץ בור זו התכונה השנייה בחשיבותה."),
    "bravery": ("להיכנס למקום שכואב.",
                "נגיחות בקהל ורגליים בתוך דו־קרב. גם סיכון פציעה.",
                "בלמים, חלוצי מטרה, שוערים."),
    "composure": ("להישאר קר כשהלחץ עולה.",
                  "ההבדל בין בעיטה למסגרת לבין בעיטה ליציע בדקה 89.",
                  "כל מי שמסיים מצבים או מוסר תחת לחץ."),
    "concentration": ("להישאר בפוקוס תשעים דקות.",
                      "מונע את הרגע האחד שבו נרדמת ועלה שער.",
                      "בלמים ושוערים בראש הרשימה."),
    "decisions": ("לבחור נכון את הפעולה הבאה.",
                  "מוסר או מכדרר, בועט או מחכה — התכונה שקובעת.",
                  "כולם, בלי יוצא מן הכלל."),
    "determination": ("כמה אתה מוכן לעבוד בשביל זה.",
                      "מכפיל ישירות את קצב ההתפתחות שלך באימונים.",
                      "כולם. זו התכונה שקובעת אם תממש את הפוטנציאל."),
    "flair": ("לעשות את מה שאף אחד לא ציפה.",
              "פותח מצבים שמערך מסודר לא היה מייצר.",
              "כנפיים, עשרות ותשע מדומה. מסוכן לבלם."),
    "leadership": ("להרים את מי שסביבך.",
                   "משפיע על הקבוצה, על הקפטנות ועל הקריירה שאחרי.",
                   "קפטנים, בלמים, שוערים."),
    "off_the_ball": ("לזוז נכון כשהכדור לא אצלך.",
                     "מייצר לך מצבים — יותר בעיטות, יותר ספרינטים.",
                     "חלוצים וכנפיים. אצל חלוץ בור זו התכונה מספר אחת."),
    "positioning": ("לעמוד במקום הנכון בהגנה.",
                    "סותם חורים לפני שהם נפתחים.",
                    "בלמים, מגנים, קשרים הגנתיים ושוערים."),
    "teamwork": ("לעשות את מה שהמערכת דורשת.",
                 "מאמנים אוהבים את זה, וזה נכנס לאמון שלהם בך.",
                 "כולם, ובעיקר בתפקידי תמיכה."),
    "vision": ("לראות את המסירה שאף אחד לא ראה.",
               "מעלה ישירות את מסירות המפתח שלך.",
               "בונים, עשרות, ובלמים שמוציאים."),
    "work_rate": ("כמה אתה עובד בלי כדור.",
                  "יותר ריצה ויותר לחיצה — הבסיס של כדורגל מודרני.",
                  "קשרי ריאות, חלוצים לוחצים, מגנים מתקדמים."),
    # --- פיזיות ---
    "acceleration": ("להגיע למהירות מלאה מעמידה.",
                     "חמישה המטרים הראשונים — ההבדל בין מצב לכלום.",
                     "כנפיים וחלוצים. חשובה יותר ממהירות שיא."),
    "agility": ("לשנות כיוון בלי לאבד שליטה.",
                "לעבור יריב במקום צר, ולהישאר על הרגליים.",
                "כדררנים, שוערים, ומגנים מול כנף מהירה."),
    "balance": ("לא ליפול ממגע.",
                "מחזיק אותך על הרגליים כשמושכים אותך.",
                "כדררנים וחלוצים שמחזיקים כדור."),
    "jumping_reach": ("כמה גבוה אתה מגיע.",
                      "קובע דו־קרבים באוויר, לא הגובה שלך.",
                      "בלמים, חלוצי מטרה, שוערים."),
    "natural_fitness": ("כמה מהר הגוף שלך חוזר לעצמו.",
                        "פחות פציעות, התאוששות מהירה יותר בין משחקים.",
                        "כולם. אצל ותיקים זה מאריך קריירה."),
    "pace": ("מהירות השיא שלך.",
             "עם סיבולת — כמה זמן תחזיק אותה.",
             "כנפיים, חלוצים ומגנים מתקדמים."),
    "stamina": ("להחזיק תשעים דקות באותה רמה.",
                "מונע את הקריסה בדקה 60 ואת הקנס בציון.",
                "כולם. קריטית בקבוצה שלוחצת."),
    "strength": ("להפעיל כוח על יריב ולנצח בו.",
                 "קובע ישירות את אחוז הדו־קרבים שלך.",
                 "חלוצי מטרה, בלמים, קשרים חוטפים."),
    # --- שוערים ---
    "aerial_reach": ("להגיע לכדורים גבוהים ברחבה.",
                     "קרנות והרמות שנגמרות בידיים שלך ולא בראש שלהם.",
                     "שוערים בלבד."),
    "command_of_area": ("לשלוט ברחבה ולארגן את ההגנה.",
                        "ההגנה עומדת נכון כי אתה צועק להם.",
                        "שוערים בלבד."),
    "communication": ("לדבר עם ההגנה תשעים דקות.",
                      "מונע בלבול בין הבלמים ברגעים הקשים.",
                      "שוערים בלבד."),
    "eccentricity": ("נטייה לעשות דברים לא צפויים.",
                     "לפעמים הצלה מדהימה, לפעמים שער מגוחך.",
                     "שוערים. ככל שנמוך יותר — כך בטוח יותר."),
    "handling": ("להחזיק את הכדור ולא לשחרר.",
                 "מונע ריבאונדים ושערים מרשלנות.",
                 "שוערים בלבד."),
    "kicking": ("לבעוט מהשער רחוק ומדויק.",
                "הופך הרחקה להתקפה.",
                "שוערים, במיוחד שוער־מנקה."),
    "one_on_ones": ("לעצור חלוץ שיצא לבד.",
                    "הרגע שבו שוער מרוויח את המשכורת שלו.",
                    "שוערים בלבד."),
    "reflexes": ("להגיב לבעיטה מטווח קצר.",
                 "התכונה המרכזית של כל שוער.",
                 "שוערים בלבד."),
    "rushing_out": ("לצאת מהשער בזמן הנכון.",
                    "חוסם כדורים לעומק לפני שהם הופכים למצב.",
                    "שוער־מנקה בקבוצה עם קו הגנה גבוה."),
    "tendency_to_punch": ("להעדיף אגרוף על תפיסה.",
                          "בטוח יותר בקהל, פחות שליטה על הכדור.",
                          "שוערים. עניין של סגנון, לא של איכות."),
    "throwing": ("לזרוק את הכדור מדויק ומהר.",
                 "פותח מעבר מהיר מיד אחרי הצלה.",
                 "שוערים בקבוצות שמשחקות מעברים."),
}

# הסבר לכל סוג אימון שאינו תכונה
FOCUS_INFO = {
    "rest": ("שבוע קליל.", "מחזיר רעננות ומקצר שיקום. החדות יורדת קצת.",
             "מי שנכנס למשחקים שרוף, או שחוזר מפציעה."),
    "badges": ("לימודי אימון.", "בונה ידע אימון ותעודות לקראת הקריירה שאחרי.",
               "ותיקים שחושבים על מה שיהיה בגיל 35."),
    "media": ("סדנת תקשורת.", "מעלה כריזמה — וזה מה שפותח חסויות ועבודות אולפן.",
              "מי שרוצה שהמותגים יתקשרו."),
    "business": ("לימודי ניהול.", "ראש עסקי — שימושי בניהול הכסף ובקריירה שאחרי.",
                 "מי שמתכנן לקנות מועדון יום אחד."),
    "school": ("בית ספר.", "מעלה קריאת משחק לאט, ומשאיר לך דלת פתוחה.",
               "נערים. ההורים יהיו מרוצים."),
    "street": ("כדורגל במגרש השכונתי.", "כדרור, בעיטה ומהירות — בלי מאמן ובלי חוקים.",
               "נערים שרוצים לפתח ברק, לא משמעת."),
}
