// ---------------------------------------------------------------------------
// שוק העברות עם משא ומתן אמיתי — תאום JS של transfers.py
//
// עד כאן ההעברה הייתה שורה אחת: מועדון אחד, סכום אחד, כן או לא. מה
// שיש כאן במקום: כמה הצעות במקביל, משא ומתן על כל סעיף, סיכון אמיתי
// (מועדון קם מהשולחן), מינוף שגדל עם מספר המתחרים, ודדליין.
// ---------------------------------------------------------------------------

// תפקיד מובטח בסגל — מה שהמועדון מתחייב לו כשהוא מחתים אותך
const SQUAD_ROLES = [
  ["star", "איש הקבוצה", 1.35],
  ["starter", "שחקן הרכב", 1.12],
  ["rotation", "רוטציה", 0.92],
  ["prospect", "לעתיד", 0.78],
];
const ROLE_NAMES = Object.fromEntries(SQUAD_ROLES.map(r => [r[0], r[1]]));
const ROLE_VALUE = Object.fromEntries(SQUAD_ROLES.map(r => [r[0], r[2]]));

const TERMS = [
  ["wage", "שכר שבועי"], ["years", "אורך חוזה"], ["bonus", "מענק חתימה"],
  ["clause", "סעיף שחרור"], ["role", "תפקיד בסגל"], ["image", "אחוזי דימוי"],
];
const TERM_NAMES = Object.fromEntries(TERMS);

const WINDOW_WEEKS = 4;

/** שווי העברה משוער. הבסיס לכל מספר אחר כאן. */
function marketValue(p) {
  let base = wageForOverall(overall(p)) * 46;
  // גיל הוא המכפיל הגדול: בן 22 עם אותו דירוג שווה כפליים מבן 31
  if (p.age <= 20) base *= 1.95;
  else if (p.age <= 23) base *= 1.70;
  else if (p.age <= 26) base *= 1.35;
  else if (p.age <= 29) base *= 1.0;
  else if (p.age <= 32) base *= 0.55;
  else base *= 0.25;
  base *= 0.72 + p.reputation / 145;
  base *= 1 + Math.max(0, p.potential - overall(p)) * 0.020;
  if (p.contract.yearsLeft <= 1) base *= 0.45;     // שנה לסיום — כמעט חינם
  else if (p.contract.yearsLeft === 2) base *= 0.80;
  return Math.round(base / 1000) * 1000;
}

/**
 * 0-1: כמה כוח יש לך סביב השולחן. מינוף הוא לא "כמה אתה טוב" אלא
 * "כמה אפשרויות יש לך".
 */
function leverage(game) {
  const me = game.me;
  const offers = openOffers(game).filter(o => o.state !== "withdrawn");
  let score = 0.20;
  score += Math.min(0.34, Math.max(0, offers.length - 1) * 0.17);
  score += Math.min(0.20, me.reputation / 500);
  if (me.contract.yearsLeft <= 1) score += 0.18;
  else if (me.contract.yearsLeft >= 4) score -= 0.08;
  if (me.season.apps >= 6)
    score += clamp((avgRating(me.season) - 6.7) * 0.16, -0.10, 0.16);
  if (me.age <= 23) score += 0.06;
  else if (me.age >= 33) score -= 0.14;
  return clamp(score, 0.03, 0.95);
}

/** חבילה שלמה ממועדון אחד, לא רק מספר. */
function buildOffer(game, club, rng, eagerness = null) {
  const me = game.me;
  if (eagerness === null) eagerness = rng.uniform(0.35, 0.95);

  const par = wageForOverall(overall(me)) * (0.88 + me.reputation / 200);
  const ceiling = Math.max(par * 1.05, club.wageBudget * 0.34);
  let wage = Math.floor(Math.min(ceiling, par * (0.80 + eagerness * 0.55)));
  wage = Math.max(wage, Math.floor(me.contract.wage * 1.08));

  const value = marketValue(me);
  const role = roleFor(club, me, eagerness);
  const years = me.age >= 31 ? 3 : (eagerness > 0.7 && me.age <= 24 ? 5 : 4);

  return {
    cid: club.cid, wage, years,
    bonus: Math.floor(value * rng.uniform(0.03, 0.09) * (0.5 + eagerness)),
    clause: 0, role, image: 0, fee: value,
    eagerness: Math.round(eagerness * 1000) / 1000,
    ceiling: Math.floor(ceiling),
    patience: 2 + Math.floor(eagerness * 3),
    asks: 0, state: "open", weeks: WINDOW_WEEKS, log: [],
  };
}

/** איזה תפקיד מועדון מוכן להבטיח — לפי הפער בינך לבין הסגל שלו. */
function roleFor(club, me, eagerness) {
  const gap = overall(me) - club.reputation;
  if (gap >= 10 && eagerness > 0.55) return "star";
  if (gap >= 0) return "starter";
  if (gap >= -9) return "rotation";
  return "prospect";
}

