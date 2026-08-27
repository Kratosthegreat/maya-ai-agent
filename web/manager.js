// ---------------------------------------------------------------------------
// המאמן של הקבוצה — פורט מ-football_manager/manager.py.
// דמות שמדברת אליך אחרי כל משחק, דורשת ממך דברים בשבוע, ומסבירה
// למה אתה בהרכב או מחוצה לו. לכל מאמן אופי, והאופי קובע מה מרגיז אותו.
// ---------------------------------------------------------------------------

// (מפתח, שם, תיאור, רגישות אמון, סבלנות לתקשורת, נטייה לרוטציה)
const MANAGER_STYLES = [
  ["disciplinarian", "איש משמעת",
   "אצלו מגיעים ראשונים לאימון ועונים אחרונים לתקשורת.", 1.35, 0.55, 0.9],
  ["man_manager", "מאמן של שחקנים",
   "מדבר איתך, לא עליך. סולח יותר, מצפה יותר.", 0.85, 1.25, 1.0],
  ["tactician", "טקטיקן",
   "מה שמעניין אותו זה אם עמדת נכון, לא כמה רצת.", 1.05, 0.9, 1.15],
  ["rotator", "מסובב סגל",
   "מאמין שכל אחד מקבל דקות — וגם מאבד אותן.", 0.95, 1.05, 1.6],
];

/** אופי המאמן — נגזר מהשם, ולכן קבוע לכל אורך הכהונה שלו. */
function managerStyle(club) {
  if (!club || !club.managerName) return MANAGER_STYLES[1];
  return MANAGER_STYLES[hashOf(club.managerName) % MANAGER_STYLES.length];
}

const DIRECTIVE_TEXT = {
  pace: "רוצה אותך מהיר יותר בחמישה המטרים הראשונים.",
  shooting: "אמר שאתה מבזבז מצבים. השבוע — סיומות.",
  passing: "רוצה שתפסיק לאבד כדורים במסירה הראשונה.",
  dribbling: "אמר שאתה מוסר מוקדם מדי. שיחקק אחד על אחד.",
  defending: "דורש שתחזור אחורה. גם חלוץ מגן.",
  physical: "שלח אותך לחדר הכושר. אמר שאתה נדחף מהכדור.",
  mental: "רוצה אותך בחדר הווידאו. אתה קורא את המשחק לאט.",
  rest: "אמר לך לנוח. הוא רואה שאתה שרוף.",
};

/** מה המאמן רוצה ממך השבוע. null כשאין לו מה להגיד. */
/**
 * מה המאמן רוצה ממך השבוע.
 * הוא לא ממציא: הוא קורא את שורת הסטטיסטיקה של המשחק האחרון שלך
 * ובוחר את התחום שבו נפלת הכי הרבה יחסית למה שהעמדה שלך דורשת.
 */
function weeklyDirective(game, rng) {
  const club = game.myClub();
  const me = game.me;
  if (!club || !["academy", "player", "veteran"].includes(game.stage)) return null;
  // מנוחה נדרשת רק כשהגוף באמת על הקצה — לא כברירת מחדל
  if (me.fitness < 34 || (me.fitness < 46 && me.sharpness < 45)) return "rest";
  const stats = game.flags.last_stats;
  if (stats) return weakestDetail(stats, me);
  const weights = D.POSITION_WEIGHTS[me.position];
  const gaps = D.ATTRIBUTES.slice().sort((a, b) =>
    ((me.attributes[a] ?? 50) - (weights[a] ?? 0.1) * 120)
    - ((me.attributes[b] ?? 50) - (weights[b] ?? 0.1) * 120));
  return rng.choice(gaps.slice(0, 3));
}

/**
 * ההוראה, עם הסיבה מהמשחק האחרון וההבטחה מה זה ייתן.
 * בלי הסיבה זו שורת טקסט אקראית. עם הסיבה זו שיחה.
 */
/** לאיזו מבין שבע הקבוצות שייכת תכונה מפורטת. */
function areaOf(detailAttr) {
  let best = "physical", bestShare = -1;
  for (const map of [D.GROUP_MAP, D.GROUP_MAP_GK])
    for (const group in map) {
      const share = map[group][detailAttr] || 0;
      if (share > bestShare) { best = group; bestShare = share; }
    }
  return best;
}

function detailDirectiveText(focus) {
  const name = D.DETAIL_NAMES_HE[focus];
  if (!name) return DIRECTIVE_TEXT[focus] || "רוצה אותך באימון נוסף.";
  return `רוצה שתעבוד השבוע על ${name}.`;
}

