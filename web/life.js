// ---------------------------------------------------------------------------
// חיים אישיים — תאום JS של football_manager/life.py
//
// המשפחה נכנסה למשחק בגיל שלוש־עשרה והתאדתה ברגע שחתמת חוזה ראשון.
// זו טעות: ההורים לא נעלמים כשהילד מצליח. וגם, לשחקן יש חיים — יש מי
// שמחכה בבית, ויש מי שנשאר ער כשהפסדתם.
// ---------------------------------------------------------------------------

// [מפתח, שם, למה, עלות, גאווה]
const PARENT_ASKS = [
  ["house", "בית להורים", "הם עדיין בדירת השכירות שגדלת בה.", 1400000, 26],
  ["car", "אוטו לאבא", "האוטו שלו לא עובר טסט כבר שנתיים.", 180000, 12],
  ["debt", "לסגור חוב", "הם לא סיפרו לך, ואתה גילית במקרה.", 320000, 18],
  ["trip", "לקחת אותם למשחק בחו\"ל", "אמא שלך אף פעם לא טסה.", 90000, 14],
  ["sibling", "לממן לימודים לאח", "הוא טוב בלימודים. אתה טוב בכדורגל.", 240000, 16],
];

const PRIDE_START = 60.0;

// [מפתח, שם השלב, כמה שבועות עד שאפשר להתקדם]
const LIFE_STAGES = [
  ["dating", "בהיכרות", 10],
  ["serious", "זוגיות", 26],
  ["engaged", "מאורסים", 30],
  ["married", "נשואים", 0],
];
const LIFE_STAGE_NAMES = Object.fromEntries(LIFE_STAGES.map(r => [r[0], r[1]]));
const LIFE_STAGE_ORDER = LIFE_STAGES.map(r => r[0]);

// הזרקור הוא לא "יותר טוב" — הוא סוג אחר של חיים.
const PARTNER_KINDS = [
  ["hometown", "מהשכונה", "מכירה אותך מלפני שהיית מישהו.", 82, 8],
  ["student", "סטודנטית לרפואה", "יש לה חיים משלה, והם תובעניים.", 64, 14],
  ["athlete", "ספורטאית", "מבינה בדיוק מה זה שבוע לפני דרבי.", 74, 34],
  ["model", "דוגמנית", "כל יציאה שלכם היא ידיעה.", 46, 88],
  ["singer", "זמרת", "מפורסמת יותר ממך, לפחות בינתיים.", 42, 95],
  ["agent_daughter", "עורכת דין", "קוראת את החוזה שלך לפני שאתה חותם.", 70, 26],
];
const PARTNER_BY_KIND = Object.fromEntries(PARTNER_KINDS.map(r => [r[0], r]));

const PARTNER_FIRST = ["מאיה", "נועה", "שירה", "רוני", "טל", "אביגיל", "ליהי",
                       "יערה", "דנה", "עדי", "הילה", "אלמה", "סתיו", "רותם",
                       "יסמין", "אמילי", "לוסיה", "אנה", "סופיה", "מיה"];

const DRIFT_PER_WEEK = 0.55;
const NEGLECT_INTENSITY = 1.3;
const BREAKUP_MOOD = 22.0;
const BREAKUP_CHANCE = 0.16;

const GIFT_COST = 45000;
const HOLIDAY_COST = 160000;
const RING_COST = 400000;
const WEDDING_COST = 900000;

/** מצב ההורים. נבנה בפעם הראשונה שמישהו שואל. */
function parents(game) {
  let data = game.flags.parents;
  if (!data || typeof data !== "object") {
    data = { pride: PRIDE_START, given: [], ask: null, asked: 0 };
    game.flags.parents = data;
  }
  return data;
}

function partner(game) {
  const data = game.flags.partner;
  return data && typeof data === "object" ? data : null;
}

function makePartner(kind, rng, name = "") {
  const [key, , , support, spotlight] = PARTNER_BY_KIND[kind];
  return {
    kind: key,
    name: name || rng.choice(PARTNER_FIRST),
    support: Math.round(clamp(support + rng.randint(-9, 9), 10, 99)),
    spotlight: Math.round(clamp(spotlight + rng.randint(-8, 8), 0, 99)),
    stage: "dating", mood: 72.0, weeks: 0, kids: 0, gifts: 0,
  };
}

