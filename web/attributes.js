// ---------------------------------------------------------------------------
// התכונות המפורטות — תאום JS של החלק הזה ב-models.py
//
// הכלל: detail הוא האמת, attributes נגזר. כל כתיבה עוברת דרך addDetail
// או addGroup, ושתיהן מסתיימות ב-recomputeGroups. אין דרך אחרת לשנות
// תכונה — וזה מה שמונע מהשניים להתפצל.
// ---------------------------------------------------------------------------

function groupMapFor(position) {
  return position === "GK" ? D.GROUP_MAP_GK : D.GROUP_MAP;
}

function attrsFor(position) {
  return position === "GK" ? D.KEEPER_ATTRS : D.OUTFIELD_ATTRS;
}

/** מחשב מחדש את שבע הקבוצות (1-100) מתוך התכונות המפורטות (1-20). */
function recomputeGroups(p) {
  const mapping = groupMapFor(p.position);
  for (const group in mapping) {
    let total = 0, weight = 0;
    const members = mapping[group];
    for (const attr in members) {
      total += (p.detail[attr] ?? 10) * members[attr];
      weight += members[attr];
    }
    p.attributes[group] = Math.round(clamp(weight ? (total / weight) * 5 : 50, 1, 99));
  }
}

/** מוסיף שבר לתכונה מפורטת. מחזיר כמה נקודות שלמות נוספו. */
function addDetail(p, attr, delta) {
  if (!(attr in D.DETAIL_NAMES_HE)) return 0;
  let current = (p.detailGrowth[attr] || 0) + delta;
  let gained = 0;
  while (current >= 1 && (p.detail[attr] ?? 10) < 20) {
    p.detail[attr] = (p.detail[attr] ?? 10) + 1;
    current -= 1; gained += 1;
  }
  while (current <= -1 && (p.detail[attr] ?? 10) > 1) {
    p.detail[attr] = (p.detail[attr] ?? 10) - 1;
    current += 1; gained -= 1;
  }
  // אין טעם לצבור שברים על תכונה שכבר בתקרה או ברצפה
  if ((p.detail[attr] ?? 10) >= 20) current = Math.min(current, 0);
  else if ((p.detail[attr] ?? 10) <= 1) current = Math.max(current, 0);
  p.detailGrowth[attr] = current;
  if (gained) recomputeGroups(p);
  return gained;
}

/**
 * מפזר שינוי בקבוצה על התכונות המפורטות שמרכיבות אותה.
 * ככה אירועי עלילה שכתובים בשפת הקבוצות ממשיכים לעבוד בלי שינוי.
 */
function addGroup(p, group, delta) {
  const members = groupMapFor(p.position)[group];
  if (!members) return {};
  const allowed = new Set(attrsFor(p.position));
  const usable = {};
  for (const attr in members) if (allowed.has(attr)) usable[attr] = members[attr];
  const keys = Object.keys(usable);
  if (!keys.length) return {};
  const total = keys.reduce((a, k) => a + usable[k], 0);
  const step = delta / 5;
  const gains = {};
  for (const attr of keys) {
    const got = addDetail(p, attr, step * (usable[attr] / total) * keys.length);
    if (got) gains[attr] = got;
  }
  return gains;
}

/** מציב קבוצה שלמה על ערך נתון, דרך התכונות שמרכיבות אותה. */
function setGroup(p, group, value) {
  const members = groupMapFor(p.position)[group];
  if (!members) return;
  const level = Math.round(clamp(value / 5, 1, 20));
  for (const attr in members) p.detail[attr] = level;
  recomputeGroups(p);
}

function setAll(p, value) {
  const level = Math.round(clamp(value / 5, 1, 20));
  for (const attr in D.DETAIL_NAMES_HE) p.detail[attr] = level;
  recomputeGroups(p);
}

// ---------------------------------------------------------------------------
// תפקידים
// ---------------------------------------------------------------------------

const ROLE_BY_KEY = {};
for (const row of D.ROLES) ROLE_BY_KEY[row[0]] = row;

function rolesFor(position) {
  return D.ROLES.filter(row => row[2].includes(position));
}

function roleRow(key) { return ROLE_BY_KEY[key] || null; }

/** 0-100: כמה השחקן מתאים לתפקיד, לפי מה שהתפקיד באמת דורש. */
function roleSuitability(p, roleKey) {
  const row = roleRow(roleKey);
  if (!row) return 0;
  let total = 0, weight = 0;
  for (const attr of row[4]) { total += (p.detail[attr] ?? 10) * 2; weight += 2; }
  for (const attr of row[5]) { total += (p.detail[attr] ?? 10) * 1; weight += 1; }
  let score = weight ? (total / weight) * 5 : 0;
  if (!row[2].includes(p.position)) score *= 0.72;
  return clamp(score, 0, 100);
}

