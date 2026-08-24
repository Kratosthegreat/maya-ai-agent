// ---------------------------------------------------------------------------
// מנוע העלילה — 28 צמתי החלטה. פורט מ-football_manager/story.py
// ---------------------------------------------------------------------------

const STORY = [];
function ev(e) { STORY.push(e); return e; }

// קיצורי אפקטים (g = GameState)
const mor = (g, d) => { g.me.morale = clamp(g.me.morale + d, 5, 99); };
const tru = (g, d) => { const c = g.myClub(); if (c) c.managerTrust = clamp(c.managerTrust + d, 0, 100); };
const fan = (g, d) => { const c = g.myClub(); if (c) c.fanSupport = clamp(c.fanSupport + d, 0, 100); };
const rep = (g, d) => { g.me.reputation = clamp(g.me.reputation + d, 1, 99); };
const att = (g, a, d) => addGrowth(g.me, a, d);

// ===========================================================================
// שלב 0 — כדורגל נוער (13-15)
// ===========================================================================

ev({
  eid: "first_boots", title: "הנעליים הראשונות", stages: ["youth"], weight: 7.0, once: true,
  cond: g => g.week >= 2,
  body: g => `אבא שלך שם על השולחן קופסה.\n` +
    `נעלי כדורגל אמיתיות — לא של אח גדול, לא מהשוק.\n\n` +
    `"אני לא מבין בזה," הוא אומר, "אבל אמרו לי שאתה טוב. תוכיח."`,
  choices: [
    { label: "לשמור אותן רק למשחקים", hint: "משמעת",
      apply: g => { att(g, "mental", 1.2); mor(g, 5);
        return "נעלת אותן רק בימי משחק. באימונים המשכת עם הישנות, עד שנקרעו."; } },
    { label: "לשחק בהן בכל יום עד שיתפרקו", hint: "כדרור ↑↑",
      apply: g => { att(g, "dribbling", 1.6); att(g, "physical", 0.4);
        return "שחקת בהן בבית ספר, ברחוב, בחצר. תוך חודשיים הן נראו כמו סמרטוט — ואתה נראית אחרת."; } },
  ],
});

ev({
  eid: "school_or_football", title: "מבחן ביום משחק", stages: ["youth"], weight: 4.0, once: false,
  cond: g => g.me.age <= 15,
  body: g => `מחר גמר מחוזי. מחר גם מבחן במתמטיקה.\n` +
    `המחנכת אמרה שאם תיעדר שוב — היא מזמינה את ההורים.`,
  choices: [
    { label: "לשחק. המבחן יחכה.", hint: "המאמן ↑, בית הספר ↓",
      apply: g => { tru(g, 8); att(g, "shooting", 0.8); g.setFlag("school_trouble", true);
        return "כבשת שניים. בבית חיכתה שיחה ארוכה, אבל אף אחד לא הזכיר את זה יותר אחרי הגמר."; } },
    { label: "מבחן. אני לא זורק את הלימודים.", hint: "ראש ↑",
      apply: g => { att(g, "mental", 1.4); tru(g, -5);
        return "עברת את המבחן. הקבוצה הפסידה 1:0 והמאמן הסתכל עליך אחרת שבועיים."; } },
    { label: "לנסות את שניהם — מבחן בבוקר, משחק בערב",
      apply: g => { att(g, "mental", 0.6); g.me.fitness = clamp(g.me.fitness - 20, 5, 100);
        mor(g, -3);
        return "הגעת למשחק שרוף. שיחקת חצי שעה ולא זכרת ממנה כלום."; } },
  ],
});

ev({
  eid: "growth_spurt", title: "פתאום הכל ארוך", stages: ["youth"], weight: 5.0, once: true,
  cond: g => g.me.age >= 14,
  body: g => `גדלת שמונה סנטימטרים בחצי שנה.\n` +
    `הרגליים לא במקום שהן היו, הכדור לא מגיע לאן שכיוונת,\n` +
    `וכל מי שהיה נמוך ממך פתאום עוקף אותך בכדרור.`,
  choices: [
    { label: "לעבוד על תיאום ושליטה", hint: "כדרור ומסירה ↑",
      apply: g => { att(g, "dribbling", 1.3); att(g, "passing", 1.0); att(g, "pace", -0.4);
        return "חודשיים של תרגילי קונוסים משעממים. חזרת לשלוט בגוף החדש שלך."; } },
    { label: "לנצל את הגובה ולהתחזק", hint: "כוח פיזי ↑↑",
      apply: g => { att(g, "physical", 2.0); att(g, "dribbling", -0.5);
        return "הפכת לילד הכי חזק במגרש. גם הכי מגושם, אבל אף אחד לא הזיז אותך מהכדור."; } },
  ],
});

