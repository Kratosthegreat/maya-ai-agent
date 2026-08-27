// ---------------------------------------------------------------------------
// סוכנים — תאום JS של football_manager/agents.py
//
// עד כאן השוק היה הוגן: מועדונים ראו אותך, שקלו, והציעו. זה נקי, וזו
// בדיוק הבעיה — הכול צפוי. כאן נכנס אדם שלישי שהאינטרס שלו לא זהה
// לשלך, והוא פועל גם כשאתה לא מסתכל.
// ---------------------------------------------------------------------------

// [מפתח, שם, תיאור, עמלה%, טווח, תוקפנות, נאמנות]
const AGENT_TYPES = [
  ["family", "סוכן המשפחה", "עורך דין שהאבא שלך מכיר. לא יעשה לך נזק, וגם לא נס.",
   3.0, 0.28, 0.10, 0.95],
  ["rookie", "הטירון", "התיק הראשון שלו זה אתה. רעב, לומד מהר, עוד לא מכיר אף אחד.",
   4.0, 0.34, 0.35, 0.80],
  ["connected", "המקושר", "מכיר מנהלים ספורטיביים בשם הפרטי. שיחה אחת פותחת דלת.",
   7.0, 0.82, 0.45, 0.55],
  ["shark", "הכריש", "יוציא לך חוזה חלומות ויעשה את זה על גופות. גם על שלך, אם צריך.",
   11.0, 0.95, 0.90, 0.30],
  ["super", "הסופר־סוכן", "מנהל תיק של ארבעים כוכבים. אתה מספר ארבעים ואחת — עד שלא.",
   9.0, 1.00, 0.70, 0.45],
];
const AGENT_BY_KEY = Object.fromEntries(AGENT_TYPES.map(r => [r[0], r]));

const SUPER_AGENT_FAME = 72.0;   // מתחת לזה הסופר־סוכן לא מחזיר טלפון

const AGENT_FIRST = ["רוני", "איציק", "ז'אן", "מרקו", "דודו", "אבי", "פאולו",
                     "שרון", "ליאור", "ז'ילבר", "אמיר", "טוני", "ניר", "סמי"];
const AGENT_LAST = ["ברזילי", "מנשה", "לוינסון", "דה סילבה", "אזולאי", "קרן",
                    "מורנו", "שגב", "בן־חיים", "רוסו", "אלמליח", "פישר"];

const MOVE_CHANCE = 0.30;
const SABOTAGE_EXPOSURE = 0.32;
const AGENT_CANDIDATES = 3;

function agentRow(game) {
  const data = game.flags.agent;
  return data && typeof data === "object" ? data : null;
}

function agentType(row) {
  return row ? (AGENT_BY_KEY[row.kind] || AGENT_BY_KEY.family) : null;
}

function agentCutPercent(game) {
  const row = agentRow(game);
  return row ? Number(row.cut != null ? row.cut : agentType(row)[3]) : 0;
}

/** העמלה על סכום — גם על שכר שבועי וגם על מענק חתימה. */
function agentCut(game, gross) {
  return Math.floor(gross * agentCutPercent(game) / 100);
}

/** בלי סוכן מגיעים רק למי שראה אותך במגרש. */
function agentReach(game) {
  const row = agentRow(game);
  return row ? Number(agentType(row)[4]) : 0.20;
}

/** סוכן חדש. העמלה מתנדנדת סביב הבסיס — אין שני סוכנים זהים. */
function makeAgent(kind, rng) {
  const [key, , , cut] = AGENT_BY_KEY[kind];
  return {
    kind: key,
    name: `${rng.choice(AGENT_FIRST)} ${rng.choice(AGENT_LAST)}`,
    cut: Math.round(cut * rng.uniform(0.85, 1.2) * 10) / 10,
    trust: rng.randint(50, 70),
    deals: 0, burned: [], moves: [], since: 0,
  };
}

/** כמה גדול השם שלך — הסולם שמחליט מי מחזיר לך טלפון. */
function agentFame(game) {
  const club = game.myClub();
  let score = game.me.reputation;
  // המועדון עוזר, אבל השם הוא שלך
  if (club) score += club.reputation * 0.14;
  return score + game.honours.length * 4;
}

/** מי מוכן לייצג אותך עכשיו. שלושה, ולא אותם שלושה תמיד. */
function agentMarket(game, rng) {
  const fame = agentFame(game);
  let pool = AGENT_TYPES.map(r => r[0]).filter(k => k !== "super");
  if (fame >= SUPER_AGENT_FAME) pool.push("super");
  if (fame < 18) pool = pool.filter(k => k === "family" || k === "rookie");
  else if (fame < 34) pool = pool.filter(k => k !== "shark");
  rng.shuffle(pool);
  return pool.slice(0, AGENT_CANDIDATES).map(kind => makeAgent(kind, rng));
}

