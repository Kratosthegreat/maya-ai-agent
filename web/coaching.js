// ---------------------------------------------------------------------------
// מה כל תכונה עושה, כמה היא שווה *לך*, ומה יקרה אם תתאמן עליה
// תאום JS של coaching.py
//
// "מה זה צמידות? במה הוא מועיל? האם השחקן צריך אותו ברגע זה?" —
// שלוש שאלות שלא הייתה להן תשובה בשום מקום במשחק.
// ---------------------------------------------------------------------------

const WEIGHT_ROLE_KEY = 34, WEIGHT_ROLE_EXTRA = 18;
const WEIGHT_POSITION = 26, WEIGHT_PLAN = 22, WEIGHT_GAP = 30;

function explainAttr(attr) {
  return D.ATTR_INFO[attr] || D.FOCUS_INFO[attr] || ["", "", ""];
}

const DEMAND_CACHE = {};

/** כמה כל תכונה נדרשת בעמדה, מנורמל כך שהחשובה ביותר היא 1.0. */
function demandTable(position) {
  if (DEMAND_CACHE[position]) return DEMAND_CACHE[position];
  const weights = D.POSITION_WEIGHTS[position];
  const mapping = groupMapFor(position);
  const raw = {};
  for (const attr of attrsFor(position)) {
    let total = 0;
    for (const group in mapping) {
      const share = mapping[group][attr];
      if (share) total += share * (weights[group] || 0);
    }
    raw[attr] = total;
  }
  const top = Math.max(...Object.values(raw)) || 1;
  const table = {};
  for (const attr in raw) table[attr] = raw[attr] / top;
  DEMAND_CACHE[position] = table;
  return table;
}

function positionDemand(attr, position) {
  return demandTable(position)[attr] || 0;
}

/** כמה התכונה הזאת שווה לך *עכשיו*, ולמה. */
function attrRelevance(game, attr) {
  const me = game.me;
  const row = roleRow(me.role);
  const reasons = [];
  let score = 0;
  let wanted = 0;            // 0-1: כמה בכלל צריך ממך את התכונה הזאת

  if (row && row[4].includes(attr)) {
    score += WEIGHT_ROLE_KEY;
    wanted = 1;
    reasons.push(`תכונת מפתח ב${row[1]}`);
  } else if (row && row[5].includes(attr)) {
    score += WEIGHT_ROLE_EXTRA;
    wanted = 0.65;
    reasons.push(`נדרשת ב${row[1]}`);
  }

  const demand = positionDemand(attr, me.position);
  score += demand * WEIGHT_POSITION;
  wanted = Math.max(wanted, demand);
  if (demand >= 0.55 && !reasons.length)
    reasons.push(`חשובה ל${D.POSITION_NAMES_HE[me.position]}`);

  for (const entry of milestoneRows(game)) {
    if (entry.claimed) continue;
    for (const part of entry.needs) {
      if (part.attr === attr && part.have < part.need) {
        score += WEIGHT_PLAN;
        wanted = 1;
        reasons.push(`חוסמת אבן דרך של גיל ${entry.age}`);
        break;
      }
    }
    break;
  }

  // כמה אתה נמוך בה — אבל רק במידה שבכלל צריך אותה. חלוץ עם צמידות 5
  // הוא לא בעיה: זה בדיוק מה שאמור להיות.
  const allowed = attrsFor(me.position);
  const average = allowed.reduce((a, k) => a + (me.detail[k] ?? 10), 0) / allowed.length;
  const level = me.detail[attr] ?? 10;
  const gap = average - level;
  if (gap > 0) {
    score += Math.min(WEIGHT_GAP, gap * 7) * wanted;
    if (gap >= 2.5 && wanted >= 0.4) reasons.push("נמוכה ביחס לשאר התכונות שלך");
  } else if (level >= 17) {
    reasons.push("כבר ברמה גבוהה");
  }

  if (SET_PIECE_ATTRS.has(attr)) {
    score *= 0.55;
    reasons.push("מומחיות — משתפרת רק באימון ישיר");
  }

  return { attr, score: Math.round(clamp(score, 0, 100)),
           reasons: reasons.slice(0, 3), level,
           average: Math.round(average * 10) / 10 };
}

