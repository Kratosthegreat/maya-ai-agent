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
  if (stats) return weakestArea(stats, me.position, me.attributes);
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
function directiveLine(club, focus, stats = null) {
  const name = club ? club.managerName : "המאמן";
  const head = `${name} ${DIRECTIVE_TEXT[focus] || "רוצה אותך באימון נוסף."}`;
  if (!stats) return head;
  const reason = reasonLine(focus, stats);
  const promise = promiseLine(focus);
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