function directiveLine(club, focus, stats = null) {
  const name = club ? club.managerName : "המאמן";
  const head = `${name} ${detailDirectiveText(focus)}`;
  if (!stats) return head;
  // הסיבה וההבטחה כתובות בשפת הקבוצות — מתרגמים חזרה
  const area = (focus in D.DIRECTIVE_REASON) ? focus : areaOf(focus);
  const reason = reasonLine(area, stats);
  const promise = promiseLine(area);
  const parts = [head];
  if (reason) parts.push(`"${reason}"`);
  if (promise) parts.push(`← ${promise}`);
  return parts.join("\n");
}

/** מה המאמן אמר לך אחרי המשחק. */
function postMatchLine(game, rating, outcome, played, rng) {
  const club = game.myClub();
  if (!club) return null;
  const [key] = managerStyle(club);
  const name = club.managerName;

  if (!played) {
    if (club.managerTrust < 35) return `${name} עבר לידך בחדר ההלבשה ולא עצר.`;
    if (rng.random() < 0.5) return `${name}: "תמשיך לעבוד. אני רואה אותך."`;
    return null;
  }
  if (rating === null || rating === undefined) return null;

  let pool;
  if (rating >= 8.0) {
    pool = [`${name}: "זה מה שחיפשתי ממך. עוד כאלה."`,
            `${name} תפס אותך במנהרה ואמר רק: "מצוין."`];
    if (key === "disciplinarian") pool.push(`${name}: "טוב. אל תתאהב בעצמך."`);
  } else if (rating >= 6.8) {
    pool = [`${name}: "עבודה טובה. תשמור על הרמה."`,
            `${name} הנהן לכיוונך. זה הרבה, ממנו.`];
  } else if (rating >= 6.0) {
    pool = [`${name}: "בסדר. לא יותר מזה."`,
            `${name} לא אמר כלום, וזה נשמע חזק.`];
  } else if (key === "man_manager") {
    pool = [`${name}: "יום קשה. קורה. מחר מתחילים מחדש."`];
  } else {
    pool = [`${name}: "מה זה היה? אנחנו נדבר מחר."`,
            `${name} החליף אותך והסתכל עליך כל הדרך לספסל.`];
  }
  if (outcome === "L" && rating < 6.5 && key === "disciplinarian")
    pool.push(`${name} ביטל את יום החופש של כל הקבוצה.`);
  return rng.choice(pool);
}

/** הסבר מה עומד בינך לבין ההרכב הפותח. */
function selectionNote(game) {
  const club = game.myClub();
  const me = game.me;
  if (!club || !["academy", "player", "veteran"].includes(game.stage)) return null;
  if (!isAvailable(me))
    return `${me.injuryName} — ${me.injuryWeeks} שבועות. לא רלוונטי להרכב.`;

  const rivals = club.squad.map(pid => game.players[pid])
    .filter(p => p && p.pid !== game.meId && isAvailable(p) && p.position === me.position);
  const best = rivals.reduce((m, p) => Math.max(m, effective(p)), 0);
  let mine = effective(me) + (club.managerTrust - 50) * 0.14;
  if (game.flag("captain")) mine += 4;
  const gap = mine - best;

  if (gap >= 6) return `אתה הבחירה הראשונה של ${club.managerName} בעמדה.`;
  if (gap >= -1) return "אתה והמתחרה שלך צמודים. כל משחק גרוע יעלה לך את המקום.";
  const rival = rivals.reduce((a, b) => (a && effective(a) >= effective(b) ? a : b), null);
  if (rival)
    return `${rival.name} (${overall(rival)}) לפניך בתור. צריך ${Math.abs(Math.round(gap))} נקודות של פער כדי לעקוף אותו.`;
  return null;
}

/** שינוי אמון מותאם לאופי המאמן. */
function trustMove(club, delta) {
  if (!club) return 0;
  club.managerTrust = clamp(club.managerTrust + delta * managerStyle(club)[3], 0, 100);
  return club.managerTrust;
}


// ---------------------------------------------------------------------------
// למאמן יש דעה עליך, ולדעה יש משקל
//
// עד כאן `managerTrust` היה מספר שהשפיע קצת על ההרכב וזהו. מאמן אמיתי
// הוא לא מד־חום: יש לו מועדפים, יש לו כלב שלא מקבל דקות, הוא מבטיח
// ולפעמים שובר, ואפשר לדפוק לו על הדלת ולשאול למה.
// ---------------------------------------------------------------------------

// [מפתח, שם, סף אמון, מה זה שווה בהרכב]
//
// הבונוס נכנס ישירות לבחירת ההרכב, ולכן "בכלוב" הוא לא תווית — הוא
// שמונה נקודות דירוג שנעלמות, וזה מורגש בכל שבוע.
const STANDINGS = [
  ["favourite", "המועדף שלו", 78, 6.0],
  ["trusted", "בתוך התוכנית", 58, 2.5],
  ["neutral", "עוד אחד בסגל", 40, 0.0],
  ["doubted", "מסומן בשאלה", 24, -3.5],
  ["frozen", "בכלוב", 0, -8.0],
];

