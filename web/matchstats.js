// ---------------------------------------------------------------------------
// שורת הסטטיסטיקה האישית שלך אחרי משחק — תאום JS של matchstats.py
//
// זה החוט שהיה חסר. עד עכשיו התאמנת על בעיטות, המספר בתפריט עלה,
// ובמשחק לא ראית כלום. כאן כל תכונה מייצרת מספר שאתה רואה, והמאמן
// קורא בדיוק את המספרים האלה כשהוא מחליט מה לדרוש ממך בשבוע הבא.
// ---------------------------------------------------------------------------

function statRate(value, low, high) {
  return low + (high - low) * clamp(value, 0, 100) / 100;
}

/** הגרלה שלמה סביב ממוצע — עם שארית הסתברותית, כדי ש-0.4 יהיה 0.4. */
function statDraw(rng, mean) {
  if (mean <= 0) return 0;
  let whole = Math.trunc(mean);
  if (rng.random() < mean - whole) whole += 1;
  const spread = Math.max(1, Math.trunc(whole * 0.45));
  return Math.max(0, whole + rng.randint(-spread, spread));
}

function matchStatLine(player, minutes, goals, assists, rng,
                       possession = 0.5, fitnessAtKickoff = null, mods = null) {
  const attrs = player.attributes;
  const share = D.POSITION_ROLE_SHARE[player.position];
  const load = (minutes / 90) * (0.72 + possession * 0.56);
  const fit = fitnessAtKickoff === null ? player.fitness : fitnessAtKickoff;
  const stamina = 0.80 + 0.20 * clamp(fit, 0, 100) / 100;
  const sharp = 0.86 + 0.28 * clamp(player.sharpness, 0, 100) / 100;

  // קוראים מהתכונות המפורטות כשהן קיימות: "בעיטות למסגרת" נגזרות
  // מסיום ולא מקבוצה שלמה, ולכן אימון ממוקד נראה מיד
  const detail = player.detail || {};
  const fine = (name, fallback) =>
    detail[name] ? detail[name] * 5 : (attrs[fallback] ?? 50);
  const shooting = fine("finishing", "shooting"), passing = fine("passing", "passing");
  const dribbling = fine("dribbling", "dribbling"), defending = fine("tackling", "defending");
  const physical = fine("strength", "physical"), pace = fine("acceleration", "pace");
  const mental = fine("decisions", "mental");
  const exp = {};
  // הטקטיקה של המאמן והתפקיד שנתן לך
  const M = mods || {};
  const mod = key => (M[key] === undefined ? 1 : M[key]);

  let shotRate = share.att * 3.4 + share.mid * 1.0 + share.def * 0.25;
  shotRate *= statRate(shooting, 0.45, 1.5) * statRate(mental, 0.7, 1.25);
  exp.shots = shotRate * load * sharp * mod("shots");
  const shots = statDraw(rng, exp.shots);
  const accuracy = statRate(shooting, 0.22, 0.66) * sharp;
  exp.on_target = exp.shots * accuracy;
  let onTarget = 0;
  for (let i = 0; i < shots; i++) if (rng.random() < accuracy) onTarget += 1;
  onTarget = Math.max(onTarget, Math.min(shots, goals));

  const passVolume = share.mid * 62 + share.def * 46 + share.att * 26;
  exp.passes = passVolume * load * (0.75 + passing / 260) * mod("passes");
  const passes = Math.max(3, statDraw(rng, exp.passes));
  exp.pass_pct = clamp((58 + passing * 0.30 - (1 - stamina) * 22) * mod("pass_pct"), 35, 96);
  const passPct = clamp(exp.pass_pct + rng.gauss(0, 3.4), 35, 96);
  const completed = Math.round(passes * passPct / 100);
  const keyRate = share.att * 1.5 + share.mid * 1.3 + share.def * 0.3;
  exp.key_passes = keyRate * statRate(passing, 0.25, 1.35) * load * mod("key_passes");
  let keyPasses = statDraw(rng, exp.key_passes);
  keyPasses = Math.max(keyPasses, assists);

  exp.dribble_tries = (share.att * 2.6 + share.mid * 1.4 + share.def * 0.5)
                      * statRate(dribbling, 0.4, 1.5) * load * mod("dribbles");
  const dribbleTries = statDraw(rng, exp.dribble_tries);
  exp.dribble_pct = clamp(24 + dribbling * 0.44, 8, 92);
  const dribblePct = clamp(exp.dribble_pct + rng.gauss(0, 5), 8, 92);
  exp.dribbles = exp.dribble_tries * exp.dribble_pct / 100;
  let dribbles = 0;
  for (let i = 0; i < dribbleTries; i++) if (rng.random() * 100 < dribblePct) dribbles += 1;

  exp.duels = (5.5 + share.def * 5.0 + share.mid * 2.5) * load * mod("duels");
  const duels = Math.max(2, statDraw(rng, exp.duels));
  exp.duels_pct = clamp(28 + physical * 0.34 + mental * 0.10 - (1 - stamina) * 26, 10, 92);
  const duelsPct = clamp(exp.duels_pct + rng.gauss(0, 4.5), 10, 92);
  const duelsWon = Math.round(duels * duelsPct / 100);
  const tackleRate = share.def * 4.6 + share.mid * 2.4 + share.att * 0.6;
  exp.tackles = tackleRate * statRate(defending, 0.35, 1.4) * load * mod("tackles");
  const tackles = statDraw(rng, exp.tackles);

  exp.losses = (exp.passes * (1 - exp.pass_pct / 100) * 0.55
                + (exp.dribble_tries - exp.dribbles) * 0.7) * mod("losses");
  const lossBase = passes * (1 - passPct / 100) * 0.55 + (dribbleTries - dribbles) * 0.7;
  const losses = Math.max(0, Math.round(lossBase + rng.gauss(0, 1.1)));

  exp.sprints = (11 + share.att * 9 + share.mid * 7)
                * statRate(pace, 0.45, 1.4) * load * stamina * mod("sprints");
  const sprints = statDraw(rng, exp.sprints);
  const distance = Math.round(clamp((7.4 + share.mid * 3.4 + share.def * 1.2
                                     + physical * 0.022) * (minutes / 90) * stamina
                                    * mod("distance") + rng.gauss(0, 0.35), 2.0, 16.5) * 10) / 10;

  exp.reads = (4.0 + share.def * 2.4 + share.mid * 2.0)
              * statRate(mental, 0.4, 1.55) * load * mod("reads");
  const reads = statDraw(rng, exp.reads);

  const rounded = {};
  for (const k in exp) rounded[k] = Math.round(exp[k] * 1000) / 1000;

  return {
    minutes, goals, assists, shots, on_target: onTarget,
    passes, completed, pass_pct: Math.round(passPct), key_passes: keyPasses,
    dribble_tries: dribbleTries, dribbles,
    duels, duels_won: duelsWon, duels_pct: Math.round(duelsPct),
    tackles, losses, sprints, distance, reads,
    fitness: Math.round(fit), exp: rounded,
  };
}