/**
 * כל התכונות שלך, מסודרות לפי כמה הן שוות לך עכשיו.
 * הפסק ניתן ביחס לעצמך: "מקום 1 מתוך 36" אומר יותר מ"45 מתוך 100".
 */
function needsTable(game) {
  const rows = attrsFor(game.me.position).map(attr => attrRelevance(game, attr));
  rows.sort((a, b) => b.score - a.score);
  const total = rows.length;
  const top = rows.length ? rows[0].score : 1;
  rows.forEach((row, index) => {
    row.rank = index + 1;
    row.of = total;
    const share = top ? row.score / top : 0;
    if (index < 3 && share >= 0.75) row.verdict = "כן — זה מה שחסר לך עכשיו";
    else if (share >= 0.62) row.verdict = "שווה, אבל לא הכי דחוף";
    else if (share >= 0.35) row.verdict = "לא בראש סדר העדיפויות";
    else row.verdict = "לא רלוונטי אליך";
    // תכונה בתקרה היא לא "פחות דחופה" — היא גמורה, וזה מה שצריך
    // להיכתב. בלי זה שחקן מתאמן שבועות על משהו שאי אפשר לשפר.
    row.capped = row.level >= D.MAX_DETAIL;
    if (row.capped) row.verdict = "בתקרה — אין לאן לשפר";
  });
  return rows;
}

function relevanceOf(game, attr) {
  const found = needsTable(game).find(row => row.attr === attr);
  if (found) return found;
  const row = attrRelevance(game, attr);
  return Object.assign(row, { rank: 0, of: 0, verdict: "לא רלוונטי אליך" });
}

function rankedNeeds(game, limit = 6) { return needsTable(game).slice(0, limit); }

// ---------------------------------------------------------------------------
// תחזית: מה יקרה אם אתאמן על זה
// ---------------------------------------------------------------------------

/** כמה נקודות (1-20) תרוויח בשבוע בממוצע. הנוסחה האמיתית, בלי ההגרלה. */
function weeklyRate(game, attr, intensity = null) {
  const me = game.me;
  const club = game.myClub();
  intensity = intensity === null ? game.intensity : intensity;
  const facilities = club ? club.trainingFacilities : 45;
  const assistant = club ? staffQuality(club, "assistant") : 0;

  let base = 0.178 * intensity;
  base *= 0.55 + facilities / 110;
  base *= 1 + assistant / 420;
  base *= Math.max(0.15, ageFactor(me.age));
  base *= 1 + clamp(me.potential - overall(me), -10, 18) * 0.032;
  if (hasTrait(me, "workhorse")) base *= 1.30;
  base *= 0.75 + me.morale / 200;
  base *= personalityEffect(me)[0];
  base *= 0.55 + (me.detail.determination ?? 10) / 22;
  base *= 1.025;                        // תוחלת ההגרלה 0.7-1.35

  const headroom = me.potential - overall(me);
  if (headroom <= 0) base *= 0.06;
  else if (headroom < 6) base *= 0.20 + headroom * 0.13;

  const shares = trainingShares(me, attr);
  const share = shares[attr] || 0;
  const keys = Object.keys(shares);
  const average = keys.length
    ? keys.reduce((a, k) => a + (me.detail[k] ?? 10), 0) / keys.length : 10;
  const level = me.detail[attr] ?? 10;
  return base * share * detailDamper(level, average) * ceilingDamper(level) / 5;
}