/** ערך שנתי מקורב של חבילה — כדי שאפשר יהיה להשוות הצעות. */
function offerWorth(offer) {
  let annual = offer.wage * 52;
  annual += Math.floor(offer.bonus / Math.max(1, offer.years));
  annual = Math.floor(annual * (ROLE_VALUE[offer.role] || 1));
  annual += Math.floor(annual * offer.image / 100);
  return annual;
}

function openOffers(game) {
  const data = game.flags.offers;
  return Array.isArray(data) ? data : [];
}

function setOffers(game, offers) { game.flags.offers = offers; }

/** מה שעדיין על השולחן, מהשווה ביותר לפחות. */
function liveOffers(game) {
  return openOffers(game)
    .filter(o => ["open", "improved", "final"].includes(o.state))
    .sort((a, b) => offerWorth(b) - offerWorth(a));
}

function offerFor(game, cid) {
  return openOffers(game).find(o => o.cid === cid) || null;
}

/** שבוע עובר: הצעות מתקרבות לפקיעה, ומתחרים מגיבים זה לזה. */
function tickOffers(game) {
  const lines = [];
  const offers = openOffers(game);
  if (!offers.length) return lines;
  const live = offers.filter(o => ["open", "improved", "final"].includes(o.state));
  for (const offer of live) {
    offer.weeks -= 1;
    const club = game.clubs[offer.cid];
    const name = club ? club.name : "מועדון";
    if (offer.weeks <= 0) {
      offer.state = "withdrawn";
      lines.push(`⌛ ${name} משכו את ההצעה — הדדליין עבר.`);
    } else if (offer.weeks === 1) {
      lines.push(`⏳ ${name} רוצים תשובה עד סוף השבוע.`);
    }
  }

  // מרוץ: כשיש כמה מתעניינים, מישהו מרים את הרף מעצמו
  const still = offers.filter(o => ["open", "improved", "final"].includes(o.state));
  if (still.length >= 2 && game.rng.random() < 0.42) {
    const best = still.reduce((a, b) => offerWorth(b) > offerWorth(a) ? b : a);
    const rivals = still.filter(o => o !== best);
    const rival = rivals[game.rng.randint(0, rivals.length - 1)];
    if (rival && rival.wage < rival.ceiling * 0.97) {
      const bump = Math.max(1, Math.floor((best.wage - rival.wage) * 0.6));
      rival.wage = Math.floor(Math.min(rival.ceiling,
        rival.wage + Math.max(bump, Math.floor(rival.wage / 20))));
      rival.state = "improved";
      const club = game.clubs[rival.cid];
      lines.push(`📈 ${club ? club.name : "מועדון"} שמעו על ההצעה השנייה `
               + `והעלו ל-₪${fmt(rival.wage)} לשבוע.`);
    }
  }
  setOffers(game, offers);
  return lines;
}

function clearOffers(game) { delete game.flags.offers; }

/** מה אפשר לבקש מההצעה הזאת עכשיו, ומה זה יעלה. */
function askOptions(offer) {
  const out = [];
  for (const [key, name] of TERMS) {
    if (key === "role" && offer.role === "star") continue;
    if (key === "years" && offer.years >= 6) continue;
    if (key === "image" && offer.image >= 25) continue;
    if (key === "clause" && offer.clause && offer.clause <= offer.fee) continue;
    out.push({ term: key, name, ask: askText(offer, key) });
  }
  return out;
}

function askText(offer, term) {
  if (term === "wage")
    return `₪${fmt(Math.floor(offer.wage * 1.22))} במקום ₪${fmt(offer.wage)}`;
  if (term === "years") return `${offer.years + 1} שנים במקום ${offer.years}`;
  if (term === "bonus")
    return `מענק ₪${fmt(Math.floor(Math.max(offer.bonus * 1.6, 120000)))}`;
  if (term === "clause") return `סעיף שחרור ₪${fmt(Math.floor(offer.fee * 1.6))}`;
  if (term === "role") return `התחייבות ל${ROLE_NAMES[betterRole(offer.role)]}`;
  if (term === "image") return `${Math.min(25, offer.image + 10)}% מזכויות הדימוי`;
  return "";
}

function betterRole(role) {
  const order = SQUAD_ROLES.map(r => r[0]);
  return order[Math.max(0, order.indexOf(role) - 1)];
}

/**
 * מבקש שיפור בסעיף אחד. זו ההחלטה האמיתית של השוק: כל בקשה שורפת
 * סבלנות, ומועדון שנגמרה לו הסבלנות קם מהשולחן.
 */