function partnerStageName(row) {
  return row ? (LIFE_STAGE_NAMES[row.stage] || row.stage) : "";
}

function nextLifeStage(stage) {
  const idx = LIFE_STAGE_ORDER.indexOf(stage);
  if (idx < 0 || idx >= LIFE_STAGE_ORDER.length - 1) return null;
  return LIFE_STAGE_ORDER[idx + 1];
}

/**
 * כמה המורל מרוויח מזה שיש מישהו בבית. לא בונוס קבוע: בן זוג במשבר
 * מוריד, ולכן המספר יכול להיות שלילי.
 */
function supportBonus(game) {
  const row = partner(game);
  if (!row) return 0;
  const quality = (row.support / 100) * (row.mood - 45) / 55;
  const weight = { dating: 0.7, serious: 1.0, engaged: 1.15, married: 1.3 }[row.stage] || 1;
  return clamp(quality * 3.4 * weight, -3.2, 3.6);
}

/** כמה מוניטין הזוגיות מוסיפה בשבוע. מפורסמת = כותרות. */
function spotlightBonus(game) {
  const row = partner(game);
  if (!row || row.mood < 30) return 0;
  return (row.spotlight / 100) * 0.22;
}

function prideWord(pride) {
  if (pride >= 85) return "לא מפסיקים לספר עליך";
  if (pride >= 65) return "גאים בך";
  if (pride >= 45) return "בסדר, אבל מרגישים רחוקים";
  return "נפגעו, ולא אומרים";
}

function moodWord(mood) {
  if (mood >= 80) return "מצוין";
  if (mood >= 60) return "טוב";
  if (mood >= 40) return "מתוח";
  if (mood >= 25) return "רע";
  return "על הקצה";
}

/** שורה אחת שמסכמת את הבית — למסך הראשי. */
function homeLine(game) {
  const row = partner(game);
  const par = parents(game);
  const bits = [`ההורים: ${prideWord(par.pride)}`];
  if (row) {
    bits.push(`${row.name} — ${partnerStageName(row)}, ${moodWord(row.mood)}`);
    if (row.kids) bits.push(`${row.kids} ילדים`);
  }
  return bits.join(" · ");
}

// ---------------------------------------------------------------------------
// השבוע
// ---------------------------------------------------------------------------

function lifeWeekly(game, rng) {
  return partnerWeek(game, rng).concat(parentsWeek(game, rng));
}

function partnerWeek(game, rng) {
  const row = partner(game);
  if (!row) return [];
  const me = game.me;
  row.weeks += 1;

  // שחיקה: זמן לבד, עצימות גבוהה, והפסדים
  let drift = DRIFT_PER_WEEK;
  if (game.intensity >= NEGLECT_INTENSITY) drift += 0.8;
  if (me.morale < 40) drift += 0.5;
  drift *= 1.25 - (row.support / 100) * 0.55;   // מי שמבין ספורט סופג פחות
  row.mood = clamp(row.mood - drift, 0, 100);

  const bonus = supportBonus(game);
  me.morale = clamp(me.morale + bonus, 5, 99);
  if (bonus > 1.4) me.resilience = clamp(me.resilience + 0.05, 0, 100);
  me.reputation = clamp(me.reputation + spotlightBonus(game), 0, 100);

  if (row.mood > BREAKUP_MOOD) return partnerEvent(game, row, rng);

  if (rng.random() < BREAKUP_CHANCE) {
    const name = row.name;
    delete game.flags.partner;
    game.flags.heartbreak = 8;
    me.morale = clamp(me.morale - 16, 5, 99);
    return [`💔 ${name} עזבה. "אני לא מתחרה בכדורגל, ואני לא רוצה."`];
  }
  return [`⚠️ ${row.name} אמרה שאתם לא נפגשים. זה לא היה שקט.`];
}