function signAgent(game, row) {
  const old = agentRow(game);
  const copy = Object.assign({}, row, { since: game.year });
  game.flags.agent = copy;
  const kind = agentType(copy);
  if (old)
    return `🤝 ${copy.name} מחליף את ${old.name}. ${kind[1]} — ${copy.cut}% מהשכר.`;
  return `🤝 חתמת עם ${copy.name}. ${kind[1]}, ${copy.cut}% מהשכר.`;
}

function agentLeave(game, reason = "") {
  const row = agentRow(game);
  delete game.flags.agent;
  if (!row) return "";
  return `👋 ${row.name} כבר לא מייצג אותך. ${reason}`.trim();
}

function reachWord(span) {
  if (span >= 0.9) return "כל מועדון באירופה";
  if (span >= 0.7) return "צמרת אירופה בהישג יד";
  if (span >= 0.32) return "הליגה המקומית, ולפעמים מעבר";
  return "מה שמסביב";
}

function agentTrustWord(trust) {
  if (trust >= 78) return "אתה התיק הכי חשוב שלו";
  if (trust >= 58) return "מרוצה, עובד בשבילך";
  if (trust >= 38) return "מתחיל לאבד עניין";
  return "מחזיק בך מהרגל";
}

/** הסוכן בשורות, למסך. */
function describeAgent(game) {
  const row = agentRow(game);
  if (!row)
    return ["אין לך סוכן. אתה מנהל את הקריירה שלך לבד — וזה נראה בכמות ההצעות."];
  const kind = agentType(row);
  const out = [`${row.name} · ${kind[1]}`, kind[2],
               `עמלה ${row.cut}% מהשכר ומהמענקים`,
               `טווח: ${reachWord(kind[4])}`,
               `מה הוא חושב עליך: ${agentTrustWord(row.trust)}`];
  if (row.deals) out.push(`סגר בשבילך ${row.deals} עסקאות`);
  const burned = (row.burned || []).map(c => game.clubs[c] && game.clubs[c].name)
    .filter(Boolean).join(", ");
  if (burned) out.push(`שרוף מולם: ${burned}`);
  return out;
}

// ---------------------------------------------------------------------------
// מה הסוכן עושה השבוע
//
// סוכן שעושה כל שבוע את אותו מהלך הוא רעש, לא דמות. לכן הוא מנהל
// קמפיין: יעד אחד, כמה שבועות, ובכל פעם שלב אחר בתהליך.
// ---------------------------------------------------------------------------

const CAMPAIGN_READY = 74.0;
const CAMPAIGN_MAX_WEEKS = 9;

// תשעה שלבים ולא חמישה, כי אחרת הקמפיין מתחיל מהתחלה מול אותו מועדון
const CAMPAIGN_STEPS = [
  ["שלח להם קלטת של שלושה משחקים.", 9],
  ["דיבר עם המנהל הספורטיבי שלהם. הם שאלו על החוזה.", 11],
  ["סידר שיבואו לראות אותך חי.", 13],
  ["ישב איתם ארוחת צהריים ארוכה מדי מכדי שתהיה נימוסית.", 12],
  ["אמר להם שיש עוד מישהו בתמונה. זה לא היה מדויק.", 15],
  ["העביר להם נתונים שהוא הזמין מחברת אנליזה.", 10],
  ["דאג שהשם שלך יעלה בישיבת הרכש שלהם.", 14],
  ["הביא את המאמן שלהם לשיחת טלפון של שתי דקות.", 16],
  ["אמר להם שהחלון נסגר, וששאלו עליך גם ממקום אחר.", 13],
];

/** המהלך של הסוכן, אם בכלל. הגרלה קודם, בנייה אחר כך. */
function agentWeekly(game, rng) {
  const row = agentRow(game);
  if (!row || !["academy", "player", "veteran"].includes(game.stage)) return [];

  const kind = agentType(row);
  const live = liveOffers(game);
  let chance = MOVE_CHANCE * (0.55 + kind[5]);
  if (live.length) chance *= 1.8;
  if (rng.random() > Math.min(0.55, chance)) return agentIdle(game, row, rng);

  const moves = [];
  if (live.length) {
    moves.push("push", "push");
    if (live.length >= 2 && kind[5] >= 0.45) moves.push("sabotage", "sabotage");
  } else {
    moves.push("campaign", "campaign", "campaign");
  }
  if (kind[5] >= 0.35) moves.push("leak");

  const move = rng.choice(moves);
  if (move === "campaign") return agentCampaign(game, row, rng);
  if (move === "push") return agentPush(game, row, rng, live);
  if (move === "leak") return agentLeak(game, row, rng);
  return agentSabotage(game, row, rng, live);
}