ev({
  eid: "scout_in_stands", title: "האיש עם המחברת", stages: ["youth"], weight: 4.5, once: true,
  cond: g => g.me.age >= 14 && g.me.season.apps >= 3,
  body: g => `מאחורי השער עומד גבר עם מעיל ומחברת.\n` +
    `כולם יודעים מי זה. הקבוצה משחקת אחרת כשהוא שם — כולם רוצים להיראות.`,
  choices: [
    { label: "לשחק בדיוק כמו תמיד", hint: "בטוח",
      apply: g => { att(g, "mental", 1.0); rep(g, 2);
        return "לא ניסית להרשים. הוא רשם משהו קצר והלך. שבוע אחרי זה שאלו עליך."; } },
    { label: "לנסות משהו מיוחד", hint: "הימור",
      apply: g => g.showOff() },
  ],
});

ev({
  eid: "left_out", title: "הרשימה על הדלת", stages: ["youth"], weight: 3.5, once: false,
  cond: g => g.me.age <= 15 && g.week >= 6,
  body: g => `רשימת הנוסעים לטורניר תלויה על דלת חדר ההלבשה.\n` +
    `קראת אותה שלוש פעמים. השם שלך לא שם.`,
  choices: [
    { label: "לשאול את המאמן למה", hint: "אמת בפנים",
      apply: g => g.askWhy() },
    { label: "להתאמן לבד כל השבוע", hint: "כוח פיזי ↑, מורל ↓",
      apply: g => { att(g, "physical", 1.4); att(g, "shooting", 0.6); mor(g, -8);
        return "כל בוקר, מגרש ריק, אתה והכדור. בטורניר הבא לא היה מה לשאול."; } },
    { label: "לא להגיע לאימונים שבוע", hint: "מסוכן",
      apply: g => { tru(g, -14); mor(g, 3);
        return "נעלמת שבוע. כשחזרת, המאמן אמר רק: \"נחמד שהצטרפת.\" זה עלה לך."; } },
  ],
});

ev({
  eid: "academy_offer", title: "מכתב ממועדון גדול", stages: ["youth"], weight: 6.0, once: true,
  cond: g => g.me.age >= 14 && g.youthAcademySuitor() !== null,
  body: g => `${g.youthAcademySuitor().name} מזמינים אותך למחלקת הנוער שלהם.\n` +
    `מתקנים אחרים, מאמנים אחרים, ילדים טובים יותר.\n\n` +
    `זה גם שעה נסיעה לכל כיוון, וחברים שלא תראה יותר.`,
  choices: [
    { label: "לעבור למועדון הגדול", hint: "מתקנים ↑↑, תחרות קשה",
      apply: g => g.joinBigAcademy() },
    { label: "להישאר בבית", hint: "דקות משחק, אמון",
      apply: g => { tru(g, 12); mor(g, 6); g.setFlag("stayed_home", true);
        return "נשארת. במועדון שלך הפכת לילד שכולם מדברים עליו — וזה בדיוק מה שהיה צריך."; } },
  ],
});

// ===========================================================================
// שלב 1 — נוער ופריצה
// ===========================================================================

ev({
  eid: "first_call_up", title: "קריאה מהמשרד", stages: ["academy"], weight: 6.0, once: true,
  cond: g => g.week >= 2,
  body: g => `עוזר המאמן עוצר אותך במסדרון של ${g.myClub().name}.\n` +
    `"${g.myClub().managerName} רוצה אותך באימון של הבוגרים ביום חמישי. אל תדפוק את זה."\n\n` +
    `אתה בן ${g.me.age}. חצי מהחדר הזה הם אנשים שראית בטלוויזיה.`,
  choices: [
    { label: "להיכנס חזק — שיזכרו את השם שלך", hint: "אמון המאמן ↑↑",
      apply: g => { tru(g, 9); mor(g, 6); att(g, "physical", 0.7); g.setFlag("bold_debut", true);
        return "נכנסת לקפטן בכניסה קשה. חצי מהקבוצה צחקה, המאמן רשם משהו במחברת. אתה בפנים."; } },
    { label: "לשחק פשוט, בלי סיכונים", hint: "בטוח",
      apply: g => { tru(g, 4); att(g, "passing", 0.6);
        return "94% מסירות מדויקות ואפס טעויות. לא הרשמת אף אחד, אבל גם לא נתת סיבה להוריד אותך."; } },
    { label: "להישאר בנוער עוד קצת", hint: "מסוכן",
      apply: g => { mor(g, -4); tru(g, -6); g.setFlag("declined_first", true);
        return "אמרת שאתה עוד לא מוכן. המאמן הנהן. לפעמים הנהון כזה עולה שנתיים."; } },
  ],
});