/** שלוש-ארבע שורות שמסבירות איך שיחקת, בשפה של מגרש. */
function statSummary(stats, position) {
  const share = D.POSITION_ROLE_SHARE[position];
  const lines = [];
  if (stats.shots)
    lines.push(`⚽ ${stats.shots} בעיטות, ${stats.on_target} למסגרת`
               + (stats.goals ? `, ${stats.goals} נכנסו` : ""));
  lines.push(`🎯 ${stats.completed}/${stats.passes} מסירות (${stats.pass_pct}%)`
             + (stats.key_passes ? ` · ${stats.key_passes} מסירות מפתח` : ""));
  if (share.def >= 0.2 || stats.tackles)
    lines.push(`🛡️ ${stats.tackles} חטיפות · ${stats.duels_won}/${stats.duels} `
               + `דו־קרבים (${stats.duels_pct}%)`);
  else
    lines.push(`💪 ${stats.duels_won}/${stats.duels} דו־קרבים (${stats.duels_pct}%)`);
  if (stats.dribble_tries)
    lines.push(`🌀 ${stats.dribbles}/${stats.dribble_tries} כדרורים`);
  lines.push(`🏃 ${stats.distance} ק"מ · ${stats.sprints} ספרינטים · `
             + `${stats.losses} איבודי כדור`);
  return lines;
}

/**
 * כמה טוב היית בכל תחום, ביחס למה שהתכונות שלך מבטיחות.
 * 70 פירושו "בדיוק כמו שאתה" — ערב ממוצע.
 */
