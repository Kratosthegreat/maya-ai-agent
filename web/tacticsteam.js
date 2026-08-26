// ---------------------------------------------------------------------------
// הטקטיקה של המאמן, ומה היא עושה לך — תאום JS של tactics.py
//
// עד עכשיו הטקטיקה הייתה משהו שקרה מעליך. במקור היא מה שקובע איך
// נראות תשעים הדקות שלך: כמה תיגע בכדור, כמה תרוץ, כמה תאבד.
// ---------------------------------------------------------------------------

function tacticHash(text) {
  let value = 2166136261;
  for (const ch of text) {
    value ^= ch.codePointAt(0);
    value = Math.imul(value, 16777619) >>> 0;
  }
  return value;
}

/** הסגנון הטקטי של המועדון — נגזר משם המאמן, ולכן קבוע. */
function tacticalStyle(club) {
  if (!club || !club.managerName) return D.TACTICAL_STYLES.find(r => r[0] === "balanced_style");
  const index = tacticHash(club.managerName + "tactics") % D.TACTICAL_STYLES.length;
  return D.TACTICAL_STYLES[index];
}

/** שבע ההוראות שהמאמן משחק איתן השבוע. */
function teamInstructions(club) {
  const style = tacticalStyle(club);
  const values = Object.assign({}, style[2]);
  if (club) {
    if (club.boardConfidence < 35) {
      values.mentality = clamp(values.mentality - 1, -2, 2);
      values.d_line = clamp(values.d_line - 1, -2, 2);
    } else if (club.boardConfidence > 75) {
      values.mentality = clamp(values.mentality + 1, -2, 2);
    }
    if (club.reputation < 40) {
      values.passing = clamp(values.passing + 1, -2, 2);
      values.pressing = clamp(values.pressing - 1, -2, 2);
    }
  }
  return values;
}

function instructionLabel(key, value) {
  const rows = D.TEAM_INSTRUCTIONS[key];
  if (!rows) return "";
  const row = rows[1].find(r => r[2] === value);
  return row ? row[1] : "";
}

function describeTactics(club) {
  const style = tacticalStyle(club);
  const values = teamInstructions(club);
  const lines = [`${style[1]} — ${style[3]}`];
  for (const key of D.INSTRUCTION_KEYS)
    lines.push(`${D.TEAM_INSTRUCTIONS[key][0]}: ${instructionLabel(key, values[key])}`);
  return lines;
}

/**
 * מכפילים לשורת הסטטיסטיקה שלך, לפי הטקטיקה והתפקיד.
 * זה הלב: אתה מרגיש את הטקטיקה בגוף.
 */
function tacticModifiers(club, player) {
  return modifiersFrom(teamInstructions(club), player);
}

/** מכפילים לשורת הסטטיסטיקה, מתוך ערכי הוראות מפורשים. */
function modifiersFrom(values, player) {
  const row = roleRow(player.role);
  const [dutyDef, dutyAtt, dutyRun] = D.DUTY_SHIFT[player.duty] || [0, 0, 0];

  const tempo = values.tempo / 2, width = values.width / 2;
  const directness = values.passing / 2, press = values.pressing / 2;
  const line = values.d_line / 2, mentality = values.mentality / 2;

  const mods = {
    passes: 1 - directness * 0.26 - tempo * 0.10,
    pass_pct: 1 - directness * 0.09 - tempo * 0.04,
    losses: 1 + directness * 0.22 + tempo * 0.14 - press * 0.05,
    shots: 1 + mentality * 0.20 + dutyAtt * 0.9,
    key_passes: 1 + mentality * 0.14 + width * 0.10 + dutyAtt * 0.6,
    dribbles: 1 + width * 0.12 - directness * 0.14,
    tackles: 1 + press * 0.30 + line * 0.10 + dutyDef * 1.0,
    duels: 1 + press * 0.18 + directness * 0.12,
    sprints: 1 + tempo * 0.22 + press * 0.24 + dutyRun * 1.2,
    distance: 1 + tempo * 0.09 + press * 0.13 + dutyRun * 0.5,
    reads: 1 + (1 - Math.abs(mentality)) * 0.05 - press * 0.04,
  };
  if (row) {
    const keyAttrs = new Set(row[4]);
    if (keyAttrs.has("crossing")) mods.key_passes *= 1.25;
    if (keyAttrs.has("finishing")) mods.shots *= 1.30;
    if (keyAttrs.has("tackling") || keyAttrs.has("marking")) mods.tackles *= 1.28;
    if (keyAttrs.has("passing") || keyAttrs.has("vision")) { mods.passes *= 1.22; mods.key_passes *= 1.15; }
    if (keyAttrs.has("dribbling")) mods.dribbles *= 1.30;
    if (keyAttrs.has("stamina") || keyAttrs.has("work_rate")) { mods.distance *= 1.12; mods.sprints *= 1.12; }
    if (keyAttrs.has("off_the_ball")) { mods.shots *= 1.12; mods.sprints *= 1.08; }
  }
  for (const key in mods) mods[key] = clamp(mods[key], 0.35, 2.4);
  return mods;
}

/** כמה הסגנון הזה מתאים לך, ולמה. */
function styleSuitsPlayer(club, player) {
  return suitsValues(teamInstructions(club), player);
}