/**
 * כמה תעלה התכונה בפועל ב-N שבועות.
 * לא הכפלה של הקצב הנוכחי: ככל שהתכונה עולה, הבלם מאט אותה והתקרה
 * עוצרת אותה. תחזית קווית הייתה מבטיחה כפול ממה שיקרה.
 */
function projectedGain(game, attr, weeks, intensity = null) {
  const me = game.me;
  let level = me.detail[attr] ?? 10;
  if (level >= 20) return 0;
  const allowed = attrsFor(me.position);
  const others = allowed.filter(a => a !== attr)
    .reduce((a, k) => a + (me.detail[k] ?? 10), 0);
  const count = Math.max(1, allowed.length);
  const rate = weeklyRate(game, attr, intensity);
  if (rate <= 0) return 0;
  const baseLevel = me.detail[attr] ?? 10;
  let total = 0;
  for (let i = 0; i < weeks && level < 20; i++) {
    const average = (others + level) / count;
    const base = detailDamper(baseLevel, average) * ceilingDamper(baseLevel);
    const now = detailDamper(level, average) * ceilingDamper(level);
    const step = rate * (base > 0 ? now / base : 1);
    level = Math.min(20, level + step);
    total += step;
  }
  return Math.min(total, 20 - (me.detail[attr] ?? 10));
}

function forecast(game, attr, weeks = 6, intensity = null) {
  const me = game.me;
  const rate = weeklyRate(game, attr, intensity);
  const level = me.detail[attr] ?? 10;
  const gain = projectedGain(game, attr, weeks, intensity);
  intensity = intensity === null ? game.intensity : intensity;
  const injury = intensity > 1.15 ? 0.022 * intensity * injuryRisk(me) : 0;
  const shares = trainingShares(me, attr);
  const side = Object.entries(shares).filter(([a]) => a !== attr)
    .sort((a, b) => b[1] - a[1]).slice(0, 3).map(([a]) => a);
  return {
    attr, rate: Math.round(rate * 1000) / 1000,
    weeks_per_point: rate > 0.001 ? Math.round(10 / rate) / 10 : null,
    gain: Math.round(gain * 10) / 10, level,
    target: Math.min(20, Math.round(level + gain)),
    fitness_cost: Math.round((2.5 + 5 * intensity) * 10) / 10,
    injury_pct: Math.round(injury * 1000) / 10,
    side,
  };
}

/** שורה אחת שאומרת מה יקרה. זה מה שהיה חסר כדי לבחור אימון. */
function forecastLine(game, attr) {
  const data = forecast(game, attr);
  const name = D.DETAIL_NAMES_HE[attr] || attr;
  if ((game.me.detail[attr] ?? 10) >= D.MAX_DETAIL)
    return `${name} ${D.MAX_DETAIL} — התקרה של הסולם. אי אפשר לשפר את זה `
         + `יותר, והאימון שמכוון לכאן עובר לתכונות שלידו.`;
  if (data.weeks_per_point === null)
    return `${name}: כרגע לא תתקדם בזה — הגעת לתקרת הפוטנציאל.`;
  const weeks = data.weeks_per_point;
  const pace = weeks >= 1.5 ? `נקודה כל ${Math.round(weeks)} שבועות`
                            : `כ-${(1 / weeks).toFixed(1)} נקודות בשבוע`;
  const side = data.side.map(a => D.DETAIL_NAMES_HE[a]).join(", ");
  return `${name} ${data.level} → ${data.target} בשישה שבועות (${pace}). `
       + `אגב זה יעלו גם ${side}.`;
}

// ---------------------------------------------------------------------------
// איך התפתחתי, ובכמה
// ---------------------------------------------------------------------------

function growthLog(game) {
  return Array.isArray(game.flags.growth_log) ? game.flags.growth_log : [];
}

