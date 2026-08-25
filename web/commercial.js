// ---------------------------------------------------------------------------
// החיים המסחריים — פורט מ-football_manager/commercial.py.
// ההצעות שמגיעות אליך הן פונקציה של מי שאתה: מוניטין, שערים, כריזמה
// והמועדון. אותו אירוע נראה אחרת בגיל 18 ובגיל 27.
// ---------------------------------------------------------------------------

/** 0-100. כמה מותג היה רוצה את הפנים שלך על שלט חוצות. */
function marketability(p, clubReputation = 40) {
  const goals = p.career.goals + p.season.goals * 2;
  let score = p.reputation * 0.62;
  score += p.mediaSkill * 0.20;
  score += Math.min(22, goals * 0.16);
  score += clubReputation * 0.12;
  if (p.age <= 23) score += 5;
  else if (p.age >= 33) score -= 6;
  if (hasTrait(p, "media_darling")) score += 9;
  if (hasTrait(p, "hothead")) score -= 4;
  if (hasTrait(p, "loyal")) score += 2;
  return clamp(score, 0, 100);
}

function openTiers(market) {
  return D.SPONSOR_TIERS.filter(tier => market >= tier[2]);
}

/**
 * בונה הצעת חסות שמתאימה לשחקן הזה עכשיו. null אם אף אחד לא מתעניין.
 * ההצעה איננה סכום חד־פעמי: זה חוזה שנתי לכמה שנים, עם סעיפי בונוס
 * שמשלמים לפי מה שתעשה בפועל.
 */
function sponsorOffer(p, rng, clubReputation = 40, matchWeek = false, honours = 0) {
  const market = marketability(p, clubReputation);
  const tiers = openTiers(market);
  if (!tiers.length) return null;

  const weights = tiers.map((tier, index) =>
    Math.pow(index + 1, 2) * (0.4 + Math.max(0, market - tier[2]) / 30));
  const total = weights.reduce((a, b) => a + b, 0);
  let roll = rng.random() * total;
  let chosen = tiers[tiers.length - 1];
  for (let i = 0; i < tiers.length; i++) {
    roll -= weights[i];
    if (roll <= 0) { chosen = tiers[i]; break; }
  }

  const [tierKey, tierHe, minRep, base, mediaMult, brands] = chosen;
  const kindKey = rng.choice(Object.keys(D.DEAL_KINDS));
  const kind = D.DEAL_KINDS[kindKey];

  const over = Math.max(0, market - minRep) / 40;
  let annual = base * kind.pay * (0.75 + over * 1.9) * rng.uniform(0.88, 1.22);
  annual *= 1 + Math.min(0.45, honours * 0.06);
  annual = Math.round(annual / 1000) * 1000;
  let years = 1;
  if (tierKey === "national") years = rng.randint(1, 2);
  else if (tierKey === "continental" || tierKey === "global") years = rng.randint(2, 4);

  // סעיפי בונוס — כמה שהמותג גדול יותר, כך יש בהם יותר בשר
  const clauseCount = { local: 1, national: 1, continental: 2, global: 3 }[tierKey];
  const pool = D.BONUS_CLAUSES.slice();
  rng.shuffle(pool);
  const clauses = pool.slice(0, clauseCount).map(c => c[0]);

  return {
    brand: rng.choice(brands), tier: tierKey, tierHe,
    kind: kindKey, kindHe: kind.name,
    annual, amount: annual, years,
    days: Math.max(1, Math.round(kind.days * mediaMult)),
    mediaGain: kind.media, clauses,
    // ימי צילום נופלים בשבוע משחק רק לפעמים
    clashes: matchWeek && rng.random() < 0.30,
    market: Math.round(market * 10) / 10,
  };
}

const CLAUSE_BY_KEY = {};
for (const row of D.BONUS_CLAUSES) CLAUSE_BY_KEY[row[0]] = row;

function clauseText(key, annual) {
  const row = CLAUSE_BY_KEY[key];
  if (!row) return "";
  return `${row[1]}: ₪${fmt(Math.round(annual * row[3] / 100) * 100)}`;
}

function dealSummary(offer) {
  const annual = offer.annual ?? offer.amount ?? 0;
  const span = offer.years === 1 ? "לשנה" : `× ${offer.years} שנים`;
  return `${offer.brand} · ${offer.kindHe} · ₪${fmt(annual)} לעונה ${span} · `
         + `${offer.days} ימי צילומים`;
}

/** פירוט מלא של החוזה, כולל מה שכתוב בסעיפים. */
function dealLines(offer) {
  const annual = offer.annual ?? offer.amount ?? 0;
  const lines = [dealSummary(offer), `סך הכל מובטח: ₪${fmt(annual * offer.years)}`];
  for (const key of (offer.clauses || [])) {
    const text = clauseText(key, annual);
    if (text) lines.push("• " + text);
  }
  return lines;
}

// ---------------------------------------------------------------------------
// תיק החסויות
// ---------------------------------------------------------------------------

