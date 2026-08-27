// ---------------------------------------------------------------------------
// מי צופה בך, ומאיפה — תאום JS של scouting.py
//
// הצעת העברה כבר לא הטלת מטבע אחת בשנה. קבוצות שולחות צופים למשחקים,
// הצופה כותב דוח לפי מה שראה, והעניין נבנה או נשחק לאורך העונה.
// ---------------------------------------------------------------------------

const SCOUT_DECAY = 0.985;
const SCOUT_DECAY_FLOOR = 0.10;
const SCOUT_NOTICED = 25;
const SCOUT_COURTED = 55;
const SCOUT_CHASED = 74;

function interestMap(game) {
  let data = game.flags.scout_interest;
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    data = {};
    game.flags.scout_interest = data;
  }
  return data;
}

function watchers(game, minimum = SCOUT_NOTICED) {
  const out = [];
  const table = interestMap(game);
  for (const cid in table) {
    const club = game.clubs[cid];
    if (club && table[cid] >= minimum)
      out.push([club, Math.round(table[cid] * 10) / 10]);
  }
  out.sort((a, b) => b[1] - a[1]);
  return out;
}

function interestLabel(score) {
  if (score >= SCOUT_CHASED) return "רודפים אחריך";
  if (score >= SCOUT_COURTED) return "מחזרים";
  if (score >= 40) return "עוקבים מקרוב";
  return "רשומים אצלם";
}

const HOME_COUNTRY = "ישראל";

function clubCountry(cid) {
  return D.CLUB_COUNTRY[cid] || HOME_COUNTRY;
}

function countryFlag(country) {
  return D.COUNTRY_FLAGS[country] || "🏳";
}

function isForeign(cid) {
  return clubCountry(cid) !== HOME_COUNTRY;
}

function leagueName(leagueId) {
  const row = D.LEAGUES.find(l => l.id === leagueId);
  return row ? row.name : "";
}

/**
 * שורת הזהות של מועדון: דגל, מדינה, וליגה.
 *
 * התלונה שהולידה את זה: "עירבבת מועדונים מקומיים עם מועדונים מחו״ל".
 * הנתונים תמיד היו נכונים — שלוש ליגות נפרדות — אבל בממשק שם של
 * מועדון אירופי הופיע בדיוק כמו שם של מועדון מקומי, בלי שום סימן.
 * זו הפונקציה שאמורה להופיע בכל מקום שבו שם מועדון מוצג.
 */
function clubTag(cid, leagueId = "") {
  const country = clubCountry(cid);
  const flag = countryFlag(country);
  const league = leagueName(leagueId);
  if (country === HOME_COUNTRY) return league ? `${flag} ${league}` : flag;
  return `${flag} ${country}` + (league ? ` · ${league}` : "");
}

/** קבוצות שרמת השחקן שלך רלוונטית להן היום. */
function candidateClubs(game) {
  const me = game.me;
  const myClub = game.myClub();
  const current = myClub ? myClub.reputation : 15;
  let ceiling = overall(me) + 6 + (me.reputation - 40) * 0.30;
  if (me.season.apps >= 6) ceiling += (avgRating(me.season) - 6.6) * 9;
  if (me.age <= 21) ceiling += 5;
  if (me.contract.yearsLeft <= 1) ceiling += 5;
  if (game.flag("open_to_europe")) ceiling += 6;
  // מי שקטן מדי לא באמת יילך על שחקן ברמה שלך — הוא לא יעמוד בשכר
  const floor = Math.max(current - 12, overall(me) - 24);
  const out = [];
  for (const cid in game.clubs) {
    const club = game.clubs[cid];
    if (myClub && club.cid === myClub.cid) continue;
    if (club.reputation > ceiling || club.reputation < floor) continue;
    out.push(club);
  }
  return out;
}

function scoutVerdict(move) {
  if (move >= 6) return "הוא לא הוריד ממך עיניים.";
  if (move >= 2) return "הוא רשם משהו וסימן וי.";
  if (move >= -2) return "ערב שגרתי. הוא ראה מה שהוא ראה.";
  return "הוא סגר את המחברת בהפסקה.";
}