ev({
  eid: "youth_mentor", title: "הוותיק שבפינת ההלבשה", stages: ["academy", "player"], weight: 2.5, once: true,
  cond: g => g.me.age <= 22,
  body: () => 'הוותיק של הקבוצה מתיישב לידך אחרי אימון.\n' +
    '"אני רואה אותך. יש לך רגליים. מה שאין לך זה ראש.\n' +
    'בוא נשב על וידאו פעמיים בשבוע — בחינם. רק תבוא בזמן."',
  choices: [
    { label: "לבוא לכל מפגש", hint: "קריאת משחק ↑↑",
      apply: g => { att(g, "mental", 2.0); mor(g, 3); g.setFlag("has_mentor", true);
        return "שלושה חודשים של וידאו. פתאום אתה רואה מסירות שלפני חודש לא היו קיימות."; } },
    { label: "תודה, אני מסתדר",
      apply: g => { att(g, "dribbling", 0.8); return "המשכת לעבוד לבד על הכדור. הוא לא הציע שוב."; } },
  ],
});

ev({
  eid: "loan_offer", title: "הצעת השאלה", stages: ["player"], weight: 3.0, once: true,
  cond: g => g.me.age <= 23 && g.minutesShare() < 0.35,
  body: g => `אתה לא משחק. ${g.loanTargetName()} מהליגה הלאומית רוצים אותך בהשאלה לעונה.\n` +
    `"אצלנו אתה משחק 90 דקות כל שבוע. אצלם אתה מחמם ספסל ומזדקן."`,
  choices: [
    { label: "לצאת להשאלה ולשחק", hint: "דקות משחק ↑↑, מוניטין ↓", apply: g => g.goOnLoan() },
    { label: "להישאר ולהילחם על מקום",
      apply: g => { tru(g, 5); mor(g, -2); return "נשארת. המאמן העריך את זה — עכשיו תוכיח שהוא צדק."; } },
  ],
});

// ===========================================================================
// שלב 2 — חיי שחקן מקצוען
// ===========================================================================

ev({
  eid: "bench_frustration", title: "שבוע חמישי על הספסל", stages: ["player", "veteran"],
  weight: 3.0, once: false,
  cond: g => g.noStartStreak >= 4 && g.me.age >= 19,
  body: g => `חמישה משחקים. אפס דקות.\nאתה עומד מול הדלת של ${g.myClub().managerName} ומחזיק את הידית.`,
  choices: [
    { label: "להיכנס ולהתעמת", hint: "מר-רווח: או שתשחק או שתיגמר", apply: g => g.confrontManager() },
    { label: "לשתוק ולהתאמן כפול", hint: "אמון ↑, מורל ↓",
      apply: g => { att(g, "physical", 1.0); tru(g, 6); mor(g, -5);
        return "נשארת אחרי כל אימון. הצוות שם לב. הסבלנות עולה לך במצב רוח."; } },
    { label: "לבקש מהסוכן למצוא מועדון אחר", hint: "פותח שוק העברות",
      apply: g => { g.setFlag("wants_transfer", true); tru(g, -10);
        return "הסוכן התחיל לעבוד. בחלון הקרוב יגיעו הצעות — והמאמן כבר יודע שאתה בדרך החוצה."; } },
  ],
});

ev({
  eid: "derby_week", title: "שבוע דרבי", stages: ["player", "veteran"], weight: 2.0, once: false,
  cond: g => g.week >= 3,
  body: g => `העיר לא ישנה. שלטי חוצות, אוהדים מחוץ למתחם האימונים,\n` +
    `וכתבה שמצטטת שחקן מהיריבה: "${g.me.name}? לא מכיר."`,
  choices: [
    { label: "לענות לו בתקשורת", hint: "מוניטין ↑, לחץ ↑",
      apply: g => { rep(g, 4); fan(g, 6); g.setFlag("derby_beef", true);
        return "הכותרת שלך פתחה את המהדורה. עכשיו אסור לך לככב פחות מהמצוין."; } },
    { label: "לשתוק ולעלות על המגרש",
      apply: g => { mor(g, 4); att(g, "mental", 0.8);
        return "לא אמרת מילה כל השבוע. בחדר ההלבשה זה נשמע חזק יותר מכל ציטוט."; } },
    { label: "להזמין את המשפחה ליציע ולנשום",
      apply: g => { mor(g, 7); return "ראית אותם ביציע בחימום. פתאום זה שוב רק כדורגל."; } },
  ],
});