/** מוסיף חוזה חתום לתיק. מותג שכבר איתך פשוט מתחדש. */
function signDeal(portfolio, offer, year) {
  const annual = offer.annual ?? offer.amount ?? 0;
  const deal = {
    brand: offer.brand, tier: offer.tier, tierHe: offer.tierHe,
    kindHe: offer.kindHe, annual, yearsLeft: offer.years,
    clauses: (offer.clauses || []).slice(), signed: year, earned: 0,
  };
  for (let i = portfolio.length - 1; i >= 0; i--)
    if (portfolio[i].brand === offer.brand) portfolio.splice(i, 1);
  portfolio.push(deal);
  return deal;
}

/**
 * מה שהחסויות משלמות לך כל שבוע. זה ההבדל בין תשלום חד־פעמי לבין
 * הכנסה שממשיכה לזרום כל עוד החוזה בתוקף.
 */
function weeklyRetainer(portfolio, seasonWeeks) {
  if (!portfolio || !portfolio.length) return 0;
  const total = portfolio.reduce((a, d) => a + d.annual, 0);
  return Math.trunc(total / Math.max(1, seasonWeeks));
}

/** תשלומי הסעיפים בסוף עונה, לפי מה שבאמת עשית. */
function seasonBonuses(portfolio, p, trophies, caps) {
  const payouts = [];
  const measures = {
    goals: p.season.goals, assists: p.season.assists,
    trophies, caps,
    rating: (p.season.apps >= 10 && avgRating(p.season) >= 7.0) ? 1 : 0,
  };
  for (const deal of portfolio) {
    for (const key of (deal.clauses || [])) {
      const row = CLAUSE_BY_KEY[key];
      if (!row) continue;
      const units = measures[row[2]] || 0;
      if (units <= 0) continue;
      const amount = Math.round(deal.annual * row[3] * units / 100) * 100;
      if (amount) {
        deal.earned = (deal.earned || 0) + amount;
        payouts.push([`${deal.brand} · ${row[1]}`, amount]);
      }
    }
  }
  return payouts;
}

/** מקדם שנה בכל החוזים ומוציא את מה שנגמר. */
function tickPortfolio(portfolio) {
  const lines = [];
  for (let i = portfolio.length - 1; i >= 0; i--) {
    portfolio[i].yearsLeft -= 1;
    if (portfolio[i].yearsLeft <= 0) {
      lines.push(`📄 החוזה עם ${portfolio[i].brand} הסתיים.`);
      portfolio.splice(i, 1);
    }
  }
  return lines.reverse();
}

/** הצעת חידוש. הסכום החדש משקף את מי שנעשית מאז שחתמת. */
function renewalOffer(deal, p, rng, clubReputation = 40) {
  const market = marketability(p, clubReputation);
  const factor = clamp(0.55 + market / 55, 0.5, 2.6) * rng.uniform(0.9, 1.15);
  const annual = Math.round(deal.annual * factor / 1000) * 1000;
  return {
    brand: deal.brand, tier: deal.tier, tierHe: deal.tierHe, kindHe: deal.kindHe,
    annual, amount: annual, years: rng.randint(2, 4), days: 2, mediaGain: 4,
    clauses: (deal.clauses || []).slice(), clashes: false,
    market: Math.round(market * 10) / 10, renewal: true,
  };
}

function portfolioTotal(portfolio) {
  return portfolio.reduce((a, d) => a + d.annual, 0);
}

/** הצעת עבודה תקשורתית שמתאימה לכריזמה ולמוניטין הנוכחיים. */
function mediaOffer(p, rng) {
  const options = D.MEDIA_JOBS.filter(job => p.mediaSkill >= job[2] && p.reputation >= job[3]);
  if (!options.length) return null;
  const [key, name, , , base] = rng.choice(options);
  const factor = 0.7 + (p.reputation / 100) * 0.9 + (p.mediaSkill / 100) * 0.6;
  return { key, name, amount: Math.round(base * factor * rng.uniform(0.9, 1.2) / 1000) * 1000 };
}

/** סוכן שמזהה שאתה שווה יותר ממה שאתה מקבל, ומביא יעד קונקרטי. */
function agentPitch(p, rng, clubs, currentClub) {
  const currentRep = currentClub ? currentClub.reputation : 20;
  const targets = clubs.filter(c =>
    (!currentClub || c.cid !== currentClub.cid)
    && c.reputation > currentRep + 6
    && c.reputation <= p.reputation + 26);
  if (!targets.length) return null;
  const target = rng.choice(targets);
  const raise = rng.uniform(1.25, 2.1) * (1 + (target.reputation - currentRep) / 130);
  return {
    agent: rng.choice(D.AGENT_NAMES),
    club: target.cid,
    clubName: target.name,
    wage: Math.round(p.contract.wage * raise / 500) * 500,
    fee: Math.round(p.contract.wage * raise * 0.12 / 500) * 500,
  };
}
