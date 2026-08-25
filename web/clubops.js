// ---------------------------------------------------------------------------
// כלכלת מועדון — פורט מ-football_manager/club_ops.py.
// קהל מייצר הכנסה, ההכנסה מממנת מתקנים וצוות, והם משפיעים בחזרה על המגרש.
// ---------------------------------------------------------------------------

const COMMERCIAL_POWER = 3.1;
const TIER_COMMERCIAL = { 0: 3.0, 1: 2.18, 2: 1.5, 3: 1.0 };

function leagueTier(leagueId) {
  const league = D.LEAGUES.find(l => l.id === leagueId);
  return league ? league.tier : 2;
}

function ticketPrice(club) {
  const base = D.TICKET_BASE[leagueTier(club.leagueId)] ?? 40;
  return Math.round(base * (0.55 + club.reputation / 90));
}

function staffWageBill(club) {
  return Object.values(club.staff || {}).reduce((sum, m) => sum + Math.round(m.wage), 0);
}

/** תפוסה נגזרת מאהדה, מיקום בטבלה, היריבה והכושר. */
function attendanceFor(club, opponent, rng, position = 10, size = 20, form = 0.5) {
  const standing = 1 - (position - 1) / Math.max(1, size - 1);
  let occupancy = 0.24
    + club.fanSupport / 100 * 0.34
    + standing * 0.17
    + opponent.reputation / 100 * 0.14
    + (form - 0.5) * 0.16;
  occupancy *= rng.uniform(0.93, 1.07);
  occupancy = clamp(occupancy, 0.22, 1.0);
  return Math.round(club.capacity * occupancy);
}

/** כרטיסים ועוד 24% מזון, חנות וחניה. */
function matchdayIncome(club, attendance) {
  return Math.round(attendance * ticketPrice(club) * 1.24);
}

function wageBill(club, players) {
  let total = 0;
  for (const pid of club.squad) {
    const player = players[pid];
    if (player && !player.retired) total += Math.round(player.contract.wage);
  }
  return total;
}

/** שידורים, חסויות ומרצ'נדייז — הכנסה קבועה בכל שבוע. */
function commercialIncome(club) {
  const mult = TIER_COMMERCIAL[leagueTier(club.leagueId)] ?? 1.2;
  return Math.round(Math.pow(club.reputation, COMMERCIAL_POWER) * mult);
}

function weeklyFinances(club, players, matchday = 0) {
  const wages = wageBill(club, players);
  const staff = staffWageBill(club);
  const commercial = commercialIncome(club);
  const net = commercial + matchday - wages - staff;
  club.balance = Math.round(club.balance + net);
  return { commercial, matchday, wages, staff, net, balance: Math.round(club.balance) };
}

// ---------------------------------------------------------------------------
// שדרוג מתקנים
// ---------------------------------------------------------------------------

function facilityLevel(club, kind) {
  return club[D.FACILITIES[kind].field];
}

/** כמה מקומות נוספים בהרחבה הבאה, מעוגל ל-500. */
function stadiumExpansion(club) {
  const added = club.capacity * D.FACILITIES.stadium.unit;
  return Math.round(Math.max(1000, Math.min(added, 9000)) / 500) * 500;
}

function upgradeCost(club, kind) {
  const spec = D.FACILITIES[kind];
  if (kind === "stadium") return Math.round(spec.cost * stadiumExpansion(club) / 1000);
  const level = facilityLevel(club, kind);
  return Math.round(spec.cost * (0.55 + Math.pow(level / 100, 1.7) * 2.6));
}

function workInProgress(club, kind) {
  return (club.works || []).find(w => w.kind === kind) || null;
}

/** מחזיר סיבה למה אי אפשר לשדרג, או null אם אפשר. */
function canUpgrade(club, kind) {
  if (workInProgress(club, kind)) return "העבודות כבר בעיצומן.";
  if (kind !== "stadium" && facilityLevel(club, kind) >= 95)
    return "המתקן כבר ברמה הגבוהה ביותר.";
  if (kind === "stadium" && club.capacity >= 75000) return "אין לאן להרחיב יותר.";
  if (club.balance < upgradeCost(club, kind)) return "אין מספיק כסף בקופה.";
  return null;
}

function startUpgrade(club, kind) {
  const blocked = canUpgrade(club, kind);
  if (blocked) return blocked;
  const spec = D.FACILITIES[kind];
  const cost = upgradeCost(club, kind);
  club.balance = Math.round(club.balance - cost);
  const added = kind === "stadium" ? stadiumExpansion(club) : 0;
  club.works.push({ kind, weeksLeft: spec.weeks, cost, added });
  if (kind === "stadium")
    return `אישרת הרחבה של ${fmt(added)} מקומות ב${club.stadiumName}. ${spec.weeks} שבועות עבודה.`;
  return `אישרת שדרוג של ${spec.name}. ${spec.weeks} שבועות עבודה.`;
}

/** מקדם את הבנייה בשבוע ומחזיר הודעות על פרויקטים שהסתיימו. */
function tickWorks(club) {
  const messages = [];
  const remaining = [];
  for (const work of club.works || []) {
    work.weeksLeft -= 1;
    if (work.weeksLeft > 0) { remaining.push(work); continue; }
    const spec = D.FACILITIES[work.kind];
    if (work.kind === "stadium") {
      club.capacity += work.added;
      messages.push(`🏟️ ההרחבה הושלמה — ${club.stadiumName} מכיל עכשיו ${fmt(club.capacity)} מקומות.`);
    } else {
      const before = club[spec.field];
      club[spec.field] = Math.round(clamp(before + spec.unit, 1, 99));
      messages.push(`🏗️ ${spec.name} שודרגו: ${Math.round(before)} → ${club[spec.field]}.`);
    }
  }
  club.works = remaining;
  return messages;
}

// ---------------------------------------------------------------------------
// שוק בעלי התפקיד
// ---------------------------------------------------------------------------

function staffCandidates(rng, club, role, count = 3) {
  const out = [];
  for (let i = 0; i < count; i++) {
    const quality = Math.round(clamp(club.reputation + rng.gauss(4, 16), 12, 95));
    out.push(staffMember(rng, role, quality));
  }
  return out.sort((a, b) => b.quality - a.quality);
}

/** דמי חתימה = שכר של ארבעה שבועות. */
function hireStaffMember(club, role, candidate) {
  const fee = Math.round(candidate.wage) * 4;
  if (club.balance < fee) return "אין מספיק כסף בקופה לדמי החתימה.";
  club.balance = Math.round(club.balance - fee);
  const outgoing = club.staff[role];
  club.staff[role] = Object.assign({}, candidate);
  const name = D.STAFF_ROLES[role].name;
  if (outgoing)
    return `${candidate.name} מחליף את ${outgoing.name} בתפקיד ${name} (איכות ${candidate.quality}).`;
  return `${candidate.name} נכנס לתפקיד ${name} (איכות ${candidate.quality}).`;
}

/** פיצויים = שכר של שמונה שבועות. */
function fireStaffMember(club, role) {
  const member = club.staff[role];
  if (!member) return "המשרה כבר פנויה.";
  const severance = Math.round(member.wage) * 8;
  club.balance = Math.round(club.balance - severance);
  delete club.staff[role];
  return `${member.name} סיים את תפקידו. פיצויים: ₪${fmt(severance)}.`;
}