function areaScores(stats, position) {
  const exp = stats.exp || {};
  const scores = {};
  const ratio = (actual, expected, floor) =>
    (expected === undefined || expected < floor) ? null
      : clamp(70 * (actual / expected), 0, 100);

  let got = ratio(stats.on_target + stats.goals * 1.4, (exp.on_target || 0) * 1.25, 0.35);
  if (got !== null) scores.shooting = got;

  const passParts = [];
  if (exp.pass_pct) passParts.push(clamp(70 * stats.pass_pct / exp.pass_pct, 0, 100));
  if ((exp.key_passes || 0) >= 0.25)
    passParts.push(clamp(70 * (stats.key_passes + stats.assists * 1.2)
                         / (exp.key_passes * 1.2), 0, 100));
  if ((exp.losses || 0) >= 1.0)
    passParts.push(clamp(140 - 70 * stats.losses / exp.losses, 0, 100));
  if (passParts.length)
    scores.passing = passParts.reduce((a, b) => a + b, 0) / passParts.length;

  got = ratio(stats.dribbles, exp.dribbles || 0, 0.30);
  if (got !== null) scores.dribbling = got;
  got = ratio(stats.tackles, exp.tackles || 0, 0.35);
  if (got !== null) scores.defending = got;
  if (exp.duels_pct) scores.physical = clamp(70 * stats.duels_pct / exp.duels_pct, 0, 100);
  got = ratio(stats.sprints, exp.sprints || 0, 1.0);
  if (got !== null) scores.pace = got;
  got = ratio(stats.reads, exp.reads || 0, 0.5);
  if (got !== null) scores.mental = got;

  if (!Object.keys(scores).length) scores.physical = 70;
  return scores;
}

/** ציון כולל למשחק, 0-100, כשהעמדה קובעת על מה מסתכלים. 70 = ערב ממוצע. */
function matchPerformance(stats, position) {
  const scores = areaScores(stats, position);
  const weights = D.POSITION_WEIGHTS[position];
  let total = 0, sum = 0;
  for (const area in scores) {
    const w = weights[area] || 0;
    total += w;
    sum += scores[area] * w;
  }
  return total <= 0 ? 70 : sum / total;
}

/**
 * מה המאמן יבקש ממך לעבוד עליו: הפער הקבוע מול דרישות העמדה,
 * ומה שקרה במשחק האחרון. תחום שהעמדה כמעט לא נוגעת בו לא עולה לדיון.
 */
function weakestArea(stats, position, attributes = null) {
  const scores = areaScores(stats, position);
  const weights = D.POSITION_WEIGHTS[position];
  const top = Math.max(...Object.values(weights)) || 1;
  const attrs = attributes || {};
  let best = null, bestKey = "physical";
  for (const area in weights) {
    const relevance = weights[area] / top;
    if (relevance < 0.18) continue;
    const need = 45 + relevance * 48;
    const gap = attributes ? ((attrs[area] ?? 60) - need) : 0;
    const matchGap = ((scores[area] === undefined ? 70 : scores[area]) - 70) * 0.30;
    const rank = gap + matchGap;
    if (best === null || rank < best) { best = rank; bestKey = area; }
  }
  return bestKey;
}

function reasonLine(area, stats) {
  const pair = D.DIRECTIVE_REASON[area];
  if (!pair) return "";
  return pair[0].replace(/\{(\w+)\}/g, (m, key) =>
    stats[key] === undefined ? m : String(stats[key]));
}

function promiseLine(area) {
  const pair = D.DIRECTIVE_REASON[area];
  return pair ? pair[1] : "";
}


/**
 * התכונה המפורטת שהמאמן יבקש ממך לעבוד עליה.
 * קודם התחום שנפל במשחק, ואז — בתוכו — התכונה הנמוכה מבין אלה
 * שהתפקיד שלך באמת דורש.
 */
function weakestDetail(stats, player) {
  const area = weakestArea(stats, player.position, player.attributes);
  if (area === "rest") return "rest";
  const members = groupMapFor(player.position)[area] || {};
  const allowed = new Set(attrsFor(player.position));
  const row = roleRow(player.role || "");
  const roleAttrs = new Set(row ? row[4].concat(row[5]) : []);
  let best = null, bestKey = area;
  for (const attr in members) {
    if (!allowed.has(attr)) continue;
    let score = (player.detail[attr] ?? 10) - members[attr] * 2.4;
    if (roleAttrs.has(attr)) score -= 3.5;
    if (best === null || score < best) { best = score; bestKey = attr; }
  }
  return bestKey;
}