ev({
  eid: "scandal_night", title: "צילום מהמועדון", stages: ["player", "veteran"], weight: 1.6, once: true,
  cond: g => g.me.age >= 19 && g.me.reputation >= 30,
  body: () => "3:40 לפנות בוקר. מישהו צילם אותך יוצא ממועדון לילה\n" +
    "שני ימים לפני משחק. הסרטון כבר ברשת.\nהדובר מחכה לתשובה שלך עוד עשר דקות.",
  choices: [
    { label: "להתנצל בפומבי ולקחת אחריות",
      apply: g => { rep(g, -3); tru(g, 4); fan(g, 2); mor(g, -2);
        return "התנצלת בלי תירוצים. התקשורת התייבשה תוך יומיים. המאמן העריך את זה יותר ממה שהודה."; } },
    { label: "להכחיש הכל", hint: "הימור", apply: g => g.denyScandal() },
    { label: "לתרום את שכר השבוע ולא לומר מילה", hint: "עולה כסף",
      apply: g => { g.spend(g.me.contract.wage); fan(g, 9); rep(g, 2);
        return "העברת את שכר השבוע למועדון ילדים בשכונה. מישהו הדליף את זה. האוהדים אימצו אותך."; } },
  ],
});

ev({
  eid: "national_call", title: "המעטפה מהנבחרת", stages: ["player", "veteran"], weight: 5.0, once: true,
  cond: g => g.me.reputation >= 52 && !g.flag("national_debut"),
  body: () => "סגל הנבחרת פורסם. השם שלך שם, בשורה התחתונה, מודפס קטן.\n" +
    "אמא שלך שלחה צילום מסך עם אחת עשרה נקודות קריאה.",
  choices: [
    { label: "לנסוע ולתת הכל", hint: "מוניטין ↑↑", apply: g => g.nationalDebut() },
    { label: "להתנצל — הגוף צריך מנוחה",
      apply: g => { rep(g, -5); g.me.fitness = 100; mor(g, -3);
        return "ויתרת על הקריאה הראשונה. הסלקטור לא שכח."; } },
  ],
});

ev({
  eid: "big_club_interest", title: "שיחה מאירופה", stages: ["player", "veteran"], weight: 4.5, once: false,
  cond: g => g.bigClubSuitor() !== null && [11, 12, 13].includes(g.week),
  body: g => `הסוכן שלך מתקשר בשתיים בלילה.\n` +
    `"${g.bigClubSuitor().name} שאלו עליך. לא סתם שאלו — הם שלחו צופה לשלושה משחקים.\n` +
    `תגיד לי עכשיו: אם תגיע הצעה, אתה בפנים?"`,
  choices: [
    { label: "תגיד להם שאני מוכן", hint: "מגדיל סיכוי להצעה",
      apply: g => { g.setFlag("open_to_europe", true); mor(g, 5);
        return "המילה עברה. עכשיו כל משחק הוא מבחן קבלה."; } },
    { label: "אני מרוכז במועדון שלי",
      apply: g => { tru(g, 8); fan(g, 7); mor(g, 2);
        return "הצהרת נאמנות. המועדון הרים לך את השכר בלי שביקשת."; } },
  ],
});

ev({
  eid: "captain_armband", title: "הסרט", stages: ["player", "veteran"], weight: 4.0, once: true,
  cond: g => g.me.age >= 25 && g.myClub() && g.myClub().managerTrust >= 65,
  body: g => `${g.myClub().managerName} סוגר את הדלת.\n` +
    `"הקפטן הולך בסוף העונה. אני רוצה שאתה תיקח את הסרט.\n` +
    `זה אומר גם את הפעמים שצריך לצעוק על מישהו שאתה אוהב."`,
  choices: [
    { label: "לקחת את הסרט", hint: "מנהיגות, אחריות, לחץ", apply: g => g.becomeCaptain() },
    { label: "להציע במקומי את הוותיק",
      apply: g => { tru(g, 3); mor(g, 2);
        return "ויתרת לטובת מישהו אחר. חדר ההלבשה זכר לך את זה שנים."; } },
  ],
});