/** שבוע שקט. סוכן שלא רואה תנועה מתחיל להתקרר — לאט. */
function agentIdle(game, row, rng) {
  const kind = agentType(row);
  row.trust = clamp(row.trust - 0.10 * (1.4 - kind[6]), 0, 100);
  if (row.trust > 20 || row.deals > 0 || rng.random() > 0.05) return [];
  return [agentLeave(game, "\"תתקשר כשיהיה מה למכור.\"")];
}

/** מי בטווח של הסוכן ועוד לא על השולחן. */
function agentCandidateClubs(game, span) {
  const me = game.me;
  const taken = new Set(openOffers(game).map(o => o.cid));
  const out = [];
  for (const club of Object.values(game.clubs)) {
    if (taken.has(club.cid) || club.cid === me.clubId) continue;
    if (club.reputation > 55 + span * 48) continue;     // מעל הטווח שלו
    if (club.reputation < overall(me) - 26) continue;   // קטן מכדי שיעניין
    out.push(club);
  }
  return out;
}

function agentPickTarget(game, row, rng) {
  const kind = agentType(row);
  const burned = new Set(row.burned || []);
  const pool = agentCandidateClubs(game, kind[4])
    .filter(c => !burned.has(c.cid) && c.cid !== row.target);
  if (!pool.length) return null;
  pool.sort((a, b) => b.reputation - a.reputation);
  const top = pool.slice(0, Math.max(2, Math.floor(pool.length * (0.15 + kind[4] * 0.4))));
  return rng.choice(top);
}

/** עובד על יעד אחד לאורך שבועות, ומדווח בכל פעם על שלב אחר. */
function agentCampaign(game, row, rng) {
  if (!game.flags.scout_interest) game.flags.scout_interest = {};
  const book = game.flags.scout_interest;
  const target = row.target;
  const heat = target ? Number(book[target] || 0) : 0;
  const stale = (row.targetWeeks || 0) >= CAMPAIGN_MAX_WEEKS;
  // "הם מוכנים" נאמר פעם אחת. בלי הדגל ההתעניינות דועכת שבוע אחרי,
  // הקמפיין מרים אותה חזרה, והשורה חוזרת על עצמה.
  const ready = row.targetDone || heat >= CAMPAIGN_READY;

  if (!game.clubs[target] || ready || stale) {
    const done = !!game.clubs[target] && ready;
    row.targetDone = false;
    const club = agentPickTarget(game, row, rng);
    if (!club) return [];
    const previous = game.clubs[target];
    row.target = club.cid;
    row.targetWeeks = 0;
    row.moves = (row.moves || []).concat([`פתח תיק: ${club.name}`]).slice(-5);
    return [done && previous
      ? `📞 ${row.name}: "סגרנו את ${previous.name}. עכשיו ${club.name}."`
      : `📞 ${row.name} התחיל לעבוד על ${club.name}. ${clubTag(club.cid, club.leagueId)}`];
  }

  const club = game.clubs[target];
  const step = row.targetWeeks || 0;
  const [text, gain] = CAMPAIGN_STEPS[step % CAMPAIGN_STEPS.length];
  row.targetWeeks = step + 1;
  book[target] = clamp(heat + gain * (0.7 + agentType(row)[4] * 0.5), 0, 100);
  if (book[target] >= CAMPAIGN_READY) {
    row.targetDone = true;
    return [`📞 ${row.name}: "${club.name} מוכנים. הם יניחו הצעה."`];
  }
  return [`📞 ${row.name} ${text} (${club.name})`];
}

/** דוחף הצעה קיימת למעלה בלי שביקשת. לפעמים זה עובד. */
function agentPush(game, row, rng, live) {
  if (!live.length) return agentCampaign(game, row, rng);
  const kind = agentType(row);
  const offer = rng.choice(live);
  const club = game.clubs[offer.cid];
  const name = club ? club.name : "המועדון";
  const chance = clamp(0.24 + kind[4] * 0.30 + kind[5] * 0.18 - offer.asks * 0.09,
                       0.05, 0.82);
  if (rng.random() < chance) {
    const before = offer.wage;
    offer.wage = Math.floor(Math.min(offer.ceiling, offer.wage * 1.11));
    offer.state = "improved";
    if (offer.wage <= before) {
      offer.bonus = Math.floor(offer.bonus * 1.25);
      return [`📈 ${row.name} סחט מ${name} מענק גדול יותר: ₪${fmt(offer.bonus)}.`];
    }
    return [`📈 ${row.name} טלפן ל${name} בלי לשאול אותך. `
          + `₪${fmt(offer.wage)} לשבוע במקום ₪${fmt(before)}.`];
  }
  offer.patience -= 1;
  if (offer.patience <= 0) {
    offer.state = "withdrawn";
    row.trust = clamp(row.trust - 6, 0, 100);
    return [`❌ ${row.name} לחץ יותר מדי. ${name} ירדו מהעסקה.`];
  }
  return [`😐 ${row.name} ניסה על ${name} ונענה "זה מה שיש".`];
}