function negotiate(game, cid, term, rng) {
  const offer = offerFor(game, cid);
  if (!offer || !["open", "improved", "final"].includes(offer.state))
    return { ok: false, text: "ההצעה כבר לא על השולחן.", gone: true };

  const club = game.clubs[cid];
  const name = club ? club.name : "המועדון";
  offer.asks += 1;
  const lev = leverage(game);

  let chance = 0.24 + offer.eagerness * 0.42 + lev * 0.38;
  chance -= (offer.asks - 1) * 0.19;
  if (term === "wage" && offer.wage >= offer.ceiling * 0.95) chance -= 0.42;
  if (term === "clause" || term === "image") chance -= 0.10;
  chance = clamp(chance, 0.04, 0.93);

  const roll = rng.random();
  if (roll < chance) {
    const text = applyAsk(offer, term, true);
    offer.state = "improved";
    offer.log.push(`✅ ${text}`);
    return { ok: true, text: `${name} הסכימו: ${text}`, gone: false };
  }

  if (offer.asks > offer.patience && rng.random() < 0.55) {
    offer.state = "withdrawn";
    offer.log.push("❌ ירדו מהעסקה");
    return { ok: false, gone: true,
             text: `${name} סגרו את התיק. "ניסינו, נתראה בקיץ הבא."` };
  }

  if (roll < chance + 0.28) {
    const text = applyAsk(offer, term, false);
    offer.state = "final";
    offer.log.push(`🤝 ${text}`);
    return { ok: true, gone: false,
             text: `${name} לא הלכו על כל הדרך, אבל: ${text}` };
  }

  offer.log.push(`🚫 סירבו על ${TERM_NAMES[term] || term}`);
  return { ok: false, gone: false,
           text: `${name} סירבו. "זה מה שיש, וזה לא ייפתח שוב."` };
}

/** מזיז את הסעיף בפועל. full=false היא פשרה — כחצי ממה שביקשת. */
function applyAsk(offer, term, full) {
  const share = full ? 1 : 0.5;
  if (term === "wage") {
    offer.wage = Math.floor(Math.min(offer.ceiling, offer.wage * (1 + 0.22 * share)));
    return `₪${fmt(offer.wage)} לשבוע`;
  }
  if (term === "years") {
    if (full) { offer.years += 1; return `${offer.years} שנים`; }
    offer.bonus = Math.floor(offer.bonus * 1.15);
    return `אותן ${offer.years} שנים, אבל מענק ₪${fmt(offer.bonus)}`;
  }
  if (term === "bonus") {
    offer.bonus = Math.floor(Math.max(offer.bonus * (1 + 0.6 * share), 120000 * share));
    return `מענק חתימה ₪${fmt(offer.bonus)}`;
  }
  if (term === "clause") {
    offer.clause = Math.floor(offer.fee * (full ? 1.6 : 2.4));
    return `סעיף שחרור ₪${fmt(offer.clause)}`;
  }
  if (term === "role") {
    if (full) {
      offer.role = betterRole(offer.role);
      return `התחייבות ל${ROLE_NAMES[offer.role]}`;
    }
    offer.wage = Math.floor(Math.min(offer.ceiling, offer.wage * 1.08));
    return `בלי התחייבות בכתב, אבל ₪${fmt(offer.wage)} לשבוע`;
  }
  if (term === "image") {
    offer.image = Math.min(25, offer.image + (full ? 10 : 5));
    return `${offer.image}% מזכויות הדימוי`;
  }
  return "";
}

/** דגל, מדינה וליגה — הזהות של המועדון במבט אחד. */
function offerClubTag(game, cid) {
  const club = game.clubs[cid];
  return clubTag(cid, club ? club.leagueId : "");
}

/** החבילה בשורות, כדי שאפשר יהיה להשוות בעין. */
function offerLines(game, offer) {
  const out = [offerClubTag(game, offer.cid),
               `₪${fmt(offer.wage)} לשבוע · ${offer.years} שנים`];
  if (offer.bonus) out.push(`מענק חתימה ₪${fmt(offer.bonus)}`);
  out.push(`תפקיד מובטח: ${ROLE_NAMES[offer.role] || offer.role}`);
  if (offer.clause) out.push(`סעיף שחרור ₪${fmt(offer.clause)}`);
  if (offer.image) out.push(`${offer.image}% זכויות דימוי`);
  const mine = game.myClub();
  out.push(mine ? `דמי העברה ₪${fmt(offer.fee)} ל${mine.name}`
                : `דמי העברה ₪${fmt(offer.fee)}`);
  return out;
}

/** כמה הם רוצים אותך, בלי לחשוף את המספר. */
function interestWord(offer) {
  if (offer.eagerness > 0.82) return "רוצים אותך מאוד";
  if (offer.eagerness > 0.62) return "מעוניינים ברצינות";
  if (offer.eagerness > 0.42) return "בודקים אפשרות";
  return "שומרים אופציה";
}