// [מפתח, שם, משפט, קושי, אמון אם הצליח, אמון אם נכשל]
const MEETINGS = [
  ["role", "לבקש מקום קבוע בהרכב", "\"אני צריך לדעת אם אני משחק כאן.\"", 0.55, 6, -8],
  ["why", "לשאול למה אתה לא משחק", "\"תסביר לי מה חסר לי.\"", 0.30, 3, -3],
  ["promise", "להבטיח לו עונה", "\"תן לי שלושה משחקים ואני אראה לך.\"", 0.45, 8, -6],
  ["position", "לבקש לשחק בעמדה שלך",
   "\"אני לא שחקן שאתה מכניס לאן שחסר.\"", 0.50, 5, -6],
  ["leave", "לבקש רשות לעזוב", "\"אני רוצה לשמוע הצעות. בלי מלחמות.\"", 0.60, -2, -12],
];
const MEETING_NAMES = Object.fromEntries(MEETINGS.map(r => [r[0], r[1]]));

const PROMISE_WEEKS = 5;
const PROMISE_TRUST_BREAK = -14.0;
const MEETING_COOLDOWN = 6;

/** איפה אתה עומד אצלו: מפתח, שם, ומה זה שווה בהרכב. */
function managerStanding(game) {
  const club = game.myClub();
  let trust = club ? club.managerTrust : 50;
  if (game.flag("doghouse")) trust -= 22;
  if (game.flag("captain")) trust += 8;
  for (const [key, name, threshold, bonus] of STANDINGS)
    if (trust >= threshold) return [key, name, bonus];
  const last = STANDINGS[STANDINGS.length - 1];
  return [last[0], last[1], last[3]];
}

/**
 * כמה נקודות המאמן מוסיף או מוריד לך בבחירת ההרכב. זה מה שהופך את
 * היחסים איתו למשהו שמרגישים.
 */
function selectionBonus(game) {
  let bonus = managerStanding(game)[2];
  const promise = activePromise(game);
  if (promise && (promise.kind === "start" || promise.kind === "role")) bonus += 9;
  return bonus;
}

function standingLine(game) {
  const club = game.myClub();
  if (!club) return "";
  const [key] = managerStanding(game);
  const who = club.managerName;
  if (key === "favourite")
    return `⭐ ${who} רואה בך את הציר. אתה משחק גם כשאתה לא בכושר.`;
  if (key === "trusted") return `✅ ${who} סופר אותך. המקום שלך תלוי בך.`;
  if (key === "neutral") return `⚖️ ${who} עוד לא החליט לגביך.`;
  if (key === "doubted")
    return `⚠️ ${who} מסתכל עליך אחרת. עוד משחק חלש וזה ייסגר.`;
  return `⛔ אתה מחוץ לתוכניות של ${who}. גם אימון מצוין לא יזיז את זה מהר.`;
}

/** המאמן מבטיח משהו. מרגע זה הוא נמדד לפיו. */
function givePromise(game, kind, weeks = PROMISE_WEEKS) {
  game.flags.promise = { kind, weeks, made: game.week, starts: 0 };
  const club = game.myClub();
  const who = club ? club.managerName : "המאמן";
  const text = { start: `${who} הבטיח לך ${weeks} משחקים בהרכב.`,
                 role: `${who} הבטיח לך את העמדה שלך.`,
                 minutes: `${who} הבטיח לך דקות.`,
                 leave: `${who} הבטיח לא לחסום מעבר בקיץ.` }[kind]
             || `${who} הבטיח לך משהו.`;
  return `🤝 ${text}`;
}

function activePromise(game) {
  const row = game.flags.promise;
  if (!row || typeof row !== "object" || (row.weeks || 0) <= 0) return null;
  return row;
}

/** שבוע עובר על הבטחה. שבורה — זה עולה לו, לא לך. */
function promiseTick(game, played) {
  const row = activePromise(game);
  if (!row) return null;
  row.weeks -= 1;
  if (played) row.starts = (row.starts || 0) + 1;
  const club = game.myClub();
  const who = club ? club.managerName : "המאמן";

  if (row.weeks > 0) return null;
  const kept = (row.starts || 0) >= Math.max(1, Math.floor(PROMISE_WEEKS / 2));
  delete game.flags.promise;
  if (kept) {
    game.me.morale = clamp(game.me.morale + 8, 5, 99);
    return `✅ ${who} עמד במילה שלו.`;
  }
  game.me.morale = clamp(game.me.morale - 12, 5, 99);
  if (club) club.managerTrust = clamp(club.managerTrust + PROMISE_TRUST_BREAK, 0, 100);
  game.setFlag("broken_promise", true);
  return `💢 ${who} הבטיח ולא קיים. אתה זוכר בדיוק מה הוא אמר ובאיזה יום.`;
}

