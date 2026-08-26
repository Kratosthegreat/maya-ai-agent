// נוצר אוטומטית מ-football_manager/data.py — אין לערוך ידנית.
// מריצים מחדש: python3 web/gen_data.py
const D = {
 "POSITIONS": [
  "GK",
  "CB",
  "LB",
  "RB",
  "DM",
  "CM",
  "AM",
  "LW",
  "RW",
  "ST"
 ],
 "POSITION_NAMES_HE": {
  "GK": "שוער",
  "CB": "בלם",
  "LB": "מגן שמאלי",
  "RB": "מגן ימני",
  "DM": "קשר הגנתי",
  "CM": "קשר מרכזי",
  "AM": "קשר התקפי",
  "LW": "כנף שמאלית",
  "RW": "כנף ימנית",
  "ST": "חלוץ"
 },
 "ATTRIBUTES": [
  "pace",
  "shooting",
  "passing",
  "dribbling",
  "defending",
  "physical",
  "mental"
 ],
 "ATTRIBUTE_NAMES_HE": {
  "pace": "מהירות",
  "shooting": "בעיטה",
  "passing": "מסירה",
  "dribbling": "כדרור",
  "defending": "הגנה",
  "physical": "כוח פיזי",
  "mental": "קריאת משחק"
 },
 "POSITION_WEIGHTS": {
  "GK": {
   "pace": 0.05,
   "shooting": 0.02,
   "passing": 0.1,
   "dribbling": 0.03,
   "defending": 0.45,
   "physical": 0.15,
   "mental": 0.2
  },
  "CB": {
   "pace": 0.1,
   "shooting": 0.03,
   "passing": 0.1,
   "dribbling": 0.05,
   "defending": 0.4,
   "physical": 0.2,
   "mental": 0.12
  },
  "LB": {
   "pace": 0.22,
   "shooting": 0.04,
   "passing": 0.15,
   "dribbling": 0.12,
   "defending": 0.27,
   "physical": 0.12,
   "mental": 0.08
  },
  "RB": {
   "pace": 0.22,
   "shooting": 0.04,
   "passing": 0.15,
   "dribbling": 0.12,
   "defending": 0.27,
   "physical": 0.12,
   "mental": 0.08
  },
  "DM": {
   "pace": 0.08,
   "shooting": 0.05,
   "passing": 0.22,
   "dribbling": 0.08,
   "defending": 0.28,
   "physical": 0.15,
   "mental": 0.14
  },
  "CM": {
   "pace": 0.1,
   "shooting": 0.1,
   "passing": 0.28,
   "dribbling": 0.15,
   "defending": 0.12,
   "physical": 0.1,
   "mental": 0.15
  },
  "AM": {
   "pace": 0.13,
   "shooting": 0.18,
   "passing": 0.25,
   "dribbling": 0.22,
   "defending": 0.03,
   "physical": 0.05,
   "mental": 0.14
  },
  "LW": {
   "pace": 0.25,
   "shooting": 0.16,
   "passing": 0.14,
   "dribbling": 0.28,
   "defending": 0.03,
   "physical": 0.05,
   "mental": 0.09
  },
  "RW": {
   "pace": 0.25,
   "shooting": 0.16,
   "passing": 0.14,
   "dribbling": 0.28,
   "defending": 0.03,
   "physical": 0.05,
   "mental": 0.09
  },
  "ST": {
   "pace": 0.2,
   "shooting": 0.34,
   "passing": 0.08,
   "dribbling": 0.15,
   "defending": 0.02,
   "physical": 0.13,
   "mental": 0.08
  }
 },
 "POSITION_ROLE_SHARE": {
  "GK": {
   "def": 1.0,
   "mid": 0.0,
   "att": 0.0
  },
  "CB": {
   "def": 0.9,
   "mid": 0.1,
   "att": 0.0
  },
  "LB": {
   "def": 0.65,
   "mid": 0.3,
   "att": 0.05
  },
  "RB": {
   "def": 0.65,
   "mid": 0.3,
   "att": 0.05
  },
  "DM": {
   "def": 0.45,
   "mid": 0.5,
   "att": 0.05
  },
  "CM": {
   "def": 0.2,
   "mid": 0.6,
   "att": 0.2
  },
  "AM": {
   "def": 0.05,
   "mid": 0.45,
   "att": 0.5
  },
  "LW": {
   "def": 0.05,
   "mid": 0.25,
   "att": 0.7
  },
  "RW": {
   "def": 0.05,
   "mid": 0.25,
   "att": 0.7
  },
  "ST": {
   "def": 0.0,
   "mid": 0.1,
   "att": 0.9
  }
 },
 "FORMATIONS": {
  "4-4-2": [
   "GK",
   "RB",
   "CB",
   "CB",
   "LB",
   "RW",
   "CM",
   "CM",
   "LW",
   "ST",
   "ST"
  ],
  "4-3-3": [
   "GK",
   "RB",
   "CB",
   "CB",
   "LB",
   "DM",
   "CM",
   "CM",
   "RW",
   "ST",
   "LW"
  ],
  "4-2-3-1": [
   "GK",
   "RB",
   "CB",
   "CB",
   "LB",
   "DM",
   "DM",
   "RW",
   "AM",
   "LW",
   "ST"
  ],
  "3-5-2": [
   "GK",
   "CB",
   "CB",
   "CB",
   "RB",
   "DM",
   "CM",
   "CM",
   "LB",
   "ST",
   "ST"
  ],
  "5-3-2": [
   "GK",
   "RB",
   "CB",
   "CB",
   "CB",
   "LB",
   "DM",
   "CM",
   "CM",
   "ST",
   "ST"
  ]
 },
 "LEAGUES": [
  {
   "id": "top",
   "name": "ליגת העל",
   "tier": 1,
   "country": "ישראל",
   "size": 20
  },
  {
   "id": "national",
   "name": "הליגה הלאומית",
   "tier": 2,
   "country": "ישראל",
   "size": 20
  },
  {
   "id": "euro",
   "name": "ליגת האלופות האירופית",
   "tier": 0,
   "country": "אירופה",
   "size": 16
  }
 ],
 "CLUBS": [
  [
   "maccabi_harel",
   "מכבי הראל",
   "הצהובים",
   "top",
   82,
   42.0
  ],
  [
   "hapoel_yam",
   "הפועל ים התיכון",
   "היַמָּאים",
   "top",
   78,
   34.0
  ],
  [
   "beitar_zion",
   "בית\"ר ציון",
   "השחורים־צהובים",
   "top",
   74,
   26.0
  ],
  [
   "bnei_negev",
   "בני הנגב",
   "בני המדבר",
   "top",
   71,
   21.0
  ],
  [
   "maccabi_sharon",
   "מכבי השרון",
   "הירוקים",
   "top",
   69,
   18.5
  ],
  [
   "hapoel_carmel",
   "הפועל הכרמל",
   "האריות",
   "top",
   67,
   16.0
  ],
  [
   "ironi_moriah",
   "עירוני מוריה",
   "אנשי ההר",
   "top",
   65,
   14.5
  ],
  [
   "maccabi_yarden",
   "מכבי ירדן",
   "הנהר",
   "top",
   63,
   13.0
  ],
  [
   "hapoel_ayalon",
   "הפועל איילון",
   "הפועלים",
   "top",
   61,
   11.5
  ],
  [
   "ironi_galil",
   "עירוני גליל עליון",
   "ההרים",
   "top",
   59,
   10.5
  ],
  [
   "shimshon_ashdod",
   "שמשון אשדוד",
   "אנשי החוף",
   "top",
   57,
   9.5
  ],
  [
   "maccabi_lachish",
   "מכבי לכיש",
   "השדות",
   "top",
   55,
   8.5
  ],
  [
   "hapoel_shfela",
   "הפועל השפלה",
   "העמק",
   "top",
   53,
   7.5
  ],
  [
   "ironi_kinneret",
   "עירוני כנרת",
   "הגלים",
   "top",
   51,
   7.0
  ],
  [
   "hakoah_arava",
   "הכוח ערבה",
   "הסופה",
   "top",
   49,
   6.2
  ],
  [
   "bnei_tavor",
   "בני תבור",
   "הפסגה",
   "top",
   47,
   5.6
  ],
  [
   "maccabi_ofek",
   "מכבי אופק",
   "האופק",
   "top",
   45,
   5.0
  ],
  [
   "hapoel_zvulun",
   "הפועל זבולון",
   "העוגן",
   "top",
   43,
   4.4
  ],
  [
   "ironi_shomron",
   "עירוני שומרון",
   "הגבעות",
   "top",
   41,
   4.0
  ],
  [
   "shimshon_dan",
   "שמשון דן",
   "הגוש",
   "top",
   39,
   3.6
  ],
  [
   "maccabi_modiin",
   "מכבי מודיעין",
   "המכבים",
   "national",
   38,
   3.4
  ],
  [
   "hapoel_ramla",
   "הפועל רמלה",
   "הצריחים",
   "national",
   37,
   3.2
  ],
  [
   "bnei_hasharon",
   "בני השרון",
   "התפוזים",
   "national",
   36,
   3.0
  ],
  [
   "ironi_besor",
   "עירוני הבשור",
   "הנחל",
   "national",
   35,
   2.8
  ],
  [
   "maccabi_arad",
   "מכבי ערד",
   "המצוק",
   "national",
   34,
   2.6
  ],
  [
   "hapoel_negba",
   "הפועל נגבה",
   "החומה",
   "national",
   33,
   2.4
  ],
  [
   "ironi_hermon",
   "עירוני חרמון",
   "השלג",
   "national",
   32,
   2.3
  ],
  [
   "maccabi_ofakim",
   "מכבי אופקים",
   "המדבר",
   "national",
   31,
   2.2
  ],
  [
   "bnei_gilboa",
   "בני גלבוע",
   "הרכס",
   "national",
   30,
   2.0
  ],
  [
   "hapoel_alexander",
   "הפועל נחל אלכסנדר",
   "הזרם",
   "national",
   29,
   1.9
  ],
  [
   "ironi_masada",
   "עירוני מצדה",
   "המצודה",
   "national",
   28,
   1.8
  ],
  [
   "maccabi_eshkol",
   "מכבי אשכול",
   "הכרמים",
   "national",
   27,
   1.7
  ],
  [
   "hapoel_hula",
   "הפועל החולה",
   "האגם",
   "national",
   26,
   1.6
  ],
  [
   "bnei_ela",
   "בני האלה",
   "העמק",
   "national",
   25,
   1.5
  ],
  [
   "ironi_ramon",
   "עירוני רמון",
   "המכתש",
   "national",
   24,
   1.4
  ],
  [
   "maccabi_yehuda",
   "מכבי הרי יהודה",
   "ההרים",
   "national",
   23,
   1.3
  ],
  [
   "hapoel_taninim",
   "הפועל תנינים",
   "הנחל",
   "national",
   22,
   1.2
  ],
  [
   "bnei_zin",
   "בני צין",
   "הערבה",
   "national",
   21,
   1.1
  ],
  [
   "ironi_habsor",
   "עירוני הבשור ב'",
   "הגדה",
   "national",
   20,
   1.0
  ],
  [
   "maccabi_shikma",
   "מכבי שקמה",
   "העצים",
   "national",
   19,
   0.9
  ],
  [
   "real_castilla",
   "ריאל קסטיליה",
   "המלכותיים",
   "euro",
   94,
   260.0
  ],
  [
   "olympia_munchen",
   "אולימפיה מינכן",
   "הבווארים",
   "euro",
   93,
   240.0
  ],
  [
   "thames_united",
   "תמז יונייטד",
   "השדים",
   "euro",
   91,
   230.0
  ],
  [
   "paris_luxe",
   "פארי לוקס",
   "הבירה",
   "euro",
   90,
   220.0
  ],
  [
   "inter_lazio",
   "אינטר לאציו",
   "הנחשים",
   "euro",
   88,
   190.0
  ],
  [
   "catalunya_fc",
   "קטלוניה",
   "הבלאוגרנה",
   "euro",
   89,
   200.0
  ],
  [
   "mersey_athletic",
   "מרסי אתלטיק",
   "האדומים",
   "euro",
   87,
   185.0
  ],
  [
   "saxon_dortmund",
   "סקסון דורטמונד",
   "הצהוב־שחור",
   "euro",
   84,
   150.0
  ],
  [
   "ajax_noord",
   "אייאקס נורד",
   "בית הספר",
   "euro",
   82,
   120.0
  ],
  [
   "porto_atlantico",
   "פורטו אטלנטיקו",
   "הדרקונים",
   "euro",
   80,
   100.0
  ],
  [
   "galata_bosphorus",
   "גלאטה בוספורוס",
   "האריות",
   "euro",
   79,
   95.0
  ],
  [
   "milano_nord",
   "מילאנו נורד",
   "הרוסונרי",
   "euro",
   85,
   165.0
  ],
  [
   "albion_north",
   "אלביון נורת'",
   "הפועלים",
   "euro",
   83,
   140.0
  ],
  [
   "sevilla_sur",
   "סביליה סור",
   "האדומים־לבנים",
   "euro",
   78,
   88.0
  ],
  [
   "wien_donau",
   "וינה דונאו",
   "הסגולים",
   "euro",
   74,
   62.0
  ],
  [
   "brugge_west",
   "ברוז' ווסט",
   "הכחולים",
   "euro",
   72,
   55.0
  ]
 ],
 "FIRST_NAMES": [
  "איתי",
  "עומר",
  "יובל",
  "נועם",
  "אורי",
  "רועי",
  "דור",
  "גיא",
  "אלון",
  "עידו",
  "שגיא",
  "ליאור",
  "עמית",
  "בר",
  "ניר",
  "טל",
  "אסף",
  "עדן",
  "מתן",
  "יונתן",
  "אריאל",
  "שחר",
  "רון",
  "נדב",
  "איל",
  "עומרי",
  "יהב",
  "אביב",
  "חן",
  "ספיר",
  "מרקו",
  "לוקאס",
  "דייגו",
  "אנזו",
  "רפאל",
  "בילאל",
  "אמארה",
  "יוסוף",
  "טיאגו",
  "פאבלו"
 ],
 "LAST_NAMES": [
  "כהן",
  "לוי",
  "מזרחי",
  "פרץ",
  "ביטון",
  "דהן",
  "אברהם",
  "פרידמן",
  "שרון",
  "אזולאי",
  "בן־חיים",
  "גולן",
  "אשכנזי",
  "טוויטו",
  "זהבי",
  "רפאלוב",
  "חמד",
  "מלמד",
  "סבן",
  "אוחיון",
  "סילבה",
  "מנדס",
  "קוסטה",
  "פרננדס",
  "מולר",
  "יאנסן",
  "נובאק",
  "פטרוב",
  "אוקונקוו",
  "דיאלו"
 ],
 "NATIONALITIES": [
  [
   "ישראל",
   0.62
  ],
  [
   "ברזיל",
   0.06
  ],
  [
   "ניגריה",
   0.05
  ],
  [
   "צרפת",
   0.04
  ],
  [
   "ספרד",
   0.04
  ],
  [
   "סרביה",
   0.04
  ],
  [
   "ארגנטינה",
   0.03
  ],
  [
   "פורטוגל",
   0.03
  ],
  [
   "גאנה",
   0.03
  ],
  [
   "קרואטיה",
   0.03
  ],
  [
   "הולנד",
   0.03
  ]
 ],
 "MANAGER_NAMES": [
  "ז'וזה ריברו",
  "אריק לוינסון",
  "פאולו מנדס",
  "יאן דה־בור",
  "משה אלגרבלי",
  "רוברטו סנטיני",
  "דייויד קלארק",
  "אמיר בן־שושן",
  "טומאס נובאק",
  "ניקולא פטרוביץ'",
  "שלומי דגן",
  "פרנק אוליביירה",
  "מרקוס שטיין",
  "עידן ברקוביץ'",
  "קרלוס אלמדה"
 ],
 "TRAITS": {
  "leader": {
   "name": "מנהיג טבעי",
   "desc": "מרים את הקבוצה ברגעים קשים."
  },
  "hothead": {
   "name": "חם מזג",
   "desc": "מקבל כרטיסים, אבל משחק עם אש."
  },
  "workhorse": {
   "name": "סוס עבודה",
   "desc": "מתאמן יותר מכולם ומתפתח מהר."
  },
  "glass": {
   "name": "שביר",
   "desc": "נוטה להיפצע."
  },
  "clutch": {
   "name": "שחקן של רגעים",
   "desc": "זורח במשחקים גדולים."
  },
  "loyal": {
   "name": "נאמן",
   "desc": "האוהדים מעריצים אותו, קשה לו לעזוב."
  },
  "media_darling": {
   "name": "חביב התקשורת",
   "desc": "יודע לדבר למצלמות."
  },
  "student": {
   "name": "תלמיד של המשחק",
   "desc": "לומד אימון מהר יותר."
  }
 },
 "CAREER_STAGES_HE": {
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
  "legend": "אגדה"
 },
 "TRAINING_FOCUS_HE": {
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
  "street": "כדורגל במגרש השכונתי"
 },
 "STADIUM_WORDS": [
  "האצטדיון העירוני",
  "היכל",
  "אצטדיון",
  "פארק",
  "הזירה"
 ],
 "STADIUM_SUFFIX": [
  "הצפון",
  "הדרום",
  "העמק",
  "החוף",
  "הגבעה",
  "המושבה",
  "הנמל",
  "הכרמל",
  "השפלה",
  "המדבר",
  "הבירה",
  "הגליל"
 ],
 "TICKET_BASE": {
  "0": 140,
  "1": 78,
  "2": 46,
  "3": 28
 },
 "FACILITIES": {
  "training": {
   "field": "trainingFacilities",
   "name": "מתקני אימון",
   "effect": "קצב ההתפתחות של כל שחקני הסגל, כולל שלך.",
   "unit": 9.0,
   "weeks": 6,
   "cost": 7000000
  },
  "youth": {
   "field": "youthAcademy",
   "name": "מחלקת נוער",
   "effect": "איכות השחקנים שעולים מהנוער ורמת היריבים בשנות הנוער.",
   "unit": 8.0,
   "weeks": 8,
   "cost": 5500000
  },
  "medical": {
   "field": "medicalCentre",
   "name": "מרכז רפואי",
   "effect": "משך הפציעות בסגל — מרכז טוב מקצר שיקום.",
   "unit": 10.0,
   "weeks": 5,
   "cost": 4500000
  },
  "stadium": {
   "field": "capacity",
   "name": "הרחבת האצטדיון",
   "effect": "כמה כרטיסים אפשר למכור במשחק בית.",
   "unit": 0.18,
   "weeks": 20,
   "cost": 7500000
  }
 },
 "STAFF_ROLES": {
  "assistant": {
   "name": "עוזר מאמן",
   "effect": "מוסיף לקצב האימון של כל הסגל.",
   "wagePerPoint": 62
  },
  "fitness": {
   "name": "מאמן כושר",
   "effect": "התאוששות מהירה יותר, ופחות פציעות מעומס אימון.",
   "wagePerPoint": 48
  },
  "physio": {
   "name": "פיזיותרפיסט",
   "effect": "מקצר את משך הפציעות.",
   "wagePerPoint": 44
  },
  "scout": {
   "name": "ראש סקאוטינג",
   "effect": "משפר את איכות השחקנים שעולים מהנוער.",
   "wagePerPoint": 40
  },
  "analyst": {
   "name": "אנליסט",
   "effect": "יתרון טקטי קטן בכל משחק.",
   "wagePerPoint": 52
  }
 },
 "STAFF_NAMES": [
  "רון אלקיים",
  "ז'אן פוליה",
  "דניאל אשכנזי",
  "מירי שגב",
  "אנדראס קלוזה",
  "יוסי דהן",
  "לורה בנקס",
  "פבלו אורטגה",
  "נועם ברזילי",
  "טל אבידן",
  "סרחיו מולינה",
  "אורית כהן",
  "מרקו יאנסן",
  "עדי פרץ",
  "חנא סרוג'י",
  "דין מקנזי",
  "רותם לביא",
  "אלכס דוברוב",
  "שרון מזרחי",
  "פייר לובלן"
 ],
 "PHYSIQUE": {
  "GK": [
   189,
   4.5
  ],
  "CB": [
   187,
   4.5
  ],
  "LB": [
   178,
   4.0
  ],
  "RB": [
   178,
   4.0
  ],
  "DM": [
   183,
   5.0
  ],
  "CM": [
   179,
   5.0
  ],
  "AM": [
   176,
   5.0
  ],
  "LW": [
   175,
   5.0
  ],
  "RW": [
   175,
   5.0
  ],
  "ST": [
   183,
   6.0
  ]
 },
 "BMI_RANGE": [
  21.8,
  24.2
 ],
 "TRAINING_SPILL": {
  "pace": [
   "physical",
   "dribbling"
  ],
  "shooting": [
   "dribbling",
   "mental"
  ],
  "passing": [
   "mental",
   "dribbling"
  ],
  "dribbling": [
   "pace",
   "passing"
  ],
  "defending": [
   "mental",
   "physical"
  ],
  "physical": [
   "pace",
   "defending"
  ],
  "mental": [
   "passing",
   "defending"
  ]
 },
 "SPILL_SHARE": 0.3,
 "GENERAL_SHARE": 0.15,
 "SPONSOR_TIERS": [
  [
   "local",
   "מקומי",
   12,
   22000,
   0.4,
   [
    "מוסך אלוני",
    "פלאפל הבורסה",
    "רהיטי בן־ארי",
    "חדר כושר אולימפוס",
    "סופרמרקט השכונה",
    "מכללת הנגב"
   ]
  ],
  [
   "national",
   "ארצי",
   34,
   105000,
   0.8,
   [
    "בנק הראשון",
    "סלקום ספורט",
    "שופרסל",
    "אלקטרה",
    "טמפו",
    "יס פלוס"
   ]
  ],
  [
   "continental",
   "יבשתי",
   58,
   450000,
   1.1,
   [
    "אאודי אירופה",
    "לופטהנזה",
    "סנטנדר",
    "אמסטל",
    "בוקינג"
   ]
  ],
  [
   "global",
   "עולמי",
   76,
   1600000,
   1.5,
   [
    "נייקי",
    "אדידס",
    "פומה",
    "רד בול",
    "ג'ילט",
    "רולקס",
    "אמירייטס"
   ]
  ]
 ],
 "DEAL_KINDS": {
  "boots": {
   "name": "חוזה נעליים",
   "pay": 1.0,
   "media": 3,
   "days": 2
  },
  "apparel": {
   "name": "חוזה ביגוד",
   "pay": 1.25,
   "media": 5,
   "days": 3
  },
  "drink": {
   "name": "משקה אנרגיה",
   "pay": 0.85,
   "media": 4,
   "days": 2
  },
  "bank": {
   "name": "קמפיין בנק",
   "pay": 1.4,
   "media": 7,
   "days": 4
  },
  "car": {
   "name": "יבואן רכב",
   "pay": 1.15,
   "media": 5,
   "days": 3
  },
  "watch": {
   "name": "מותג שעונים",
   "pay": 1.6,
   "media": 6,
   "days": 2
  }
 },
 "MEDIA_JOBS": [
  [
   "column",
   "טור שבועי בעיתון ספורט",
   22,
   30,
   45000
  ],
  [
   "panel",
   "פאנל אולפן אחרי משחקים",
   40,
   45,
   120000
  ],
  [
   "doc",
   "סרט תיעודי על העונה שלך",
   55,
   55,
   340000
  ],
  [
   "boot_launch",
   "השקה בינלאומית של דגם נעל",
   70,
   70,
   900000
  ]
 ],
 "AGENT_NAMES": [
  "ז'ורז' מנדוזה",
  "רפי אלמוג",
  "סימונה בלאנקו",
  "טוני קרסטיץ'",
  "עידו שרעבי",
  "מארק דיוויס",
  "לואיז פררה",
  "יוסי בן־דוד"
 ],
 "CLUB_COUNTRY": {
  "real_castilla": "ספרד",
  "catalunya_fc": "ספרד",
  "sevilla_sur": "ספרד",
  "olympia_munchen": "גרמניה",
  "saxon_dortmund": "גרמניה",
  "thames_united": "אנגליה",
  "mersey_athletic": "אנגליה",
  "albion_north": "אנגליה",
  "paris_luxe": "צרפת",
  "inter_lazio": "איטליה",
  "milano_nord": "איטליה",
  "ajax_noord": "הולנד",
  "brugge_west": "בלגיה",
  "porto_atlantico": "פורטוגל",
  "galata_bosphorus": "טורקיה",
  "wien_donau": "אוסטריה"
 },
 "STAT_LINES": [
  [
   "shots",
   "בעיטות",
   true,
   "shooting"
  ],
  [
   "on_target",
   "בעיטות למסגרת",
   true,
   "shooting"
  ],
  [
   "key_passes",
   "מסירות מפתח",
   true,
   "passing"
  ],
  [
   "pass_pct",
   "אחוז מסירה",
   true,
   "passing"
  ],
  [
   "dribbles",
   "כדרורים שהצליחו",
   true,
   "dribbling"
  ],
  [
   "duels_pct",
   "אחוז דו־קרב",
   true,
   "physical"
  ],
  [
   "tackles",
   "חטיפות",
   true,
   "defending"
  ],
  [
   "losses",
   "איבודי כדור",
   false,
   "passing"
  ],
  [
   "sprints",
   "ספרינטים",
   true,
   "pace"
  ],
  [
   "distance",
   "ק\"מ ריצה",
   true,
   "physical"
  ],
  [
   "reads",
   "קריאות נכונות",
   true,
   "mental"
  ]
 ],
 "STAT_LABELS": {
  "shots": "בעיטות",
  "on_target": "בעיטות למסגרת",
  "key_passes": "מסירות מפתח",
  "pass_pct": "אחוז מסירה",
  "dribbles": "כדרורים שהצליחו",
  "duels_pct": "אחוז דו־קרב",
  "tackles": "חטיפות",
  "losses": "איבודי כדור",
  "sprints": "ספרינטים",
  "distance": "ק\"מ ריצה",
  "reads": "קריאות נכונות"
 },
 "DIRECTIVE_REASON": {
  "shooting": [
   "בעטת {shots} פעמים ורק {on_target} הלכו למסגרת.",
   "אם הסיומות ישתפרו, המצבים שאתה כבר מייצר יהפכו לשערים."
  ],
  "passing": [
   "איבדת {losses} כדורים ואחוז המסירה שלך היה {pass_pct}%.",
   "פחות איבודים זה יותר זמן עם הכדור — וקו הקישור יזרום דרכך."
  ],
  "dribbling": [
   "ניסית לעבור אחד על אחד ויצאת מזה {dribbles} פעמים בלבד.",
   "כדרור טוב יותר יפתח לך מסירות מפתח שהיום לא קיימות."
  ],
  "defending": [
   "חטפת {tackles} כדורים. בעמדה שלך זה מעט.",
   "עבודה הגנתית תקנה לך דקות גם במשחקים שאתה לא זורח בהם."
  ],
  "physical": [
   "הפסדת את רוב הדו־קרבים — {duels_pct}% בלבד.",
   "גוף חזק יותר גם שובר פחות: פחות פציעות, יותר דקות."
  ],
  "pace": [
   "{sprints} ספרינטים. בכל פעם שהיה צריך להגיע ראשון, לא הגעת.",
   "חמישה המטרים הראשונים הם ההבדל בין מצב לבין כלום."
  ],
  "mental": [
   "היית במקום הלא נכון יותר מדי פעמים — {reads} קריאות נכונות.",
   "קריאת משחק טובה חוסכת לך ריצות ומכניסה אותך למצבים."
  ],
  "rest": [
   "נכנסת למשחק על {fitness}% כושר, ובדקה 60 זה נראה.",
   "שבוע קליל עכשיו מחזיר אותך שלם למשחק הבא."
  ]
 },
 "MILESTONE_REWARD": {
  "potential": 2.2,
  "rep": 1.6,
  "morale": 8,
  "trust": 5
 },
 "TECHNICAL": [
  [
   "corners",
   "קרנות"
  ],
  [
   "crossing",
   "הרמות"
  ],
  [
   "dribbling",
   "כדרור"
  ],
  [
   "finishing",
   "סיום"
  ],
  [
   "first_touch",
   "נגיעה ראשונה"
  ],
  [
   "free_kick",
   "בעיטות חופשיות"
  ],
  [
   "heading",
   "נגיחות"
  ],
  [
   "long_shots",
   "בעיטות מרחוק"
  ],
  [
   "long_throws",
   "זריקות ארוכות"
  ],
  [
   "marking",
   "צמידות"
  ],
  [
   "passing",
   "מסירה"
  ],
  [
   "penalty_taking",
   "פנדלים"
  ],
  [
   "tackling",
   "חטיפה"
  ],
  [
   "technique",
   "טכניקה"
  ]
 ],
 "MENTAL": [
  [
   "aggression",
   "אגרסיביות"
  ],
  [
   "anticipation",
   "חיזוי"
  ],
  [
   "bravery",
   "אומץ"
  ],
  [
   "composure",
   "קור רוח"
  ],
  [
   "concentration",
   "ריכוז"
  ],
  [
   "decisions",
   "קבלת החלטות"
  ],
  [
   "determination",
   "נחישות"
  ],
  [
   "flair",
   "ברק"
  ],
  [
   "leadership",
   "מנהיגות"
  ],
  [
   "off_the_ball",
   "תנועה בלי כדור"
  ],
  [
   "positioning",
   "מיקום"
  ],
  [
   "teamwork",
   "עבודת צוות"
  ],
  [
   "vision",
   "ראיית משחק"
  ],
  [
   "work_rate",
   "קצב עבודה"
  ]
 ],
 "PHYSICAL": [
  [
   "acceleration",
   "האצה"
  ],
  [
   "agility",
   "זריזות"
  ],
  [
   "balance",
   "שיווי משקל"
  ],
  [
   "jumping_reach",
   "קפיצה"
  ],
  [
   "natural_fitness",
   "כושר טבעי"
  ],
  [
   "pace",
   "מהירות"
  ],
  [
   "stamina",
   "סיבולת"
  ],
  [
   "strength",
   "כוח"
  ]
 ],
 "GOALKEEPING": [
  [
   "aerial_reach",
   "הגעה באוויר"
  ],
  [
   "command_of_area",
   "שליטה ברחבה"
  ],
  [
   "communication",
   "תקשורת"
  ],
  [
   "eccentricity",
   "אקסצנטריות"
  ],
  [
   "handling",
   "אחיזה"
  ],
  [
   "kicking",
   "בעיטה"
  ],
  [
   "one_on_ones",
   "אחד על אחד"
  ],
  [
   "reflexes",
   "רפלקסים"
  ],
  [
   "rushing_out",
   "יציאה מהשער"
  ],
  [
   "tendency_to_punch",
   "נטייה לאגרוף"
  ],
  [
   "throwing",
   "זריקה"
  ]
 ],
 "ATTR_GROUPS": [
  [
   "technical",
   "טכניות",
   [
    [
     "corners",
     "קרנות"
    ],
    [
     "crossing",
     "הרמות"
    ],
    [
     "dribbling",
     "כדרור"
    ],
    [
     "finishing",
     "סיום"
    ],
    [
     "first_touch",
     "נגיעה ראשונה"
    ],
    [
     "free_kick",
     "בעיטות חופשיות"
    ],
    [
     "heading",
     "נגיחות"
    ],
    [
     "long_shots",
     "בעיטות מרחוק"
    ],
    [
     "long_throws",
     "זריקות ארוכות"
    ],
    [
     "marking",
     "צמידות"
    ],
    [
     "passing",
     "מסירה"
    ],
    [
     "penalty_taking",
     "פנדלים"
    ],
    [
     "tackling",
     "חטיפה"
    ],
    [
     "technique",
     "טכניקה"
    ]
   ]
  ],
  [
   "mental",
   "מנטליות",
   [
    [
     "aggression",
     "אגרסיביות"
    ],
    [
     "anticipation",
     "חיזוי"
    ],
    [
     "bravery",
     "אומץ"
    ],
    [
     "composure",
     "קור רוח"
    ],
    [
     "concentration",
     "ריכוז"
    ],
    [
     "decisions",
     "קבלת החלטות"
    ],
    [
     "determination",
     "נחישות"
    ],
    [
     "flair",
     "ברק"
    ],
    [
     "leadership",
     "מנהיגות"
    ],
    [
     "off_the_ball",
     "תנועה בלי כדור"
    ],
    [
     "positioning",
     "מיקום"
    ],
    [
     "teamwork",
     "עבודת צוות"
    ],
    [
     "vision",
     "ראיית משחק"
    ],
    [
     "work_rate",
     "קצב עבודה"
    ]
   ]
  ],
  [
   "physical",
   "פיזיות",
   [
    [
     "acceleration",
     "האצה"
    ],
    [
     "agility",
     "זריזות"
    ],
    [
     "balance",
     "שיווי משקל"
    ],
    [
     "jumping_reach",
     "קפיצה"
    ],
    [
     "natural_fitness",
     "כושר טבעי"
    ],
    [
     "pace",
     "מהירות"
    ],
    [
     "stamina",
     "סיבולת"
    ],
    [
     "strength",
     "כוח"
    ]
   ]
  ],
  [
   "goalkeeping",
   "שוערים",
   [
    [
     "aerial_reach",
     "הגעה באוויר"
    ],
    [
     "command_of_area",
     "שליטה ברחבה"
    ],
    [
     "communication",
     "תקשורת"
    ],
    [
     "eccentricity",
     "אקסצנטריות"
    ],
    [
     "handling",
     "אחיזה"
    ],
    [
     "kicking",
     "בעיטה"
    ],
    [
     "one_on_ones",
     "אחד על אחד"
    ],
    [
     "reflexes",
     "רפלקסים"
    ],
    [
     "rushing_out",
     "יציאה מהשער"
    ],
    [
     "tendency_to_punch",
     "נטייה לאגרוף"
    ],
    [
     "throwing",
     "זריקה"
    ]
   ]
  ]
 ],
 "DETAIL_NAMES_HE": {
  "corners": "קרנות",
  "crossing": "הרמות",
  "dribbling": "כדרור",
  "finishing": "סיום",
  "first_touch": "נגיעה ראשונה",
  "free_kick": "בעיטות חופשיות",
  "heading": "נגיחות",
  "long_shots": "בעיטות מרחוק",
  "long_throws": "זריקות ארוכות",
  "marking": "צמידות",
  "passing": "מסירה",
  "penalty_taking": "פנדלים",
  "tackling": "חטיפה",
  "technique": "טכניקה",
  "aggression": "אגרסיביות",
  "anticipation": "חיזוי",
  "bravery": "אומץ",
  "composure": "קור רוח",
  "concentration": "ריכוז",
  "decisions": "קבלת החלטות",
  "determination": "נחישות",
  "flair": "ברק",
  "leadership": "מנהיגות",
  "off_the_ball": "תנועה בלי כדור",
  "positioning": "מיקום",
  "teamwork": "עבודת צוות",
  "vision": "ראיית משחק",
  "work_rate": "קצב עבודה",
  "acceleration": "האצה",
  "agility": "זריזות",
  "balance": "שיווי משקל",
  "jumping_reach": "קפיצה",
  "natural_fitness": "כושר טבעי",
  "pace": "מהירות",
  "stamina": "סיבולת",
  "strength": "כוח",
  "aerial_reach": "הגעה באוויר",
  "command_of_area": "שליטה ברחבה",
  "communication": "תקשורת",
  "eccentricity": "אקסצנטריות",
  "handling": "אחיזה",
  "kicking": "בעיטה",
  "one_on_ones": "אחד על אחד",
  "reflexes": "רפלקסים",
  "rushing_out": "יציאה מהשער",
  "tendency_to_punch": "נטייה לאגרוף",
  "throwing": "זריקה"
 },
 "DETAIL_GROUP": {
  "corners": "technical",
  "crossing": "technical",
  "dribbling": "technical",
  "finishing": "technical",
  "first_touch": "technical",
  "free_kick": "technical",
  "heading": "technical",
  "long_shots": "technical",
  "long_throws": "technical",
  "marking": "technical",
  "passing": "technical",
  "penalty_taking": "technical",
  "tackling": "technical",
  "technique": "technical",
  "aggression": "mental",
  "anticipation": "mental",
  "bravery": "mental",
  "composure": "mental",
  "concentration": "mental",
  "decisions": "mental",
  "determination": "mental",
  "flair": "mental",
  "leadership": "mental",
  "off_the_ball": "mental",
  "positioning": "mental",
  "teamwork": "mental",
  "vision": "mental",
  "work_rate": "mental",
  "acceleration": "physical",
  "agility": "physical",
  "balance": "physical",
  "jumping_reach": "physical",
  "natural_fitness": "physical",
  "pace": "physical",
  "stamina": "physical",
  "strength": "physical",
  "aerial_reach": "goalkeeping",
  "command_of_area": "goalkeeping",
  "communication": "goalkeeping",
  "eccentricity": "goalkeeping",
  "handling": "goalkeeping",
  "kicking": "goalkeeping",
  "one_on_ones": "goalkeeping",
  "reflexes": "goalkeeping",
  "rushing_out": "goalkeeping",
  "tendency_to_punch": "goalkeeping",
  "throwing": "goalkeeping"
 },
 "OUTFIELD_ATTRS": [
  "corners",
  "crossing",
  "dribbling",
  "finishing",
  "first_touch",
  "free_kick",
  "heading",
  "long_shots",
  "long_throws",
  "marking",
  "passing",
  "penalty_taking",
  "tackling",
  "technique",
  "aggression",
  "anticipation",
  "bravery",
  "composure",
  "concentration",
  "decisions",
  "determination",
  "flair",
  "leadership",
  "off_the_ball",
  "positioning",
  "teamwork",
  "vision",
  "work_rate",
  "acceleration",
  "agility",
  "balance",
  "jumping_reach",
  "natural_fitness",
  "pace",
  "stamina",
  "strength"
 ],
 "KEEPER_ATTRS": [
  "aerial_reach",
  "command_of_area",
  "communication",
  "eccentricity",
  "handling",
  "kicking",
  "one_on_ones",
  "reflexes",
  "rushing_out",
  "tendency_to_punch",
  "throwing",
  "aggression",
  "anticipation",
  "bravery",
  "composure",
  "concentration",
  "decisions",
  "determination",
  "flair",
  "leadership",
  "off_the_ball",
  "positioning",
  "teamwork",
  "vision",
  "work_rate",
  "acceleration",
  "agility",
  "balance",
  "jumping_reach",
  "natural_fitness",
  "pace",
  "stamina",
  "strength",
  "first_touch",
  "passing",
  "technique"
 ],
 "GROUP_MAP": {
  "pace": {
   "acceleration": 1.0,
   "pace": 1.0,
   "agility": 0.45,
   "balance": 0.3
  },
  "shooting": {
   "finishing": 1.0,
   "long_shots": 0.55,
   "technique": 0.45,
   "composure": 0.45,
   "heading": 0.3
  },
  "passing": {
   "passing": 1.0,
   "vision": 0.7,
   "technique": 0.45,
   "first_touch": 0.4,
   "crossing": 0.3
  },
  "dribbling": {
   "dribbling": 1.0,
   "first_touch": 0.5,
   "agility": 0.45,
   "flair": 0.4,
   "balance": 0.3,
   "technique": 0.35
  },
  "defending": {
   "tackling": 1.0,
   "marking": 0.95,
   "positioning": 0.7,
   "anticipation": 0.45,
   "concentration": 0.35,
   "aggression": 0.2
  },
  "physical": {
   "strength": 1.0,
   "stamina": 0.8,
   "jumping_reach": 0.55,
   "natural_fitness": 0.45,
   "work_rate": 0.55,
   "bravery": 0.3
  },
  "mental": {
   "decisions": 1.0,
   "anticipation": 0.7,
   "off_the_ball": 0.6,
   "teamwork": 0.55,
   "concentration": 0.55,
   "composure": 0.5,
   "vision": 0.45,
   "determination": 0.4,
   "positioning": 0.35
  }
 },
 "GROUP_MAP_GK": {
  "pace": {
   "acceleration": 1.0,
   "agility": 0.8,
   "pace": 0.55
  },
  "shooting": {
   "kicking": 1.0,
   "technique": 0.45,
   "throwing": 0.35
  },
  "passing": {
   "kicking": 1.0,
   "passing": 0.7,
   "vision": 0.55,
   "throwing": 0.45
  },
  "dribbling": {
   "first_touch": 1.0,
   "technique": 0.65,
   "rushing_out": 0.45,
   "composure": 0.4
  },
  "defending": {
   "reflexes": 1.0,
   "handling": 0.95,
   "one_on_ones": 0.75,
   "positioning": 0.7,
   "command_of_area": 0.6,
   "aerial_reach": 0.55
  },
  "physical": {
   "strength": 1.0,
   "jumping_reach": 0.85,
   "natural_fitness": 0.55,
   "agility": 0.55,
   "stamina": 0.3
  },
  "mental": {
   "decisions": 1.0,
   "concentration": 0.85,
   "communication": 0.65,
   "anticipation": 0.6,
   "composure": 0.55
  }
 },
 "HIDDEN_ATTRS": [
  [
   "ambition",
   "שאפתנות"
  ],
  [
   "loyalty",
   "נאמנות"
  ],
  [
   "pressure",
   "עמידות בלחץ"
  ],
  [
   "professionalism",
   "מקצוענות"
  ],
  [
   "sportsmanship",
   "רוח ספורטיבית"
  ],
  [
   "temperament",
   "מזג"
  ],
  [
   "controversy",
   "נטייה לסערות"
  ]
 ],
 "PERSONALITIES": [
  [
   "model_citizen",
   "אזרח מופת",
   "מקצוען עד הסוף, בלי רעש, ומרים את כל מי שסביבו.",
   {
    "professionalism": 18,
    "determination": 15,
    "sportsmanship": 15,
    "temperament": 15
   }
  ],
  [
   "model_professional",
   "מקצוען מודל",
   "ראשון באימון, אחרון בחדר הכושר. מתפתח מהר יותר מכולם.",
   {
    "professionalism": 18,
    "determination": 15,
    "ambition": 12
   }
  ],
  [
   "perfectionist",
   "פרפקציוניסט",
   "לא מרוצה גם אחרי שער. זה מה שדוחף אותו, וזה גם מה ששוחק אותו.",
   {
    "professionalism": 17,
    "determination": 18,
    "ambition": 17
   }
  ],
  [
   "resolute",
   "נחוש",
   "לא נשבר. משחקים גדולים הם המקום שלו.",
   {
    "determination": 18,
    "pressure": 15
   }
  ],
  [
   "driven",
   "מונע מבפנים",
   "רוצה להגיע רחוק, ומוכן לשלם על זה.",
   {
    "ambition": 17,
    "determination": 14,
    "professionalism": 12
   }
  ],
  [
   "professional",
   "מקצוען",
   "עושה את העבודה, בלי דרמות.",
   {
    "professionalism": 15,
    "determination": 12
   }
  ],
  [
   "fairly_professional",
   "מקצוען למדי",
   "לרוב עושה את הדבר הנכון.",
   {
    "professionalism": 12,
    "determination": 10
   }
  ],
  [
   "loyal",
   "נאמן",
   "המועדון שגידל אותו הוא הבית, וקשה לו לעזוב.",
   {
    "loyalty": 17,
    "professionalism": 10
   }
  ],
  [
   "temperamental",
   "מזגזג",
   "יום אחד הוא מכריע, יום אחר הוא לא שם.",
   {
    "temperament": -7
   }
  ],
  [
   "casual",
   "מזלזל",
   "כישרון יש. את השעה הנוספת באימון אין.",
   {
    "professionalism": -7
   }
  ],
  [
   "unambitious",
   "חסר שאיפה",
   "מרוצה ממה שיש. זה לא בהכרח רע — זה פשוט לא ייקח אותו רחוק.",
   {
    "ambition": -6
   }
  ],
  [
   "balanced",
   "מאוזן",
   "בלי קצוות. עובד, משחק, הולך הביתה.",
   {}
  ]
 ],
 "PERSONALITY_EFFECT": {
  "model_citizen": [
   1.3,
   0.7,
   1.25
  ],
  "model_professional": [
   1.28,
   0.72,
   1.2
  ],
  "perfectionist": [
   1.26,
   1.15,
   1.05
  ],
  "resolute": [
   1.18,
   0.8,
   1.1
  ],
  "driven": [
   1.16,
   0.95,
   1.05
  ],
  "professional": [
   1.1,
   0.9,
   1.1
  ],
  "fairly_professional": [
   1.02,
   1.0,
   1.0
  ],
  "loyal": [
   1.0,
   0.9,
   1.15
  ],
  "balanced": [
   0.96,
   1.0,
   1.0
  ],
  "temperamental": [
   0.82,
   1.45,
   0.8
  ],
  "casual": [
   0.8,
   1.1,
   0.85
  ],
  "unambitious": [
   0.88,
   0.95,
   1.0
  ]
 },
 "ROLES": [
  [
   "gk",
   "שוער",
   [
    "GK"
   ],
   [
    "defend"
   ],
   [
    "reflexes",
    "handling",
    "one_on_ones",
    "positioning",
    "concentration"
   ],
   [
    "aerial_reach",
    "command_of_area",
    "communication",
    "decisions"
   ],
   "נשאר על הקו, שומר על הרחבה, ולא מחפש הרפתקאות."
  ],
  [
   "sweeper_keeper",
   "שוער־מנקה",
   [
    "GK"
   ],
   [
    "defend",
    "support",
    "attack"
   ],
   [
    "rushing_out",
    "one_on_ones",
    "first_touch",
    "passing",
    "decisions"
   ],
   [
    "reflexes",
    "handling",
    "composure",
    "anticipation",
    "acceleration"
   ],
   "יוצא מהרחבה, מוסר ראשונה, ומשחק כמו שחקן אחד־עשר."
  ],
  [
   "cd_defend",
   "בלם",
   [
    "CB"
   ],
   [
    "defend",
    "stopper",
    "cover"
   ],
   [
    "marking",
    "tackling",
    "positioning",
    "heading",
    "jumping_reach"
   ],
   [
    "strength",
    "concentration",
    "bravery",
    "anticipation"
   ],
   "לא נותן לכדור לעבור. פשוט, ובלי סיבוכים."
  ],
  [
   "bpd",
   "בלם שמוציא",
   [
    "CB"
   ],
   [
    "defend",
    "stopper",
    "cover"
   ],
   [
    "passing",
    "vision",
    "first_touch",
    "composure",
    "technique"
   ],
   [
    "marking",
    "tackling",
    "positioning",
    "decisions"
   ],
   "לא רק הורס — פותח. המסירה הראשונה שלו היא ההתקפה."
  ],
  [
   "ncb",
   "בלם בלי שטויות",
   [
    "CB"
   ],
   [
    "defend",
    "stopper",
    "cover"
   ],
   [
    "heading",
    "jumping_reach",
    "strength",
    "bravery",
    "marking"
   ],
   [
    "tackling",
    "aggression",
    "positioning"
   ],
   "כדור באוויר, כדור לצד השני. אין בעיות."
  ],
  [
   "libero",
   "ליברו",
   [
    "CB"
   ],
   [
    "defend",
    "support"
   ],
   [
    "passing",
    "vision",
    "technique",
    "decisions",
    "off_the_ball"
   ],
   [
    "marking",
    "tackling",
    "first_touch",
    "composure",
    "stamina"
   ],
   "יוצא מהקו האחורי עם הכדור ומייצר עודף במרכז."
  ],
  [
   "fb",
   "מגן",
   [
    "LB",
    "RB"
   ],
   [
    "defend",
    "support",
    "automatic"
   ],
   [
    "marking",
    "tackling",
    "positioning",
    "anticipation",
    "concentration"
   ],
   [
    "crossing",
    "stamina",
    "teamwork",
    "work_rate"
   ],
   "מגן קודם כול. עולה רק כשבטוח."
  ],
  [
   "wb",
   "מגן מתקדם",
   [
    "LB",
    "RB"
   ],
   [
    "defend",
    "support",
    "attack",
    "automatic"
   ],
   [
    "crossing",
    "dribbling",
    "stamina",
    "work_rate",
    "acceleration"
   ],
   [
    "marking",
    "tackling",
    "teamwork",
    "off_the_ball"
   ],
   "עולה ויורד תשעים דקות בקו. שני תפקידים בגוף אחד."
  ],
  [
   "cwb",
   "מגן מתקדם מלא",
   [
    "LB",
    "RB"
   ],
   [
    "support",
    "attack"
   ],
   [
    "crossing",
    "dribbling",
    "flair",
    "stamina",
    "acceleration",
    "technique"
   ],
   [
    "off_the_ball",
    "work_rate",
    "agility",
    "passing"
   ],
   "כמעט כנף. הקו כולו שלו, וההגנה תסתדר."
  ],
  [
   "iwb",
   "מגן מתהפך",
   [
    "LB",
    "RB"
   ],
   [
    "defend",
    "support",
    "attack"
   ],
   [
    "passing",
    "vision",
    "first_touch",
    "decisions",
    "positioning"
   ],
   [
    "tackling",
    "marking",
    "composure",
    "teamwork"
   ],
   "נכנס פנימה לקו הקישור ומייצר עודף במרכז, לא בקו."
  ],
  [
   "nfb",
   "מגן בלי שטויות",
   [
    "LB",
    "RB"
   ],
   [
    "defend"
   ],
   [
    "marking",
    "tackling",
    "positioning",
    "strength",
    "bravery"
   ],
   [
    "concentration",
    "anticipation",
    "aggression"
   ],
   "לא מרים ראש. מרחיק, וממשיך לעבוד."
  ],
  [
   "dm",
   "קשר הגנתי",
   [
    "DM"
   ],
   [
    "defend",
    "support"
   ],
   [
    "positioning",
    "tackling",
    "anticipation",
    "concentration",
    "teamwork"
   ],
   [
    "marking",
    "strength",
    "decisions",
    "passing"
   ],
   "לפני ההגנה, אחרי הקישור. השקט של הקבוצה."
  ],
  [
   "anchor",
   "עוגן",
   [
    "DM"
   ],
   [
    "defend"
   ],
   [
    "positioning",
    "marking",
    "tackling",
    "concentration",
    "decisions"
   ],
   [
    "anticipation",
    "strength",
    "teamwork"
   ],
   "לא זז מהמקום. סותם את החור שבין הקווים."
  ],
  [
   "half_back",
   "מגן־קשר",
   [
    "DM"
   ],
   [
    "defend"
   ],
   [
    "positioning",
    "marking",
    "tackling",
    "anticipation",
    "teamwork"
   ],
   [
    "passing",
    "first_touch",
    "composure",
    "stamina"
   ],
   "יורד בין הבלמים בבנייה, ועולה בהגנה. שלושה נגד שניים, תמיד."
  ],
  [
   "bwm",
   "קשר חוטף",
   [
    "DM",
    "CM"
   ],
   [
    "defend",
    "support"
   ],
   [
    "tackling",
    "aggression",
    "work_rate",
    "stamina",
    "bravery"
   ],
   [
    "anticipation",
    "positioning",
    "teamwork",
    "determination"
   ],
   "רודף את הכדור עד שהוא מקבל אותו. או עד שהשופט שורק."
  ],
  [
   "dlp",
   "קשר בונה עמוק",
   [
    "DM",
    "CM"
   ],
   [
    "defend",
    "support"
   ],
   [
    "passing",
    "vision",
    "technique",
    "composure",
    "decisions"
   ],
   [
    "first_touch",
    "teamwork",
    "anticipation",
    "positioning"
   ],
   "המשחק עובר דרכו. רואה את המסירה שלושה מהלכים לפני כולם."
  ],
  [
   "regista",
   "רג'יסטה",
   [
    "DM"
   ],
   [
    "support"
   ],
   [
    "vision",
    "passing",
    "flair",
    "technique",
    "composure",
    "decisions"
   ],
   [
    "first_touch",
    "off_the_ball",
    "dribbling",
    "anticipation"
   ],
   "בונה עמוק אבל בלי רסן — מחפש את המסירה שתשבור את הכל."
  ],
  [
   "volante",
   "סגונדו וולנטה",
   [
    "DM"
   ],
   [
    "support",
    "attack"
   ],
   [
    "stamina",
    "work_rate",
    "long_shots",
    "off_the_ball",
    "tackling"
   ],
   [
    "passing",
    "positioning",
    "strength",
    "acceleration"
   ],
   "מתחיל אחורה ומסיים ברחבה. ריאות של שניים."
  ],
  [
   "cm",
   "קשר מרכזי",
   [
    "CM"
   ],
   [
    "defend",
    "support",
    "attack",
    "automatic"
   ],
   [
    "passing",
    "teamwork",
    "decisions",
    "work_rate",
    "positioning"
   ],
   [
    "first_touch",
    "tackling",
    "stamina",
    "composure"
   ],
   "הדבק. עושה את מה שהמשחק צריך באותו רגע."
  ],
  [
   "b2b",
   "קשר ריאות",
   [
    "CM"
   ],
   [
    "support"
   ],
   [
    "stamina",
    "work_rate",
    "teamwork",
    "off_the_ball",
    "passing"
   ],
   [
    "tackling",
    "long_shots",
    "strength",
    "determination"
   ],
   "רץ שנים־עשר קילומטר וגם מוסר. מרגישים כשהוא לא שם."
  ],
  [
   "mezzala",
   "מצאלה",
   [
    "CM"
   ],
   [
    "support",
    "attack"
   ],
   [
    "dribbling",
    "passing",
    "off_the_ball",
    "flair",
    "vision"
   ],
   [
    "technique",
    "acceleration",
    "long_shots",
    "work_rate"
   ],
   "נפתח לחצי־חלל בין המגן לבלם, ומשם שובר."
  ],
  [
   "carrilero",
   "קארילרו",
   [
    "CM"
   ],
   [
    "support"
   ],
   [
    "teamwork",
    "work_rate",
    "positioning",
    "stamina",
    "passing"
   ],
   [
    "tackling",
    "decisions",
    "anticipation"
   ],
   "מכסה את הרצועה שבין המרכז לקו. עבודה שאף אחד לא מריע לה."
  ],
  [
   "rpm",
   "בונה נודד",
   [
    "CM"
   ],
   [
    "support"
   ],
   [
    "passing",
    "vision",
    "technique",
    "off_the_ball",
    "stamina"
   ],
   [
    "dribbling",
    "first_touch",
    "work_rate",
    "composure"
   ],
   "אין לו עמדה. הוא הולך לאן שהכדור, והכדור הולך אליו."
  ],
  [
   "ap",
   "בונה מתקדם",
   [
    "CM",
    "AM"
   ],
   [
    "support",
    "attack"
   ],
   [
    "passing",
    "vision",
    "technique",
    "flair",
    "first_touch"
   ],
   [
    "dribbling",
    "composure",
    "off_the_ball",
    "decisions"
   ],
   "עובד גבוה, בין הקווים, ומחפש את הכדור האחרון."
  ],
  [
   "am",
   "קשר התקפי",
   [
    "AM"
   ],
   [
    "support",
    "attack"
   ],
   [
    "passing",
    "off_the_ball",
    "technique",
    "vision",
    "long_shots"
   ],
   [
    "first_touch",
    "dribbling",
    "composure",
    "flair"
   ],
   "בין הקישור להתקפה, במקום שקשה לשמור עליו."
  ],
  [
   "enganche",
   "אנגנצ'ה",
   [
    "AM"
   ],
   [
    "support"
   ],
   [
    "vision",
    "passing",
    "technique",
    "composure",
    "flair"
   ],
   [
    "first_touch",
    "decisions",
    "anticipation"
   ],
   "העשר הקלאסי. לא רץ אחורה, ולא צריך — הכדור מגיע אליו."
  ],
  [
   "shadow",
   "חלוץ צל",
   [
    "AM"
   ],
   [
    "attack"
   ],
   [
    "off_the_ball",
    "finishing",
    "acceleration",
    "anticipation",
    "composure"
   ],
   [
    "dribbling",
    "first_touch",
    "long_shots",
    "work_rate"
   ],
   "נכנס מאחורי החלוץ בדיוק כשההגנה מסתכלת עליו."
  ],
  [
   "trequartista",
   "טרקוורטיסטה",
   [
    "AM",
    "ST"
   ],
   [
    "attack"
   ],
   [
    "flair",
    "vision",
    "technique",
    "dribbling",
    "off_the_ball"
   ],
   [
    "passing",
    "finishing",
    "first_touch",
    "composure"
   ],
   "משוחרר מכל חובה הגנתית. או שהוא מכריע, או שהוא נעלם."
  ],
  [
   "winger",
   "כנף",
   [
    "LW",
    "RW"
   ],
   [
    "support",
    "attack"
   ],
   [
    "crossing",
    "dribbling",
    "acceleration",
    "pace",
    "technique"
   ],
   [
    "agility",
    "flair",
    "off_the_ball",
    "balance"
   ],
   "אחד על אחד, ואז הרמה. הקהל קם כשהכדור מגיע אליו."
  ],
  [
   "if",
   "חלוץ פנימי",
   [
    "LW",
    "RW"
   ],
   [
    "support",
    "attack"
   ],
   [
    "dribbling",
    "finishing",
    "off_the_ball",
    "acceleration",
    "first_touch"
   ],
   [
    "long_shots",
    "agility",
    "flair",
    "composure"
   ],
   "חותך פנימה מהקו על הרגל החזקה ומחפש שער."
  ],
  [
   "iw",
   "כנף מתהפכת",
   [
    "LW",
    "RW"
   ],
   [
    "support",
    "attack"
   ],
   [
    "passing",
    "crossing",
    "dribbling",
    "vision",
    "technique"
   ],
   [
    "off_the_ball",
    "agility",
    "first_touch",
    "decisions"
   ],
   "חותך פנימה, אבל כדי לבשל — לא כדי לבעוט."
  ],
  [
   "wp",
   "בונה מהקו",
   [
    "LW",
    "RW"
   ],
   [
    "support",
    "attack"
   ],
   [
    "passing",
    "vision",
    "technique",
    "crossing",
    "first_touch"
   ],
   [
    "dribbling",
    "composure",
    "decisions",
    "flair"
   ],
   "מקבל את הכדור בקו ומנהל ממנו את ההתקפה."
  ],
  [
   "raumdeuter",
   "ראומדויטר",
   [
    "LW",
    "RW"
   ],
   [
    "attack"
   ],
   [
    "off_the_ball",
    "anticipation",
    "finishing",
    "concentration",
    "composure"
   ],
   [
    "decisions",
    "acceleration",
    "first_touch",
    "teamwork"
   ],
   "לא מכדרר ולא מרים. פשוט נמצא במקום שאף אחד לא שמר עליו."
  ],
  [
   "wtf",
   "כנף מטרה",
   [
    "LW",
    "RW"
   ],
   [
    "support",
    "attack"
   ],
   [
    "heading",
    "jumping_reach",
    "strength",
    "bravery",
    "first_touch"
   ],
   [
    "crossing",
    "teamwork",
    "off_the_ball"
   ],
   "מחזיק את הכדור בקו ומושך אליו את המגן."
  ],
  [
   "dw",
   "כנף הגנתית",
   [
    "LW",
    "RW"
   ],
   [
    "defend",
    "support"
   ],
   [
    "work_rate",
    "stamina",
    "teamwork",
    "tackling",
    "positioning"
   ],
   [
    "crossing",
    "dribbling",
    "anticipation",
    "marking"
   ],
   "רץ אחורה עם המגן שלהם. לא זוהר, אבל בלעדיו הקו נשבר."
  ],
  [
   "af",
   "חלוץ מתקדם",
   [
    "ST"
   ],
   [
    "attack"
   ],
   [
    "finishing",
    "off_the_ball",
    "acceleration",
    "composure",
    "dribbling"
   ],
   [
    "first_touch",
    "anticipation",
    "pace",
    "technique"
   ],
   "רץ לעומק בכל הזדמנות, ומחפש את הכדור מאחורי ההגנה."
  ],
  [
   "poacher",
   "חלוץ בור",
   [
    "ST"
   ],
   [
    "attack"
   ],
   [
    "finishing",
    "off_the_ball",
    "anticipation",
    "composure",
    "concentration"
   ],
   [
    "first_touch",
    "acceleration",
    "heading",
    "decisions"
   ],
   "לא נוגע בכדור תשעים דקות, ומכריע ברגע הנכון."
  ],
  [
   "tf",
   "חלוץ מטרה",
   [
    "ST"
   ],
   [
    "support",
    "attack"
   ],
   [
    "heading",
    "jumping_reach",
    "strength",
    "bravery",
    "first_touch"
   ],
   [
    "finishing",
    "teamwork",
    "balance",
    "composure"
   ],
   "מחזיק עם הגב לשער עד שכל הקבוצה עולה."
  ],
  [
   "cf",
   "חלוץ מושלם",
   [
    "ST"
   ],
   [
    "support",
    "attack"
   ],
   [
    "finishing",
    "dribbling",
    "passing",
    "first_touch",
    "technique",
    "off_the_ball"
   ],
   [
    "composure",
    "vision",
    "strength",
    "acceleration",
    "flair"
   ],
   "כובש, מבשל, מחזיק, פותח. עושה הכול, וטוב בהכול."
  ],
  [
   "dlf",
   "חלוץ נסוג",
   [
    "ST"
   ],
   [
    "support",
    "attack"
   ],
   [
    "first_touch",
    "passing",
    "technique",
    "composure",
    "vision"
   ],
   [
    "finishing",
    "off_the_ball",
    "strength",
    "teamwork"
   ],
   "יורד לקבל בין הקווים ומושך את הבלם אחריו."
  ],
  [
   "pf",
   "חלוץ לוחץ",
   [
    "ST"
   ],
   [
    "defend",
    "support",
    "attack"
   ],
   [
    "work_rate",
    "stamina",
    "aggression",
    "bravery",
    "teamwork"
   ],
   [
    "finishing",
    "off_the_ball",
    "anticipation",
    "acceleration"
   ],
   "הלחיצה מתחילה ממנו. ההגנה שלהם לא נחה רגע."
  ],
  [
   "f9",
   "תשע מדומה",
   [
    "ST"
   ],
   [
    "support"
   ],
   [
    "passing",
    "vision",
    "first_touch",
    "technique",
    "off_the_ball",
    "flair"
   ],
   [
    "dribbling",
    "finishing",
    "composure",
    "decisions"
   ],
   "יורד לקישור ומשאיר את הרחבה ריקה — למישהו אחר."
  ]
 ],
 "DUTY_NAMES_HE": {
  "defend": "הגנה",
  "support": "תמיכה",
  "attack": "התקפה",
  "stopper": "בולם",
  "cover": "מכסה",
  "automatic": "אוטומטי"
 },
 "DUTY_SHIFT": {
  "defend": [
   0.28,
   -0.22,
   -0.05
  ],
  "cover": [
   0.3,
   -0.24,
   -0.02
  ],
  "stopper": [
   0.24,
   -0.16,
   0.06
  ],
  "support": [
   0.0,
   0.0,
   0.08
  ],
  "automatic": [
   0.05,
   0.05,
   0.04
  ],
  "attack": [
   -0.22,
   0.3,
   0.05
  ]
 },
 "TEAM_INSTRUCTIONS": {
  "mentality": [
   "מנטליות",
   [
    [
     "very_defensive",
     "הגנתית מאוד",
     -2
    ],
    [
     "defensive",
     "הגנתית",
     -1
    ],
    [
     "balanced",
     "מאוזנת",
     0
    ],
    [
     "positive",
     "חיובית",
     1
    ],
    [
     "attacking",
     "התקפית",
     2
    ]
   ]
  ],
  "tempo": [
   "קצב",
   [
    [
     "much_lower",
     "איטי מאוד",
     -2
    ],
    [
     "lower",
     "איטי",
     -1
    ],
    [
     "standard",
     "רגיל",
     0
    ],
    [
     "higher",
     "מהיר",
     1
    ],
    [
     "much_higher",
     "מהיר מאוד",
     2
    ]
   ]
  ],
  "width": [
   "רוחב",
   [
    [
     "very_narrow",
     "צר מאוד",
     -2
    ],
    [
     "narrow",
     "צר",
     -1
    ],
    [
     "standard",
     "רגיל",
     0
    ],
    [
     "wide",
     "רחב",
     1
    ],
    [
     "very_wide",
     "רחב מאוד",
     2
    ]
   ]
  ],
  "passing": [
   "אורך מסירה",
   [
    [
     "much_shorter",
     "קצר מאוד",
     -2
    ],
    [
     "shorter",
     "קצר",
     -1
    ],
    [
     "standard",
     "רגיל",
     0
    ],
    [
     "direct",
     "ישיר",
     1
    ],
    [
     "much_direct",
     "ישיר מאוד",
     2
    ]
   ]
  ],
  "pressing": [
   "עוצמת לחיצה",
   [
    [
     "much_less",
     "נמוכה מאוד",
     -2
    ],
    [
     "less",
     "נמוכה",
     -1
    ],
    [
     "standard",
     "רגילה",
     0
    ],
    [
     "more",
     "גבוהה",
     1
    ],
    [
     "much_more",
     "גבוהה מאוד",
     2
    ]
   ]
  ],
  "engagement": [
   "קו לחיצה",
   [
    [
     "much_deeper",
     "עמוק מאוד",
     -2
    ],
    [
     "deeper",
     "עמוק",
     -1
    ],
    [
     "standard",
     "רגיל",
     0
    ],
    [
     "higher",
     "גבוה",
     1
    ],
    [
     "much_higher",
     "גבוה מאוד",
     2
    ]
   ]
  ],
  "d_line": [
   "קו הגנה",
   [
    [
     "much_deeper",
     "עמוק מאוד",
     -2
    ],
    [
     "deeper",
     "עמוק",
     -1
    ],
    [
     "standard",
     "רגיל",
     0
    ],
    [
     "higher",
     "גבוה",
     1
    ],
    [
     "much_higher",
     "גבוה מאוד",
     2
    ]
   ]
  ]
 },
 "INSTRUCTION_KEYS": [
  "mentality",
  "tempo",
  "width",
  "passing",
  "pressing",
  "engagement",
  "d_line"
 ],
 "TACTICAL_STYLES": [
  [
   "gegenpress",
   "גגנפרסינג",
   {
    "mentality": 2,
    "tempo": 2,
    "width": 1,
    "passing": 0,
    "pressing": 2,
    "engagement": 2,
    "d_line": 2
   },
   "מאבדים את הכדור? מחזירים אותו תוך שש שניות. תשעים דקות של ריצה."
  ],
  [
   "tiki_taka",
   "טיקי־טאקה",
   {
    "mentality": 1,
    "tempo": -1,
    "width": -1,
    "passing": -2,
    "pressing": 1,
    "engagement": 1,
    "d_line": 1
   },
   "החזקה כשיטת הגנה. מאות מסירות, וסבלנות עד שנפתח חור."
  ],
  [
   "counter",
   "מעברים מהירים",
   {
    "mentality": -1,
    "tempo": 2,
    "width": 0,
    "passing": 2,
    "pressing": -1,
    "engagement": -1,
    "d_line": -1
   },
   "נותנים להם את הכדור, ואז רצים שישים מטר בשלוש מסירות."
  ],
  [
   "control",
   "שליטה",
   {
    "mentality": 1,
    "tempo": 0,
    "width": 1,
    "passing": -1,
    "pressing": 0,
    "engagement": 0,
    "d_line": 1
   },
   "מנהלים את הקצב, מחזיקים גבוה, ולא ממהרים לשום מקום."
  ],
  [
   "direct",
   "כדורגל ישיר",
   {
    "mentality": 1,
    "tempo": 1,
    "width": 1,
    "passing": 2,
    "pressing": 0,
    "engagement": 0,
    "d_line": 0
   },
   "קדימה מהר, שנייה, ולחפש את הראש של החלוץ."
  ],
  [
   "catenaccio",
   "בטון",
   {
    "mentality": -2,
    "tempo": -1,
    "width": -2,
    "passing": -1,
    "pressing": -2,
    "engagement": -2,
    "d_line": -2
   },
   "אחד־אפס זה ניצחון מושלם. שני קווים של ארבעה, ובהצלחה."
  ],
  [
   "wing_play",
   "משחק קו",
   {
    "mentality": 1,
    "tempo": 1,
    "width": 2,
    "passing": 1,
    "pressing": 0,
    "engagement": 0,
    "d_line": 0
   },
   "הכול דרך הקווים. הרמות, קרנות, ועוד הרמות."
  ],
  [
   "balanced_style",
   "מאוזן",
   {
    "mentality": 0,
    "tempo": 0,
    "width": 0,
    "passing": 0,
    "pressing": 0,
    "engagement": 0,
    "d_line": 0
   },
   "בלי אג'נדה. מגיבים למה שהמשחק נותן."
  ]
 ],
 "ATTR_INFO": {
  "corners": [
   "בעיטת קרן מדויקת.",
   "קובע כמה מהקרנות שלך מגיעות לראש הנכון ברחבה.",
   "מי שבועט קרנות — לרוב קשר או כנף עם רגל טובה."
  ],
  "crossing": [
   "הרמה מהאגף לרחבה.",
   "מעלה את מסירות המפתח שלך כשאתה מגיע לקו הרוחב.",
   "כנפיים ומגנים מתקדמים. חסר ערך לבלם."
  ],
  "dribbling": [
   "לרוץ עם הכדור בשליטה צמודה.",
   "קובע כמה יריבים תעבור אחד על אחד, ופחות איבודי כדור.",
   "כנפיים, קשרים התקפיים וחלוצים שמקבלים עם הפנים לשער."
  ],
  "finishing": [
   "להכניס את הכדור לרשת ממצב.",
   "הקובע הישיר בכמה מהבעיטות שלך הולכות למסגרת ונכנסות.",
   "כל מי שנמצא ברחבה. התכונה החשובה ביותר לחלוץ."
  ],
  "first_touch": [
   "הנגיעה הראשונה בכדור.",
   "נגיעה טובה חוסכת חצי שנייה, וחצי שנייה זה מצב.",
   "כולם, וקריטית למי שמקבל עם הגב לשער."
  ],
  "free_kick": [
   "בעיטה חופשית מדויקת.",
   "מכריעה משחקים צמודים. משתפרת רק באימון ישיר.",
   "בועט הכדורים הנייחים של הקבוצה."
  ],
  "heading": [
   "לכוון נגיחה, לא רק להגיע לכדור.",
   "שערים מקרנות והרחקות מהרחבה שלך.",
   "בלמים, חלוצי מטרה, וכל מי שגבוה."
  ],
  "long_shots": [
   "בעיטה מחוץ לרחבה.",
   "פותחת הגנות שמסתגרות, כשאין דרך פנימה.",
   "קשרים התקפיים וקשרי ריאות שמגיעים לקצה הרחבה."
  ],
  "long_throws": [
   "זריקת חוץ ארוכה.",
   "הופכת זריקה לקרן. נישתי, אבל אמיתי.",
   "מגנים בקבוצות שמשחקות ישיר."
  ],
  "marking": [
   "להישאר צמוד ליריב שלך.",
   "שומר שהיריב שאתה אחראי עליו לא יקבל כדור בכלל.",
   "בלמים ומגנים. קשר הגנתי גם צריך."
  ],
  "passing": [
   "להעביר את הכדור למקום הנכון.",
   "מעלה את אחוז המסירה ומוריד איבודי כדור.",
   "כולם. הבסיס של כל תפקיד בקישור."
  ],
  "penalty_taking": [
   "לבעוט מ-11 מטר.",
   "אחד־עשר מטר, ותשעים דקות תלויות בזה.",
   "בועט הפנדלים. משתפר רק באימון ישיר."
  ],
  "tackling": [
   "לחטוף כדור בלי לעשות עבירה.",
   "כל חטיפה נקייה היא התקפה שנעצרה ואחת שמתחילה.",
   "בלמים, מגנים וקשרים הגנתיים."
  ],
  "technique": [
   "האיכות הכללית שלך עם הכדור.",
   "מכפיל שקט: משפר בעיטה, מסירה, הרמה וכדרור יחד.",
   "כולם. במיוחד מי שהתפקיד שלו הוא לבנות."
  ],
  "aggression": [
   "כמה אתה נכנס לכל אירוע.",
   "יותר לחיצה ויותר חטיפות — וגם יותר כרטיסים.",
   "קשרים חוטפים וחלוצים לוחצים. פחות לבנאים."
  ],
  "anticipation": [
   "לקרוא מה עומד לקרות רגע לפני.",
   "מגיע ראשון לכדור בלי לרוץ מהר יותר.",
   "כולם. לחלוץ בור זו התכונה השנייה בחשיבותה."
  ],
  "bravery": [
   "להיכנס למקום שכואב.",
   "נגיחות בקהל ורגליים בתוך דו־קרב. גם סיכון פציעה.",
   "בלמים, חלוצי מטרה, שוערים."
  ],
  "composure": [
   "להישאר קר כשהלחץ עולה.",
   "ההבדל בין בעיטה למסגרת לבין בעיטה ליציע בדקה 89.",
   "כל מי שמסיים מצבים או מוסר תחת לחץ."
  ],
  "concentration": [
   "להישאר בפוקוס תשעים דקות.",
   "מונע את הרגע האחד שבו נרדמת ועלה שער.",
   "בלמים ושוערים בראש הרשימה."
  ],
  "decisions": [
   "לבחור נכון את הפעולה הבאה.",
   "מוסר או מכדרר, בועט או מחכה — התכונה שקובעת.",
   "כולם, בלי יוצא מן הכלל."
  ],
  "determination": [
   "כמה אתה מוכן לעבוד בשביל זה.",
   "מכפיל ישירות את קצב ההתפתחות שלך באימונים.",
   "כולם. זו התכונה שקובעת אם תממש את הפוטנציאל."
  ],
  "flair": [
   "לעשות את מה שאף אחד לא ציפה.",
   "פותח מצבים שמערך מסודר לא היה מייצר.",
   "כנפיים, עשרות ותשע מדומה. מסוכן לבלם."
  ],
  "leadership": [
   "להרים את מי שסביבך.",
   "משפיע על הקבוצה, על הקפטנות ועל הקריירה שאחרי.",
   "קפטנים, בלמים, שוערים."
  ],
  "off_the_ball": [
   "לזוז נכון כשהכדור לא אצלך.",
   "מייצר לך מצבים — יותר בעיטות, יותר ספרינטים.",
   "חלוצים וכנפיים. אצל חלוץ בור זו התכונה מספר אחת."
  ],
  "positioning": [
   "לעמוד במקום הנכון בהגנה.",
   "סותם חורים לפני שהם נפתחים.",
   "בלמים, מגנים, קשרים הגנתיים ושוערים."
  ],
  "teamwork": [
   "לעשות את מה שהמערכת דורשת.",
   "מאמנים אוהבים את זה, וזה נכנס לאמון שלהם בך.",
   "כולם, ובעיקר בתפקידי תמיכה."
  ],
  "vision": [
   "לראות את המסירה שאף אחד לא ראה.",
   "מעלה ישירות את מסירות המפתח שלך.",
   "בונים, עשרות, ובלמים שמוציאים."
  ],
  "work_rate": [
   "כמה אתה עובד בלי כדור.",
   "יותר ריצה ויותר לחיצה — הבסיס של כדורגל מודרני.",
   "קשרי ריאות, חלוצים לוחצים, מגנים מתקדמים."
  ],
  "acceleration": [
   "להגיע למהירות מלאה מעמידה.",
   "חמישה המטרים הראשונים — ההבדל בין מצב לכלום.",
   "כנפיים וחלוצים. חשובה יותר ממהירות שיא."
  ],
  "agility": [
   "לשנות כיוון בלי לאבד שליטה.",
   "לעבור יריב במקום צר, ולהישאר על הרגליים.",
   "כדררנים, שוערים, ומגנים מול כנף מהירה."
  ],
  "balance": [
   "לא ליפול ממגע.",
   "מחזיק אותך על הרגליים כשמושכים אותך.",
   "כדררנים וחלוצים שמחזיקים כדור."
  ],
  "jumping_reach": [
   "כמה גבוה אתה מגיע.",
   "קובע דו־קרבים באוויר, לא הגובה שלך.",
   "בלמים, חלוצי מטרה, שוערים."
  ],
  "natural_fitness": [
   "כמה מהר הגוף שלך חוזר לעצמו.",
   "פחות פציעות, התאוששות מהירה יותר בין משחקים.",
   "כולם. אצל ותיקים זה מאריך קריירה."
  ],
  "pace": [
   "מהירות השיא שלך.",
   "עם סיבולת — כמה זמן תחזיק אותה.",
   "כנפיים, חלוצים ומגנים מתקדמים."
  ],
  "stamina": [
   "להחזיק תשעים דקות באותה רמה.",
   "מונע את הקריסה בדקה 60 ואת הקנס בציון.",
   "כולם. קריטית בקבוצה שלוחצת."
  ],
  "strength": [
   "להפעיל כוח על יריב ולנצח בו.",
   "קובע ישירות את אחוז הדו־קרבים שלך.",
   "חלוצי מטרה, בלמים, קשרים חוטפים."
  ],
  "aerial_reach": [
   "להגיע לכדורים גבוהים ברחבה.",
   "קרנות והרמות שנגמרות בידיים שלך ולא בראש שלהם.",
   "שוערים בלבד."
  ],
  "command_of_area": [
   "לשלוט ברחבה ולארגן את ההגנה.",
   "ההגנה עומדת נכון כי אתה צועק להם.",
   "שוערים בלבד."
  ],
  "communication": [
   "לדבר עם ההגנה תשעים דקות.",
   "מונע בלבול בין הבלמים ברגעים הקשים.",
   "שוערים בלבד."
  ],
  "eccentricity": [
   "נטייה לעשות דברים לא צפויים.",
   "לפעמים הצלה מדהימה, לפעמים שער מגוחך.",
   "שוערים. ככל שנמוך יותר — כך בטוח יותר."
  ],
  "handling": [
   "להחזיק את הכדור ולא לשחרר.",
   "מונע ריבאונדים ושערים מרשלנות.",
   "שוערים בלבד."
  ],
  "kicking": [
   "לבעוט מהשער רחוק ומדויק.",
   "הופך הרחקה להתקפה.",
   "שוערים, במיוחד שוער־מנקה."
  ],
  "one_on_ones": [
   "לעצור חלוץ שיצא לבד.",
   "הרגע שבו שוער מרוויח את המשכורת שלו.",
   "שוערים בלבד."
  ],
  "reflexes": [
   "להגיב לבעיטה מטווח קצר.",
   "התכונה המרכזית של כל שוער.",
   "שוערים בלבד."
  ],
  "rushing_out": [
   "לצאת מהשער בזמן הנכון.",
   "חוסם כדורים לעומק לפני שהם הופכים למצב.",
   "שוער־מנקה בקבוצה עם קו הגנה גבוה."
  ],
  "tendency_to_punch": [
   "להעדיף אגרוף על תפיסה.",
   "בטוח יותר בקהל, פחות שליטה על הכדור.",
   "שוערים. עניין של סגנון, לא של איכות."
  ],
  "throwing": [
   "לזרוק את הכדור מדויק ומהר.",
   "פותח מעבר מהיר מיד אחרי הצלה.",
   "שוערים בקבוצות שמשחקות מעברים."
  ]
 },
 "FOCUS_INFO": {
  "rest": [
   "שבוע קליל.",
   "מחזיר רעננות ומקצר שיקום. החדות יורדת קצת.",
   "מי שנכנס למשחקים שרוף, או שחוזר מפציעה."
  ],
  "badges": [
   "לימודי אימון.",
   "בונה ידע אימון ותעודות לקראת הקריירה שאחרי.",
   "ותיקים שחושבים על מה שיהיה בגיל 35."
  ],
  "media": [
   "סדנת תקשורת.",
   "מעלה כריזמה — וזה מה שפותח חסויות ועבודות אולפן.",
   "מי שרוצה שהמותגים יתקשרו."
  ],
  "business": [
   "לימודי ניהול.",
   "ראש עסקי — שימושי בניהול הכסף ובקריירה שאחרי.",
   "מי שמתכנן לקנות מועדון יום אחד."
  ],
  "school": [
   "בית ספר.",
   "מעלה קריאת משחק לאט, ומשאיר לך דלת פתוחה.",
   "נערים. ההורים יהיו מרוצים."
  ],
  "street": [
   "כדורגל במגרש השכונתי.",
   "כדרור, בעיטה ומהירות — בלי מאמן ובלי חוקים.",
   "נערים שרוצים לפתח ברק, לא משמעת."
  ]
 },
 "DETAIL_DECLINE": {
  "acceleration": 1.9,
  "pace": 1.9,
  "agility": 1.5,
  "balance": 1.0,
  "stamina": 1.4,
  "jumping_reach": 1.3,
  "strength": 0.9,
  "natural_fitness": 1.1,
  "dribbling": 1.1,
  "flair": 0.6,
  "work_rate": 0.9,
  "aggression": 0.4,
  "finishing": 0.6,
  "long_shots": 0.5,
  "heading": 0.7,
  "crossing": 0.4,
  "first_touch": 0.2,
  "technique": 0.1,
  "passing": 0.2,
  "corners": 0.0,
  "free_kick": 0.0,
  "penalty_taking": 0.0,
  "long_throws": 0.5,
  "tackling": 0.8,
  "marking": 0.4,
  "anticipation": -0.6,
  "composure": -0.6,
  "concentration": -0.4,
  "decisions": -0.7,
  "determination": -0.2,
  "leadership": -0.9,
  "off_the_ball": -0.2,
  "positioning": -0.7,
  "teamwork": -0.4,
  "vision": -0.5,
  "bravery": 0.0,
  "reflexes": 1.0,
  "handling": 0.3,
  "one_on_ones": 0.2,
  "aerial_reach": 1.1,
  "command_of_area": -0.4,
  "communication": -0.6,
  "kicking": 0.3,
  "throwing": 0.3,
  "rushing_out": 0.8,
  "eccentricity": 0.0,
  "tendency_to_punch": 0.0
 },
 "ASSETS": [
  [
   "studio_flat",
   "דירת סטודיו להשכרה",
   "נדל\"ן",
   1400000,
   0.036,
   0.1,
   0,
   "שתי חדרים ליד המגרש. לא מרגש, ומשלם כל חודש."
  ],
  [
   "family_flat",
   "דירת ארבעה חדרים",
   "נדל\"ן",
   3200000,
   0.033,
   0.11,
   0,
   "הדירה שההורים שלך תמיד רצו. גם שוכר טוב יושב בה."
  ],
  [
   "penthouse",
   "פנטהאוז על הים",
   "נדל\"ן",
   14000000,
   0.026,
   0.16,
   30,
   "יותר סטייטמנט מהשקעה — אבל הוא עולה בערכו בזמן שאתה ישן בו."
  ],
  [
   "shops",
   "שתי חנויות ברחוב ראשי",
   "נדל\"ן מסחרי",
   6500000,
   0.061,
   0.2,
   20,
   "שכירות מסחרית משלמת יותר, וגם מתפנה בלי להודיע."
  ],
  [
   "office_floor",
   "קומת משרדים",
   "נדל\"ן מסחרי",
   22000000,
   0.058,
   0.22,
   45,
   "חוזה ארוך עם חברת הייטק. עד שהם מתכווצים."
  ],
  [
   "restaurant",
   "מסעדה בשם שלך",
   "עסק",
   5000000,
   0.085,
   0.45,
   35,
   "השם שלך על השלט. זה מביא אנשים — כל עוד השם שווה משהו."
  ],
  [
   "padel",
   "מתחם פאדל",
   "עסק",
   9000000,
   0.095,
   0.34,
   30,
   "שמונה מגרשים ותורים בערב. ספורט שמוכר את עצמו."
  ],
  [
   "academy",
   "אקדמיית כדורגל לילדים",
   "עסק",
   7500000,
   0.072,
   0.28,
   40,
   "מאתיים ילדים בשנה. גם עסק, וגם משהו שנשאר אחריך."
  ],
  [
   "agency_stake",
   "אחזקה בסוכנות שחקנים",
   "פיננסי",
   18000000,
   0.11,
   0.5,
   55,
   "עמלות של אחרים נכנסות אליך. תלוי לגמרי בעסקאות שייסגרו."
  ],
  [
   "index_fund",
   "קרן מדד עולמית",
   "פיננסי",
   1000000,
   0.068,
   0.3,
   0,
   "משעמם, נזיל, ובטווח ארוך מנצח כמעט הכול."
  ],
  [
   "club_shares",
   "מניות מיעוט במועדון",
   "פיננסי",
   55000000,
   0.045,
   0.55,
   70,
   "אחוזים במועדון בליגה. הערך שלהן זז עם הטבלה."
  ]
 ],
 "ASSET_EVENTS": [
  [
   "נדל\"ן",
   "השוכר עזב באמצע החוזה. חודשיים בלי הכנסה.",
   -0.35
  ],
  [
   "נדל\"ן",
   "התחדשות עירונית בשכונה — השווי קפץ.",
   0.22
  ],
  [
   "נדל\"ן מסחרי",
   "רשת גדולה חתמה על החנות. השכירות עלתה.",
   0.28
  ],
  [
   "נדל\"ן מסחרי",
   "הרחוב נסגר לשיפוצים לחצי שנה.",
   -0.3
  ],
  [
   "עסק",
   "ביקורת מצוינת במוסף הסופ\"ש. תורים בכניסה.",
   0.4
  ],
  [
   "עסק",
   "מנהל התחלף וחצי מהצוות הלך. חודש גרוע.",
   -0.38
  ],
  [
   "פיננסי",
   "רבעון חזק בשווקים.",
   0.33
  ],
  [
   "פיננסי",
   "תיקון חד בשווקים. על הנייר, בינתיים.",
   -0.36
  ]
 ],
 "BONUS_CLAUSES": [
  [
   "per_goal",
   "בונוס לכל שער בעונה",
   "goals",
   0.03
  ],
  [
   "per_assist",
   "בונוס לכל בישול בעונה",
   "assists",
   0.018
  ],
  [
   "trophy",
   "בונוס על תואר",
   "trophies",
   0.32
  ],
  [
   "caps",
   "בונוס על משחקי נבחרת",
   "caps",
   0.055
  ],
  [
   "rating",
   "בונוס על ציון עונה מעל 7.0",
   "rating",
   0.24
  ]
 ],
 "INJURY_TYPES": [
  [
   "מתיחה בשריר הירך",
   1,
   3
  ],
  [
   "נקע בקרסול",
   2,
   5
  ],
  [
   "חבלה בברך",
   4,
   10
  ],
  [
   "שבר בכף הרגל",
   8,
   18
  ],
  [
   "קרע ברצועה הצולבת",
   24,
   40
  ],
  [
   "זעזוע מוח",
   1,
   2
  ],
  [
   "פציעת גב",
   2,
   6
  ]
 ],
 "MENTALITIES": {
  "ultra_defensive": [
   "בטון מזוין",
   0.72,
   1.3,
   -0.15
  ],
  "defensive": [
   "הגנתי",
   0.86,
   1.15,
   -0.07
  ],
  "balanced": [
   "מאוזן",
   1.0,
   1.0,
   0.0
  ],
  "attacking": [
   "התקפי",
   1.16,
   0.88,
   0.08
  ],
  "all_out": [
   "הכל קדימה",
   1.34,
   0.7,
   0.18
  ]
 },
 "PRESSING": {
  "low": [
   "בלוק נמוך",
   -0.05,
   0.06,
   0.6
  ],
  "medium": [
   "לחץ מדוד",
   0.0,
   0.0,
   1.0
  ],
  "high": [
   "לחץ גבוה",
   0.09,
   -0.06,
   1.5
  ]
 },
 "AGE_CURVE": {
  "13": 1.6,
  "14": 1.58,
  "15": 1.54,
  "16": 1.48,
  "17": 1.42,
  "18": 1.34,
  "19": 1.26,
  "20": 1.18,
  "21": 1.1,
  "22": 1.02,
  "23": 0.94,
  "24": 0.85,
  "25": 0.75,
  "26": 0.63,
  "27": 0.51,
  "28": 0.39,
  "29": 0.27,
  "30": 0.14,
  "31": 0.02,
  "32": -0.14,
  "33": -0.28,
  "34": -0.42,
  "35": -0.56,
  "36": -0.72,
  "37": -0.86,
  "38": -1.0
 },
 "DECLINE_SENSITIVITY": {
  "pace": 1.7,
  "physical": 1.4,
  "dribbling": 1.1,
  "shooting": 0.7,
  "passing": 0.4,
  "defending": 0.5,
  "mental": -0.5
 },
 "SQUAD_TEMPLATE": [
  "GK",
  "GK",
  "GK",
  "CB",
  "CB",
  "CB",
  "CB",
  "LB",
  "LB",
  "RB",
  "RB",
  "DM",
  "DM",
  "CM",
  "CM",
  "CM",
  "AM",
  "AM",
  "LW",
  "LW",
  "RW",
  "RW",
  "ST",
  "ST",
  "ST"
 ],
 "STORY_PACK": [
  {
   "eid": "p_first_touch",
   "title": "הנגיעה הראשונה בקבוצה",
   "stages": [
    "youth"
   ],
   "weight": 3.0,
   "cooldown": 40,
   "once": true,
   "when": {
    "week_min": 3
   },
   "body": "האימון הראשון עם הקבוצה. כולם מכירים אחד את השני, ואתה החדש.\nהמאמן זורק כדור לרחבה ואומר: \"תראו לי מי אתם.\"",
   "choices": [
    {
     "label": "לרוץ על כל כדור",
     "hint": "כוח, מורל",
     "text": "רצת עד שהריאות בערו. בסוף האימון {manager} רק אמר: \"הילד הזה לא מוותר.\"",
     "fx": {
      "attr": [
       "physical",
       1.0
      ],
      "morale": 4,
      "trust": 3
     }
    },
    {
     "label": "לשחק פשוט ולא לאבד כדורים",
     "hint": "מסירה",
     "text": "לא ניסית שום דבר מיוחד. גם לא איבדת כדור אחד.",
     "fx": {
      "attr": [
       "passing",
       1.2
      ],
      "trust": 2
     }
    },
    {
     "label": "לנסות משהו שיזכרו",
     "hint": "כדרור, אבל מסוכן",
     "text": "עשית תרגיל שהוציא צחוק מהיציע ופרצוף חמוץ מהמאמן. חצי הצליח.",
     "fx": {
      "attr": [
       "dribbling",
       1.5
      ],
      "trust": -2,
      "morale": 5
     }
    }
   ]
  },
  {
   "eid": "p_homesick",
   "title": "רחוק מהבית",
   "stages": [
    "youth"
   ],
   "weight": 2.2,
   "cooldown": 45,
   "once": true,
   "when": {
    "age_min": 14
   },
   "body": "הפנימייה של מחלקת הנוער נמצאת שעה וחצי מהבית.\nבלילה השלישי אתה שומע את עצמך חושב על המיטה בבית.",
   "choices": [
    {
     "label": "להתקשר הביתה כל ערב",
     "hint": "מורל",
     "text": "אמא ענתה בצלצול הראשון בכל פעם. זה עזר יותר ממה שהודית.",
     "fx": {
      "morale": 8,
      "attr": [
       "mental",
       -0.3
      ]
     }
    },
    {
     "label": "להתרכז בכדורגל ולא להסתכל אחורה",
     "hint": "קריאת משחק",
     "text": "סגרת את הטלפון בארון. היה קשה חודש. אחר כך זה הפך לבית.",
     "fx": {
      "attr": [
       "mental",
       1.4
      ],
      "morale": -5,
      "resilience": 2
     }
    }
   ]
  },
  {
   "eid": "p_too_small",
   "title": "\"אתה קטן מדי\"",
   "stages": [
    "youth",
    "academy"
   ],
   "weight": 2.4,
   "cooldown": 45,
   "once": true,
   "when": {
    "age_max": 17
   },
   "body": "אחד המאמנים אמר לך את זה בפנים, בלי לרכך:\n\"טכנית אתה מהטובים. אבל בגודל הזה לא תחזיק בבוגרים.\"",
   "choices": [
    {
     "label": "לעלות לחדר הכושר",
     "hint": "כוח פיזי, עמידות",
     "text": "התחלת לעבוד על הגוף. זה לקח שנה, אבל אף אחד לא אמר את זה שוב.",
     "fx": {
      "attr": [
       "physical",
       2.0
      ],
      "resilience": 4,
      "morale": -2
     }
    },
    {
     "label": "להפוך את הגודל ליתרון",
     "hint": "מהירות וכדרור",
     "text": "החלטת שאם אתה קטן — תהיה מהיר יותר משכולם יספיקו לחשוב.",
     "fx": {
      "attrs": [
       [
        "pace",
        1.4
       ],
       [
        "dribbling",
        1.2
       ]
      ]
     }
    },
    {
     "label": "להוכיח אותו על המגרש",
     "hint": "מורל ואמון",
     "text": "לא ענית. במשחק הבא כבשת פעמיים והסתכלת לכיוון הספסל.",
     "fx": {
      "morale": 7,
      "trust": 4,
      "form": 8
     }
    }
   ]
  },
  {
   "eid": "p_street_rival",
   "title": "היריב מהשכונה",
   "stages": [
    "youth"
   ],
   "weight": 2.0,
   "cooldown": 30,
   "body": "יש ילד מהשכונה השנייה שכולם מדברים עליו.\nהשבוע אתם משחקים אחד נגד השני, והמגרש יהיה מלא.",
   "choices": [
    {
     "label": "לשחק בשביל לנצח אותו",
     "hint": "אישי",
     "text": "שכחת מהקבוצה וניסית לנצח אותו לבד. הצלחת בחצי מהמקרים.",
     "fx": {
      "attr": [
       "dribbling",
       1.1
      ],
      "trust": -2,
      "morale": 4
     }
    },
    {
     "label": "לשחק בשביל הקבוצה",
     "hint": "מסירה ואמון",
     "text": "בישלת שניים ולא כבשת. המאמן ראה בדיוק מה שרצה לראות.",
     "fx": {
      "attr": [
       "passing",
       1.2
      ],
      "trust": 5
     }
    }
   ]
  },
  {
   "eid": "p_first_final",
   "title": "גמר מחוזי",
   "stages": [
    "youth"
   ],
   "weight": 2.6,
   "cooldown": 45,
   "when": {
    "week_min": 20
   },
   "body": "גמר. מגרש עם קווים לבנים אמיתיים, שופט עם חולצה, ומאה איש ביציע.\nבחדר ההלבשה שקט שלא שמעת קודם.",
   "choices": [
    {
     "label": "לדבר לקבוצה",
     "hint": "מנהיגות",
     "text": "עמדת באמצע ואמרת משפט אחד. הוא לא היה חכם, אבל הוא עבד.",
     "fx": {
      "attr": [
       "mental",
       1.3
      ],
      "trust": 4,
      "trait": "leader"
     }
    },
    {
     "label": "לשים אוזניות ולהתכנס",
     "hint": "ריכוז",
     "text": "לא דיברת עם אף אחד עד השריקה. יצאת למגרש ריכוז אחד גדול.",
     "fx": {
      "form": 12,
      "attr": [
       "mental",
       0.8
      ]
     }
    }
   ]
  },
  {
   "eid": "p_parent_pressure",
   "title": "אבא ביציע",
   "stages": [
    "youth"
   ],
   "weight": 2.2,
   "cooldown": 34,
   "body": "אבא שלך צועק מהיציע. לא לעודד — להנחות.\nאתה שומע אותו יותר מאשר את המאמן, ושני הילדים לידך שמעו גם.",
   "choices": [
    {
     "label": "לבקש ממנו לשתוק",
     "hint": "קשה, אבל נכון",
     "text": "דיברתם בדרך הביתה. הוא נעלב שבוע, ואז הפסיק לצעוק.",
     "fx": {
      "attr": [
       "mental",
       1.0
      ],
      "morale": -3
     }
    },
    {
     "label": "לתת לזה לעבור",
     "hint": "שלום בית",
     "text": "לא אמרת כלום. הוא המשיך, ואתה למדת לסנן.",
     "fx": {
      "morale": 2,
      "attr": [
       "mental",
       0.4
      ]
     }
    }
   ]
  },
  {
   "eid": "p_trial_elsewhere",
   "title": "מבחן בקבוצה אחרת",
   "stages": [
    "youth"
   ],
   "weight": 2.0,
   "cooldown": 40,
   "when": {
    "age_min": 14
   },
   "body": "קבוצה מהעיר הגדולה מזמינה אותך לשבוע מבחנים.\nזה אומר להחסיר אימונים ב{club}, ולהסביר למה.",
   "choices": [
    {
     "label": "ללכת",
     "hint": "מוניטין, אבל אמון יורד",
     "text": "נסעת. הם אמרו \"נהיה בקשר\". ב{club} שמו לב שלא היית.",
     "fx": {
      "rep": 4,
      "trust": -6,
      "attr": [
       "mental",
       0.5
      ]
     }
    },
    {
     "label": "להישאר",
     "hint": "אמון",
     "text": "אמרת לא. {manager} שמע על זה, ולא שכח.",
     "fx": {
      "trust": 8,
      "morale": -3
     }
    }
   ]
  },
  {
   "eid": "p_friend_quits",
   "title": "החבר שעוזב",
   "stages": [
    "youth"
   ],
   "weight": 1.8,
   "cooldown": 45,
   "once": true,
   "body": "החבר הכי טוב שלך בקבוצה מודיע שהוא מפסיק.\n\"זה לא הולך לקרות לי,\" הוא אומר. \"עדיף שאלמד.\"",
   "choices": [
    {
     "label": "לנסות לשכנע אותו להישאר",
     "hint": "מנהיגות",
     "text": "שכנעת אותו לתת לזה עוד חצי שנה. הוא נשאר, ואתה הפסקת לקחת את זה כמובן מאליו.",
     "fx": {
      "attr": [
       "mental",
       1.1
      ],
      "morale": 4
     }
    },
    {
     "label": "לקבל ולהמשיך",
     "hint": "התמקדות",
     "text": "לחצתם ידיים. באימון הבא היה חסר מישהו, ואתה רצת קצת יותר.",
     "fx": {
      "attr": [
       "physical",
       0.8
      ],
      "morale": -4,
      "resilience": 2
     }
    }
   ]
  },
  {
   "eid": "p_first_wage",
   "title": "המשכורת הראשונה",
   "stages": [
    "academy"
   ],
   "weight": 3.0,
   "cooldown": 45,
   "once": true,
   "when": {
    "needs_club": true
   },
   "body": "נכנס לחשבון סכום ראשון מ{club}: ₪{wage} לשבוע.\nזה לא הרבה, וזה הכי הרבה כסף שהיה לך בחיים.",
   "choices": [
    {
     "label": "לשים בצד הכל",
     "hint": "ראש עסקי",
     "text": "לא נגעת. פתחת חיסכון והרגשת מבוגר בפעם הראשונה.",
     "fx": {
      "business": 5,
      "money": 4000
     }
    },
    {
     "label": "לקנות משהו להורים",
     "hint": "מורל",
     "text": "קנית להם מקרר חדש. אמא בכתה, אבא אמר \"לא היה צריך\" ופתח אותו עשר פעמים.",
     "fx": {
      "morale": 10,
      "money": -3000
     }
    },
    {
     "label": "לבזבז על עצמך",
     "hint": "כיף עכשיו",
     "text": "נעליים, אוזניות, ושעה במסעדה שלא היית נכנס אליה. היה שווה.",
     "fx": {
      "morale": 6,
      "money": -5000,
      "media": 2
     }
    }
   ]
  },
  {
   "eid": "p_position_switch",
   "title": "הצעה להחליף עמדה",
   "stages": [
    "academy",
    "player"
   ],
   "weight": 2.2,
   "cooldown": 40,
   "when": {
    "needs_club": true,
    "age_max": 24
   },
   "body": "{manager} עצר אותך אחרי אימון.\n\"אני חושב שאתה משחק בעמדה הלא נכונה. אני רוצה לנסות אותך אחורה.\"",
   "choices": [
    {
     "label": "לנסות",
     "hint": "הגנה וקריאת משחק",
     "text": "ניסית. היה מוזר שבועיים, ואז פתאום ראית את המגרש אחרת.",
     "fx": {
      "attrs": [
       [
        "defending",
        1.4
       ],
       [
        "mental",
        1.0
       ]
      ],
      "trust": 6
     }
    },
    {
     "label": "לסרב — אני יודע מי אני",
     "hint": "עמדה, אבל אמון",
     "text": "אמרת שאתה {position} וזהו. הוא הנהן ולא חזר לזה.",
     "fx": {
      "trust": -5,
      "morale": 4,
      "attr": [
       "mental",
       0.6
      ]
     }
    }
   ]
  },
  {
   "eid": "p_reserve_grind",
   "title": "ליגת הרזרבה",
   "stages": [
    "academy"
   ],
   "weight": 2.4,
   "cooldown": 26,
   "when": {
    "needs_club": true
   },
   "body": "עוד משחק רזרבה בשדה אימונים ריק, מול קבוצה שאף אחד לא זוכר את שמה.\nקל מאוד לרדת מהגז כאן.",
   "choices": [
    {
     "label": "לשחק כאילו זה גמר",
     "hint": "חדות ואמון",
     "text": "היית הכי טוב על המגרש. אחד הצוות המקצועי רשם משהו במחברת.",
     "fx": {
      "sharpness": 6,
      "trust": 4,
      "form": 6
     }
    },
    {
     "label": "לחסוך את עצמך",
     "hint": "כושר",
     "text": "רצת מספיק כדי שלא יגידו כלום. גם לא מספיק כדי שיגידו משהו.",
     "fx": {
      "fitness": 8,
      "trust": -2
     }
    }
   ]
  },
  {
   "eid": "p_agent_choice",
   "title": "לבחור סוכן",
   "stages": [
    "academy",
    "player"
   ],
   "weight": 2.0,
   "cooldown": 50,
   "once": true,
   "when": {
    "age_min": 16
   },
   "body": "שני סוכנים רוצים אותך.\nאחד ותיק, מסודר, לוקח אחוזים גבוהים. השני צעיר, רעב, מבטיח עולם.",
   "choices": [
    {
     "label": "הוותיק",
     "hint": "יציבות",
     "text": "חתמת עם המשרד הגדול. פחות טלפונים, יותר סדר.",
     "fx": {
      "business": 4,
      "flag": "agent_veteran",
      "money": -8000
     }
    },
    {
     "label": "הצעיר",
     "hint": "הימור",
     "text": "חתמת עם הרעב. הוא עונה בשתיים בלילה, וזה כנראה יביא משהו.",
     "fx": {
      "rep": 3,
      "flag": "agent_hungry",
      "media": 3
     }
    },
    {
     "label": "בלי סוכן בינתיים",
     "hint": "עצמאות",
     "text": "אבא שלך אמר שהוא יטפל. זה יעבוד עד שזה לא יעבוד.",
     "fx": {
      "money": 6000,
      "attr": [
       "mental",
       0.5
      ]
     }
    }
   ]
  },
  {
   "eid": "p_hazing",
   "title": "טקס החניכה",
   "stages": [
    "academy"
   ],
   "weight": 1.8,
   "cooldown": 45,
   "once": true,
   "body": "בחדר ההלבשה עומדים על הכיסא ושרים. זה התור שלך.\nכולם מסתכלים, כולל שלושה שחקנים בוגרים שבאו במיוחד לצחוק.",
   "choices": [
    {
     "label": "לשיר בקול, בלי בושה",
     "hint": "חדר הלבשה",
     "text": "שרת רע ובקול. צחקו איתך, לא עליך. מאותו יום היית בפנים.",
     "fx": {
      "morale": 8,
      "trust": 3,
      "media": 3
     }
    },
    {
     "label": "לסרב",
     "hint": "עצמאות, אבל מבודד",
     "text": "ירדת מהכיסא. איש לא אמר כלום, ולקח חודשיים עד שהזמינו אותך לקפה.",
     "fx": {
      "morale": -6,
      "attr": [
       "mental",
       0.8
      ]
     }
    }
   ]
  },
  {
   "eid": "p_debut_nerves",
   "title": "הבכורה",
   "stages": [
    "player"
   ],
   "weight": 3.2,
   "cooldown": 60,
   "once": true,
   "when": {
    "needs_club": true,
    "apps_max": 3
   },
   "body": "{manager} קרא לך בחימום ואמר: \"תתחמם ברצינות. אתה נכנס.\"\nהיציע ב{stadium} רועש, והרגליים שלך פתאום כבדות.",
   "choices": [
    {
     "label": "לבקש את הכדור מהרגע הראשון",
     "hint": "ביטחון",
     "text": "נגעת שבע פעמים בשתי הדקות הראשונות. אף אחד לא זכר שאתה חדש.",
     "fx": {
      "morale": 10,
      "form": 12,
      "rep": 3,
      "trust": 4
     }
    },
    {
     "label": "לשחק בטוח, לא לטעות",
     "hint": "בלי סיכון",
     "text": "מסירות קצרות, שום דבר מיוחד, שום דבר גרוע. בכורה בלי סיפור.",
     "fx": {
      "morale": 4,
      "attr": [
       "passing",
       0.8
      ],
      "trust": 2
     }
    }
   ]
  },
  {
   "eid": "p_training_fight",
   "title": "מכה באימון",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.0,
   "cooldown": 30,
   "when": {
    "needs_club": true,
    "has_mate": true
   },
   "body": "{mate} נכנס בך בסיבוב מאוחר באימון. לא בטעות.\nכולם עצרו והסתכלו לראות מה תעשה.",
   "choices": [
    {
     "label": "להיכנס בו בחזרה",
     "hint": "כבוד, ומחיר",
     "text": "נכנסתם אחד בשני עד שהפרידו. {manager} הוציא את שניכם מהאימון.",
     "fx": {
      "trust": -7,
      "morale": 4,
      "trait": "hothead",
      "attr": [
       "physical",
       0.6
      ]
     }
    },
    {
     "label": "לקום ולהמשיך",
     "hint": "אופי",
     "text": "קמת, ניקית את הברך והמשכת. חדר ההלבשה ראה הכל.",
     "fx": {
      "attr": [
       "mental",
       1.2
      ],
      "trust": 5,
      "morale": -2
     }
    },
    {
     "label": "לדבר איתו אחרי",
     "hint": "בגרות",
     "text": "חיכית לו במסדרון ודיברתם. בשבוע הבא הוא חיפש אותך במסירה הראשונה.",
     "fx": {
      "morale": 6,
      "attr": [
       "mental",
       0.8
      ],
      "trust": 3
     }
    }
   ]
  },
  {
   "eid": "p_penalty_duty",
   "title": "מי בועט פנדלים",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.2,
   "cooldown": 40,
   "when": {
    "needs_club": true,
    "position_in": [
     "ST",
     "AM",
     "LW",
     "RW",
     "CM"
    ]
   },
   "body": "הבועט הקבוע נפצע. {manager} מסתכל סביב חדר ההלבשה ושואל מי לוקח.",
   "choices": [
    {
     "label": "אני לוקח",
     "hint": "בעיטה ולחץ",
     "text": "הרמת יד. מהיום זה עליך — כולל הפעם שתחטיא בדקה 90.",
     "fx": {
      "attrs": [
       [
        "shooting",
        1.4
       ],
       [
        "mental",
        0.8
       ]
      ],
      "flag": "penalty_taker",
      "rep": 3,
      "trust": 4
     }
    },
    {
     "label": "לתת ל{mate}",
     "hint": "בלי לחץ",
     "text": "הצבעת עליו. הוא הודה לך, ואתה לא ישנת פחות טוב בלילה.",
     "fx": {
      "morale": 3,
      "trust": 1
     }
    }
   ]
  },
  {
   "eid": "p_new_manager",
   "title": "מאמן חדש נכנס",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.8,
   "cooldown": 34,
   "when": {
    "needs_club": true,
    "trust_max": 45
   },
   "body": "פיטרו את המאמן. {manager} נכנס במקומו, ובפגישה הראשונה הוא אומר:\n\"אני מתחיל מדף חלק. כולם מתחילים מאפס אצלי.\"",
   "choices": [
    {
     "label": "להתאמן כאילו אתה חדש בקבוצה",
     "hint": "אמון מאפס",
     "text": "היית הראשון בשדה והאחרון שיצא. הוא שם לב בשבוע הראשון.",
     "fx": {
      "trust": 14,
      "fitness": -8,
      "attr": [
       "physical",
       0.6
      ]
     }
    },
    {
     "label": "לבקש פגישה ולשאול מה התפקיד שלך",
     "hint": "בגרות",
     "text": "נכנסת למשרד ושאלת ישירות. הוא כיבד את זה, גם אם לא הבטיח כלום.",
     "fx": {
      "trust": 8,
      "attr": [
       "mental",
       1.0
      ],
      "morale": 4
     }
    },
    {
     "label": "לחכות ולראות",
     "hint": "בלי סיכון",
     "text": "לא עשית כלום מיוחד. הוא גם לא.",
     "fx": {
      "morale": -2
     }
    }
   ]
  },
  {
   "eid": "p_dropped_publicly",
   "title": "הוצאת מההרכב בעיתון",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.4,
   "cooldown": 24,
   "when": {
    "needs_club": true,
    "form_max": 45
   },
   "body": "גילית שאתה מחוץ להרכב מכתבה באתר, לפני ש{manager} אמר לך מילה.\nהכותרת: \"{me} מאבד את המקום\".",
   "choices": [
    {
     "label": "להיכנס למשרד ולדרוש הסבר",
     "hint": "עימות",
     "text": "אמרת לו שזה לא בסדר. הוא הסכים שזה לא בסדר, ולא שינה כלום.",
     "fx": {
      "trust": -4,
      "morale": 5,
      "attr": [
       "mental",
       0.6
      ]
     }
    },
    {
     "label": "לענות במגרש",
     "hint": "כושר",
     "text": "לא אמרת מילה. במשחק הבא נכנסת ורצת כאילו גנבו לך משהו.",
     "fx": {
      "form": 14,
      "sharpness": 5,
      "trust": 3,
      "morale": -3
     }
    },
    {
     "label": "לדבר לתקשורת",
     "hint": "מסוכן",
     "text": "אמרת לכתב מה שחשבת. הכותרת הייתה גדולה יותר מהמשחק הבא שלך.",
     "fx": {
      "trust": -12,
      "rep": 5,
      "media": 6,
      "fans": 3
     }
    }
   ]
  },
  {
   "eid": "p_captain_challenge",
   "title": "מאבק על הסרט",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 45,
   "when": {
    "needs_club": true,
    "overall_min": 68,
    "not_flag": "captain"
   },
   "body": "הקפטן נפצע לחודשיים. שני שמות עולים בחדר ההלבשה — שלך ושל {mate}.",
   "choices": [
    {
     "label": "לדבר עם {manager} ולבקש",
     "hint": "יוזמה",
     "text": "נכנסת ואמרת שאתה רוצה. הוא העריך את הישירות.",
     "fx": {
      "trust": 6,
      "rep": 3,
      "flag": "captain_bid"
     }
    },
    {
     "label": "לתמוך ב{mate}",
     "hint": "חדר הלבשה",
     "text": "אמרת בקול שהוא הבחירה הנכונה. הוא לא שכח את זה.",
     "fx": {
      "morale": 6,
      "trust": 4,
      "trait": "loyal"
     }
    }
   ]
  },
  {
   "eid": "p_fan_confrontation",
   "title": "אוהד בחניון",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.0,
   "cooldown": 30,
   "when": {
    "needs_club": true,
    "form_max": 50
   },
   "body": "אחרי הפסד, אוהד מחכה לך בחניון ואומר לך בפנים כמה הוא חושב שאתה גרוע.\nיש שם טלפונים מצלמים.",
   "choices": [
    {
     "label": "לעצור ולדבר איתו",
     "hint": "אוהדים",
     "text": "עצרת. דיברתם שלוש דקות. הסרטון שהתפרסם שינה את מה שחשבו עליך.",
     "fx": {
      "fans": 8,
      "media": 4,
      "rep": 2,
      "morale": 3
     }
    },
    {
     "label": "להיכנס לאוטו ולסגור",
     "hint": "בלי סיכון",
     "text": "נסעת. זה נגמר שם, וגם לא נהיה טוב יותר.",
     "fx": {
      "fans": -3,
      "morale": -2
     }
    },
    {
     "label": "לענות לו",
     "hint": "מסוכן",
     "text": "עניתׂ לו משהו שלא כדאי לחזור עליו. זה היה באינטרנט תוך שעה.",
     "fx": {
      "fans": -10,
      "media": 5,
      "trust": -6,
      "trait": "hothead"
     }
    }
   ]
  },
  {
   "eid": "p_play_through_pain",
   "title": "לשחק על זריקה",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.2,
   "cooldown": 34,
   "when": {
    "needs_club": true,
    "fitness_max": 70
   },
   "body": "יש לך משהו בקרסול. הרופא אומר שאפשר לשחק עם זריקה, אבל לא ממליץ.\n{manager} אומר שהמשחק הזה גדול.",
   "choices": [
    {
     "label": "לשחק",
     "hint": "אמון עכשיו, גוף אחר כך",
     "text": "שיחקת. היה שווה 90 דקות ועלה יותר.",
     "fx": {
      "trust": 10,
      "injury": [
       2,
       "החמרה בקרסול"
      ],
      "resilience": -4,
      "rep": 2
     }
    },
    {
     "label": "לא לשחק",
     "hint": "גוף",
     "text": "אמרת שאתה לא מוכן. {manager} אמר \"בסדר\" בטון שאמר משהו אחר.",
     "fx": {
      "trust": -8,
      "fitness": 20,
      "resilience": 2
     }
    }
   ]
  },
  {
   "eid": "p_teammate_injury",
   "title": "הפציעה של {mate}",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 36,
   "when": {
    "needs_club": true,
    "has_mate": true
   },
   "body": "{mate} נשאר על הדשא ולא קם. שמעת את זה מהצד השני של המגרש.\nבחדר ההלבשה אחרי המשחק אף אחד לא דיבר.",
   "choices": [
    {
     "label": "לבקר אותו בבית החולים",
     "hint": "חדר הלבשה",
     "text": "ישבת איתו שעתיים. הקבוצה שמעה, וזה שינה משהו.",
     "fx": {
      "morale": 5,
      "trust": 5,
      "attr": [
       "mental",
       0.6
      ]
     }
    },
    {
     "label": "לקחת את המקום שלו ברצינות",
     "hint": "הזדמנות",
     "text": "לא נעים להודות, אבל זו הזדמנות. ניצלת אותה.",
     "fx": {
      "form": 10,
      "sharpness": 5,
      "morale": -3
     }
    }
   ]
  },
  {
   "eid": "p_wage_gap",
   "title": "מה שמישהו גילה על השכר",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.0,
   "cooldown": 40,
   "when": {
    "needs_club": true,
    "overall_min": 65,
    "has_mate": true
   },
   "body": "התפרסם דירוג שכר בקבוצה. {mate} מרוויח יותר ממך, ולפי כולם אתה טוב יותר.",
   "choices": [
    {
     "label": "לדרוש שיחה על החוזה",
     "hint": "כסף",
     "text": "ביקשת פגישה. הם אמרו \"בסוף העונה\", ורשמו שאתה לא רגוע.",
     "fx": {
      "trust": -5,
      "flag": "wants_raise",
      "morale": 3
     }
    },
    {
     "label": "לא להתעסק בזה",
     "hint": "ריכוז",
     "text": "אמרת לעצמך שהמספרים ידברו. זה עבד, פחות או יותר.",
     "fx": {
      "attr": [
       "mental",
       1.0
      ],
      "morale": -4
     }
    },
    {
     "label": "לדבר עם {mate}",
     "hint": "חדר הלבשה",
     "text": "שאלת אותו ישירות. הוא נבוך, וזה סגר את העניין בלי מרירות.",
     "fx": {
      "morale": 5,
      "trust": 2
     }
    }
   ]
  },
  {
   "eid": "p_slump",
   "title": "שישה משחקים בלי כלום",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.6,
   "cooldown": 26,
   "when": {
    "needs_club": true,
    "form_max": 42
   },
   "body": "שישה משחקים. אפס שערים, אפס בישולים, ציון ממוצע שאתה לא רוצה לראות.\nבעיתון כתבו שזה \"משבר\".",
   "choices": [
    {
     "label": "להישאר אחרי האימון כל יום",
     "hint": "עבודה",
     "text": "נשארת עם עוזר המאמן וסל כדורים. חודש. אחר כך זה חזר.",
     "fx": {
      "attr": [
       "shooting",
       1.6
      ],
      "form": 10,
      "trust": 6,
      "fitness": -6
     }
    },
    {
     "label": "לקחת שבוע לנשום",
     "hint": "ראש",
     "text": "יצאת מהבועה לכמה ימים. חזרת עם ראש נקי וגוף רענן.",
     "fx": {
      "morale": 10,
      "fitness": 15,
      "form": 6,
      "sharpness": -4
     }
    },
    {
     "label": "ללכת לפסיכולוג ספורט",
     "hint": "קריאת משחק",
     "text": "ישבת עם מישהו שידע לשאול. גילית שהבעיה לא הייתה ברגליים.",
     "fx": {
      "attr": [
       "mental",
       1.8
      ],
      "morale": 6,
      "form": 8
     }
    }
   ]
  },
  {
   "eid": "p_european_night",
   "title": "לילה אירופי",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.0,
   "cooldown": 40,
   "when": {
    "needs_club": true,
    "rep_min": 45,
    "table_top": 4
   },
   "body": "המנון, יציע מלא, ומצלמות מכל זווית.\nמהספסל אתה רואה שהיריבה רצינית יותר מכל מה שהכרת.",
   "choices": [
    {
     "label": "לשחק בלי פחד",
     "hint": "מוניטין",
     "text": "לקחת אחריות מהדקה הראשונה. אחרי המשחק ידעו את השם שלך בחו\"ל.",
     "fx": {
      "rep": 8,
      "form": 10,
      "morale": 8,
      "media": 4
     }
    },
    {
     "label": "להיצמד למשמעת הטקטית",
     "hint": "אמון",
     "text": "עשית בדיוק מה שביקשו. לא זרחת, וגם לא נכשלת.",
     "fx": {
      "trust": 8,
      "attr": [
       "mental",
       1.0
      ]
     }
    }
   ]
  },
  {
   "eid": "p_relegation_fight",
   "title": "קרב הישרדות",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.4,
   "cooldown": 30,
   "when": {
    "needs_club": true,
    "table_bottom": 15,
    "week_min": 25
   },
   "body": "חמישה משחקים לסוף, ו{club} במקום שאף אחד לא רוצה להיות בו.\nהאוהדים חיכו מחוץ למתחם האימונים. לא כדי לעודד.",
   "choices": [
    {
     "label": "לצאת לדבר איתם",
     "hint": "אוהדים ואומץ",
     "text": "יצאת לבד מול מאה איש כועסים. חלקם צעקו. בסוף מחאו כפיים.",
     "fx": {
      "fans": 12,
      "rep": 4,
      "morale": 5,
      "trait": "leader"
     }
    },
    {
     "label": "לכנס את הקבוצה בלי הצוות",
     "hint": "מנהיגות",
     "text": "סגרתם את הדלת ודיברתם שעה. מה שנאמר שם נשאר שם.",
     "fx": {
      "trust": 8,
      "morale": 8,
      "form": 8
     }
    },
    {
     "label": "להתרכז רק במשחק שלך",
     "hint": "אישי",
     "text": "עשית את שלך. חלק מהחבר'ה שמו לב שלא היית שם בשבילם.",
     "fx": {
      "form": 8,
      "morale": -4,
      "trust": -3
     }
    }
   ]
  },
  {
   "eid": "p_title_race",
   "title": "מרוץ אליפות",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.2,
   "cooldown": 40,
   "when": {
    "needs_club": true,
    "table_top": 2,
    "week_min": 28
   },
   "body": "שלוש נקודות מפרידות, ושישה משחקים נשארו.\nכל טעות שלך תהיה בכותרת, וכל רגע טוב ייזכר שנים.",
   "choices": [
    {
     "label": "לקחת אחריות",
     "hint": "לחץ, אבל תהילה",
     "text": "ביקשת את הכדור גם כשלא היה נוח. זה מה שזוכרים.",
     "fx": {
      "form": 12,
      "rep": 6,
      "trait": "clutch",
      "morale": 6
     }
    },
    {
     "label": "לתת לוותיקים להוביל",
     "hint": "בלי לחץ",
     "text": "עשית את התפקיד שלך בשקט. גם זה חלק מזה.",
     "fx": {
      "trust": 5,
      "morale": 3,
      "attr": [
       "mental",
       0.6
      ]
     }
    }
   ]
  },
  {
   "eid": "p_cup_final_pen",
   "title": "הפנדל בגמר",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 50,
   "when": {
    "needs_club": true,
    "flag": "penalty_taker"
   },
   "body": "גמר גביע, 1:1, דקה 88, והשופט מצביע על הנקודה.\nאתה הבועט. {stadium} שותק לגמרי.",
   "choices": [
    {
     "label": "לבעוט חזק לפינה",
     "hint": "הכל או כלום",
     "text": "פגעת בפנימי ופנימה. הקבוצה קברה אותך מתחת לגוף.",
     "fx": {
      "rep": 10,
      "morale": 15,
      "fans": 10,
      "form": 15,
      "honour": "שער הזכייה בגמר הגביע"
     }
    },
    {
     "label": "פאנקה",
     "hint": "ביטחון עצום",
     "text": "השוער התכופף מוקדם, והכדור נחת באמצע השער. חוצפה שנכנסה להיסטוריה.",
     "fx": {
      "rep": 12,
      "media": 8,
      "morale": 12,
      "trait": "clutch",
      "honour": "פאנקה בגמר הגביע"
     }
    },
    {
     "label": "לתת למישהו אחר",
     "hint": "בלי סיכון",
     "text": "מסרת את הכדור ל{mate} והסתובבת. הוא כבש, ואתה לא היית בתמונה.",
     "fx": {
      "morale": -5,
      "trust": -4
     }
    }
   ]
  },
  {
   "eid": "p_racism_stands",
   "title": "קריאות מהיציע",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 50,
   "when": {
    "needs_club": true
   },
   "body": "בחוץ, מפינת היציע, שמעת קריאות שאין להן מקום בשום מגרש.\nהשופט לא עצר. חלק מהשחקנים שמעו וחלק לא.",
   "choices": [
    {
     "label": "לעצור את המשחק ולסמן לשופט",
     "hint": "עמדה ברורה",
     "text": "עמדת ליד הקו עד שהשופט עצר. הקבוצה שלך באה ועמדה סביבך.",
     "fx": {
      "rep": 6,
      "media": 6,
      "morale": 4,
      "fans": 5,
      "attr": [
       "mental",
       1.0
      ]
     }
    },
    {
     "label": "להמשיך ולענות עם משחק",
     "hint": "אישי",
     "text": "כבשת וחגגת מולם. הם השתתקו, וזה גם סוג של תשובה.",
     "fx": {
      "form": 12,
      "morale": 6,
      "rep": 4
     }
    }
   ]
  },
  {
   "eid": "p_charity_visit",
   "title": "ביקור בבית חולים",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 40,
   "when": {
    "needs_club": true
   },
   "body": "המועדון מארגן ביקור במחלקת ילדים. זה ביום החופש שלך.",
   "choices": [
    {
     "label": "ללכת",
     "hint": "אוהדים ותקשורת",
     "text": "היית שם ארבע שעות במקום שעה. ילד אחד לא הרפה מהיד שלך.",
     "fx": {
      "fans": 8,
      "media": 4,
      "morale": 8,
      "rep": 2
     }
    },
    {
     "label": "לוותר ולנוח",
     "hint": "כושר",
     "text": "נשארת בבית. גופנית זה היה נכון.",
     "fx": {
      "fitness": 12,
      "fans": -4
     }
    }
   ]
  },
  {
   "eid": "p_gambling",
   "title": "האפליקציה בטלפון",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 45,
   "when": {
    "needs_club": true,
    "age_min": 19
   },
   "body": "מישהו בחדר ההלבשה הראה לך אפליקציית הימורים.\n\"רק בשביל העניין,\" הוא אמר. בשבוע האחרון פתחת אותה שמונה פעמים.",
   "choices": [
    {
     "label": "למחוק עכשיו",
     "hint": "ראש נקי",
     "text": "מחקת. שבועיים היה מוזר, ואז שכחת מזה לגמרי.",
     "fx": {
      "attr": [
       "mental",
       1.2
      ],
      "morale": 3,
      "business": 2
     }
    },
    {
     "label": "להמשיך בקטן",
     "hint": "מסוכן",
     "text": "\"בקטן\" הפך לסכומים שלא סיפרת עליהם לאף אחד.",
     "fx": {
      "money": -35000,
      "morale": -6,
      "attr": [
       "mental",
       -0.6
      ],
      "flag": "gambling"
     }
    }
   ]
  },
  {
   "eid": "p_doping_test",
   "title": "בדיקת סמים",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.2,
   "cooldown": 50,
   "when": {
    "needs_club": true
   },
   "body": "שני אנשים בחליפות מחכים לך אחרי האימון. בדיקה אקראית.\nאתה לוקח תוסף שקנית באינטרנט, ופתאום אתה לא בטוח מה יש בו.",
   "choices": [
    {
     "label": "להגיד להם מראש מה לקחת",
     "hint": "שקיפות",
     "text": "אמרת הכל. הרופא של המועדון הסביר לך למה אף פעם לא קונים באינטרנט.",
     "fx": {
      "trust": 5,
      "attr": [
       "mental",
       0.8
      ],
      "morale": -2
     }
    },
    {
     "label": "לא להגיד כלום",
     "hint": "הימור",
     "text": "לא אמרת. הבדיקה חזרה נקייה, ולא ישנת שבועיים.",
     "fx": {
      "morale": -8,
      "attr": [
       "mental",
       0.4
      ]
     }
    }
   ]
  },
  {
   "eid": "p_family_baby",
   "title": "לילות בלי שינה",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 60,
   "once": true,
   "when": {
    "age_min": 23
   },
   "body": "נולד לך ילד.\nהאושר אמיתי, וגם העובדה שלא ישנת שלוש שעות רצוף כבר חודש.",
   "choices": [
    {
     "label": "לקחת חופשת לידה קצרה",
     "hint": "משפחה",
     "text": "החסרת שני משחקים. {manager} הבין, האוהדים פחות.",
     "fx": {
      "morale": 12,
      "trust": -3,
      "fans": -2,
      "sharpness": -6
     }
    },
    {
     "label": "להמשיך לשחק כרגיל",
     "hint": "מקצוענות",
     "text": "שיחקת הכל. הציונים ירדו קצת, והבית לא ראה אותך.",
     "fx": {
      "fitness": -10,
      "form": -6,
      "trust": 5,
      "morale": -3
     }
    }
   ]
  },
  {
   "eid": "p_club_finance",
   "title": "המשכורות מתעכבות",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 40,
   "when": {
    "needs_club": true
   },
   "body": "המשכורת לא נכנסה. גם לא של אף אחד אחר.\nבהנהלה מדברים על \"עיכוב טכני\" בפעם השלישית החודש.",
   "choices": [
    {
     "label": "להוביל שביתת אימונים",
     "hint": "עימות",
     "text": "לא יצאתם לאימון. הכסף נכנס אחרי יומיים, וההנהלה זכרה מי ארגן.",
     "fx": {
      "board": -12,
      "trust": 4,
      "morale": 6,
      "rep": 3,
      "trait": "leader"
     }
    },
    {
     "label": "לחכות בשקט",
     "hint": "בלי סיכון",
     "text": "חיכית. זה הגיע באיחור של שלושה שבועות.",
     "fx": {
      "morale": -6,
      "board": 3
     }
    }
   ]
  },
  {
   "eid": "p_takeover",
   "title": "בעלים חדשים",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 45,
   "when": {
    "needs_club": true
   },
   "body": "{club} נמכר. הבעלים החדשים מדברים על \"פרויקט\" ועל \"שינוי כיוון\".\nאף אחד לא יודע מי נשאר.",
   "choices": [
    {
     "label": "להיפגש איתם ולהציג את עצמך",
     "hint": "פוליטיקה",
     "text": "נכנסת ראשון לפגישה. יצאת עם רושם טוב ועם מספר טלפון.",
     "fx": {
      "board": 10,
      "business": 4,
      "rep": 2
     }
    },
    {
     "label": "לשמור על הראש למטה",
     "hint": "מקצוענות",
     "text": "רק שיחקת. בסוף גם זה מדבר.",
     "fx": {
      "form": 6,
      "trust": 4
     }
    }
   ]
  },
  {
   "eid": "p_youth_mentor_role",
   "title": "הילד שמסתכל עליך",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 34,
   "when": {
    "needs_club": true,
    "age_min": 24,
    "has_mate": true
   },
   "body": "בן 17 מהנוער עלה להתאמן עם הבוגרים. הוא מחקה את החימום שלך בדיוק,\nוכשהוא חושב שאתה לא מסתכל הוא מנסה את התרגילים שלך.",
   "choices": [
    {
     "label": "לקחת אותו תחת חסותך",
     "hint": "אימון ומוניטין",
     "text": "לימדת אותו דברים שאף אחד לא לימד אותך. זה חזר אליך בכמה דרכים.",
     "fx": {
      "coaching": 6,
      "rep": 3,
      "morale": 5,
      "trust": 4
     }
    },
    {
     "label": "להתעלם — יש לך מספיק",
     "hint": "ריכוז",
     "text": "היית עסוק בעצמך. הוא הפסיק להסתכל אחרי חודש.",
     "fx": {
      "form": 4,
      "morale": -2
     }
    }
   ]
  },
  {
   "eid": "p_shirt_number_row",
   "title": "מישהו רוצה את המספר שלך",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 45,
   "when": {
    "needs_club": true,
    "has_mate": true
   },
   "body": "חתמו על שחקן חדש, והוא ביקש את מספר {number}.\nמנהל הציוד שאל אם זה בסדר מבחינתך.",
   "choices": [
    {
     "label": "לא לוותר",
     "hint": "המספר שלי",
     "text": "אמרת לא. הוא קיבל מספר אחר ולא לחץ את היד שלך שבועיים.",
     "fx": {
      "morale": 4,
      "trust": -2
     }
    },
    {
     "label": "לוותר תמורת תרומה לקהילה",
     "hint": "אוהדים",
     "text": "ויתרת בתנאי שהוא יתרום. הסיפור הגיע לעיתונות והיה נחמד לכולם.",
     "fx": {
      "fans": 6,
      "media": 4,
      "morale": 3,
      "money": 15000
     }
    }
   ]
  },
  {
   "eid": "p_tapped_up",
   "title": "פנייה מאחורי הגב",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 36,
   "when": {
    "needs_club": true,
    "rep_min": 40
   },
   "body": "מספר לא מוכר. בצד השני מישהו שמציג את עצמו כ\"מקורב\" למועדון אחר.\nהוא לא אומר איזה, ומדבר על סכומים.",
   "choices": [
    {
     "label": "להקשיב",
     "hint": "דלת פתוחה",
     "text": "הקשבת עשרים דקות. לא הבטחת כלום, וכבר לא היית באותו מקום.",
     "fx": {
      "flag": "tapped_up",
      "rep": 3,
      "morale": 4
     }
    },
    {
     "label": "לנתק ולספר למועדון",
     "hint": "נאמנות",
     "text": "ניתקת וסיפרת. {club} הגישו תלונה, ואתה קיבלת נקודות שאי אפשר לקנות.",
     "fx": {
      "trust": 12,
      "board": 8,
      "trait": "loyal",
      "fans": 5
     }
    }
   ]
  },
  {
   "eid": "p_transfer_request",
   "title": "לבקש לעזוב",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 40,
   "when": {
    "needs_club": true,
    "morale_max": 45,
    "rep_min": 35
   },
   "body": "אתה לא מאושר. אפשר להגיש בקשת העברה רשמית ולפתוח את הדלת בכוח —\nאבל ב{club} יזכרו את זה בין אם תעזוב ובין אם לא.",
   "choices": [
    {
     "label": "להגיש בקשה",
     "hint": "דלת יוצאת",
     "text": "הגשת. האוהדים גילו תוך שעה, והשיר עליך ביציע השתנה.",
     "fx": {
      "flag": "transfer_request",
      "fans": -14,
      "trust": -10,
      "morale": 8
     }
    },
    {
     "label": "לתת לזה עוד חצי עונה",
     "hint": "סבלנות",
     "text": "החלטת לחכות. אולי משהו ישתנה, אולי לא.",
     "fx": {
      "morale": -3,
      "trust": 4
     }
    }
   ]
  },
  {
   "eid": "p_gulf_money",
   "title": "הצעה מהמפרץ",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 45,
   "when": {
    "needs_club": true,
    "rep_min": 55,
    "age_min": 26
   },
   "body": "מועדון מהמפרץ מציע פי שלושה ממה שאתה מרוויח, לשלוש שנים.\nהרמה נמוכה יותר. הכסף לא.",
   "choices": [
    {
     "label": "לקחת את הכסף",
     "hint": "ביטחון כלכלי",
     "text": "חתמת. הבנק שמח, ואירופה הפסיקה להתקשר.",
     "fx": {
      "money": 2500000,
      "rep": -10,
      "morale": 6,
      "flag": "gulf_move"
     }
    },
    {
     "label": "לסרב — עוד לא",
     "hint": "שאפתנות",
     "text": "אמרת לא. הסוכן שלך שאל אם אתה בטוח. אמרת שכן, פעמיים.",
     "fx": {
      "rep": 4,
      "morale": -2,
      "attr": [
       "mental",
       1.0
      ]
     }
    }
   ]
  },
  {
   "eid": "p_national_debut",
   "title": "הבכורה בנבחרת",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 50,
   "once": true,
   "when": {
    "rep_min": 55
   },
   "body": "החולצה תלויה בתא עם השם שלך והמספר, וההמנון מתנגן בעוד עשרים דקות.\nאמא שלך ביציע, מקום ראשון בשורה עשירית.",
   "choices": [
    {
     "label": "לשיר את ההמנון בקול",
     "hint": "רגע",
     "text": "שרת ובכית קצת. המצלמה תפסה, וזה נשאר תמונה של הקריירה.",
     "fx": {
      "rep": 8,
      "morale": 15,
      "media": 5,
      "honour": "בכורה בנבחרת"
     }
    },
    {
     "label": "להתרכז במשחק",
     "hint": "מקצוענות",
     "text": "עצמת עיניים בהמנון וחשבת רק על ההתחלה. שיחקת טוב.",
     "fx": {
      "rep": 6,
      "form": 10,
      "attr": [
       "mental",
       1.0
      ],
      "honour": "בכורה בנבחרת"
     }
    }
   ]
  },
  {
   "eid": "p_tournament_squad",
   "title": "רשימת הטורניר",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 50,
   "when": {
    "rep_min": 62
   },
   "body": "מפרסמים היום את סגל הטורניר. אתה על הגבול.\nהסוכן אומר שאם תבקש — מאמן הנבחרת יקשיב.",
   "choices": [
    {
     "label": "להתקשר בעצמך",
     "hint": "יוזמה",
     "text": "התקשרת. הוא הופתע, וזה כנראה עזר יותר משהזיק.",
     "fx": {
      "rep": 5,
      "morale": 5,
      "media": 2
     }
    },
    {
     "label": "לחכות בשקט",
     "hint": "כבוד",
     "text": "לא עשית כלום. הרשימה יצאה, ואתה קראת אותה כמו כולם.",
     "fx": {
      "attr": [
       "mental",
       0.8
      ]
     }
    }
   ]
  },
  {
   "eid": "p_boot_deal_upgrade",
   "title": "שדרוג חוזה הנעליים",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 45,
   "when": {
    "rep_min": 50
   },
   "body": "החברה שמלבישה אותך רוצה לשדרג — דגם ייחודי, שם שלך על הצד.\nבתמורה: יום צילומים בכל חודש והתחייבות לשלוש שנים.",
   "choices": [
    {
     "label": "לחתום",
     "hint": "כסף וחשיפה",
     "text": "יש נעל עם השם שלך. ילדים בחנויות מסתכלים עליה.",
     "fx": {
      "money": 900000,
      "media": 8,
      "rep": 4,
      "trust": -2
     }
    },
    {
     "label": "לדרוש שיפור",
     "hint": "הימור",
     "text": "דרשת יותר. הם לקחו שבועיים לחשוב וחזרו עם פחות.",
     "fx": {
      "money": 450000,
      "business": 5,
      "media": 3
     }
    }
   ]
  },
  {
   "eid": "p_documentary",
   "title": "צוות צילום בבית",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.2,
   "cooldown": 50,
   "when": {
    "rep_min": 65
   },
   "body": "מפיקים רוצים לעשות סדרה תיעודית על העונה שלך.\nזה אומר מצלמה גם בימים שאתה לא רוצה שיראו.",
   "choices": [
    {
     "label": "להסכים לגישה מלאה",
     "hint": "הכל מצולם",
     "text": "הם צילמו גם את ההפסדים. הסדרה הייתה טובה בדיוק בגלל זה.",
     "fx": {
      "money": 620000,
      "media": 12,
      "rep": 7,
      "morale": -3,
      "trust": -3
     }
    },
    {
     "label": "רק ימי משחק",
     "hint": "גבולות",
     "text": "הגבלת אותם. יצא משהו נחמד ובינוני.",
     "fx": {
      "money": 260000,
      "media": 5,
      "rep": 2
     }
    }
   ]
  },
  {
   "eid": "p_pace_gone",
   "title": "הרגליים לא מגיעות",
   "stages": [
    "veteran"
   ],
   "weight": 2.6,
   "cooldown": 30,
   "when": {
    "age_min": 31
   },
   "body": "היה כדור לעומק שלפני שלוש שנים היית מגיע אליו בקלות.\nלא הגעת. ראית את זה, והספסל ראה גם.",
   "choices": [
    {
     "label": "לפצות בראש",
     "hint": "קריאת משחק",
     "text": "התחלת לזוז שנייה לפני. פתאום לא היה צריך לרוץ מהר.",
     "fx": {
      "attrs": [
       [
        "mental",
        2.0
       ],
       [
        "passing",
        0.8
       ]
      ],
      "morale": 3
     }
    },
    {
     "label": "לעבוד על הגוף כמו משוגע",
     "hint": "עוד שנה",
     "text": "הוספת שעתיים ביום. קנית לעצמך עוד עונה, ושילמת בברכיים.",
     "fx": {
      "attr": [
       "pace",
       1.2
      ],
      "resilience": -6,
      "fitness": -8,
      "trust": 4
     }
    }
   ]
  },
  {
   "eid": "p_deeper_role",
   "title": "לרדת אחורה",
   "stages": [
    "veteran"
   ],
   "weight": 2.2,
   "cooldown": 40,
   "when": {
    "age_min": 32,
    "needs_club": true,
    "position_in": [
     "ST",
     "AM",
     "LW",
     "RW",
     "CM"
    ]
   },
   "body": "{manager} מציע להזיז אותך עמדה אחורה.\n\"פחות ריצה, יותר מוח. יש לך עוד ארבע שנים שם.\"",
   "choices": [
    {
     "label": "להסכים",
     "hint": "להאריך קריירה",
     "text": "ירדת אחורה. תוך חודשיים הבנת שהוא צדק.",
     "fx": {
      "attrs": [
       [
        "passing",
        1.8
       ],
       [
        "defending",
        1.4
       ],
       [
        "mental",
        1.2
       ]
      ],
      "trust": 8
     }
    },
    {
     "label": "לסרב",
     "hint": "גאווה",
     "text": "אמרת שאתה {position} עד הסוף. הדקות התחילו להתקצר.",
     "fx": {
      "trust": -8,
      "morale": 5
     }
    }
   ]
  },
  {
   "eid": "p_testimonial",
   "title": "משחק לכבודך",
   "stages": [
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 60,
   "once": true,
   "when": {
    "age_min": 33,
    "rep_min": 50
   },
   "body": "{club} מציעים לארגן משחק לכבודך בסוף העונה.\nכל ההכנסות אליך, או לאן שתחליט.",
   "choices": [
    {
     "label": "לתרום הכל",
     "hint": "אוהדים",
     "text": "תרמת הכל למחלקת הנוער. השם שלך על המגרש שם עד היום.",
     "fx": {
      "fans": 18,
      "rep": 8,
      "morale": 12,
      "honour": "משחק כבוד — התרומה למחלקת הנוער"
     }
    },
    {
     "label": "לקחת את הכסף",
     "hint": "ביטחון",
     "text": "לקחת. אף אחד לא באמת שפט אותך, וגם לא שכחו.",
     "fx": {
      "money": 1200000,
      "fans": -3,
      "honour": "משחק כבוד ב{stadium}"
     }
    }
   ]
  },
  {
   "eid": "p_badges_course",
   "title": "קורס המאמנים",
   "stages": [
    "veteran"
   ],
   "weight": 2.0,
   "cooldown": 36,
   "when": {
    "age_min": 30
   },
   "body": "פתחו קורס תעודת אימון, ואפשר להתחיל אותו כבר עכשיו —\nאבל זה שלושה ערבים בשבוע, על חשבון ההתאוששות.",
   "choices": [
    {
     "label": "להירשם",
     "hint": "היום שאחרי",
     "text": "ישבת בכיתה עם שחקנים שפרשו לפניך. הבנת כמה אתה לא יודע.",
     "fx": {
      "coaching": 9,
      "fitness": -8,
      "attr": [
       "mental",
       0.8
      ]
     }
    },
    {
     "label": "לא עכשיו",
     "hint": "כדורגל",
     "text": "אמרת שקודם תשחק. לזה יהיה זמן.",
     "fx": {
      "fitness": 10,
      "form": 4
     }
    }
   ]
  },
  {
   "eid": "p_last_dance",
   "title": "העונה האחרונה",
   "stages": [
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 50,
   "when": {
    "age_min": 34
   },
   "body": "אתה יודע שזו כנראה האחרונה. אף אחד לא אמר את זה בקול.\nהשאלה היא איך אתה רוצה שיזכרו את השנה הזאת.",
   "choices": [
    {
     "label": "לשחק כל דקה שנותנים",
     "hint": "עד הטיפה",
     "text": "שיחקת עם כאבים ובלי להתלונן. הגוף שילם, והזיכרון נשאר.",
     "fx": {
      "trust": 10,
      "rep": 4,
      "resilience": -8,
      "morale": 8
     }
    },
    {
     "label": "להקדיש את השנה לצעירים",
     "hint": "מורשת",
     "text": "בכל אימון היית ליד מישהו בן 18. שלושה מהם הפכו לשחקנים.",
     "fx": {
      "coaching": 10,
      "trust": 8,
      "rep": 3,
      "trait": "leader"
     }
    }
   ]
  },
  {
   "eid": "p_knee_verdict",
   "title": "מה שהצילום הראה",
   "stages": [
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 50,
   "when": {
    "age_min": 32
   },
   "body": "רופא הקבוצה שם את הצילום על המסך ולא ניסה לרכך:\n\"הסחוס בברך הזאת נגמר. אתה יכול להמשיך, אבל תשלם על זה כל החיים.\"",
   "choices": [
    {
     "label": "להמשיך",
     "hint": "עוד כדורגל, פחות אחר כך",
     "text": "המשכת. עוד שנתיים על המגרש, ומדרגות שלא תאהב בגיל חמישים.",
     "fx": {
      "resilience": -12,
      "trust": 6,
      "morale": 4,
      "flag": "bad_knee"
     }
    },
    {
     "label": "לשמוע בקולו",
     "hint": "גוף",
     "text": "הורדת עומסים בחצי. פחות דקות, יותר שנים.",
     "fx": {
      "fitness": 20,
      "resilience": 5,
      "trust": -5
     }
    }
   ]
  },
  {
   "eid": "m_first_team_talk",
   "title": "נאום ההפסקה הראשון",
   "stages": [
    "coach",
    "manager"
   ],
   "weight": 2.4,
   "cooldown": 26,
   "when": {
    "needs_club": true
   },
   "body": "0:2 בהפסקה. אחת עשרה זוגות עיניים מחכות לראות מי אתה.",
   "choices": [
    {
     "label": "לצעוק",
     "hint": "אנרגיה מיידית",
     "text": "בעטת בארגז וצעקת. הם יצאו רותחים וכבשו תוך שש דקות.",
     "fx": {
      "trust": 5,
      "board": 3,
      "morale": 5
     }
    },
    {
     "label": "לדבר בשקט ולשנות מערך",
     "hint": "טקטיקה",
     "text": "לא הרמת קול. ציירת שני חצים על הלוח, וזה הספיק.",
     "fx": {
      "coaching": 5,
      "trust": 8,
      "board": 5
     }
    },
    {
     "label": "לתת להם לדבר בעצמם",
     "hint": "אחריות",
     "text": "יצאת מהחדר לחמש דקות. מה שקרה שם היה שווה יותר מכל נאום.",
     "fx": {
      "trust": 10,
      "morale": 6,
      "coaching": 3
     }
    }
   ]
  },
  {
   "eid": "m_press_ambush",
   "title": "מלכודת במסיבת עיתונאים",
   "stages": [
    "manager"
   ],
   "weight": 2.2,
   "cooldown": 22,
   "when": {
    "needs_club": true
   },
   "body": "כתב שואל: \"אתה חושב ש{opponent} פשוט טובים יותר, או שהבעיה היא אתה?\"\nהחדר מחכה.",
   "choices": [
    {
     "label": "לקחת אחריות מלאה",
     "hint": "כבוד",
     "text": "אמרת שזו האחריות שלך. ההנהלה שמעה, השחקנים גם.",
     "fx": {
      "board": 6,
      "trust": 10,
      "media": 4
     }
    },
    {
     "label": "להגן על השחקנים בהתקפה",
     "hint": "חדר הלבשה",
     "text": "התקפת את השאלה ואת מי ששאל. חדר ההלבשה עמד מאחוריך.",
     "fx": {
      "trust": 12,
      "media": 6,
      "board": -5,
      "fans": 4
     }
    },
    {
     "label": "לתת תשובה טכנית ומשעממת",
     "hint": "בלי כותרות",
     "text": "דיברת על מבנים וריווח. אף אחד לא כתב כלום.",
     "fx": {
      "media": -2,
      "board": 2
     }
    }
   ]
  },
  {
   "eid": "m_agent_pressure",
   "title": "סוכן בדלת",
   "stages": [
    "manager"
   ],
   "weight": 2.0,
   "cooldown": 30,
   "when": {
    "needs_club": true
   },
   "body": "סוכן של אחד השחקנים הגיע בלי לתאם.\n\"הוא לא מקבל דקות. או שזה משתנה, או שאנחנו מדברים עם אחרים.\"",
   "choices": [
    {
     "label": "לזרוק אותו מהמשרד",
     "hint": "סמכות",
     "text": "אמרת לו איפה הדלת. השחקן קיבל את המסר, לטוב ולרע.",
     "fx": {
      "trust": 6,
      "board": 3,
      "morale": -3
     }
    },
    {
     "label": "להסכים לתת לו דקות",
     "hint": "שקט",
     "text": "נתת לו לשחק. חדר ההלבשה שם לב שאפשר ללחוץ עליך.",
     "fx": {
      "trust": -8,
      "board": -3,
      "morale": 4
     }
    },
    {
     "label": "להציע עסקה: דקות תמורת ביצועים",
     "hint": "ניהול",
     "text": "הצבת תנאים ברורים. הוא עמד בהם, וזה עבד לשניכם.",
     "fx": {
      "coaching": 4,
      "trust": 4,
      "board": 4
     }
    }
   ]
  },
  {
   "eid": "m_scout_report",
   "title": "דוח סקאוטינג",
   "stages": [
    "manager",
    "director"
   ],
   "weight": 2.0,
   "cooldown": 28,
   "when": {
    "needs_club": true
   },
   "body": "הסקאוט מניח תיק על השולחן.\n\"בן 19, ליגה שלישית באירופה. או שהוא יהיה שווה עשרה מיליון, או כלום.\"",
   "choices": [
    {
     "label": "לחתום עליו",
     "hint": "הימור",
     "text": "חתמתם. חצי מההנהלה חשבה שאתה משוגע.",
     "fx": {
      "board": -4,
      "coaching": 3,
      "flag": "gem_signed"
     }
    },
    {
     "label": "לשלוח אותו להשאלה קודם",
     "hint": "זהירות",
     "text": "השאלתם אותו לשנה. הוא חזר מוכן יותר, ויקר יותר.",
     "fx": {
      "board": 4,
      "business": 3
     }
    },
    {
     "label": "לוותר",
     "hint": "בלי סיכון",
     "text": "ויתרתם. אחרי שנתיים ראית אותו במדים אחרים, ולא היה נעים.",
     "fx": {
      "board": 2,
      "coaching": -2
     }
    }
   ]
  },
  {
   "eid": "m_veteran_bench",
   "title": "להושיב אגדה",
   "stages": [
    "manager"
   ],
   "weight": 1.8,
   "cooldown": 34,
   "when": {
    "needs_club": true,
    "has_mate": true
   },
   "body": "{mate} שיחק כאן עשור. הרגליים נגמרו, האהבה של האוהדים לא.\nצריך להוציא אותו מההרכב.",
   "choices": [
    {
     "label": "להגיד לו פנים אל פנים",
     "hint": "כבוד",
     "text": "ישבתם שעה. הוא לא הסכים, אבל הוא כיבד את זה שבאת.",
     "fx": {
      "trust": 8,
      "fans": -4,
      "coaching": 3
     }
    },
    {
     "label": "להוציא בלי לדבר",
     "hint": "מהיר",
     "text": "הוא גילה מהרשימה. חדר ההלבשה למד משהו עליך.",
     "fx": {
      "trust": -12,
      "fans": -8,
      "board": 2
     }
    },
    {
     "label": "להשאיר אותו בהרכב",
     "hint": "רגש",
     "text": "לא הצלחת. הוא שיחק, והקבוצה שילמה.",
     "fx": {
      "fans": 6,
      "board": -6,
      "trust": -4
     }
    }
   ]
  },
  {
   "eid": "m_derby_build",
   "title": "שבוע הדרבי — מהצד של המאמן",
   "stages": [
    "manager"
   ],
   "weight": 2.0,
   "cooldown": 26,
   "when": {
    "needs_club": true
   },
   "body": "העיר לא מדברת על שום דבר אחר.\nהמאמן של {opponent} אמר שאתה \"מאמן של טבלה, לא של משחקים גדולים\".",
   "choices": [
    {
     "label": "לענות לו",
     "hint": "אש",
     "text": "ענית בכותרת גדולה. עכשיו אסור לך להפסיד.",
     "fx": {
      "media": 6,
      "fans": 6,
      "board": -3,
      "trust": 4
     }
    },
    {
     "label": "לשתוק ולעבוד",
     "hint": "מקצוענות",
     "text": "לא אמרת מילה כל השבוע. ההכנה הייתה הטובה ביותר שלך.",
     "fx": {
      "coaching": 5,
      "trust": 6,
      "board": 3
     }
    }
   ]
  },
  {
   "eid": "m_january_window",
   "title": "חלון ינואר",
   "stages": [
    "manager",
    "director"
   ],
   "weight": 2.2,
   "cooldown": 40,
   "when": {
    "needs_club": true,
    "week_min": 20,
    "week_max": 26
   },
   "body": "ההנהלה שמה על השולחן סכום מוגבל.\nאפשר לחזק עמדה אחת, או לשמור את הכסף לקיץ.",
   "choices": [
    {
     "label": "לחזק עכשיו",
     "hint": "העונה הזאת",
     "text": "הבאתם שחקן. הוא נתן בדיוק את מה שהיה חסר בחצי השנה.",
     "fx": {
      "board": -5,
      "trust": 8,
      "coaching": 3
     }
    },
    {
     "label": "לשמור לקיץ",
     "hint": "העונה הבאה",
     "text": "לא עשיתם כלום. חדר ההלבשה הבין שההנהלה לא מאמינה מספיק.",
     "fx": {
      "board": 6,
      "trust": -6,
      "business": 3
     }
    }
   ]
  },
  {
   "eid": "m_fan_protest",
   "title": "מחאה ביציע",
   "stages": [
    "manager"
   ],
   "weight": 1.8,
   "cooldown": 30,
   "when": {
    "needs_club": true,
    "table_bottom": 12
   },
   "body": "בדקה 70 היציע הצפוני התחיל לשיר נגדך.\nבסוף המשחק חיכו במגרש החניה עם שלטים.",
   "choices": [
    {
     "label": "לצאת ולעמוד מולם",
     "hint": "אומץ",
     "text": "עמדת שם עשרים דקות וספגת. חלק מהם הפסיקו לצעוק.",
     "fx": {
      "fans": 8,
      "media": 5,
      "board": 3,
      "morale": -4
     }
    },
    {
     "label": "לצאת מהיציאה האחורית",
     "hint": "בלי עימות",
     "text": "יצאת בלי שראו. למחרת זו הייתה הכותרת.",
     "fx": {
      "fans": -8,
      "media": -3
     }
    }
   ]
  },
  {
   "eid": "m_academy_push",
   "title": "לפתוח את השער לנוער",
   "stages": [
    "manager"
   ],
   "weight": 1.8,
   "cooldown": 40,
   "when": {
    "needs_club": true
   },
   "body": "יש שלושה בני 18 שמוכנים. לשלב אותם עכשיו זה סיכון בטבלה,\nולהמתין זה אולי לאבד אותם.",
   "choices": [
    {
     "label": "לשלב את שלושתם",
     "hint": "עתיד",
     "text": "שילבת. היו טעויות, והיו גם שני משחקים שלא תשכח.",
     "fx": {
      "board": -6,
      "fans": 8,
      "coaching": 6,
      "flag": "youth_project"
     }
    },
    {
     "label": "אחד, בזהירות",
     "hint": "איזון",
     "text": "העלית אחד. הוא לא איכזב, והשניים האחרים המשיכו לחכות.",
     "fx": {
      "coaching": 3,
      "board": 2,
      "trust": 3
     }
    }
   ]
  },
  {
   "eid": "m_ultimatum",
   "title": "אולטימטום מההנהלה",
   "stages": [
    "manager"
   ],
   "weight": 2.0,
   "cooldown": 30,
   "when": {
    "needs_club": true,
    "table_bottom": 13
   },
   "body": "יו\"ר המועדון ניסח את זה יפה, אבל המשמעות ברורה:\n\"שלושה משחקים. אנחנו רוצים לראות שינוי.\"",
   "choices": [
    {
     "label": "לשנות שיטה לגמרי",
     "hint": "הימור גדול",
     "text": "הפכת את הכל. או שזה יעבוד, או שזה ייגמר מהר.",
     "fx": {
      "coaching": 6,
      "board": -3,
      "trust": -4,
      "flag": "system_change"
     }
    },
    {
     "label": "לבקש עוד זמן",
     "hint": "כנות",
     "text": "אמרת בדיוק כמה זמן צריך ולמה. הם הקשיבו, ורשמו תאריך.",
     "fx": {
      "board": 5,
      "media": 2
     }
    },
    {
     "label": "לאיים בהתפטרות",
     "hint": "כוח",
     "text": "אמרת שאם אין אמון — הנה המפתחות. הם נסוגו, והיחסים לא חזרו.",
     "fx": {
      "board": -10,
      "trust": 8,
      "media": 6
     }
    }
   ]
  },
  {
   "eid": "d_sell_the_star",
   "title": "למכור את הכוכב",
   "stages": [
    "director",
    "owner"
   ],
   "weight": 2.2,
   "cooldown": 34,
   "when": {
    "needs_club": true
   },
   "body": "הצעה על השולחן שמכסה שנתיים של תקציב.\nהמאמן אומר שבלעדיו אין קבוצה. החשב אומר שבלי הכסף אין מועדון.",
   "choices": [
    {
     "label": "למכור",
     "hint": "כסף",
     "text": "מכרת. הטבלה שילמה, המאזן נשם.",
     "fx": {
      "board": 10,
      "fans": -12,
      "business": 6
     }
    },
    {
     "label": "לסרב",
     "hint": "ספורט",
     "text": "סירבת. האוהדים אהבו, החשב הפסיק לישון.",
     "fx": {
      "fans": 14,
      "board": -8,
      "trust": 6
     }
    },
    {
     "label": "למכור בתנאי שנקבל שניים במקום",
     "hint": "מו\"מ",
     "text": "סגרת עסקה משולבת. אף אחד לא היה מרוצה לגמרי, וזה בדרך כלל סימן טוב.",
     "fx": {
      "business": 8,
      "board": 5,
      "fans": -3
     }
    }
   ]
  },
  {
   "eid": "d_new_manager_hire",
   "title": "לבחור מאמן",
   "stages": [
    "director",
    "owner"
   ],
   "weight": 2.0,
   "cooldown": 40,
   "when": {
    "needs_club": true
   },
   "body": "שלושה מועמדים: שם גדול עם אגו גדול, מאמן צעיר עם רעיונות,\nואיש מקצוע אפור שעושה עבודה.",
   "choices": [
    {
     "label": "השם הגדול",
     "hint": "מיידי",
     "text": "מכירת הכרטיסים זינקה. גם החיכוכים.",
     "fx": {
      "fans": 12,
      "board": 4,
      "trust": -4
     }
    },
    {
     "label": "הצעיר",
     "hint": "פרויקט",
     "text": "לקחת סיכון. אם זה יעבוד, ידברו על זה עשור.",
     "fx": {
      "board": -4,
      "coaching": 5,
      "flag": "young_coach"
     }
    },
    {
     "label": "האפור",
     "hint": "יציבות",
     "text": "אף אחד לא התלהב. הקבוצה גם לא ירדה.",
     "fx": {
      "board": 8,
      "fans": -3
     }
    }
   ]
  },
  {
   "eid": "d_stadium_plan",
   "title": "תוכנית האצטדיון",
   "stages": [
    "director",
    "owner"
   ],
   "weight": 1.8,
   "cooldown": 45,
   "when": {
    "needs_club": true
   },
   "body": "אדריכל הביא שתי תוכניות: הרחבה של הקיים, או מגרש חדש מחוץ לעיר.\nהאוהדים הוותיקים כבר שמעו ולא אוהבים.",
   "choices": [
    {
     "label": "להרחיב את הקיים",
     "hint": "שורשים",
     "text": "נשארתם בבית. פחות מקומות, יותר נשמה.",
     "fx": {
      "fans": 12,
      "board": -3
     }
    },
    {
     "label": "לבנות חדש",
     "hint": "כסף",
     "text": "בניתם. הקהל הכפיל את עצמו, וחלק מהוותיקים לא באו יותר.",
     "fx": {
      "board": 12,
      "fans": -10,
      "business": 8
     }
    }
   ]
  },
  {
   "eid": "d_youth_investment",
   "title": "כמה שמים בנוער",
   "stages": [
    "director",
    "owner"
   ],
   "weight": 1.8,
   "cooldown": 40,
   "when": {
    "needs_club": true
   },
   "body": "אפשר להזרים את התקציב לסגל הבוגר, או להשקיע במחלקת הנוער\nולראות תוצאה בעוד חמש שנים.",
   "choices": [
    {
     "label": "נוער",
     "hint": "טווח ארוך",
     "text": "השקעת בילדים. בעוד חמש שנים מישהו יגיד שהיית חכם.",
     "fx": {
      "board": -5,
      "fans": 6,
      "coaching": 6,
      "flag": "youth_project"
     }
    },
    {
     "label": "הסגל הבוגר",
     "hint": "עכשיו",
     "text": "חיזקתם עכשיו. העונה הזאת נראית טוב יותר.",
     "fx": {
      "board": 6,
      "fans": 4
     }
    }
   ]
  },
  {
   "eid": "u_pundit_hot_take",
   "title": "אמירה באולפן",
   "stages": [
    "pundit"
   ],
   "weight": 2.2,
   "cooldown": 24,
   "body": "המנחה מסתובב אליך ושואל על מאמן שאתה מכיר אישית, שעל סף פיטורים.",
   "choices": [
    {
     "label": "להגיד את האמת",
     "hint": "אמינות",
     "text": "אמרת מה שחשבת. הוא לא דיבר איתך שנה, והצופים סמכו עליך יותר.",
     "fx": {
      "media": 8,
      "rep": 5,
      "money": 40000
     }
    },
    {
     "label": "להגן עליו",
     "hint": "נאמנות",
     "text": "הגנת עליו באולפן. הוא זכר, והרייטינג לא.",
     "fx": {
      "media": -3,
      "rep": 2,
      "morale": 5
     }
    }
   ]
  },
  {
   "eid": "u_pundit_offer",
   "title": "הצעה מרשת גדולה",
   "stages": [
    "pundit",
    "legend"
   ],
   "weight": 1.6,
   "cooldown": 45,
   "when": {
    "rep_min": 55
   },
   "body": "רשת בינלאומית מציעה לך מקום קבוע בפאנל, באנגלית, בשידור לכל העולם.",
   "choices": [
    {
     "label": "לקחת",
     "hint": "קריירה שנייה",
     "text": "עברת לשידור הגדול. הפכת לפרצוף שמכירים בכל מקום.",
     "fx": {
      "money": 1800000,
      "media": 12,
      "rep": 8
     }
    },
    {
     "label": "להישאר מקומי",
     "hint": "בית",
     "text": "נשארת. פחות כסף, יותר אנשים שאומרים לך שלום ברחוב.",
     "fx": {
      "fans": 8,
      "morale": 8,
      "money": 300000
     }
    }
   ]
  },
  {
   "eid": "a_agent_first_client",
   "title": "הלקוח הראשון",
   "stages": [
    "agent"
   ],
   "weight": 2.4,
   "cooldown": 30,
   "body": "בן 17 עם משפחה שלא מבינה כלום בחוזים יושב מולך.\nאתה יכול לקחת אחוזים רגילים, או לנצל את זה.",
   "choices": [
    {
     "label": "תנאים הוגנים",
     "hint": "מוניטין",
     "text": "לקחת מה שמגיע ולא יותר. תוך שנתיים שלושה שחקנים באו בגללו.",
     "fx": {
      "rep": 8,
      "business": 6,
      "money": 120000
     }
    },
    {
     "label": "לקחת יותר",
     "hint": "כסף מהיר",
     "text": "החתמת אותו על משהו שהוא לא הבין. הרווחת, וזה יצא לאור בסוף.",
     "fx": {
      "money": 700000,
      "rep": -10,
      "business": 4
     }
    }
   ]
  },
  {
   "eid": "a_big_transfer",
   "title": "העסקה הגדולה",
   "stages": [
    "agent"
   ],
   "weight": 2.0,
   "cooldown": 34,
   "when": {
    "rep_min": 40
   },
   "body": "שני מועדונים רוצים את הלקוח שלך. אחד משלם יותר, השני יותר נכון לו.",
   "choices": [
    {
     "label": "לדחוף לכסף",
     "hint": "עמלה",
     "text": "סגרת עם המשלם. העמלה הייתה יפה, והוא ישב שנה על הספסל.",
     "fx": {
      "money": 1600000,
      "rep": -6,
      "business": 6
     }
    },
    {
     "label": "לדחוף למה שנכון לו",
     "hint": "טווח ארוך",
     "text": "שלחת אותו למקום הנכון. הוא פרץ, וכולם ידעו מי הסוכן.",
     "fx": {
      "money": 500000,
      "rep": 10,
      "business": 4
     }
    }
   ]
  },
  {
   "eid": "o_owner_ticket_prices",
   "title": "מחירי הכרטיסים",
   "stages": [
    "owner"
   ],
   "weight": 2.0,
   "cooldown": 40,
   "when": {
    "needs_club": true
   },
   "body": "החשב מציע להעלות מחירי מנוי ב-15 אחוז. המספרים תומכים.\nהאוהדים כבר שמעו שמועה.",
   "choices": [
    {
     "label": "להעלות",
     "hint": "הכנסה",
     "text": "העלית. הקופה נשמה, והיציע הצפוני הוציא שלט.",
     "fx": {
      "board": 10,
      "fans": -14,
      "business": 5
     }
    },
    {
     "label": "להקפיא לשלוש שנים",
     "hint": "אוהדים",
     "text": "הודעת על הקפאה. זה עלה כסף, וקנה משהו שלא קונים בכסף.",
     "fx": {
      "fans": 18,
      "board": -6,
      "rep": 4
     }
    }
   ]
  },
  {
   "eid": "l_legend_statue",
   "title": "הפסל",
   "stages": [
    "legend"
   ],
   "weight": 1.4,
   "cooldown": 60,
   "once": true,
   "body": "{club} רוצים להציב פסל שלך מחוץ ל{stadium}.\nהפסל בגובה שלושה מטרים, והם שואלים איזו תנוחה.",
   "choices": [
    {
     "label": "החגיגה מהגמר",
     "hint": "רגע",
     "text": "בחרת את הרגע ההוא. ילדים מצטלמים שם כל שבת.",
     "fx": {
      "fans": 12,
      "rep": 6,
      "morale": 15,
      "honour": "פסל מחוץ ל{stadium}"
     }
    },
    {
     "label": "פשוט עומד, עם הכדור",
     "hint": "צנוע",
     "text": "בחרת משהו שקט. יצא יפה יותר ממה שחשבו.",
     "fx": {
      "fans": 8,
      "morale": 12,
      "honour": "פסל מחוץ ל{stadium}"
     }
    }
   ]
  },
  {
   "eid": "y_first_away",
   "title": "הנסיעה הראשונה",
   "stages": [
    "youth"
   ],
   "weight": 2.0,
   "cooldown": 34,
   "body": "אוטובוס בשש בבוקר, שלוש שעות דרך, ומגרש שאף אחד לא מכיר.\nחצי מהקבוצה ישן, חצי צועק.",
   "choices": [
    {
     "label": "לישון ולשמור כוח",
     "hint": "כושר",
     "text": "ישנת את כל הדרך ויצאת רענן. שיחקת טוב.",
     "fx": {
      "fitness": 10,
      "form": 6
     }
    },
    {
     "label": "להישאר ער עם החבר'ה",
     "hint": "חדר הלבשה",
     "text": "צחקתם שלוש שעות. הקבוצה יצאה למגרש כמו קבוצה.",
     "fx": {
      "morale": 8,
      "trust": 3,
      "fitness": -6
     }
    }
   ]
  },
  {
   "eid": "y_favourite",
   "title": "המאמן שיש לו מועדפים",
   "stages": [
    "youth"
   ],
   "weight": 2.0,
   "cooldown": 30,
   "body": "יש ילד אחד ש{manager} מעלה בכל משחק, גם כשהוא רע.\nכולם רואים, אף אחד לא אומר.",
   "choices": [
    {
     "label": "לדבר עם המאמן",
     "hint": "אומץ",
     "text": "שאלת אותו ישירות. הוא נעלב, ואז התחיל להסתכל אחרת על שניכם.",
     "fx": {
      "trust": -4,
      "attr": [
       "mental",
       1.2
      ],
      "morale": 3
     }
    },
    {
     "label": "לעבוד עד שאי אפשר להתעלם",
     "hint": "עבודה",
     "text": "הפכת את עצמך לבעיה שלו. תוך חודשיים שיחקת.",
     "fx": {
      "attr": [
       "physical",
       1.2
      ],
      "trust": 6,
      "form": 8
     }
    }
   ]
  },
  {
   "eid": "y_lost_final",
   "title": "הפסד בגמר",
   "stages": [
    "youth"
   ],
   "weight": 2.0,
   "cooldown": 40,
   "body": "הפסדתם 1:0 בדקה האחרונה. חצי מהקבוצה בוכה על הדשא,\nוההורים ביציע לא יודעים לאן להסתכל.",
   "choices": [
    {
     "label": "להרים את החבר'ה",
     "hint": "מנהיגות",
     "text": "עברת אחד־אחד והרמת אותם. בגיל הזה זה נדיר.",
     "fx": {
      "attr": [
       "mental",
       1.4
      ],
      "trust": 5,
      "trait": "leader"
     }
    },
    {
     "label": "לשבת לבד ולעכל",
     "hint": "אופי",
     "text": "ישבת על הדשא עשרים דקות. משהו בפנים התקשה שם.",
     "fx": {
      "resilience": 4,
      "attr": [
       "mental",
       1.0
      ],
      "morale": -5
     }
    }
   ]
  },
  {
   "eid": "y_kit_money",
   "title": "הנעליים שנקרעו",
   "stages": [
    "youth"
   ],
   "weight": 1.8,
   "cooldown": 40,
   "body": "הנעליים נקרעו, וזוג חדש עולה יותר ממה שנוח בבית החודש.",
   "choices": [
    {
     "label": "לתקן ולשחק עם מה שיש",
     "hint": "אופי",
     "text": "תפרת אותן בעצמך. שיחקת ככה חצי עונה.",
     "fx": {
      "attr": [
       "mental",
       1.2
      ],
      "morale": -3,
      "resilience": 3
     }
    },
    {
     "label": "לבקש מהמועדון",
     "hint": "בקשה",
     "text": "ביקשת ממנהל הנוער. הוא סידר, ולא עשה מזה עניין.",
     "fx": {
      "trust": 3,
      "morale": 5
     }
    }
   ]
  },
  {
   "eid": "y_weak_foot",
   "title": "הרגל השנייה",
   "stages": [
    "youth",
    "academy"
   ],
   "weight": 2.2,
   "cooldown": 30,
   "when": {
    "age_max": 18
   },
   "body": "עוזר המאמן עצר אותך: \"אתה שחקן של רגל אחת. זה יעצור אותך בגיל 20.\"",
   "choices": [
    {
     "label": "לעבוד רק על החלשה חודשיים",
     "hint": "כאב עכשיו",
     "text": "היה מתסכל. אחרי חודשיים אף אחד לא ידע איזו רגל חזקה אצלך.",
     "fx": {
      "attrs": [
       [
        "shooting",
        1.0
       ],
       [
        "passing",
        1.2
       ],
       [
        "dribbling",
        0.8
       ]
      ],
      "form": -6
     }
    },
    {
     "label": "להמשיך עם מה שעובד",
     "hint": "התמחות",
     "text": "המשכת להיות מצוין ברגל אחת. זה עבד, עד שזה הפסיק.",
     "fx": {
      "attr": [
       "shooting",
       1.4
      ],
      "morale": 3
     }
    }
   ]
  },
  {
   "eid": "y_viral_clip",
   "title": "הסרטון ברשת",
   "stages": [
    "youth"
   ],
   "weight": 1.8,
   "cooldown": 40,
   "body": "מישהו צילם אותך עושה תרגיל במשחק, והסרטון הגיע לחצי מיליון צפיות.\nפתאום כולם בבית ספר יודעים מי אתה.",
   "choices": [
    {
     "label": "ליהנות מזה",
     "hint": "מוניטין",
     "text": "ענית לתגובות ונהנית. גם המאמן ראה, ולא התלהב.",
     "fx": {
      "rep": 6,
      "media": 5,
      "trust": -3,
      "morale": 8
     }
    },
    {
     "label": "למחוק ולהתמקד",
     "hint": "ראש",
     "text": "ביקשת שיורידו. בשקט המשכת לעבוד.",
     "fx": {
      "attr": [
       "mental",
       1.2
      ],
      "trust": 5
     }
    }
   ]
  },
  {
   "eid": "y_bully",
   "title": "הגדול מהקבוצה",
   "stages": [
    "youth"
   ],
   "weight": 1.6,
   "cooldown": 40,
   "body": "יש בקבוצה מישהו שגדול משנתיים ומחליט מי משחק איפה בחימום.\nהיום הוא החליט שאתה מחוץ.",
   "choices": [
    {
     "label": "לעמוד מולו",
     "hint": "כבוד",
     "text": "לא זזת. הוא ויתר, ומאותו יום התייחסו אליך אחרת.",
     "fx": {
      "attr": [
       "mental",
       1.4
      ],
      "morale": 6,
      "resilience": 3
     }
    },
    {
     "label": "לספר למאמן",
     "hint": "פתרון",
     "text": "סיפרת. זה נפתר, וחלק מהחבר'ה קראו לך מלשן שבועיים.",
     "fx": {
      "trust": 3,
      "morale": -4
     }
    }
   ]
  },
  {
   "eid": "y_rain_training",
   "title": "אימון בגשם",
   "stages": [
    "youth"
   ],
   "weight": 1.6,
   "cooldown": 26,
   "body": "יורד גשם, המגרש בוץ, וחצי מהקבוצה לא הגיעה.\nהמאמן עומד לבד באמצע עם שק כדורים.",
   "choices": [
    {
     "label": "להתאמן בכל זאת",
     "hint": "אמון",
     "text": "היית אחד משלושה שהגיעו. {manager} לא שכח את זה שנים.",
     "fx": {
      "trust": 10,
      "attr": [
       "physical",
       1.0
      ],
      "fitness": -8
     }
    },
    {
     "label": "להישאר בבית",
     "hint": "היגיון",
     "text": "נשארת יבש. גם לא היית בסיפור שסיפרו אחר כך.",
     "fx": {
      "fitness": 8,
      "trust": -4
     }
    }
   ]
  },
  {
   "eid": "y_first_captain",
   "title": "הסרט הראשון",
   "stages": [
    "youth"
   ],
   "weight": 1.8,
   "cooldown": 45,
   "once": true,
   "when": {
    "age_min": 14
   },
   "body": "{manager} מגלגל אליך את הסרט לפני המשחק. \"היום אתה.\"\nזה פיסת בד, וזה הרבה יותר מזה.",
   "choices": [
    {
     "label": "לדבר לפני המשחק",
     "hint": "מנהיגות",
     "text": "אמרת שלושה משפטים בחדר. הם עבדו, ולמדת משהו על עצמך.",
     "fx": {
      "attr": [
       "mental",
       1.5
      ],
      "trait": "leader",
      "morale": 8,
      "trust": 5
     }
    },
    {
     "label": "להוביל בשקט",
     "hint": "דוגמה",
     "text": "לא אמרת כלום ורצת הכי הרבה. גם זו מנהיגות.",
     "fx": {
      "attr": [
       "physical",
       1.0
      ],
      "trust": 6,
      "morale": 5
     }
    }
   ]
  },
  {
   "eid": "y_foreign_scout",
   "title": "סקאוט מחו\"ל ביציע",
   "stages": [
    "youth"
   ],
   "weight": 1.6,
   "cooldown": 45,
   "when": {
    "age_min": 15
   },
   "body": "מישהו עם מבטא זר ומחברת ישב ביציע כל המשחק וכתב.\nאחרי המשחק הוא שאל את המאמן על מספר {number}.",
   "choices": [
    {
     "label": "ללכת להציג את עצמך",
     "hint": "יוזמה",
     "text": "ניגשת ולחצת יד. הוא רשם את השם ואמר \"נשמע ממני\".",
     "fx": {
      "rep": 5,
      "morale": 6,
      "flag": "foreign_interest"
     }
    },
    {
     "label": "לתת לכדורגל לדבר",
     "hint": "כבוד",
     "text": "לא ניגשת. הוא בכל זאת רשם משהו.",
     "fx": {
      "rep": 3,
      "attr": [
       "mental",
       0.6
      ]
     }
    }
   ]
  },
  {
   "eid": "y_school_report",
   "title": "התעודה",
   "stages": [
    "youth"
   ],
   "weight": 1.8,
   "cooldown": 30,
   "body": "התעודה הגיעה הביתה, ואף אחד לא מרוצה חוץ ממורה הספורט.\nבבית מדברים על \"תוכנית ב'\".",
   "choices": [
    {
     "label": "להשקיע בלימודים",
     "hint": "ראש",
     "text": "ויתרת על שני אימונים בשבוע. הציונים עלו, והכושר ירד.",
     "fx": {
      "attr": [
       "mental",
       1.6
      ],
      "business": 4,
      "trust": -4,
      "fitness": 6
     }
    },
    {
     "label": "כדורגל בלבד",
     "hint": "הכל על אחד",
     "text": "אמרת שזה מה שיהיה. ההורים לא ישנו טוב, ואתה הפכת רציני יותר.",
     "fx": {
      "attr": [
       "shooting",
       1.0
      ],
      "morale": 5,
      "trust": 5
     }
    }
   ]
  },
  {
   "eid": "y_physio_warning",
   "title": "אזהרה ראשונה מהפיזיו",
   "stages": [
    "youth"
   ],
   "weight": 1.6,
   "cooldown": 40,
   "when": {
    "age_min": 14
   },
   "body": "הפיזיו של המחלקה בדק אותך ואמר:\n\"הגוף שלך גדל מהר מדי. אם תעמיס עכשיו — תשלם בגיל 20.\"",
   "choices": [
    {
     "label": "להוריד עומסים",
     "hint": "עמידות",
     "text": "ירדת לשלושה אימונים בשבוע. הרגשת שאתה מפגר אחרי כולם.",
     "fx": {
      "resilience": 8,
      "morale": -5,
      "form": -4
     }
    },
    {
     "label": "להתעלם",
     "hint": "מסוכן",
     "text": "המשכת בעומס מלא. הרגשת מעולה, וזה יחזור.",
     "fx": {
      "attr": [
       "physical",
       1.2
      ],
      "resilience": -6,
      "form": 6
     }
    }
   ]
  },
  {
   "eid": "y_tactics_lesson",
   "title": "הלוח הראשון",
   "stages": [
    "youth"
   ],
   "weight": 1.6,
   "cooldown": 34,
   "body": "לראשונה הושיבו אתכם מול לוח טקטי עם חצים.\nחצי מהחדר לא הבין כלום, וזה היה ברור על הפרצופים.",
   "choices": [
    {
     "label": "לשאול שאלות",
     "hint": "קריאת משחק",
     "text": "שאלת ארבע שאלות. שניים צחקו, {manager} רשם לעצמו.",
     "fx": {
      "attr": [
       "mental",
       1.6
      ],
      "trust": 6
     }
    },
    {
     "label": "להעתיק ממי שמבין",
     "hint": "מהיר",
     "text": "עשית מה שהשחקן לידך עשה. זה עבד למשחק אחד.",
     "fx": {
      "attr": [
       "mental",
       0.5
      ],
      "morale": 2
     }
    }
   ]
  },
  {
   "eid": "y_snow_game",
   "title": "משחק בשלג",
   "stages": [
    "youth"
   ],
   "weight": 1.4,
   "cooldown": 45,
   "body": "המגרש לבן, הכדור לא מתגלגל, והשופט החליט שמשחקים.",
   "choices": [
    {
     "label": "לשחק פשוט וארוך",
     "hint": "חוכמה",
     "text": "הבנת ראשון שזה משחק אחר. שיחקת ארוך וניצחתם.",
     "fx": {
      "attr": [
       "mental",
       1.2
      ],
      "form": 8,
      "trust": 4
     }
    },
    {
     "label": "לנסות לשחק כרגיל",
     "hint": "עקשנות",
     "text": "ניסית לכדרר בבוץ. איבדת כל כדור.",
     "fx": {
      "form": -6,
      "attr": [
       "dribbling",
       0.6
      ]
     }
    }
   ]
  },
  {
   "eid": "a_driving_test",
   "title": "רישיון נהיגה",
   "stages": [
    "academy"
   ],
   "weight": 1.6,
   "cooldown": 45,
   "once": true,
   "when": {
    "age_min": 17
   },
   "body": "עברת טסט. עכשיו אתה יכול להגיע לאימונים לבד —\nוגם לצאת בלילה בלי לבקש טרמפ.",
   "choices": [
    {
     "label": "רכב משומש וזול",
     "hint": "ראש עסקי",
     "text": "קנית משהו ישן שמגיע. שאר הכסף נשאר בחשבון.",
     "fx": {
      "business": 5,
      "money": -12000
     }
    },
    {
     "label": "משהו שיראו בחניון",
     "hint": "רושם",
     "text": "קנית מעל מה שאתה מרוויח. חצי חדר ההלבשה צילם.",
     "fx": {
      "money": -90000,
      "morale": 8,
      "media": 3,
      "trust": -3
     }
    }
   ]
  },
  {
   "eid": "a_loan_third",
   "title": "השאלה לליגה נמוכה",
   "stages": [
    "academy",
    "player"
   ],
   "weight": 2.2,
   "cooldown": 40,
   "when": {
    "needs_club": true,
    "age_max": 22,
    "apps_max": 6
   },
   "body": "מועדון מליגה נמוכה רוצה אותך בהשאלה לחצי עונה.\nזה כדורגל אמיתי, עם מבוגרים שמשחקים על הפרנסה.",
   "choices": [
    {
     "label": "ללכת",
     "hint": "דקות אמיתיות",
     "text": "שיחקת מול גברים בני 30 שרצו לאכול אותך. חזרת אחר.",
     "fx": {
      "attrs": [
       [
        "physical",
        1.8
       ],
       [
        "mental",
        1.4
       ]
      ],
      "sharpness": 12,
      "resilience": 4,
      "rep": 2
     }
    },
    {
     "label": "להישאר ולהילחם על מקום",
     "hint": "סבלנות",
     "text": "נשארת. התאמנת מצוין, ושיחקת ארבע דקות בחודש.",
     "fx": {
      "trust": 5,
      "sharpness": -8,
      "morale": -4
     }
    }
   ]
  },
  {
   "eid": "a_first_yellow",
   "title": "הכרטיס הראשון",
   "stages": [
    "academy"
   ],
   "weight": 1.4,
   "cooldown": 34,
   "body": "עצרת התקפה בעבירה טקטית וקיבלת צהוב.\nעוזר המאמן אמר \"יפה\", מנהל הנוער אמר משהו אחר.",
   "choices": [
    {
     "label": "ללמוד מתי כן ומתי לא",
     "hint": "בגרות",
     "text": "הבנת שיש עבירות חכמות ויש טיפשות. זה חסך לך כרטיסים אחר כך.",
     "fx": {
      "attr": [
       "mental",
       1.2
      ],
      "trust": 3
     }
    },
    {
     "label": "לשחק קשוח מעכשיו",
     "hint": "אופי",
     "text": "החלטת שלא ידרכו עליך. זה עלה בכרטיסים.",
     "fx": {
      "attr": [
       "defending",
       1.0
      ],
      "trait": "hothead",
      "trust": -2
     }
    }
   ]
  },
  {
   "eid": "a_nutritionist",
   "title": "התזונאית",
   "stages": [
    "academy"
   ],
   "weight": 1.6,
   "cooldown": 40,
   "body": "המועדון הביא תזונאית. היא הסתכלה על מה שאתה אוכל ולא הסתירה את הפרצוף.",
   "choices": [
    {
     "label": "לעשות בדיוק מה שאמרה",
     "hint": "גוף",
     "text": "חודשיים של אוכל משעמם. הכושר עלה בצורה שהרגשת בכל ריצה.",
     "fx": {
      "fitness": 14,
      "resilience": 6,
      "attr": [
       "physical",
       0.8
      ],
      "morale": -3
     }
    },
    {
     "label": "בערך",
     "hint": "פשרה",
     "text": "שינית חצי. זה עזר חצי.",
     "fx": {
      "fitness": 5,
      "resilience": 2
     }
    }
   ]
  },
  {
   "eid": "a_night_before",
   "title": "מסיבה בלילה שלפני",
   "stages": [
    "academy",
    "player"
   ],
   "weight": 1.8,
   "cooldown": 30,
   "when": {
    "age_min": 17
   },
   "body": "יום שישי, מסיבה של חברים מבית ספר, ומחר משחק בעשר בבוקר.",
   "choices": [
    {
     "label": "ללכת שעה ולחזור",
     "hint": "איזון",
     "text": "הופעת, נראית, וחזרת ב-11. שיחקת בסדר.",
     "fx": {
      "morale": 5,
      "fitness": -4
     }
    },
    {
     "label": "להישאר בבית",
     "hint": "מקצוענות",
     "text": "נשארת. למחרת היית הכי טוב על המגרש והחברים לא הבינו.",
     "fx": {
      "form": 10,
      "trust": 5,
      "fitness": 8,
      "morale": -3
     }
    },
    {
     "label": "להישאר עד הסוף",
     "hint": "יקר",
     "text": "חזרת בשלוש. במשחק החלפת אחרי 55 דקות, ו{manager} ידע בדיוק למה.",
     "fx": {
      "trust": -10,
      "form": -12,
      "fitness": -18,
      "morale": 6
     }
    }
   ]
  },
  {
   "eid": "a_pro_contract",
   "title": "החוזה המקצועני הראשון",
   "stages": [
    "academy"
   ],
   "weight": 2.6,
   "cooldown": 50,
   "once": true,
   "when": {
    "needs_club": true,
    "age_min": 17
   },
   "body": "על השולחן חוזה מקצועני ראשון מ{club}. שלוש שנים.\nהסוכן אומר שאפשר לדרוש יותר, מנהל הנוער אומר שזה נדיב.",
   "choices": [
    {
     "label": "לחתום מיד",
     "hint": "ביטחון",
     "text": "חתמת באותו יום. בבית פתחו בקבוק, ואתה ישנת רגוע.",
     "fx": {
      "morale": 12,
      "trust": 8,
      "money": 25000
     }
    },
    {
     "label": "לדרוש יותר",
     "hint": "הימור",
     "text": "דרשת. קיבלת קצת יותר, ומישהו בהנהלה רשם שאתה \"מסובך\".",
     "fx": {
      "money": 90000,
      "board": -5,
      "business": 5
     }
    },
    {
     "label": "לבקש סעיף שחרור",
     "hint": "חופש עתידי",
     "text": "התעקשת על סעיף. הם הסכימו בסכום גבוה, וזה יהיה שימושי.",
     "fx": {
      "flag": "release_clause",
      "business": 6,
      "trust": -3
     }
    }
   ]
  },
  {
   "eid": "a_reserve_coach",
   "title": "מאמן הרזרבה שלא סובל אותך",
   "stages": [
    "academy"
   ],
   "weight": 1.6,
   "cooldown": 36,
   "body": "מאמן הקבוצה השנייה החליט שאתה \"מפונק\".\nהוא אומר את זה בקול, מול כולם.",
   "choices": [
    {
     "label": "לשתוק ולעבוד",
     "hint": "אופי",
     "text": "לא ענית שלושה חודשים. בסוף הוא בעצמו המליץ עליך למעלה.",
     "fx": {
      "attr": [
       "mental",
       1.6
      ],
      "trust": 8,
      "resilience": 3
     }
    },
    {
     "label": "לענות לו",
     "hint": "עימות",
     "text": "ענית לו מול הקבוצה. הוא לא שכח, ואתה שיחקת פחות.",
     "fx": {
      "trust": -10,
      "morale": 6,
      "trait": "hothead"
     }
    }
   ]
  },
  {
   "eid": "a_fitness_test",
   "title": "מבחני הכושר",
   "stages": [
    "academy",
    "player"
   ],
   "weight": 1.8,
   "cooldown": 34,
   "when": {
    "needs_club": true
   },
   "body": "מבחני יו-יו לפני העונה. כל התוצאות נתלות על הקיר, לפי סדר.",
   "choices": [
    {
     "label": "לתת הכל",
     "hint": "מקום ראשון",
     "text": "היית ראשון על הקיר. הצוות המקצועי הסתכל אחרת מאותו יום.",
     "fx": {
      "attr": [
       "physical",
       1.6
      ],
      "fitness": -14,
      "trust": 8,
      "morale": 6
     }
    },
    {
     "label": "לשמור על עצמך",
     "hint": "בלי להישרף",
     "text": "סיימת באמצע. אף אחד לא דיבר עליך, לטוב או לרע.",
     "fx": {
      "fitness": 6
     }
    }
   ]
  },
  {
   "eid": "a_poach_attempt",
   "title": "אקדמיה יריבה מתקשרת",
   "stages": [
    "academy"
   ],
   "weight": 1.6,
   "cooldown": 40,
   "when": {
    "needs_club": true
   },
   "body": "אקדמיה של מועדון יריב פנתה למשפחה שלך ישירות.\nהם מציעים תנאים טובים יותר ודקות מובטחות.",
   "choices": [
    {
     "label": "לעבור",
     "hint": "דקות",
     "text": "עברת. קיבלת דקות, ואיבדת את הבית שגדלת בו.",
     "fx": {
      "rep": 4,
      "morale": -4,
      "fans": -8
     }
    },
    {
     "label": "להישאר ולספר ל{manager}",
     "hint": "נאמנות",
     "text": "סיפרת. הוא הודה לך, וההנהלה שיפרה לך את התנאים בשקט.",
     "fx": {
      "trust": 12,
      "money": 30000,
      "trait": "loyal"
     }
    }
   ]
  },
  {
   "eid": "g_first_goal",
   "title": "השער הראשון בבוגרים",
   "stages": [
    "player"
   ],
   "weight": 2.8,
   "cooldown": 60,
   "once": true,
   "when": {
    "needs_club": true,
    "career_goals_min": 1
   },
   "body": "הכדור נכנס, והשנייה הבאה לא הייתה שלך.\n{stadium} התפוצץ, והרגליים הובילו אותך לאנשהו.",
   "choices": [
    {
     "label": "לרוץ ליציע",
     "hint": "אוהדים",
     "text": "קפצת לגדר. שוטר הזיז אותך, האוהדים לא שכחו.",
     "fx": {
      "fans": 10,
      "morale": 12,
      "rep": 3,
      "honour": "השער הראשון בבוגרים"
     }
    },
    {
     "label": "להצביע על מי שבישל",
     "hint": "חדר הלבשה",
     "text": "הצבעת על {mate} וחיבקת אותו. חדר ההלבשה ראה.",
     "fx": {
      "trust": 6,
      "morale": 10,
      "honour": "השער הראשון בבוגרים"
     }
    },
    {
     "label": "להרים את החולצה עם שם",
     "hint": "אישי",
     "text": "מתחת לחולצה היה שם. קיבלת צהוב וזה היה שווה.",
     "fx": {
      "morale": 15,
      "media": 5,
      "honour": "השער הראשון בבוגרים"
     }
    }
   ]
  },
  {
   "eid": "g_hattrick",
   "title": "שלושער",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 45,
   "when": {
    "needs_club": true,
    "form_min": 65,
    "position_in": [
     "ST",
     "AM",
     "LW",
     "RW"
    ]
   },
   "body": "שלושה שערים במשחק אחד. השופט נתן לך את הכדור,\nוצלם עיתונות ביקש שתחתום עליו מולו.",
   "choices": [
    {
     "label": "לקחת את הכדור הביתה",
     "hint": "זיכרון",
     "text": "הכדור על המדף. אתה מסתכל עליו יותר ממה שתודה.",
     "fx": {
      "morale": 12,
      "rep": 6,
      "form": 8,
      "honour": "שלושער מול {opponent}"
     }
    },
    {
     "label": "לתת אותו לילד ביציע",
     "hint": "אוהדים",
     "text": "זרקת את הכדור לילד בשורה הראשונה. התמונה הזאת רצה שבוע.",
     "fx": {
      "fans": 14,
      "media": 8,
      "rep": 5,
      "honour": "שלושער מול {opponent}"
     }
    }
   ]
  },
  {
   "eid": "g_own_goal",
   "title": "שער עצמי",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 34,
   "when": {
    "needs_club": true
   },
   "body": "הכדור פגע בברך שלך ונכנס. השוער הסתכל עליך ולא אמר כלום.\nהיציע כן אמר.",
   "choices": [
    {
     "label": "לרוץ ולנסות לתקן",
     "hint": "אופי",
     "text": "רצת עשרים דקות כמו מטורף. לא תיקנת, אבל כולם ראו.",
     "fx": {
      "attr": [
       "physical",
       0.8
      ],
      "trust": 5,
      "fitness": -10,
      "morale": -4
     }
    },
    {
     "label": "לשקוע",
     "hint": "אנושי",
     "text": "לא נגעת בכדור עוד עשרים דקות. החליפו אותך.",
     "fx": {
      "morale": -10,
      "form": -12,
      "trust": -4
     }
    }
   ]
  },
  {
   "eid": "g_red_card",
   "title": "אדום",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 30,
   "when": {
    "needs_club": true
   },
   "body": "השופט הוציא כרטיס אדום, ואתה עוד לא בטוח שהבנת למה.\nהקבוצה נשארה עם עשרה בדקה 34.",
   "choices": [
    {
     "label": "להתנצל בחדר ההלבשה",
     "hint": "אחריות",
     "text": "עמדת מולם והתנצלת. אף אחד לא רצה לשמוע, וכולם כיבדו.",
     "fx": {
      "trust": 5,
      "morale": -5,
      "attr": [
       "mental",
       1.0
      ]
     }
    },
    {
     "label": "להתווכח עם השופט במנהרה",
     "hint": "יקר",
     "text": "המשכת לצעוק. קיבלת שלושה משחקים במקום אחד.",
     "fx": {
      "trust": -8,
      "trait": "hothead",
      "morale": 4,
      "media": 4
     }
    }
   ]
  },
  {
   "eid": "g_sitter_miss",
   "title": "ההחמצה",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 28,
   "when": {
    "needs_club": true,
    "position_in": [
     "ST",
     "AM",
     "LW",
     "RW"
    ]
   },
   "body": "שער ריק, שני מטרים, ואתה שלחת את הכדור מעל הרשת.\nהתמונה תופיע בכל תוכנית ספורט השבוע.",
   "choices": [
    {
     "label": "לבקש את הכדור בהתקפה הבאה",
     "hint": "אופי",
     "text": "ביקשת מיד. כבשת בדקה 88, ואף אחד לא זכר את ההחמצה.",
     "fx": {
      "attr": [
       "mental",
       1.5
      ],
      "form": 10,
      "trait": "clutch",
      "morale": 6
     }
    },
    {
     "label": "להיעלם למשך המשחק",
     "hint": "אנושי",
     "text": "לא ביקשת כדור יותר. זה נמשך שלושה משחקים.",
     "fx": {
      "form": -14,
      "morale": -8,
      "trust": -5
     }
    }
   ]
  },
  {
   "eid": "g_comeback_debut",
   "title": "החזרה מהפציעה",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.0,
   "cooldown": 34,
   "when": {
    "needs_club": true,
    "injured": false
   },
   "body": "חמישה חודשים בחדר כושר ובבריכה, והיום אתה חוזר לדשא עם הקבוצה.\nהראש רוצה, הגוף עוד לא בטוח.",
   "choices": [
    {
     "label": "להיכנס בכל כדור מהרגע הראשון",
     "hint": "להוכיח",
     "text": "נכנסת בכל דו-קרב. הרגשת חי, ושילמת בשריר.",
     "fx": {
      "sharpness": 10,
      "trust": 6,
      "resilience": -3,
      "morale": 8
     }
    },
    {
     "label": "לחזור בהדרגה",
     "hint": "חכם",
     "text": "עשית בדיוק מה שהפיזיו אמר. שבועיים אחר כך היית שלם.",
     "fx": {
      "resilience": 6,
      "fitness": 12,
      "sharpness": 4,
      "trust": -2
     }
    }
   ]
  },
  {
   "eid": "g_bid_rejected",
   "title": "המועדון דחה הצעה",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 34,
   "when": {
    "needs_club": true,
    "rep_min": 45
   },
   "body": "היתה הצעה עליך, ו{club} דחו אותה בלי לספר לך.\nגילית מכתבה.",
   "choices": [
    {
     "label": "לדרוש הסבר מההנהלה",
     "hint": "עימות",
     "text": "נכנסת לחדר. הם אמרו שאתה לא למכירה, בטון שסגר את הדיון.",
     "fx": {
      "board": -6,
      "morale": 4,
      "trust": -3
     }
    },
    {
     "label": "לקבל ולהמשיך",
     "hint": "מקצוענות",
     "text": "לא עשית עניין. ההנהלה זכרה שהתנהגת יפה.",
     "fx": {
      "board": 8,
      "trust": 5,
      "morale": -4
     }
    }
   ]
  },
  {
   "eid": "g_new_signing",
   "title": "חתמו על מישהו בעמדה שלך",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 2.2,
   "cooldown": 30,
   "when": {
    "needs_club": true
   },
   "body": "{club} הביאו {position} חדש בסכום גדול.\nההודעה יצאה לפני שמישהו טרח לדבר איתך.",
   "choices": [
    {
     "label": "לקבל אותו יפה",
     "hint": "חדר הלבשה",
     "text": "היית הראשון שלחץ לו יד. הוא לא שכח, ואתם שיחקנו יחד טוב.",
     "fx": {
      "trust": 6,
      "morale": 3,
      "trait": "loyal"
     }
    },
    {
     "label": "להתאמן כאילו יש מלחמה",
     "hint": "תחרות",
     "text": "כל אימון היה קרב. שניכם השתפרו, והמאמן נהנה.",
     "fx": {
      "attr": [
       "physical",
       1.0
      ],
      "form": 10,
      "sharpness": 6,
      "morale": -3
     }
    },
    {
     "label": "לבקש הבהרה מ{manager}",
     "hint": "ישירות",
     "text": "שאלת מה התפקיד שלך. הוא ענה כנה, וזה לא היה נעים.",
     "fx": {
      "trust": 3,
      "morale": -5,
      "attr": [
       "mental",
       0.8
      ]
     }
    }
   ]
  },
  {
   "eid": "g_late_fine",
   "title": "קנס על איחור",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 30,
   "when": {
    "needs_club": true
   },
   "body": "פקק, טלפון שלא צלצל, ואיחור של עשרים דקות לאימון.\nהקנס תלוי על לוח המודעות עם השם שלך.",
   "choices": [
    {
     "label": "לשלם ולשתוק",
     "hint": "כבוד",
     "text": "שילמת בלי מילה. זה נגמר שם.",
     "fx": {
      "money": -18000,
      "trust": 2
     }
    },
    {
     "label": "להתווכח",
     "hint": "עימות",
     "text": "טענת שזה לא הוגן. זה נהיה שיחת חדר ההלבשה של השבוע.",
     "fx": {
      "trust": -7,
      "morale": 3
     }
    }
   ]
  },
  {
   "eid": "g_social_post",
   "title": "הפוסט שלא היה צריך",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 32,
   "when": {
    "age_min": 18
   },
   "body": "פרסמת משהו בלילה אחרי הפסד. עכשיו זה בכל אתר,\nוההנהלה ביקשה לדבר איתך בבוקר.",
   "choices": [
    {
     "label": "למחוק ולהתנצל",
     "hint": "לסגור",
     "text": "מחקת והתנצלת. זה נמוג תוך יומיים.",
     "fx": {
      "media": -2,
      "board": 3,
      "morale": -3
     }
    },
    {
     "label": "להשאיר",
     "hint": "אותנטי ויקר",
     "text": "השארת. חצי מהאוהדים אהבו, ההנהלה בכלל לא.",
     "fx": {
      "fans": 6,
      "board": -8,
      "media": 6,
      "trust": -5
     }
    }
   ]
  },
  {
   "eid": "g_ex_club",
   "title": "מול המועדון שגידל אותך",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 40,
   "when": {
    "needs_club": true,
    "age_min": 21
   },
   "body": "השבוע אתה משחק מול המועדון שבו גדלת.\nחצי היציע שם עוד אוהב אותך, וחצי כבר לא.",
   "choices": [
    {
     "label": "לא לחגוג אם תכבוש",
     "hint": "כבוד",
     "text": "כבשת והרמת יד להתנצלות. שני היציעים מחאו כפיים.",
     "fx": {
      "fans": 8,
      "rep": 4,
      "morale": 6
     }
    },
    {
     "label": "לחגוג בכל הכוח",
     "hint": "מקצוענות קרה",
     "text": "חגגת מולם. הם שרו עליך שירים שלא נעים לחזור עליהם.",
     "fx": {
      "form": 10,
      "fans": -6,
      "media": 5,
      "morale": 4
     }
    }
   ]
  },
  {
   "eid": "g_handshake",
   "title": "היד שלא נלחצה",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 36,
   "when": {
    "needs_club": true
   },
   "body": "בטקס לחיצות הידיים שחקן היריבה עבר אותך בלי לעצור.\nהמצלמות תפסו הכל.",
   "choices": [
    {
     "label": "להתעלם",
     "hint": "בגרות",
     "text": "המשכת הלאה כאילו כלום. זה נראה טוב יותר משנשמע.",
     "fx": {
      "rep": 3,
      "attr": [
       "mental",
       1.0
      ],
      "media": 2
     }
    },
    {
     "label": "לרדוף אחריו במשחק",
     "hint": "אש",
     "text": "נדבקת אליו 90 דקות. הוא לא נגע בכדור, וגם אתה לא.",
     "fx": {
      "form": -4,
      "trait": "hothead",
      "morale": 6,
      "media": 4
     }
    }
   ]
  },
  {
   "eid": "g_var_row",
   "title": "ה-VAR",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 30,
   "when": {
    "needs_club": true
   },
   "body": "שער בוטל אחרי ארבע דקות בדיקה, על סנטימטר.\nהיציע השתגע, וגם חצי מהספסל.",
   "choices": [
    {
     "label": "לתקוף את השופט בראיון",
     "hint": "מסוכן",
     "text": "אמרת מה שכולם חשבו. קיבלת קנס והפכת לגיבור ליומיים.",
     "fx": {
      "fans": 10,
      "media": 8,
      "money": -40000,
      "board": -5
     }
    },
    {
     "label": "לא להגיב",
     "hint": "מקצוענות",
     "text": "אמרת שהשופט עשה את עבודתו. שום כותרת, שום בעיה.",
     "fx": {
      "board": 4,
      "attr": [
       "mental",
       0.8
      ]
     }
    }
   ]
  },
  {
   "eid": "g_heat_game",
   "title": "38 מעלות",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 36,
   "when": {
    "needs_club": true
   },
   "body": "משחק בשתיים בצהריים בשרב. השופט נותן הפסקות שתייה,\nוהחולצה שלך שוקלת פי שניים.",
   "choices": [
    {
     "label": "לנהל את הגוף",
     "hint": "חוכמה",
     "text": "חסכת בריצות ופוצצת בעשרים האחרונות. שיחקת חכם.",
     "fx": {
      "attr": [
       "mental",
       1.2
      ],
      "form": 8,
      "fitness": -6
     }
    },
    {
     "label": "לרוץ כרגיל",
     "hint": "לב",
     "text": "רצת כאילו זה חורף. בדקה 70 היית גמור.",
     "fx": {
      "fitness": -22,
      "attr": [
       "physical",
       0.8
      ],
      "trust": 4
     }
    }
   ]
  },
  {
   "eid": "g_pitch_invasion",
   "title": "פריצה למגרש",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.2,
   "cooldown": 45,
   "when": {
    "needs_club": true
   },
   "body": "אוהד קפץ מהיציע ורץ ישר אליך. הביטחון רחוק שניות.",
   "choices": [
    {
     "label": "לחבק אותו",
     "hint": "אוהדים",
     "text": "הוא בכה, ואתה חיבקת. התמונה הפכה לכרזה.",
     "fx": {
      "fans": 12,
      "media": 6,
      "morale": 5
     }
    },
    {
     "label": "להתרחק",
     "hint": "בטוח",
     "text": "התרחקת ונתת לביטחון לעשות את שלהם. נכון, ולא צילומי.",
     "fx": {
      "morale": 2
     }
    }
   ]
  },
  {
   "eid": "g_legend_funeral",
   "title": "דקת דומייה",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.2,
   "cooldown": 50,
   "when": {
    "needs_club": true
   },
   "body": "אגדה של {club} הלכה לעולמה. לפני המשחק דקת דומייה,\nוסרט שחור על השרוול.",
   "choices": [
    {
     "label": "להקדיש לו את המשחק",
     "hint": "כבוד",
     "text": "שיחקת כאילו הוא מסתכל. אחרי המשחק הצבעת לשמיים.",
     "fx": {
      "form": 12,
      "fans": 8,
      "morale": 5
     }
    },
    {
     "label": "לבקר את המשפחה",
     "hint": "אנושי",
     "text": "הגעת לניחום בלי מצלמות. המשפחה סיפרה על זה שנים.",
     "fx": {
      "fans": 6,
      "rep": 3,
      "morale": 6
     }
    }
   ]
  },
  {
   "eid": "l_first_house",
   "title": "הדירה הראשונה",
   "stages": [
    "player"
   ],
   "weight": 1.6,
   "cooldown": 50,
   "once": true,
   "when": {
    "age_min": 20
   },
   "body": "יש מספיק בחשבון בשביל דירה. הבנק מציע משכנתה,\nוהסוכן אומר שכדאי דווקא להשקיע.",
   "choices": [
    {
     "label": "לקנות דירה",
     "hint": "יציבות",
     "text": "קנית. בפעם הראשונה בחיים הרגשת שיש קרקע מתחת.",
     "fx": {
      "money": -900000,
      "morale": 12,
      "business": 4
     }
    },
    {
     "label": "לשכור ולהשקיע",
     "hint": "ראש עסקי",
     "text": "שכרת, והשקעת את השאר. בעוד עשור זו תהיה החלטה חכמה.",
     "fx": {
      "business": 9,
      "money": -120000,
      "morale": 3
     }
    }
   ]
  },
  {
   "eid": "l_family_asks",
   "title": "בן משפחה מבקש",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.8,
   "cooldown": 40,
   "when": {
    "age_min": 21
   },
   "body": "דוד שלא ראית שנים מתקשר. יש לו \"עסק בטוח\",\nוצריך רק שתשים את החלק שלך.",
   "choices": [
    {
     "label": "לתת",
     "hint": "משפחה",
     "text": "נתת. העסק לא היה בטוח, וגם לא היה עסק.",
     "fx": {
      "money": -320000,
      "morale": -6,
      "business": 3
     }
    },
    {
     "label": "לסרב בנימוס",
     "hint": "גבולות",
     "text": "אמרת לא. באירועים משפחתיים היה מוזר שנתיים.",
     "fx": {
      "morale": -4,
      "business": 5,
      "attr": [
       "mental",
       0.8
      ]
     }
    },
    {
     "label": "לתת חצי כמתנה, בלי לצפות לכלום",
     "hint": "שקט",
     "text": "נתת מתנה, לא הלוואה. זה סגר את העניין נקי.",
     "fx": {
      "money": -120000,
      "morale": 4,
      "business": 4
     }
    }
   ]
  },
  {
   "eid": "l_burglary",
   "title": "פריצה לבית",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.2,
   "cooldown": 50,
   "when": {
    "rep_min": 45
   },
   "body": "חזרת ממשחק חוץ והבית פתוח. לקחו שעונים, מדליות, ואת הכדור של השער הראשון.",
   "choices": [
    {
     "label": "לשכור אבטחה ולהמשיך",
     "hint": "מעשי",
     "text": "סידרת אבטחה. הכסף חזר, הכדור לא.",
     "fx": {
      "money": -180000,
      "morale": -8
     }
    },
    {
     "label": "לפרסם בקשה להחזיר את הכדור",
     "hint": "אוהדים",
     "text": "פרסמת. שבוע אחר כך הכדור חיכה בשק ליד השער.",
     "fx": {
      "fans": 10,
      "media": 5,
      "morale": 6
     }
    }
   ]
  },
  {
   "eid": "l_old_friend_story",
   "title": "חבר שמכר סיפור",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 45,
   "when": {
    "rep_min": 55
   },
   "body": "חבר מהתיכון מכר לעיתון סיפורים עליך מגיל 16.\nרובם לא נכונים. חלקם כן.",
   "choices": [
    {
     "label": "לתבוע",
     "hint": "עיקרון",
     "text": "הלכת לעורכי דין. זה נמשך שנתיים ועלה יותר ממה שהרווחת מזה.",
     "fx": {
      "money": -250000,
      "media": 4,
      "morale": -3
     }
    },
    {
     "label": "לצחוק על זה בפומבי",
     "hint": "חוכמה",
     "text": "התייחסת לזה בהומור בראיון. הסיפור מת תוך יומיים.",
     "fx": {
      "media": 7,
      "fans": 5,
      "morale": 4,
      "rep": 2
     }
    }
   ]
  },
  {
   "eid": "l_tax_letter",
   "title": "מכתב ממס הכנסה",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 50,
   "when": {
    "age_min": 24,
    "rep_min": 40
   },
   "body": "רואה החשבון שהסוכן הביא לך עשה תרגילים.\nעכשיו יש חקירה, והשם שלך בתיק.",
   "choices": [
    {
     "label": "לשלם הכל מיד ולסגור",
     "hint": "נקי",
     "text": "שילמת עד השקל האחרון. כאב, ונגמר.",
     "fx": {
      "money": -800000,
      "business": 6,
      "morale": -5
     }
    },
    {
     "label": "להילחם",
     "hint": "ממושך",
     "text": "נלחמת שנתיים. חסכת חלק, ושילמת בכותרות.",
     "fx": {
      "money": -400000,
      "media": -5,
      "rep": -4,
      "morale": -6
     }
    }
   ]
  },
  {
   "eid": "l_fan_tattoo",
   "title": "הקעקוע",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.2,
   "cooldown": 45,
   "when": {
    "rep_min": 50
   },
   "body": "אוהד קעקע את הפרצוף שלך על הזרוע ושלח תמונה.\nזה מחמיא ומפחיד באותה מידה.",
   "choices": [
    {
     "label": "להזמין אותו למשחק",
     "hint": "אוהדים",
     "text": "הזמנת אותו לתא. הוא בכה, והמועדון קיבל סיפור טוב.",
     "fx": {
      "fans": 12,
      "media": 5,
      "morale": 5
     }
    },
    {
     "label": "להודות ולהשאיר",
     "hint": "מרחק",
     "text": "כתבת \"תודה\" והמשכת. גם זה בסדר.",
     "fx": {
      "fans": 3
     }
    }
   ]
  },
  {
   "eid": "l_game_cover",
   "title": "השער של המשחק",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 45,
   "when": {
    "rep_min": 70
   },
   "body": "חברת משחקי הווידאו רוצה אותך על העטיפה של הגרסה הבאה.\nיש אנשים שמאמינים שזו קללה.",
   "choices": [
    {
     "label": "לקחת",
     "hint": "כסף וחשיפה",
     "text": "הפרצוף שלך על כל מדף בעולם. הקללה, מסתבר, היא רק סיפור.",
     "fx": {
      "money": 1400000,
      "media": 10,
      "rep": 6
     }
    },
    {
     "label": "לוותר",
     "hint": "אמונות",
     "text": "ויתרת. חצי חדר ההלבשה אמר שאתה חכם, חצי שאתה משוגע.",
     "fx": {
      "morale": 3,
      "attr": [
       "mental",
       0.6
      ]
     }
    }
   ]
  },
  {
   "eid": "l_book_offer",
   "title": "הצעה לכתוב ספר",
   "stages": [
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 50,
   "when": {
    "age_min": 32,
    "rep_min": 55
   },
   "body": "הוצאה רוצה אוטוביוגרפיה. הם רומזים שהחלקים המעניינים\nהם אלה שיכעיסו אנשים.",
   "choices": [
    {
     "label": "לכתוב הכל",
     "hint": "כותרות",
     "text": "כתבת בלי לרכך. הספר נמכר, וארבעה אנשים לא מדברים איתך.",
     "fx": {
      "money": 700000,
      "media": 12,
      "rep": 5,
      "trust": -8,
      "fans": -4
     }
    },
    {
     "label": "ספר נקי",
     "hint": "יחסים",
     "text": "כתבת משהו יפה ולא חד. נמכר פחות, וכולם נשארו חברים.",
     "fx": {
      "money": 250000,
      "media": 5,
      "rep": 3,
      "morale": 4
     }
    }
   ]
  },
  {
   "eid": "l_charity_foundation",
   "title": "לפתוח עמותה",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.4,
   "cooldown": 50,
   "when": {
    "rep_min": 55
   },
   "body": "יש מספיק שם ומספיק כסף כדי להקים קרן על שמך.\nזה גם עבודה אמיתית, לא רק לוגו.",
   "choices": [
    {
     "label": "להקים ולנהל ברצינות",
     "hint": "מורשת",
     "text": "הקמת. שלושה מגרשים בשכונות שלא היו בהן. זה נשאר אחריך.",
     "fx": {
      "money": -600000,
      "fans": 16,
      "rep": 8,
      "business": 5,
      "morale": 10,
      "honour": "הקרן על שם {me}"
     }
    },
    {
     "label": "לתת תרומות ולא להתעסק",
     "hint": "פשוט",
     "text": "העברת כסף בלי כותרות. גם זה עוזר.",
     "fx": {
      "money": -200000,
      "morale": 5,
      "fans": 4
     }
    }
   ]
  },
  {
   "eid": "l_mental_health",
   "title": "השבוע שבו לא רצית לצאת מהבית",
   "stages": [
    "player",
    "veteran"
   ],
   "weight": 1.6,
   "cooldown": 45,
   "when": {
    "morale_max": 40
   },
   "body": "לא הפציעה ולא הכושר. פשוט אין כוח, ואתה לא מבין למה.\nיש מספר של מישהו שהמועדון נותן לשחקנים.",
   "choices": [
    {
     "label": "להתקשר",
     "hint": "טיפול",
     "text": "התקשרת. לקח חודשים, ובסוף חזרת להיות אתה.",
     "fx": {
      "morale": 18,
      "attr": [
       "mental",
       1.6
      ],
      "form": 8
     }
    },
    {
     "label": "לדחוף את זה למטה",
     "hint": "מסוכן",
     "text": "אמרת לעצמך שזה יעבור. זה לא עבר, זה רק נהיה שקט יותר.",
     "fx": {
      "morale": -6,
      "form": -8,
      "attr": [
       "mental",
       -0.4
      ]
     }
    },
    {
     "label": "לדבר עם {mate}",
     "hint": "חבר",
     "text": "סיפרת לאחד. הוא הקשיב ולא ניסה לתקן. זה הספיק בשביל להתחיל.",
     "fx": {
      "morale": 10,
      "trust": 3
     }
    }
   ]
  },
  {
   "eid": "c_credit_stolen",
   "title": "מי קיבל את הקרדיט",
   "stages": [
    "coach"
   ],
   "weight": 2.2,
   "cooldown": 30,
   "when": {
    "needs_club": true
   },
   "body": "השינוי הטקטי שהפך את המשחק היה הרעיון שלך.\nבמסיבת העיתונאים המנג'ר סיפר עליו בגוף ראשון.",
   "choices": [
    {
     "label": "לבלוע",
     "hint": "סבלנות",
     "text": "לא אמרת כלום. חדר ההלבשה ידע, וזה מה שחשוב בטווח הארוך.",
     "fx": {
      "coaching": 4,
      "trust": 6,
      "morale": -4
     }
    },
    {
     "label": "לדבר איתו ביחידות",
     "hint": "ישירות",
     "text": "אמרת לו. הוא נעלב שבוע, ואז התחיל לתת קרדיט.",
     "fx": {
      "coaching": 3,
      "rep": 4,
      "trust": -3
     }
    }
   ]
  },
  {
   "eid": "c_reserve_command",
   "title": "לקבל את הקבוצה השנייה",
   "stages": [
    "coach"
   ],
   "weight": 2.0,
   "cooldown": 40,
   "when": {
    "needs_club": true
   },
   "body": "מציעים לך לנהל את קבוצת הרזרבה. זה לא הכיסא הגדול,\nאבל זו הפעם הראשונה שההחלטות שלך.",
   "choices": [
    {
     "label": "לקחת",
     "hint": "ניסיון",
     "text": "לקחת. טעית הרבה, ולמדת יותר משנתיים על הספסל.",
     "fx": {
      "coaching": 10,
      "rep": 3,
      "flag": "ran_reserves"
     }
    },
    {
     "label": "להישאר ליד המנג'ר",
     "hint": "קרבה",
     "text": "נשארת ליד הכיסא. ראית איך מקבלים החלטות גדולות.",
     "fx": {
      "coaching": 5,
      "business": 3,
      "board": 4
     }
    }
   ]
  },
  {
   "eid": "c_session_flop",
   "title": "אימון שלא עבד",
   "stages": [
    "coach",
    "manager"
   ],
   "weight": 1.8,
   "cooldown": 28,
   "when": {
    "needs_club": true
   },
   "body": "בנית אימון שלם, והשחקנים לא הבינו כלום.\nאחרי עשרים דקות זה נראה כמו כאוס.",
   "choices": [
    {
     "label": "לעצור ולהתחיל מחדש פשוט",
     "hint": "ענווה",
     "text": "עצרת הכל, פישטת, והצי השני של האימון היה מצוין.",
     "fx": {
      "coaching": 6,
      "trust": 5
     }
    },
    {
     "label": "להמשיך ולהתעקש",
     "hint": "עקשנות",
     "text": "התעקשת. סיימתם באווירה רעה ובלי שלמד מזה מישהו.",
     "fx": {
      "trust": -6,
      "coaching": 1
     }
    }
   ]
  },
  {
   "eid": "m_assistant_wants_job",
   "title": "העוזר שרוצה את הכיסא",
   "stages": [
    "manager"
   ],
   "weight": 1.8,
   "cooldown": 36,
   "when": {
    "needs_club": true
   },
   "body": "העוזר שלך מדבר עם עיתונאים בלעדיך, ובהנהלה מזכירים את שמו.",
   "choices": [
    {
     "label": "לפטר אותו",
     "hint": "סמכות",
     "text": "פיטרת. ההנהלה לא אהבה, וחדר ההלבשה הבין מי קובע.",
     "fx": {
      "board": -8,
      "trust": 8,
      "media": 4
     }
    },
    {
     "label": "לקרב אותו",
     "hint": "פוליטיקה",
     "text": "נתת לו יותר אחריות. הוא הפסיק לדבר, והתחיל לעבוד.",
     "fx": {
      "coaching": 5,
      "trust": 4,
      "board": 4
     }
    }
   ]
  },
  {
   "eid": "m_leak",
   "title": "דליפה מחדר ההלבשה",
   "stages": [
    "manager"
   ],
   "weight": 2.0,
   "cooldown": 30,
   "when": {
    "needs_club": true
   },
   "body": "מה שאמרת בהפסקה הופיע מילה במילה באתר חדשות.\nמישהו בחדר מדבר החוצה.",
   "choices": [
    {
     "label": "לעמת את כולם",
     "hint": "עימות",
     "text": "עצרת אימון ודיברת ישר. האווירה הייתה רעה שבוע, והדליפות נפסקו.",
     "fx": {
      "trust": -4,
      "morale": -5,
      "flag": "leak_closed"
     }
    },
    {
     "label": "לשתול מידע כוזב ולתפוס",
     "hint": "תחכום",
     "text": "שתלת פרט שגוי. הוא הופיע, ומצאת את מי שדיבר.",
     "fx": {
      "coaching": 4,
      "trust": 6,
      "board": 3
     }
    },
    {
     "label": "להתעלם",
     "hint": "שקט",
     "text": "לא עשית כלום. זה נמשך כל העונה.",
     "fx": {
      "trust": -6,
      "media": -3
     }
    }
   ]
  },
  {
   "eid": "m_player_night_out",
   "title": "שחקן שנתפס בלילה",
   "stages": [
    "manager"
   ],
   "weight": 2.0,
   "cooldown": 30,
   "when": {
    "needs_club": true,
    "has_mate": true
   },
   "body": "{mate} צולם בשלוש לפנות בוקר, יומיים לפני משחק גדול.\nהתמונות בכל מקום.",
   "choices": [
    {
     "label": "להוציא אותו מהסגל",
     "hint": "משמעת",
     "text": "הוצאת. הקבוצה הבינה שיש קווים, וההפסד באותו שבוע כאב.",
     "fx": {
      "trust": 8,
      "board": -4,
      "fans": 3
     }
    },
    {
     "label": "לקנוס בשקט ולהעלות אותו",
     "hint": "תוצאות",
     "text": "קנסת בלי פרסום והוא כבש. חלק מהחדר רשם שיש כללים גמישים.",
     "fx": {
      "board": 5,
      "trust": -5,
      "fans": -2
     }
    }
   ]
  },
  {
   "eid": "m_fixture_pileup",
   "title": "שלושה משחקים בשבוע",
   "stages": [
    "manager"
   ],
   "weight": 2.0,
   "cooldown": 26,
   "when": {
    "needs_club": true
   },
   "body": "ליגה, גביע, ושוב ליגה — בשמונה ימים.\nהפיזיו מביא רשימה של מי כבר בסיכון.",
   "choices": [
    {
     "label": "לסובב סגל",
     "hint": "גוף",
     "text": "סובבת. הפסדתם בגביע, וסיימתם את השבוע בריאים.",
     "fx": {
      "board": -4,
      "trust": 6,
      "coaching": 4
     }
    },
    {
     "label": "להעלות את החזקים בכל משחק",
     "hint": "הכל עכשיו",
     "text": "העלית את אותם אחד עשר. שני שחקנים נפצעו לחודש.",
     "fx": {
      "board": 5,
      "trust": -6,
      "fans": 4
     }
    }
   ]
  },
  {
   "eid": "m_touchline_ban",
   "title": "הרחקה מהקו",
   "stages": [
    "manager"
   ],
   "weight": 1.6,
   "cooldown": 40,
   "when": {
    "needs_club": true
   },
   "body": "אחרי הוויכוח עם השופט קיבלת שלושה משחקים ביציע.\nהעוזר צריך להעביר הוראות בטלפון.",
   "choices": [
    {
     "label": "להכין אותו לכל תרחיש",
     "hint": "מקצועיות",
     "text": "ישבתם לילה שלם על תרחישים. הוא ניהל שלושה משחקים כמו שצריך.",
     "fx": {
      "coaching": 6,
      "trust": 5,
      "board": 3
     }
    },
    {
     "label": "לנהל מהיציע בטלפון",
     "hint": "שליטה",
     "text": "צעקת לטלפון 90 דקות. זה נראה נורא, ועבד בקושי.",
     "fx": {
      "media": 5,
      "board": -4,
      "trust": -2
     }
    }
   ]
  },
  {
   "eid": "m_rival_mindgames",
   "title": "משחקי ראש",
   "stages": [
    "manager"
   ],
   "weight": 1.8,
   "cooldown": 30,
   "when": {
    "needs_club": true
   },
   "body": "המאמן של {opponent} אמר בעיתון שהקבוצה שלך \"משחקת אנטי-כדורגל\".\nהכתבים מחכים לתגובה שלך.",
   "choices": [
    {
     "label": "לענות בחריפות",
     "hint": "אש",
     "text": "ענית בציטוט שהיה בכל שידור. עכשיו זה משחק אחר.",
     "fx": {
      "media": 8,
      "fans": 6,
      "board": -3,
      "trust": 5
     }
    },
    {
     "label": "להחמיא לו",
     "hint": "לפרק",
     "text": "שיבחת אותו בכנות. הוא לא ידע מה לעשות עם זה.",
     "fx": {
      "media": 4,
      "board": 4,
      "coaching": 3
     }
    }
   ]
  },
  {
   "eid": "m_bribe",
   "title": "המעטפה",
   "stages": [
    "manager"
   ],
   "weight": 1.2,
   "cooldown": 60,
   "when": {
    "needs_club": true
   },
   "body": "מישהו שאתה לא מכיר מציע סכום גדול בשביל תוצאה אחת.\nהוא אומר שזה \"רק משחק אחד שלא משנה\".",
   "choices": [
    {
     "label": "לדווח מיד",
     "hint": "נקי",
     "text": "התקשרת להתאחדות באותו ערב. החקירה נמשכה שנה, ואתה יצאת נקי.",
     "fx": {
      "rep": 10,
      "board": 8,
      "media": 6,
      "honour": "דיווח על ניסיון שחיתות"
     }
    },
    {
     "label": "לסרב ולשתוק",
     "hint": "מרחק",
     "text": "אמרת לא וניתקת. חודש אחר כך שמעת ששניים אחרים אמרו כן.",
     "fx": {
      "morale": -4,
      "attr": [
       "mental",
       1.0
      ]
     }
    }
   ]
  },
  {
   "eid": "m_data_vs_eyes",
   "title": "הנתונים נגד העיניים",
   "stages": [
    "manager"
   ],
   "weight": 1.8,
   "cooldown": 34,
   "when": {
    "needs_club": true
   },
   "body": "האנליסט מראה שהשחקן שאתה הכי אוהב הוא הגרוע בקבוצה במספרים.\nהעיניים שלך אומרות אחרת.",
   "choices": [
    {
     "label": "ללכת עם הנתונים",
     "hint": "מודרני",
     "text": "הורדת אותו. המספרים צדקו, וזה לקח חודשיים להוכיח.",
     "fx": {
      "coaching": 7,
      "board": 5,
      "trust": -4
     }
    },
    {
     "label": "ללכת עם העיניים",
     "hint": "אינטואיציה",
     "text": "השארת אותו. הוא הכריע שני משחקים, והאנליסט הוסיף עמודה חדשה לדוח.",
     "fx": {
      "trust": 8,
      "board": -3,
      "coaching": 3
     }
    }
   ]
  },
  {
   "eid": "m_preseason_tour",
   "title": "סיבוב הכנה בחו\"ל",
   "stages": [
    "manager"
   ],
   "weight": 1.6,
   "cooldown": 45,
   "when": {
    "needs_club": true,
    "week_max": 4
   },
   "body": "ההנהלה מכרה סיבוב הכנה בן עשרה ימים בצד השני של העולם.\nזה כסף גדול וג'ט לג גדול.",
   "choices": [
    {
     "label": "לנצל לגיבוש",
     "hint": "קבוצה",
     "text": "עשית מזה מחנה אימונים אמיתי. חזרתם קבוצה.",
     "fx": {
      "trust": 10,
      "morale": 8,
      "coaching": 4,
      "board": 4
     }
    },
    {
     "label": "להתלונן בפומבי",
     "hint": "עימות",
     "text": "אמרת שזה פוגע בהכנה. ההנהלה לא אהבה את הכותרת.",
     "fx": {
      "board": -10,
      "media": 5,
      "trust": 4
     }
    }
   ]
  },
  {
   "eid": "m_captain_rebellion",
   "title": "הקפטן מול הדלת",
   "stages": [
    "manager"
   ],
   "weight": 1.8,
   "cooldown": 40,
   "when": {
    "needs_club": true,
    "has_mate": true
   },
   "body": "הקפטן ביקש להיכנס. הוא אומר שהוא מדבר בשם הקבוצה,\nושהשיטה החדשה לא עובדת.",
   "choices": [
    {
     "label": "להקשיב ולשנות משהו",
     "hint": "גמישות",
     "text": "שינית פרט אחד שהם ביקשו. זה קנה לך את החדר.",
     "fx": {
      "trust": 12,
      "coaching": 4,
      "board": -2
     }
    },
    {
     "label": "להוריד לו את הסרט",
     "hint": "כוח",
     "text": "לקחת את הסרט. החדר השתתק, וחצי ממנו הפסיק להתאמץ.",
     "fx": {
      "trust": -14,
      "morale": -8,
      "board": 3
     }
    },
    {
     "label": "להסביר למה זה יעבוד",
     "hint": "שכנוע",
     "text": "פתחת את הלוח והראית להם. שניים השתכנעו, והשאר נתנו זמן.",
     "fx": {
      "coaching": 6,
      "trust": 5
     }
    }
   ]
  },
  {
   "eid": "m_cup_minnows",
   "title": "מול קבוצה מליגה נמוכה",
   "stages": [
    "manager"
   ],
   "weight": 1.6,
   "cooldown": 34,
   "when": {
    "needs_club": true
   },
   "body": "גביע, מגרש קטן, קבוצה חובבנית, ואלף אנשים שחיכו לזה כל השנה.",
   "choices": [
    {
     "label": "להעלות הרכב מלא",
     "hint": "כבוד",
     "text": "העלית את הטובים. ניצחתם 4:0, והמארחים אמרו שכיבדת אותם.",
     "fx": {
      "fans": 6,
      "board": 4,
      "trust": 3,
      "coaching": 2
     }
    },
    {
     "label": "להעלות צעירים",
     "hint": "הזדמנות",
     "text": "נתת לילדים לשחק. אחד מהם קבע ונכנס להרכב הבוגר.",
     "fx": {
      "coaching": 6,
      "trust": 5,
      "flag": "youth_project",
      "board": -3
     }
    }
   ]
  },
  {
   "eid": "m_star_contract",
   "title": "לחדש לכוכב",
   "stages": [
    "manager",
    "director"
   ],
   "weight": 1.8,
   "cooldown": 36,
   "when": {
    "needs_club": true,
    "has_mate": true
   },
   "body": "החוזה של {mate} נגמר בקיץ. הוא רוצה להיות השכיר הגבוה במועדון,\nופער השכר יישבר.",
   "choices": [
    {
     "label": "לשלם",
     "hint": "לשמור אותו",
     "text": "שילמתם. הוא נשאר, וחמישה אחרים ביקשו פגישה.",
     "fx": {
      "trust": 6,
      "board": -8,
      "fans": 8
     }
    },
    {
     "label": "לסרב ולמכור",
     "hint": "משמעת שכר",
     "text": "מכרתם. האוהדים כעסו, והמאזן נשם.",
     "fx": {
      "board": 10,
      "fans": -12,
      "trust": -4
     }
    }
   ]
  },
  {
   "eid": "d_ffp",
   "title": "הרגולטור על הקו",
   "stages": [
    "director",
    "owner"
   ],
   "weight": 1.8,
   "cooldown": 45,
   "when": {
    "needs_club": true
   },
   "body": "הליגה מודיעה שהמועדון חורג מכללי האיזון התקציבי.\nיש שלושה חודשים להציג תוכנית.",
   "choices": [
    {
     "label": "למכור שני שחקנים",
     "hint": "מהיר",
     "text": "מכרתם שניים. עמדתם בכללים והקבוצה נחלשה.",
     "fx": {
      "board": 10,
      "fans": -10,
      "business": 5
     }
    },
    {
     "label": "לקצץ בשכר ובצוות",
     "hint": "כואב פנימה",
     "text": "קיצצתם בפנים. הסגל נשאר, והאווירה במשרדים לא.",
     "fx": {
      "board": 6,
      "trust": -6,
      "business": 6
     }
    }
   ]
  },
  {
   "eid": "d_naming_rights",
   "title": "למכור את שם האצטדיון",
   "stages": [
    "director",
    "owner"
   ],
   "weight": 1.6,
   "cooldown": 45,
   "when": {
    "needs_club": true
   },
   "body": "חברה מציעה סכום גדול תמורת שם על {stadium}.\nהאוהדים קוראים לו בשם הישן מאז 1954.",
   "choices": [
    {
     "label": "למכור",
     "hint": "כסף",
     "text": "מכרתם. השלט הוחלף, והאוהדים ממשיכים לומר את השם הישן.",
     "fx": {
      "board": 14,
      "fans": -12,
      "business": 8
     }
    },
    {
     "label": "לשמור על השם",
     "hint": "זהות",
     "text": "ויתרתם על הכסף. ביציע תלו שלט תודה.",
     "fx": {
      "fans": 16,
      "board": -8,
      "rep": 4
     }
    }
   ]
  },
  {
   "eid": "d_womens_team",
   "title": "קבוצת הנשים",
   "stages": [
    "director",
    "owner"
   ],
   "weight": 1.6,
   "cooldown": 50,
   "when": {
    "needs_club": true
   },
   "body": "יש הצעה להקים מחלקת נשים מקצועית תחת המועדון.\nזה עולה כסף שלא רואים ממנו החזר בקרוב.",
   "choices": [
    {
     "label": "להקים",
     "hint": "טווח ארוך",
     "text": "הקמתם. תוך שלוש שנים זה היה אחד הדברים שהכי גאים בהם.",
     "fx": {
      "board": -6,
      "fans": 12,
      "rep": 6,
      "business": 3
     }
    },
    {
     "label": "לדחות",
     "hint": "עכשיו לא",
     "text": "דחיתם. שאלו על זה בכל ראיון במשך שנתיים.",
     "fx": {
      "board": 4,
      "fans": -6,
      "media": -4
     }
    }
   ]
  },
  {
   "eid": "d_staff_poached",
   "title": "חוטפים לך את הצוות",
   "stages": [
    "director",
    "manager"
   ],
   "weight": 1.6,
   "cooldown": 40,
   "when": {
    "needs_club": true
   },
   "body": "מועדון עשיר יותר מציע לראש הסקאוטינג שלך פי שניים.",
   "choices": [
    {
     "label": "להשוות ולשמור",
     "hint": "יקר",
     "text": "השווית. הוא נשאר, ושאר הצוות למד שאפשר לבקש.",
     "fx": {
      "board": -6,
      "coaching": 5,
      "trust": 4
     }
    },
    {
     "label": "לתת לו ללכת ולקדם מבפנים",
     "hint": "הזדמנות",
     "text": "קידמת את העוזרת שלו. היא הייתה טובה יותר.",
     "fx": {
      "coaching": 6,
      "board": 5,
      "business": 3
     }
    }
   ]
  },
  {
   "eid": "o_super_league",
   "title": "ההזמנה לליגת העל",
   "stages": [
    "owner"
   ],
   "weight": 1.4,
   "cooldown": 60,
   "when": {
    "needs_club": true
   },
   "body": "קבוצה של מועדונים מזמינה אתכם לליגה סגורה בלי ירידה.\nהכסף אינסופי, האוהדים כבר מארגנים מחאה.",
   "choices": [
    {
     "label": "להצטרף",
     "hint": "כסף",
     "text": "הצטרפתם. המועדון התעשר, וחלק מהאוהדים לא חזרו לעולם.",
     "fx": {
      "board": 20,
      "fans": -30,
      "rep": -8,
      "business": 10
     }
    },
    {
     "label": "לסרב פומבית",
     "hint": "עמדה",
     "text": "סירבת בהצהרה. הפכת לאחד הטובים בעולם הכדורגל למשך שבוע.",
     "fx": {
      "fans": 25,
      "rep": 12,
      "board": -10,
      "media": 10,
      "honour": "הסירוב לליגת העל"
     }
    }
   ]
  },
  {
   "eid": "o_sack_decision",
   "title": "לפטר או לא",
   "stages": [
    "owner"
   ],
   "weight": 2.0,
   "cooldown": 34,
   "when": {
    "needs_club": true,
    "table_bottom": 12
   },
   "body": "המאמן שאתה מאמין בו נמצא בסדרה גרועה.\nהיועצים אומרים לפטר עכשיו. הבטן אומרת אחרת.",
   "choices": [
    {
     "label": "לתת לו זמן",
     "hint": "אמון",
     "text": "נתת. זה הסתדר, ואתה זכית לומר \"אמרתי לכם\".",
     "fx": {
      "board": -6,
      "trust": 14,
      "coaching": 3
     }
    },
    {
     "label": "לפטר",
     "hint": "החלטה",
     "text": "פיטרת. הקבוצה קפצה לשלושה משחקים ואז חזרה למקום.",
     "fx": {
      "board": 6,
      "fans": 4,
      "trust": -10
     }
    }
   ]
  },
  {
   "eid": "o_community",
   "title": "השכונה סביב האצטדיון",
   "stages": [
    "owner"
   ],
   "weight": 1.4,
   "cooldown": 50,
   "when": {
    "needs_club": true
   },
   "body": "התושבים מתלוננים על חניה, רעש ולכלוך בכל משחק בית.\nהעירייה מאיימת בהגבלות.",
   "choices": [
    {
     "label": "להשקיע בשכונה",
     "hint": "שכנות",
     "text": "מימנתם חניון ומגרש שכונתי. ההתנגדות נעלמה.",
     "fx": {
      "board": -8,
      "fans": 10,
      "rep": 5
     }
    },
    {
     "label": "להילחם משפטית",
     "hint": "עימות",
     "text": "ניצחתם בבית משפט. הפכתם לשכן שאף אחד לא אוהב.",
     "fx": {
      "board": 4,
      "fans": -8,
      "media": -4
     }
    }
   ]
  },
  {
   "eid": "u_podcast",
   "title": "לפתוח פודקאסט",
   "stages": [
    "pundit",
    "legend",
    "retired"
   ],
   "weight": 1.8,
   "cooldown": 40,
   "body": "שני מפיקים מציעים פודקאסט שבועי שלך.\nזה חופש מוחלט, ובלי רשת מאחורי הגב.",
   "choices": [
    {
     "label": "לפתוח",
     "hint": "עצמאות",
     "text": "פתחת. תוך שנה זה היה גדול יותר מהתוכנית שעזבת.",
     "fx": {
      "money": 500000,
      "media": 10,
      "rep": 6,
      "business": 5
     }
    },
    {
     "label": "להישאר ברשת",
     "hint": "יציבות",
     "text": "נשארת. משכורת בטוחה, פחות חופש.",
     "fx": {
      "money": 700000,
      "media": 4
     }
    }
   ]
  },
  {
   "eid": "u_wrong_on_air",
   "title": "טעית בשידור חי",
   "stages": [
    "pundit"
   ],
   "weight": 1.8,
   "cooldown": 30,
   "body": "אמרת בביטחון משהו שהתברר כשגוי לגמרי, ובאולפן צחקו.\nהקטע כבר ברשת.",
   "choices": [
    {
     "label": "להתנצל ולצחוק על עצמך",
     "hint": "אנושי",
     "text": "פתחת את התוכנית הבאה בקטע. הצופים אהבו אותך יותר.",
     "fx": {
      "media": 6,
      "fans": 6,
      "rep": 2
     }
    },
    {
     "label": "להתעקש שצדקת",
     "hint": "גאווה",
     "text": "התעקשת. זה הפך לבדיחה שרודפת אותך.",
     "fx": {
      "media": -5,
      "rep": -3,
      "morale": -3
     }
    }
   ]
  },
  {
   "eid": "u_criticise_friend",
   "title": "לבקר חבר בשידור",
   "stages": [
    "pundit"
   ],
   "weight": 1.6,
   "cooldown": 34,
   "body": "השחקן שהיה השותף שלך לחדר במשך שש שנים היה גרוע היום.\nהמנחה מסתובב אליך.",
   "choices": [
    {
     "label": "להגיד את האמת",
     "hint": "אמינות",
     "text": "אמרת בדיוק מה שראית, בכבוד. הוא הבין, בסוף.",
     "fx": {
      "media": 7,
      "rep": 5,
      "morale": -4
     }
    },
    {
     "label": "לרכך",
     "hint": "חברות",
     "text": "ריככת. הצופים הרגישו, והחבר שלך ישן טוב.",
     "fx": {
      "media": -3,
      "morale": 5
     }
    }
   ]
  },
  {
   "eid": "ag_client_scandal",
   "title": "הלקוח בכותרות",
   "stages": [
    "agent"
   ],
   "weight": 2.0,
   "cooldown": 30,
   "body": "הלקוח הכי גדול שלך עשה משהו טיפשי, וזה בכל מקום.\nהטלפון שלך לא מפסיק.",
   "choices": [
    {
     "label": "לצאת להגנה פומבית",
     "hint": "נאמנות",
     "text": "עמדת מולם. הוא לא שכח, וחלק מהמועדונים כן.",
     "fx": {
      "rep": -4,
      "media": 6,
      "money": 200000
     }
    },
    {
     "label": "לנהל את זה בשקט מאחורי הקלעים",
     "hint": "מקצוענות",
     "text": "טיפלת בלי מיקרופון. תוך חודש זה נעלם.",
     "fx": {
      "business": 8,
      "rep": 4,
      "money": 400000
     }
    }
   ]
  },
  {
   "eid": "ag_deal_collapse",
   "title": "העסקה שהתפוצצה בדקה 89",
   "stages": [
    "agent"
   ],
   "weight": 1.8,
   "cooldown": 32,
   "body": "חצי שעה לסגירת החלון, והמועדון הקונה מושך את ההצעה.\nהלקוח שלך יושב במלון עם מזוודות.",
   "choices": [
    {
     "label": "למצוא מועדון חלופי בשעה",
     "hint": "לחץ",
     "text": "עשית עשרים טלפונים. בדקה האחרונה נחתם משהו סביר.",
     "fx": {
      "business": 8,
      "rep": 6,
      "money": 300000
     }
    },
    {
     "label": "להחזיר אותו ולתקן בקיץ",
     "hint": "סבלנות",
     "text": "הוא חזר, שיחק חצי שנה מצוין, ובקיץ קיבל הצעה טובה יותר.",
     "fx": {
      "rep": 4,
      "money": 700000,
      "business": 4
     }
    }
   ]
  },
  {
   "eid": "ag_client_retires",
   "title": "לקוח שרוצה לפרוש",
   "stages": [
    "agent"
   ],
   "weight": 1.6,
   "cooldown": 40,
   "body": "שחקן בן 29 אומר לך שנמאס לו. הוא רוצה לפתוח בית קפה.",
   "choices": [
    {
     "label": "לשכנע אותו להמשיך",
     "hint": "עמלה",
     "text": "שכנעת. הוא שיחק עוד שנתיים ולא היה מאושר.",
     "fx": {
      "money": 450000,
      "rep": -3
     }
    },
    {
     "label": "לעזור לו לצאת יפה",
     "hint": "אנושי",
     "text": "סידרת לו פרידה מכובדת ועסקה על בית הקפה. הוא שולח לך קפה עד היום.",
     "fx": {
      "business": 7,
      "rep": 8,
      "morale": 6
     }
    }
   ]
  },
  {
   "eid": "lg_grandchild",
   "title": "הדור השלישי",
   "stages": [
    "legend"
   ],
   "weight": 1.4,
   "cooldown": 60,
   "once": true,
   "body": "הנכד שלך התקבל למחלקת הנוער של {club}.\nהוא לובש את המספר שלך.",
   "choices": [
    {
     "label": "לבוא לכל משחק ולשתוק",
     "hint": "נוכחות",
     "text": "ישבת ביציע ולא אמרת מילה. הוא ידע שאתה שם.",
     "fx": {
      "morale": 18,
      "fans": 6,
      "honour": "הדור השלישי ב{club}"
     }
    },
    {
     "label": "להתרחק כדי לא להעיק",
     "hint": "חופש",
     "text": "לא הגעת. הוא שיחק בלי הצל שלך, וזה כנראה היה נכון.",
     "fx": {
      "morale": 8,
      "attr": [
       "mental",
       0.5
      ]
     }
    }
   ]
  },
  {
   "eid": "lg_old_teammate",
   "title": "חבר מהקבוצה ההיא",
   "stages": [
    "legend",
    "retired"
   ],
   "weight": 1.6,
   "cooldown": 45,
   "body": "אחד מהחבר'ה של אותה קבוצה נקלע לצרות. כלכליות, ולא רק.",
   "choices": [
    {
     "label": "לעזור בשקט",
     "hint": "חברות",
     "text": "העברת כסף ולא סיפרת לאיש. הוא קם על הרגליים.",
     "fx": {
      "money": -400000,
      "morale": 12,
      "rep": 2
     }
    },
    {
     "label": "לארגן משחק התרמה",
     "hint": "פומבי",
     "text": "אירגנת משחק ותיקים. הוא נעלב קצת, וזה הציל אותו.",
     "fx": {
      "fans": 12,
      "media": 6,
      "money": -80000,
      "morale": 8
     }
    }
   ]
  }
 ]
};