/** אירוע קטן מהבית. נדיר מספיק כדי שלא יהפוך לרעש. */
function partnerEvent(game, row, rng) {
  if (rng.random() > 0.09) return [];
  const name = row.name;
  const pool = [];
  if (row.spotlight >= 60)
    pool.push(["📸 צילמו אתכם יוצאים ממסעדה. הכותרת לא עסקה בכדורגל.",
               { reputation: 1.2 }]);
  if (row.support >= 70)
    pool.push([`🏠 ${name} חיכתה ער עד שחזרת מהמשחק. זה נשמע קטן, וזה לא.`,
               { morale: 3.0 }]);
  pool.push([`🍽️ ערב בלי טלפונים עם ${name}.`, { mood: 6.0 }]);
  if (row.stage === "engaged" || row.stage === "married")
    pool.push([`👨‍👩‍👦 ${name} שאלה מתי מתכננים קדימה.`, { mood: -3.0 }]);
  const [text, effect] = rng.choice(pool);
  applyLifeEffect(game, row, effect);
  return [text];
}

function applyLifeEffect(game, row, effect) {
  const me = game.me;
  if (effect.morale != null) me.morale = clamp(me.morale + effect.morale, 5, 99);
  if (effect.reputation != null)
    me.reputation = clamp(me.reputation + effect.reputation, 0, 100);
  if (effect.mood != null && row) row.mood = clamp(row.mood + effect.mood, 0, 100);
}

/** ההורים מבקשים משהו — לא כל שבוע, ורק כשיש מה לבקש. */
function parentsWeek(game, rng) {
  if (!["academy", "player", "veteran"].includes(game.stage)) return [];
  const par = parents(game);
  if (par.ask) return [];
  const left = PARENT_ASKS.filter(r => !par.given.includes(r[0]));
  if (!left.length) return [];
  // ככל שאתה מרוויח יותר, כך הבקשות מגיעות מוקדם יותר
  const chance = 0.012 + Math.min(0.03, game.money / 40000000);
  if (rng.random() > chance) return [];
  const [key, name, why, cost, pride] = rng.choice(left);
  par.ask = { key, name, why, cost, pride };
  par.asked += 1;
  return [`📞 אבא שלך התקשר. ${why} (${name} — בתפריט: 'חיים')`];
}

function grantAsk(game) {
  const par = parents(game);
  const ask = par.ask;
  if (!ask) return "אין בקשה פתוחה.";
  if (game.money < ask.cost) return `אין לך ₪${fmt(ask.cost)}. עוד לא.`;
  game.spend(ask.cost);
  par.given = par.given.concat([ask.key]);
  par.pride = clamp(par.pride + ask.pride, 0, 100);
  par.ask = null;
  game.me.morale = clamp(game.me.morale + 6, 5, 99);
  return `✅ ${ask.name} — ₪${fmt(ask.cost)}. אמא שלך בכתה בטלפון.`;
}

function declineAsk(game) {
  const par = parents(game);
  if (!par.ask) return "אין בקשה פתוחה.";
  par.ask = null;
  par.pride = clamp(par.pride - 9, 0, 100);
  return "אמרת שעכשיו לא. הוא אמר \"בסדר, בסדר\" וניתק מהר מדי.";
}

// ---------------------------------------------------------------------------
// מה אתה יכול לעשות
// ---------------------------------------------------------------------------

function stageWait(stage) {
  const row = LIFE_STAGES.find(r => r[0] === stage);
  return row ? row[2] : 0;
}

function advanceName(stage) {
  return { serious: "להפוך את זה לרציני", engaged: "להציע נישואין",
           married: "להתחתן" }[stage] || "להתקדם";
}