ev({
  eid: "serious_injury", title: "הרגל נתקעה בדשא", stages: ["player", "veteran"], weight: 3.0, once: false,
  cond: g => g.me.injuryWeeks >= 8,
  body: g => `${g.me.injuryName}. ${g.me.injuryWeeks} שבועות, אם הכל ילך טוב.\n` +
    `הרופא מדבר, אתה שומע רק את המילה "אם".`,
  choices: [
    { label: "שיקום לפי הספר, בלי קיצורי דרך", hint: "בטוח",
      apply: g => { att(g, "mental", 1.2); mor(g, -4); g.setFlag("clean_rehab", true);
        return "חזרת בזמן, בלי הישנות. איבדת חצי עונה והרווחת גוף שמחזיק."; } },
    { label: "לדחוף חזרה מוקדם — הקבוצה צריכה אותי", hint: "הימור מסוכן", apply: g => g.rushRehab() },
    { label: "לנצל את הזמן ללימודי אימון", hint: "פותח דלתות לעתיד", apply: g => g.studyDuringInjury() },
  ],
});

ev({
  eid: "sponsor_deal", title: "חוזה פרסום", stages: ["player", "veteran"], weight: 2.2, once: false,
  cond: g => g.me.reputation >= 45,
  body: () => "חברת נעליים שמה על השולחן חוזה שנתי.\n" +
    "הכסף מכובד. התנאי: שלושה ימי צילומים בעונה, אחד מהם בשבוע של משחק.",
  choices: [
    { label: "לחתום", hint: "₪450,000",
      apply: g => { g.earn(450000); g.me.mediaSkill = clamp(g.me.mediaSkill + 6, 0, 100); tru(g, -3);
        return "חתמת. הצטלמת. המאמן ראה את הפוסטר בכניסה למתחם ולא חייך."; } },
    { label: "לסרב — לא בשבוע של משחק",
      apply: g => { tru(g, 5); att(g, "mental", 0.5); return "סירבת. הסוכן כעס. הצוות המקצועי לא."; } },
  ],
});

ev({
  eid: "contract_talks", title: "שולחן המשא ומתן", stages: ["player", "veteran"], weight: 8.0, once: false,
  cond: g => g.me.contract.yearsLeft <= 0 && g.myClub() !== null,
  body: g => `החוזה שלך נגמר בסוף העונה.\n${g.myClub().name} הניחו הצעה על השולחן: ` +
    `₪${fmt(g.renewalOffer())} לשבוע.`,
  choices: [
    { label: "לחתום מיד", hint: "ביטחון", apply: g => g.signRenewal(1.0) },
    { label: "לדרוש יותר", hint: "הימור על היחסים", apply: g => g.demandRaise() },
    { label: "לא לחתום — לצאת חופשי בקיץ", hint: "מסוכן, אבל משתלם",
      apply: g => { g.setFlag("free_agent_soon", true); tru(g, -14); fan(g, -8);
        return "לא חתמת. בקיץ תהיה חופשי — ועד אז אתה זר במועדון שלך."; } },
  ],
});

ev({
  eid: "dressing_room_split", title: "חדר הלבשה מפוצל", stages: ["player", "veteran"], weight: 2.0, once: false,
  cond: g => g.myClub() && g.myClub().managerTrust <= 40,
  body: g => `חצי מהקבוצה רוצה ש${g.myClub().managerName} ילך.\n` +
    `מישהו כבר דיבר עם עיתונאי. עכשיו מסתכלים עליך — אתה בין הבכירים.`,
  choices: [
    { label: "לתמוך במאמן בפומבי",
      apply: g => { tru(g, 16); mor(g, -3); g.setFlag("manager_ally", true);
        return "עמדת מולו והצהרת. חלק מהחבר'ה הפסיקו לדבר איתך. המאמן לא יוריד אותך יותר לעולם."; } },
    { label: "להצטרף למרד", hint: "עלול לפוצץ את העונה", apply: g => g.joinRevolt() },
    { label: "לכנס את הקבוצה בלי המאמן", hint: "מנהיגות",
      apply: g => { att(g, "mental", 1.5); mor(g, 5); g.setFlag("leader_moment", true);
        return "כינסת את כולם. שעה של אמת בלי צוות מקצועי. מאותו יום אתה המנהיג של החדר."; } },
  ],
});

ev({
  eid: "youngster_threat", title: "הילד שהגיע לתפוס את המקום", stages: ["player", "veteran"], weight: 2.0, once: false,
  cond: g => g.me.age >= 26 && g.rivalYoungster() !== null,
  body: g => {
    const kid = g.rivalYoungster();
    return `${kid.name}, בן ${kid.age}, נכנס לקבוצה.\n` +
      `אותה עמדה. אותן רגליים שהיו לך פעם. הצוות מדבר עליו בהתלהבות שכבר לא מדברים עליך.`;
  },
  choices: [
    { label: "לקחת אותו תחת חסותך", hint: "פותח דלת לאימון בעתיד", apply: g => g.mentorYoungster() },
    { label: "להילחם בו על כל דקה",
      apply: g => { att(g, "physical", 1.2); mor(g, -3); tru(g, 4);
        return "הפכת כל אימון לקרב. שנית בחזרה את הכיסא — לעונה אחת לפחות."; } },
    { label: "לבקש מהמאמן לשחק במקום אחר במגרש", hint: "מאריך קריירה", apply: g => g.changePosition() },
  ],
});