/** דליפה לעיתונות — לוחצת על המועדון, ומרגיזה אותו. */
function agentLeak(game, row, rng) {
  const kind = agentType(row);
  const club = game.myClub();
  const live = liveOffers(game);
  const book = game.flags.scout_interest || {};
  let target = null;
  if (live.length) target = game.clubs[live[0].cid];
  else {
    const keys = Object.keys(book);
    if (keys.length) {
      const best = keys.reduce((a, b) => (book[b] > book[a] ? b : a));
      target = game.clubs[best];
    }
  }
  if (!target) return [];

  // דרך `pressPush` ולא ביד: הוא זה שיודע מה הצורה של פריט בפיד
  pressPush(game, { key: "agent_leak", source: "insider", true: true,
                    text: `מקורב לשחקן: "יש קשר עם ${target.name}, `
                        + `והשחקן פתוח לשמוע."` });

  const out = [`📰 ${row.name} דלף לעיתונות. הכותרת יצאה: "${target.name} בודקים אותך."`];
  if (club && rng.random() < 0.55 + kind[5] * 0.25) {
    club.managerTrust = clamp(club.managerTrust - 4.5, 0, 100);
    out.push(`😠 ב${club.name} לא אהבו את הכותרת.`);
  }
  if (!game.flags.scout_interest) game.flags.scout_interest = {};
  const cur = game.flags.scout_interest;
  cur[target.cid] = clamp(Number(cur[target.cid] || 0) + 9, 0, 100);
  return out;
}

/**
 * מחסל הצעה מתחרה כדי לפנות מקום לזו שמשלמת לו יותר.
 * זה המהלך שהופך סוכן לדמות: הוא עושה את זה בלי לשאול, וכשזה נחשף
 * אתה משלם — לא הוא.
 */
function agentSabotage(game, row, rng, live) {
  if (live.length < 2) return agentPush(game, row, rng, live);
  const kind = agentType(row);
  if (kind[5] < 0.25) return agentPush(game, row, rng, live);

  const best = live[0];
  const victim = rng.choice(live.slice(1));
  const vclub = game.clubs[victim.cid];
  const bclub = game.clubs[best.cid];
  if (!vclub || !bclub) return [];

  victim.state = "withdrawn";
  victim.log.push("🕳️ נעלמו בלי הסבר");
  best.wage = Math.floor(Math.min(best.ceiling, best.wage * 1.07));
  best.state = "improved";
  row.burned = (row.burned || []).concat([vclub.cid]).slice(-6);
  row.moves = (row.moves || []).concat([`חיסל את ${vclub.name}`]).slice(-5);

  const out = [`🕳️ ${vclub.name} ירדו מהעסקה בלי הסבר. ${row.name} לא נראה מופתע.`];
  if (rng.random() < SABOTAGE_EXPOSURE + kind[5] * 0.12) {
    game.me.reputation = clamp(game.me.reputation - 3.5, 0, 100);
    const club = game.myClub();
    if (club) club.managerTrust = clamp(club.managerTrust - 6, 0, 100);
    pressPush(game, { key: "agent_exposed", source: "insider", true: true,
                      text: `"הסוכן של השחקן טרפד את המהלך של ${vclub.name}." `
                          + `בחדרי חדרים כועסים.` });
    out.push("🔥 זה יצא החוצה. \"ככה לא עובדים\" — וזה נדבק בך, לא בו.");
  }
  return out;
}

/** הסוכן גובה את שלו ברגע החתימה, ומרוצה בהתאם. */
function agentOnDeal(game, offer) {
  const row = agentRow(game);
  if (!row) return [];
  row.deals += 1;
  row.trust = clamp(row.trust + 9, 0, 100);
  const fee = agentCut(game, offer.bonus || 0);
  if (fee <= 0) return [`🤝 ${row.name} סגר. "אמרתי לך שאני עובד."`];
  game.spend(fee);
  return [`🤝 ${row.name} סגר את העסקה ולקח ₪${fmt(fee)} מהמענק.`];
}