/** לא "כאילו מתפתח": מספרים מדויקים מהעונה הראשונה שנרשמה ועד היום. */
function growthSummary(game) {
  const me = game.me;
  const log = growthLog(game);
  if (!log.length) return { seasons: [], since: null, moved: [], physical: null };

  const first = log[0];
  const rows = [];
  let previous = null;
  for (const shot of log) {
    const row = Object.assign({}, shot);
    if (previous) {
      row.d_overall = shot.overall - previous.overall;
      row.d_height = shot.height - previous.height;
      row.d_weight = shot.weight - previous.weight;
      row.d_points = Object.keys(shot.detail).reduce((a, k) =>
        a + Math.max(0, (shot.detail[k] ?? 10) - (previous.detail[k] ?? 10)), 0);
    } else {
      row.d_overall = row.d_height = row.d_weight = row.d_points = 0;
    }
    delete row.detail;
    rows.push(row);
    previous = shot;
  }

  const moved = [];
  for (const attr of attrsFor(me.position)) {
    const start = first.detail[attr] ?? 10;
    const delta = (me.detail[attr] ?? 10) - start;
    if (delta) moved.push({ attr, name: D.DETAIL_NAMES_HE[attr], from: start,
                            to: me.detail[attr] ?? 10, delta });
  }
  moved.sort((a, b) => b.delta - a.delta);

  return {
    seasons: rows, since: first.year, since_age: first.age, moved,
    total_points: moved.filter(r => r.delta > 0).reduce((a, r) => a + r.delta, 0),
    overall_from: first.overall, overall_to: overall(me),
    physical: {
      height_from: first.height, height_to: me.height,
      weight_from: first.weight, weight_to: me.weight,
      adult_height: me.adultHeight,
      left: Math.max(0, (me.adultHeight || me.height) - me.height),
    },
  };
}

// ---------------------------------------------------------------------------
// מה יש בקבוצה שלי
// ---------------------------------------------------------------------------

/** פרטי הקבוצה שהיו חסרים: עומק לפי עמדה, מי לפניך, ואיפה אתה עומד. */
function squadReport(game) {
  const club = game.myClub();
  const me = game.me;
  if (!club) return { has_club: false };

  const squad = club.squad.map(pid => game.players[pid]).filter(Boolean);
  const byPosition = {};
  for (const player of squad) {
    (byPosition[player.position] = byPosition[player.position] || []).push({
      pid: player.pid, name: player.name, age: player.age,
      overall: overall(player), role: player.role, number: player.number,
      available: isAvailable(player), is_me: player.pid === me.pid,
    });
  }
  for (const rows of Object.values(byPosition)) rows.sort((a, b) => b.overall - a.overall);

  const rivals = (byPosition[me.position] || []).filter(r => !r.is_me);
  const ages = squad.length ? squad.map(p => p.age) : [25];
  const leagueClubs = Object.values(game.clubs).filter(c => c.leagueId === club.leagueId);
  const ranked = leagueClubs.slice().sort((a, b) => b.reputation - a.reputation);

  return {
    has_club: true, name: club.name, nickname: club.nickname,
    reputation: club.reputation,
    rep_rank: ranked.findIndex(c => c.cid === club.cid) + 1,
    rep_of: ranked.length,
    manager: club.managerName, squad_size: squad.length,
    average_age: Math.round(ages.reduce((a, b) => a + b, 0) / ages.length * 10) / 10,
    average_overall: Math.round(squad.reduce((a, p) => a + overall(p), 0)
                                / Math.max(1, squad.length)),
    by_position: byPosition,
    ahead_of_me: rivals.filter(r => r.overall > overall(me)),
    depth_here: (byPosition[me.position] || []).length,
    facilities: Object.entries(D.FACILITIES).map(([key, info]) => ({
      key, name: info.name, value: Math.trunc(facilityLevel(club, key)),
      desc: info.desc || "" })),
    staff: Object.entries(D.STAFF_ROLES).map(([key, info]) => ({
      role: key, name: info.name, member: club.staff[key] || null,
      quality: staffQuality(club, key) })),
  };
}
