// ---------------------------------------------------------------------------
// מה אתה באמת יודע על שחקן אחר — תאום JS של knowledge.py
//
// "אתה מקבל את מה שאתה רואה": במשחק היה אפשר לפתוח כל שחקן בעולם
// ולראות את כל המספרים שלו במדויק. במקור ידע הוא משאב.
// ---------------------------------------------------------------------------

const KNOW_LEVEL_NAMES = {
  0: "שמועות בלבד", 1: "דוח ראשוני", 2: "דוח מלא", 3: "ידיעה מוחלטת",
};

function knowledgeLevel(game, player) {
  if (player.pid === game.meId) return 3;
  const myClub = game.myClub();
  if (myClub && player.clubId === myClub.cid) return 3;
  if (game.flag(`scouted_${player.pid}`)) return 2;
  const scouted = game.flag("scouted");
  if (!player.clubId) return scouted ? 1 : 0;
  const club = game.clubs[player.clubId];
  if (!club) return 0;

  let level = 0;
  if (myClub && club.leagueId === myClub.leagueId) level = 1;
  if (player.reputation >= 62) level = Math.max(level, 1);
  if (player.reputation >= 80) level = Math.max(level, 2);
  if (scouted) level = Math.min(3, level + 1);
  if (myClub && club.reputation >= 70 && myClub.reputation >= 70) level = Math.max(level, 1);
  return level;
}

/** התכונות כפי שאתה רואה אותן — מדויקות, בטווח, או בכלל לא. */
function shownDetail(game, player) {
  const level = knowledgeLevel(game, player);
  const width = { 3: 0, 2: 1, 1: 3, 0: 5 }[level];
  const out = {};
  for (const attr of attrsFor(player.position)) {
    const value = player.detail[attr] ?? 10;
    if (level >= 3) out[attr] = { value, low: value, high: value, exact: true };
    else if (level === 0) out[attr] = { value: null, low: 0, high: 0, exact: false };
    else out[attr] = { value: null, low: Math.max(1, value - width),
                       high: Math.min(20, value + width), exact: false };
  }
  return out;
}

function knowStars(value, scale = 100) {
  return Math.round(clamp(value / scale * 5, 0, 5) * 2) / 2;
}

function starText(count) {
  const full = Math.trunc(count);
  const half = count - full >= 0.5 ? 1 : 0;
  return "★".repeat(full) + (half ? "½" : "") + "☆".repeat(5 - full - half);
}

/** FNV-1a — אותו מספר בפייתון וב-JS, ואותו מספר בכל הרצה. */
function stableHash(text) {
  let value = 2166136261;
  for (const ch of text) {
    value ^= ch.codePointAt(0);
    value = Math.imul(value, 16777619) >>> 0;
  }
  return value;
}

function abilityStars(game, player) {
  const level = knowledgeLevel(game, player);
  let value = overall(player);
  if (level < 3) {
    // ההערכה גסה יותר ככל שאתה יודע פחות — וקבועה לשחקן, לא מהבהבת
    const noise = (stableHash(player.pid) % 11 - 5) * (3 - level) * 0.9;
    value = clamp(value + noise, 1, 99);
  }
  return knowStars(value);
}

/** טווח הפוטנציאל בכוכבים. אף אחד לא באמת יודע — גם לא אתה. */
function potentialStars(game, player) {
  const level = knowledgeLevel(game, player);
  if (player.pid === game.meId) return [knowStars(player.potential), knowStars(player.potential)];
  const spread = { 3: 6, 2: 11, 1: 18, 0: 26 }[level];
  return [knowStars(clamp(player.potential - spread, 1, 99)),
          knowStars(clamp(player.potential + spread * 0.6, 1, 99))];
}

function knowledgeSummary(game, player) {
  const level = knowledgeLevel(game, player);
  const [low, high] = potentialStars(game, player);
  return {
    level, level_he: KNOW_LEVEL_NAMES[level],
    ability: abilityStars(game, player),
    potential_low: low, potential_high: high,
    exact: level >= 3, detail: shownDetail(game, player),
    role: player.role, personality: level >= 2,
  };
}

/** לשלוח את הצוות לבדוק שחקן מסוים. עולה כסף למועדון. */
function scoutPlayer(game, player) {
  const club = game.myClub();
  if (!club) return "אין לך מועדון שישלח צופה.";
  if (game.flag(`scouted_${player.pid}`)) return `כבר יש לך דוח מלא על ${player.name}.`;
  const cost = Math.trunc(18000 + player.reputation * 900);
  if (club.balance < cost) return `הסריקה עולה ₪${fmt(cost)} והקופה לא עומדת בזה.`;
  club.balance -= cost;
  game.setFlag(`scouted_${player.pid}`, true);
  return `🔍 הצוות נסע לראות את ${player.name}. ₪${fmt(cost)} מהקופה — `
       + "ועכשיו יש עליו דוח מלא.";
}