// ===========================================================================
// שלב 3 — ותיק ופרישה
// ===========================================================================

ev({
  eid: "body_signals", title: "הגוף מדבר", stages: ["veteran"], weight: 3.0, once: false,
  cond: g => g.me.age >= 32,
  body: g => `אתה בן ${g.me.age}. הבוקר לקח לך עשרים דקות לרדת מהמיטה.\n` +
    `הפיזיותרפיסט אומר שאפשר להמשיך — עם מחיר.`,
  choices: [
    { label: "להוריד עומסים ולשחק חכם",
      apply: g => { att(g, "mental", 1.4); att(g, "pace", -0.6); g.me.fitness = 100;
        return "התחלת לשחק בראש במקום ברגליים. פחות ספרינטים, יותר מסירות נכונות."; } },
    { label: "זריקות ולהמשיך כרגיל", hint: "מסוכן", apply: g => g.painkillers() },
    { label: "להתחיל לתכנן את היום שאחרי", hint: "מכין את הקריירה הבאה",
      apply: g => { mor(g, 2); return g.studyDuringInjury(); } },
  ],
});

ev({
  eid: "retirement_call", title: "ההחלטה", stages: ["veteran"], weight: 9.0, once: false,
  cond: g => g.retirementReady(),
  body: g => `${g.me.age}. ${g.me.career.apps + g.me.season.apps} משחקים בקריירה.\n` +
    `${g.me.career.goals + g.me.season.goals} שערים.\n` +
    `הסוכן שואל את השאלה שאתה מתחמק ממנה חודשים:\n` +
    `"עוד עונה, או שאנחנו מתחילים לדבר על מה שאחרי?"`,
  choices: [
    { label: "עוד עונה אחת. אני עוד מסוגל.",
      apply: g => { mor(g, 5); g.setFlag("one_more_year", true);
        return "עוד עונה. הגוף ישלם, אבל אתה עוד לא מוכן להוריד את הנעליים."; } },
    { label: "להכריז על פרישה בסוף העונה", hint: "פותח את הפרק הבא", apply: g => g.announceRetirement() },
  ],
});

ev({
  eid: "farewell_match", title: "משחק הפרידה", stages: ["retired"], weight: 10.0, once: true,
  cond: g => g.flag("retired_announced"),
  body: g => `${g.lastClubName()} מארגנים לך משחק פרידה.\n` +
    `האצטדיון מלא. הילדים ביציע לובשים את החולצה עם השם שלך.`,
  choices: [
    { label: "לשחק 20 דקות ולצאת לתשואות",
      apply: g => { rep(g, 6); g.recordHonour("משחק פרידה מול אצטדיון מלא"); g.earn(700000);
        return "עשרים דקות, נגיעה אחת שהזכירה לכולם למה. יצאת כשכל האצטדיון עומד."; } },
    { label: "לוותר על הטקס ולהיעלם בשקט",
      apply: g => { rep(g, -2); g.setFlag("quiet_exit", true);
        return "לא הגעת. חלק כיבדו את זה, רובם לא הבינו."; } },
  ],
});

ev({
  eid: "next_chapter", title: "הפרק הבא", stages: ["retired"], weight: 12.0, once: true,
  cond: () => true,
  body: g => `עברו שלושה חודשים מאז המשחק האחרון.\n` +
    `הטלפון עדיין מצלצל — אבל עכשיו מציעים לך דברים אחרים.\n\n${g.careerOptionsSummary()}`,
  choices: [
    { label: "מסלול אימון — מאמן עוזר במועדון", hint: "דורש תעודות אימון", apply: g => g.startCoaching() },
    { label: "אולפן — פרשן טלוויזיה", hint: "דורש כריזמה תקשורתית", apply: g => g.startPunditry() },
    { label: "סוכנות שחקנים", hint: "דורש ראש עסקי", apply: g => g.startAgency() },
    { label: "לקחת שנה חופש",
      apply: g => { g.setFlag("gap_year", true); mor(g, 8);
        return "שנה של כלום. משפחה, ים, שינה. כשחזרת, הטלפון עדיין צלצל."; } },
  ],
});

// ===========================================================================
// שלב 4 — מאמן ומנג'ר
// ===========================================================================