function lifeActions(game) {
  const out = [];
  const row = partner(game);
  const par = parents(game);

  if (par.ask) {
    out.push({ key: "grant", name: `לתת: ${par.ask.name}`,
               cost: par.ask.cost, note: par.ask.why });
    out.push({ key: "decline", name: "להגיד שעכשיו לא", cost: 0,
               note: "הם יבינו. פחות ממה שהם יגידו." });
  }
  if (!row) return out;

  out.push({ key: "gift", name: `מתנה ל${row.name}`, cost: GIFT_COST,
             note: "לא פותר, אבל עוזר." });
  out.push({ key: "holiday", name: "לקחת חופשה ביחד", cost: HOLIDAY_COST,
             note: "שבוע בלי כדורגל. הגוף גם ירוויח." });
  const nxt = nextLifeStage(row.stage);
  if (nxt && row.weeks >= stageWait(row.stage) && row.mood >= 62) {
    const cost = nxt === "engaged" ? RING_COST : nxt === "married" ? WEDDING_COST : 0;
    out.push({ key: "advance", name: advanceName(nxt), cost,
               note: "צעד גדול. אין דרך חזרה." });
  }
  if (row.stage === "married" && row.kids < 3 && row.mood >= 60)
    out.push({ key: "child", name: "להביא ילד", cost: 0,
               note: "החיים ישתנו. גם המשחק." });
  return out;
}

function doLifeAction(game, key) {
  if (key === "grant") return grantAsk(game);
  if (key === "decline") return declineAsk(game);

  const row = partner(game);
  if (!row) return "אין למי.";

  if (key === "gift") {
    if (game.money < GIFT_COST) return "אין לך מספיק.";
    game.spend(GIFT_COST);
    row.gifts += 1;
    // מתנה חמישית כבר לא מרגשת אף אחד
    const gain = Math.max(3, 12 - row.gifts * 1.5);
    row.mood = clamp(row.mood + gain, 0, 100);
    return `🎁 ${row.name} שמחה. (+${Math.round(gain)} למצב הקשר)`;
  }

  if (key === "holiday") {
    if (game.money < HOLIDAY_COST) return "אין לך מספיק.";
    game.spend(HOLIDAY_COST);
    row.mood = clamp(row.mood + 22, 0, 100);
    game.me.fitness = clamp(game.me.fitness + 12, 0, 100);
    game.me.morale = clamp(game.me.morale + 8, 5, 99);
    game.me.sharpness = clamp(game.me.sharpness - 6, 0, 100);
    return "✈️ שבוע איתה, בלי טלפונים. חזרת רענן ופחות חד — וזה שווה את זה.";
  }

  if (key === "advance") {
    const nxt = nextLifeStage(row.stage);
    if (!nxt) return "אין לאן.";
    const cost = nxt === "engaged" ? RING_COST : nxt === "married" ? WEDDING_COST : 0;
    if (cost && game.money < cost) return `זה עולה ₪${fmt(cost)}. עוד לא.`;
    if (cost) game.spend(cost);
    row.stage = nxt;
    row.weeks = 0;
    row.mood = clamp(row.mood + 14, 0, 100);
    game.me.morale = clamp(game.me.morale + 10, 5, 99);
    if (row.spotlight >= 55)
      game.me.reputation = clamp(game.me.reputation + 2.5, 0, 100);
    return { serious: `אתם ביחד. ${row.name} עברה לגור אצלך.`,
             engaged: "💍 היא אמרה כן. הטלפון שלך התפוצץ.",
             married: "💒 התחתנתם. חצי מהסגל היה שם." }[nxt];
  }

  if (key === "child") {
    row.kids += 1;
    row.mood = clamp(row.mood + 10, 0, 100);
    game.me.morale = clamp(game.me.morale + 12, 5, 99);
    // לילה ראשון בבית עם תינוק — הגוף יודע
    game.me.fitness = clamp(game.me.fitness - 10, 0, 100);
    return "👶 נולד לכם ילד. חגגת את השער הבא עם אצבע באוויר, וכולם הבינו.";
  }
  return "לא ידוע.";
}

/** פרידה לא נגמרת בשבוע. זה נגרר, וזה נמדד. */
function heartbreakTick(game) {
  const weeks = Number(game.flags.heartbreak || 0);
  if (weeks <= 0) return null;
  game.flags.heartbreak = weeks - 1;
  const me = game.me;
  me.morale = clamp(me.morale - 1.6, 5, 99);
  me.sharpness = clamp(me.sharpness - 0.8, 0, 100);
  if (weeks === 1) return "🙂 מתחיל להיות בסדר. הראש חזר למגרש.";
  return null;
}