/** מריץ שבוע של סקאוטינג ומחזיר שורות לדוח. */
function scoutsThisWeek(game, rng, rating) {
  const me = game.me;
  const table = interestMap(game);
  const lines = [];

  for (const cid of Object.keys(table)) {
    table[cid] = Math.round((table[cid] * SCOUT_DECAY - SCOUT_DECAY_FLOOR) * 100) / 100;
    if (table[cid] <= 1) delete table[cid];
  }
  if (rating === null || rating === undefined) return lines;
  if (!["academy", "player", "veteran"].includes(game.stage)) return lines;

  const pool = candidateClubs(game);
  if (!pool.length) return lines;

  let visits = rng.random() < 0.34 + me.reputation / 260 ? 1 : 0;
  if (me.reputation >= 55 && rng.random() < 0.22) visits += 1;
  for (let v = 0; v < visits; v++) {
    const weights = pool.map(club => [club,
      Math.pow(club.reputation / 30, 1.4) * (1 + (table[club.cid] || 0) / 14)]);
    const total = weights.reduce((a, w) => a + w[1], 0);
    let roll = rng.random() * total;
    let club = weights[weights.length - 1][0];
    for (const [candidate, weight] of weights) {
      roll -= weight;
      if (roll <= 0) { club = candidate; break; }
    }
    // הצופה לא שופט אותך במוחלט — הוא שואל אם אתה מספיק *לו*
    let move = (rating - 6.5) * 4.5;
    move += (overall(me) - club.reputation * 0.92) * 0.38;
    move += rng.uniform(-1.5, 1.5);
    if (me.age <= 20) move = move * 1.15 + 0.8;

    const before = table[club.cid] || 0;
    table[club.cid] = Math.round(clamp(before + move, 0, 100) * 100) / 100;
    const country = clubCountry(club.cid);
    const where = country !== "ישראל" ? ` (${country})` : "";
    lines.push(`👀 צופה מ${club.name}${where} היה ביציע. ${scoutVerdict(move)}`);
    if (before < SCOUT_NOTICED && table[club.cid] >= SCOUT_NOTICED)
      lines.push(`📋 ${club.name} פתחו עליך תיק.`);
  }
  return lines;
}

function topSuitor(game, minimum = SCOUT_CHASED) {
  const ranked = watchers(game, minimum);
  return ranked.length ? ranked[0][0] : null;
}

/** סוכן מחו"ל שמתקשר בעקבות מה שהצופים שלו כתבו. */
function foreignAgent(game, rng) {
  const ranked = watchers(game, SCOUT_COURTED)
    .filter(([club]) => clubCountry(club.cid) !== "ישראל");
  if (!ranked.length) return null;
  const [club, score] = ranked[0];
  const me = game.me;
  const myClub = game.myClub();
  const country = clubCountry(club.cid);
  const raiseFactor = 1.6 + (club.reputation - (myClub ? myClub.reputation : 20)) / 90;
  const wage = Math.round(Math.max(me.contract.wage * 1.4, club.wageBudget * 0.16)
                          * rng.uniform(0.85, 1.2) / 500) * 500;
  return {
    agent: rng.choice(D.AGENT_NAMES), club: club.cid, club_name: club.name,
    country, score: Math.round(score * 10) / 10, wage,
    fee: Math.round(wage * 0.18 / 500) * 500,
    raise_factor: Math.round(raiseFactor * 100) / 100,
  };
}

/** מה כתוב בתיק שיש עליך אצל מועדון מסוים. */
function scoutReport(game, club) {
  const me = game.me;
  const score = interestMap(game)[club.cid] || 0;
  const country = clubCountry(club.cid);
  const lines = [`${club.name} · ${country} · מוניטין ${club.reputation}`,
                 `רמת עניין: ${interestLabel(score)} (${Math.round(score)}/100)`];
  // הצופה כותב על תכונות אמיתיות, לא על קטגוריות
  const row = roleRow(me.role);
  const watched = row ? row[4].concat(row[5]) : attrsFor(me.position);
  const ranked = watched.slice().sort((a, b) => (me.detail[b] ?? 10) - (me.detail[a] ?? 10));
  const best = ranked[0], worst = ranked[ranked.length - 1];
  lines.push(`"${D.DETAIL_NAMES_HE[best]} ברמה שאנחנו מחפשים `
             + `(${me.detail[best] ?? 10}). ${D.DETAIL_NAMES_HE[worst]} — עוד לא."`);
  if (row) lines.push(`מסומן אצלנו כ${row[1]}.`);
  if (me.age <= 21) lines.push('"בגיל הזה, מה שחסר עוד אפשר ללמד."');
  else if (me.age >= 30) lines.push('"הגיל אצלנו הוא שיקול. חוזה קצר, לא יותר."');
  if (score < SCOUT_NOTICED) lines.push("עוד לא פתחו עליך תיק אמיתי.");
  return lines;
}