/** כמה סיכוי שהוא יגיד כן. גלוי לשחקן — זו החלטה, לא הימור עיוור. */
function meetingOdds(game, difficulty) {
  const club = game.myClub();
  const trust = club ? club.managerTrust : 50;
  const me = game.me;
  let chance = 0.9 - difficulty;
  chance += (trust - 50) / 145;
  chance += (me.reputation - 40) / 320;
  if (me.season.apps >= 5)
    chance += clamp((avgRating(me.season) - 6.7) * 0.14, -0.12, 0.16);
  if (game.flag("doghouse")) chance -= 0.22;
  chance += (managerStyle(club)[4] - 1.0) * 0.18;   // מאמן שסולח יותר
  return clamp(chance, 0.05, 0.92);
}

function meetingOptions(game) {
  const club = game.myClub();
  if (!club || !["academy", "player", "veteran"].includes(game.stage)) return [];
  const last = Number(game.flag("meeting_week", -99));
  if (game.week - last < MEETING_COOLDOWN) return [];
  return MEETINGS.map(([key, name, line, difficulty]) =>
    ({ key, name, line, odds: meetingOdds(game, difficulty) }));
}

/** נכנס אליו למשרד ומבקש. יוצא עם משהו, או עם פחות ממה שנכנסת. */
function managerRequest(game, key, rng) {
  const club = game.myClub();
  if (!club) return "אין לך מועדון.";
  const row = MEETINGS.find(r => r[0] === key);
  if (!row) return "לא ידוע.";
  const [, , , difficulty, gain, cost] = row;
  game.setFlag("meeting_week", game.week);
  const who = club.managerName;

  if (rng.random() < meetingOdds(game, difficulty)) {
    club.managerTrust = clamp(club.managerTrust + gain, 0, 100);
    game.setFlag("doghouse", false);
    if (key === "role")
      return givePromise(game, "start") + `\n${who}: "תוכיח לי שצדקתי."`;
    if (key === "position")
      return givePromise(game, "role") + `\n${who}: "בסדר. העמדה שלך."`;
    if (key === "promise")
      return givePromise(game, "minutes") + `\n${who}: "שלושה משחקים. לא יותר."`;
    if (key === "leave") {
      game.setFlag("free_to_leave", true);
      return `🤝 ${who}: "אני לא כולא אף אחד. תביא הצעה נורמלית ואני לא אעמוד בדרך."`;
    }
    return `🎙️ ${who} הסביר בדיוק מה חסר לך, בלי לרכך. `
         + `יצאת עם רשימה ולא עם תירוץ.`;
  }

  club.managerTrust = clamp(club.managerTrust + cost, 0, 100);
  game.me.morale = clamp(game.me.morale - 5, 5, 99);
  if ((key === "role" || key === "leave") && rng.random() < 0.45) {
    game.setFlag("doghouse", true);
    return `⛔ ${who}: "אתה לא במצב לבקש." מהשבוע הבא אתה מתאמן עם הקבוצה השנייה.`;
  }
  return `🚫 ${who} שמע עד הסוף ואמר "לא עכשיו". זה לא נשמע כמו "אחר כך".`;
}

/**
 * הנהלה מאבדת סבלנות — ומאמן חדש הוא דף חדש, לטוב ולרע. כל היחסים
 * שבנית חצי שנה נמחקים ברביעי בבוקר, והחדש לא חייב לך כלום.
 */
function maybeReplaceManager(game, rng) {
  const club = game.myClub();
  if (!club || !["academy", "player", "veteran"].includes(game.stage)) return null;
  let pressure = 0;
  if (club.boardConfidence < 35) pressure += 0.05;
  if (club.boardConfidence < 22) pressure += 0.07;
  if (club.fanSupport < 30) pressure += 0.02;
  if (pressure <= 0 || rng.random() > pressure) return null;

  const old = club.managerName;
  club.managerName = rng.choice(D.MANAGER_NAMES.filter(n => n !== old));
  // אמון מתאפס לאמצע, וכל מה שנצבר — הבטחות, כלוב, סרט — יורד לטמיון
  club.managerTrust = clamp(rng.uniform(38, 58), 0, 100);
  club.boardConfidence = clamp(club.boardConfidence + 12, 0, 100);
  delete game.flags.promise;
  game.setFlag("doghouse", false);
  game.setFlag("new_manager", true);
  const style = managerStyle(club);
  return `📣 ${old} פוטר. ${club.managerName} נכנס — ${style[1]}. ${style[2]}\n`
       + `   כל מה שבנית מול הקודם — מתחיל מאפס.`;
}