ev({
  eid: "first_manager_offer", title: "הצעה לשבת בכיסא הגדול", stages: ["coach"], weight: 8.0, once: true,
  cond: g => g.me.coaching >= 45,
  body: g => `${g.managerJobOfferName()} מחפשים מנג'ר.\n` +
    `הם רוצים מישהו שמכיר את המועדון מבפנים. הם רוצים אותך.\n` +
    `התנאי: אתה לוקח את זה עכשיו, באמצע משבר.`,
  choices: [
    { label: "לקחת את התפקיד", hint: "הופך אותך למנג'ר ראשי", apply: g => g.takeManagerJob() },
    { label: "עוד שנה כעוזר, ללמוד עוד",
      apply: g => { g.me.coaching = clamp(g.me.coaching + 10, 0, 100);
        return "נשארת ללמוד. ידע האימון שלך קפץ — וההצעה הבאה תהיה טובה יותר."; } },
  ],
});

ev({
  eid: "board_meeting", title: "ישיבת הנהלה", stages: ["manager"], weight: 4.0, once: false,
  cond: g => [6, 13, 20].includes(g.week) && g.myClub() !== null,
  body: g => `היו"ר פורש טבלה על השולחן.\n` +
    `"ציפינו ל${g.myClub().seasonExpectation}. אנחנו במקום ${g.leaguePosition()}.\n` +
    `תסביר לי מה קורה — ובלי סיסמאות."`,
  choices: [
    { label: "לקחת אחריות מלאה",
      apply: g => { g.board(6); return "לקחת הכל על עצמך. ההנהלה נתנה לך עוד זמן."; } },
    { label: "לדרוש תקציב להעברות", hint: "הימור על היחסים", apply: g => g.demandBudget() },
    { label: "להאשים את השופטים ואת הפציעות",
      apply: g => { g.board(-9); fan(g, 4);
        return "האוהדים אהבו את זה. ההנהלה ספרה את המילים ולא התרשמה."; } },
  ],
});

ev({
  eid: "star_wants_out", title: "הכוכב רוצה ללכת", stages: ["manager"], weight: 3.0, once: false,
  cond: g => g.squadStar() !== null,
  body: g => {
    const s = g.squadStar();
    return `${s.name} (${overall(s)}) נכנס למשרד עם הסוכן.\n"יש הצעה מבחוץ. אני רוצה שתשחרר אותי."`;
  },
  choices: [
    { label: "למכור ולהשקיע בסגל", hint: "תקציב ↑, איכות ↓", apply: g => g.sellStar() },
    { label: "לסרב ולהחזיק אותו בכוח", hint: "מורל הקבוצה בסיכון", apply: g => g.keepStar() },
    { label: "להציע לו את הקפטן והעלאה", hint: "עולה כסף", apply: g => g.promoteStar() },
  ],
});

ev({
  eid: "wonderkid", title: "ילד מהנוער", stages: ["manager"], weight: 3.0, once: false,
  cond: g => g.myClub() !== null,
  body: () => "מאמן הנוער מביא לך שם.\nבן 17. באימון הבוגרים הוריד שני בלמים בתנועה אחת.",
  choices: [
    { label: "להעלות אותו לסגל הבוגרים", hint: "הימור ארוך טווח", apply: g => g.promoteYouth() },
    { label: "להשאיר אותו בנוער עוד שנה",
      apply: g => { g.board(2); return "השארת אותו למטה. בטוח, אבל שקט מדי."; } },
  ],
});

ev({
  eid: "sack_race", title: "השם שלך בעיתון", stages: ["manager"], weight: 6.0, once: false,
  cond: g => g.myClub() && g.myClub().boardConfidence <= 32,
  body: g => `"${g.me.name} על הכוונת" — כותרת ראשית.\n` +
    `אמון ההנהלה: ${Math.round(g.myClub().boardConfidence)}%. שלושה משחקים להוכיח.`,
  choices: [
    { label: "לשנות הכל — טקטיקה, הרכב, הכל", hint: "הימור גדול", apply: g => g.radicalChange() },
    { label: "להמשיך בדרך שלי",
      apply: g => { g.board(-2); g.setFlag("stubborn", true);
        return "לא זזת מילימטר. אם זה יעבוד — אתה גאון. אם לא — אתה מובטל."; } },
    { label: "להתפטר בכבוד", hint: "יוצא בתנאים שלך", apply: g => g.resign() },
  ],
});