/** כמה סגנון נתון מתאים לשחקן. */
function suitsValues(values, player) {
  const d = player.detail;
  let score = 50;
  const notes = [];
  const pace = ((d.acceleration ?? 10) + (d.pace ?? 10)) / 2;
  const tech = ((d.technique ?? 10) + (d.first_touch ?? 10)) / 2;
  const engine = ((d.stamina ?? 10) + (d.work_rate ?? 10)) / 2;
  const brain = ((d.decisions ?? 10) + (d.vision ?? 10)) / 2;

  if (values.tempo >= 1 || values.pressing >= 1) {
    score += (engine - 11) * 4.4;
    notes.push(engine < 11 ? "קצב ולחיצה — צריך ריאות" : "הקצב הזה בנוי בשבילך");
  }
  if (values.passing <= -1) {
    score += (tech - 11) * 4.2;
    notes.push(tech >= 11 ? "משחק קצר — הכול עובר בנגיעה"
                          : "משחק קצר, והנגיעה שלך עוד לא שם");
  }
  if (values.passing >= 1) {
    score += (pace - 11) * 3.8;
    notes.push(pace >= 11 ? "כדורים לעומק — בשביל זה צריך רגליים"
                          : "הם משחקים ארוך, ואתה לא הכי מהיר");
  }
  if (values.mentality <= -1) {
    score += (brain - 11) * 3.0;
    notes.push("קבוצה שמחכה — הסבלנות שלך נמדדת");
  }
  return [clamp(score, 0, 100), notes.length ? notes[0] : "סגנון שלא מושך לשום קיצון"];
}

/** האם התפקיד שנתנו לך הוא באמת שלך. */
function roleFitNote(player) {
  if (!player.role) return null;
  const mine = roleSuitability(player, player.role);
  const [bestKey, bestScore] = bestRole(player);
  const row = roleRow(player.role);
  if (!row) return null;
  if (bestKey === player.role || bestScore - mine < 5)
    return `✅ ${row[1]} — זה התפקיד שמוציא ממך את המקסימום.`;
  const bestRow = roleRow(bestKey);
  return `↔️ אתה משחק ${row[1]} (${Math.round(mine)}), אבל התכונות שלך אומרות `
       + `${bestRow[1]} (${Math.round(bestScore)}).`;
}

// ---------------------------------------------------------------------------
// מי מחלק את התפקידים
// ---------------------------------------------------------------------------

/** המאמן נותן לך תפקיד. לרוב הנכון — לא תמיד. */
function assignRole(player, club, rng) {
  const options = rolesFor(player.position);
  if (!options.length) return "";
  const style = tacticalStyle(club);
  const bonus = {
    gegenpress: ["work_rate", "stamina", "aggression"],
    tiki_taka: ["passing", "vision", "technique"],
    counter: ["acceleration", "pace", "off_the_ball"],
    wing_play: ["crossing", "heading"],
    catenaccio: ["marking", "positioning", "tackling"],
  }[style[0]] || [];
  let best = null, bestScore = -1e9;
  for (const row of options) {
    let score = roleSuitability(player, row[0]);
    const keyAttrs = new Set(row[4]);
    if (bonus.some(a => keyAttrs.has(a))) score += 9;
    score += rng.uniform(-4, 4);
    if (score > bestScore) { bestScore = score; best = row; }
  }
  return best ? best[0] : "";
}

function dutyFor(roleKey, club, rng) {
  const row = roleRow(roleKey);
  if (!row) return "support";
  const duties = row[3];
  if (duties.length === 1) return duties[0];
  const mentality = teamInstructions(club).mentality;
  const order = { attack: 2, support: 0, automatic: 0, defend: -2, cover: -2, stopper: -1 };
  const wanted = clamp(mentality, -2, 2);
  const ranked = duties.slice().sort((a, b) =>
    Math.abs((order[a] || 0) - wanted) - Math.abs((order[b] || 0) - wanted));
  return rng.random() < 0.75 ? ranked[0] : rng.choice(duties);
}

/** לבקש מהמאמן תפקיד אחר. הוא לא חייב להסכים. */
function requestRole(game, roleKey) {
  const me = game.me;
  const club = game.myClub();
  const row = roleRow(roleKey);
  if (!row || !row[2].includes(me.position)) return "זה לא תפקיד שאפשר למלא בעמדה שלך.";
  if (roleKey === me.role) return `אתה כבר משחק ${row[1]}.`;
  if (!club) { me.role = roleKey; return `מהיום אתה ${row[1]}.`; }

  const fit = roleSuitability(me, roleKey);
  const current = me.role ? roleSuitability(me, me.role) : 0;
  const trust = club.managerTrust;
  const chance = 0.16 + trust / 190 + Math.max(0, fit - current) / 90;
  if (game.rng.random() < clamp(chance, 0.05, 0.9)) {
    me.role = roleKey;
    me.duty = dutyFor(roleKey, club, game.rng);
    club.managerTrust = clamp(trust - 3, 0, 100);
    return `✅ ${club.managerName} הסכים. מהשבוע אתה ${row[1]} `
         + `(${D.DUTY_NAMES_HE[me.duty] || ""}).`;
  }
  club.managerTrust = clamp(trust - 5, 0, 100);
  return `⛔ ${club.managerName} שמע ואמר שהוא לא משנה מערכת בשביל `
       + "שחקן אחד. השיחה הזאת לא עזרה לך.";
}

/** כמה הטקטיקה הזאת שוחקת אותך. גגנפרסינג עולה בגוף. */
function tacticFitnessCost(club, player) {
  const values = teamInstructions(club);
  const run = (D.DUTY_SHIFT[player.duty] || [0, 0, 0])[2];
  let load = 1 + values.pressing * 0.09 + values.tempo * 0.06 + run * 0.8;
  const stamina = player.detail.stamina ?? 10;
  const natural = player.detail.natural_fitness ?? 10;
  load *= 1.24 - ((stamina + natural) / 2) * 0.024;
  return clamp(load, 0.6, 1.7);
}