function bestRole(p) {
  const options = rolesFor(p.position);
  if (!options.length) return ["", 0];
  let bestKey = "", best = -1;
  for (const row of options) {
    const score = roleSuitability(p, row[0]);
    if (score > best) { best = score; bestKey = row[0]; }
  }
  return [bestKey, best];
}

function roleName(p) {
  const row = roleRow(p.role);
  if (!row) return D.POSITION_NAMES_HE[p.position];
  const duty = D.DUTY_NAMES_HE[p.duty] || "";
  return duty ? `${row[1]} (${duty})` : row[1];
}

// ---------------------------------------------------------------------------
// אישיות
// ---------------------------------------------------------------------------

/** האישיות נגזרת מהתכונות הנסתרות ומהנחישות — בדיוק כמו במקור. */
function personalityKey(p) {
  const values = Object.assign({}, p.hidden);
  values.determination = p.detail.determination ?? 10;
  for (const [key, , , needs] of D.PERSONALITIES) {
    let ok = true;
    for (const attr in needs) {
      const level = needs[attr];
      const value = values[attr] ?? 10;
      // ערך שלילי בתנאי פירושו "לכל היותר"
      if (level < 0 ? value <= -level : value >= level) continue;
      ok = false; break;
    }
    if (ok) return key;
  }
  return "balanced";
}

function personalityName(p) {
  const key = personalityKey(p);
  const row = D.PERSONALITIES.find(r => r[0] === key);
  return row ? row[1] : "מאוזן";
}

function personalityEffect(p) {
  return D.PERSONALITY_EFFECT[personalityKey(p)] || [1, 1, 1];
}

// ---------------------------------------------------------------------------
// ייצור
// ---------------------------------------------------------------------------

/**
 * מייצר את התכונות המפורטות (1-20) סביב רמה מבוקשת.
 * התפקיד קובע את הפרופיל — זה מה שהופך שני חלוצים באותו דירוג
 * לשני שחקנים שונים לגמרי.
 */
function generateDetail(rng, position, targetOverall, roleKey = "") {
  let row = roleKey ? roleRow(roleKey) : null;
  if (!row) {
    const options = rolesFor(position);
    row = options.length ? rng.choice(options) : null;
  }
  const keyAttrs = new Set(row ? row[4] : []);
  const extra = new Set(row ? row[5] : []);
  const allowed = new Set(attrsFor(position));
  const centre = clamp(targetOverall / 5, 1, 19.5);
  const detail = {};
  for (const attr in D.DETAIL_NAMES_HE) {
    if (!allowed.has(attr)) {
      detail[attr] = Math.round(clamp(rng.gauss(6, 2.5), 1, 14));
      continue;
    }
    let base;
    if (keyAttrs.has(attr)) base = centre + rng.gauss(2.2, 1.3);
    else if (extra.has(attr)) base = centre + rng.gauss(0.8, 1.4);
    else base = centre + rng.gauss(-1.6, 2.0);
    detail[attr] = Math.round(clamp(base, 1, 20));
  }
  // נחישות אינה תלויה ברמה — יש נערים נחושים וכוכבים עצלים
  detail.determination = Math.round(clamp(rng.gauss(11, 3.6), 1, 20));
  return detail;
}

function generateHidden(rng) {
  const out = {};
  for (const [key] of D.HIDDEN_ATTRS) out[key] = Math.round(clamp(rng.gauss(10.5, 3.8), 1, 20));
  return out;
}

/** מזיז את התכונות המפורטות עד שהדירוג הכללי קולע ליעד. */
function fitDetailToOverall(p, target) {
  const allowed = attrsFor(p.position).slice();
  const row = roleRow(p.role);
  if (row) {
    const priority = {};
    for (const a of row[5]) priority[a] = 1;
    for (const a of row[4]) priority[a] = 2;
    allowed.sort((a, b) => (priority[b] || 0) - (priority[a] || 0));
  }
  for (let pass = 0; pass < 14; pass++) {
    recomputeGroups(p);
    const diff = target - overall(p);
    if (Math.abs(diff) < 1) return;
    const steps = Math.max(1, Math.round(Math.abs(diff) / 5 * allowed.length));
    const step = diff > 0 ? 1 : -1;
    const pool = diff > 0 ? allowed : allowed.slice().reverse();
    let moved = 0;
    for (const attr of pool) {
      if (moved >= steps) break;
      const value = p.detail[attr] ?? 10;
      if (value + step >= 1 && value + step <= 20) { p.detail[attr] = value + step; moved += 1; }
    }
    if (!moved) break;
  }
  recomputeGroups(p);
}