ev({
  eid: "bigger_job", title: "מועדון גדול מתקשר", stages: ["manager"], weight: 4.0, once: false,
  cond: g => g.managerSuitor() !== null,
  body: g => `${g.managerSuitor().name} רוצים אותך.\n` +
    `תקציב אחר, לחץ אחר, אצטדיון אחר.\nובמועדון שלך יש חוזה ואוהדים שקראו לך בשם.`,
  choices: [
    { label: "לעבור למועדון הגדול", hint: "מוניטין ↑↑", apply: g => g.moveManagerJob() },
    { label: "להישאר ולסיים את הפרויקט",
      apply: g => { g.board(10); fan(g, 12); rep(g, 3);
        return "נשארת. בעיר הזאת לא ישכחו לך את זה."; } },
  ],
});

// ===========================================================================
// שלב 5 — אחרי הכל
// ===========================================================================

ev({
  eid: "director_offer", title: "מהספסל למשרד", stages: ["manager"], weight: 3.0, once: true,
  cond: g => g.me.age >= 50 && g.me.business >= 30,
  body: () => "הבעלים מציע לך לעלות קומה: מנהל ספורטיבי.\n" +
    "בלי אימונים בגשם, בלי שריקות. רק החלטות — ואחריות על כולן.",
  choices: [
    { label: "לעלות למשרד", hint: "שלב קריירה חדש", apply: g => g.becomeDirector() },
    { label: "אני שייך לקו הצדדי",
      apply: g => { mor(g, 4); return "סירבת. הדשא עוד קורא לך."; } },
  ],
});

ev({
  eid: "buy_childhood_club", title: "המועדון שבו התחלת",
  stages: ["pundit", "agent", "director", "manager", "retired"], weight: 2.5, once: true,
  cond: g => g.money >= 4000000,
  body: g => `${g.firstClubName()} — המועדון שבו התחלת — בקשיים.\n` +
    `מציעים לך לרכוש שליטה. המחיר: ₪4,000,000 והרבה כאב ראש.`,
  choices: [
    { label: "לקנות את המועדון", hint: "₪4,000,000 — הופך אותך לבעלים", apply: g => g.buyClub() },
    { label: "לתרום ולהישאר בחוץ",
      apply: g => { g.spend(500000); rep(g, 3);
        return "תרמת חצי מיליון. שם המגרש הפך לשם שלך."; } },
  ],
});

ev({
  eid: "hall_of_fame", title: "היכל התהילה",
  stages: ["retired", "coach", "manager", "pundit", "agent", "director", "owner"], weight: 4.0, once: true,
  cond: g => g.me.career.apps >= 250 || g.honours.length >= 3,
  body: g => `מכתב רשמי: אתה נכנס להיכל התהילה.\n` +
    `${g.me.career.apps} משחקים. ${g.me.career.goals} שערים. ${g.honours.length} הישגים.`,
  choices: [
    { label: "לנאום ולהודות לכולם",
      apply: g => { rep(g, 8); g.recordHonour("היכל התהילה");
        return "עמדת שם עם הנאום ביד ולא הסתכלת בו אפילו פעם אחת."; } },
  ],
});

ev({
  eid: "child_debut", title: "הדור הבא",
  stages: ["coach", "manager", "pundit", "agent", "director", "owner", "legend"], weight: 2.0, once: true,
  cond: g => g.me.age >= 45,
  body: () => "הבן שלך חתם חוזה נעורים.\n" +
    "מאמן הנוער אומר שהוא טוב יותר ממה שאתה היית בגיל הזה.\n" +
    "העיתונות כבר כותבת את השם המשפחה בכותרות.",
  choices: [
    { label: "להגן עליו מהתקשורת",
      apply: g => { rep(g, 2); g.setFlag("protective_parent", true);
        return "סגרת את הדלת בפני כולם. הוא גדל בשקט."; } },
    { label: "לאמן אותו בעצמך",
      apply: g => { g.me.coaching = clamp(g.me.coaching + 5, 0, 100); g.setFlag("coaching_child", true);
        return "כל בוקר, שעה לפני כולם, במגרש הריק. זה הדבר הכי טוב שעשית מאז שפרשת."; } },
  ],
});

// ---------------------------------------------------------------------------

function eligibleEvents(g) {
  return STORY.filter(e => {
    if (e.stages.length && !e.stages.includes(g.stage)) return false;
    if (e.once && g.firedEvents.includes(e.eid)) return false;
    try { return !!e.cond(g); } catch (err) { return false; }
  });
}

function pickEvent(g, rng, chance = 0.34) {
  const candidates = eligibleEvents(g);
  if (!candidates.length) return null;
  const forced = candidates.filter(e => e.weight >= 8.0);
  if (!forced.length && rng.random() > chance) return null;
  const pool = forced.length ? forced : candidates;
  return rng.weighted(pool.map(e => [e, e.weight]));
}

function findEvent(eid) { return STORY.find(e => e.eid === eid) || null; }
