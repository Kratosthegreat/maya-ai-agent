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

/** בונה הצעת חסות שמתאימה לשחקן הזה עכשיו. null אם אף אחד לא מתעניין. */
function sponsorOffer(p, rng, clubReputation = 40, matchWeek = false) {
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
  const amount = base * kind.pay * (0.75 + over * 1.5) * rng.uniform(0.85, 1.25);
  const years = (tierKey === "continental" || tierKey === "global") ? rng.randint(1, 3) : 1;

  return {
    brand: rng.choice(brands),
    tier: tierKey,
    tierHe,
    kind: kindKey,
    kindHe: kind.name,
    amount: Math.round(amount / 1000) * 1000,
    years,
    days: Math.max(1, Math.round(kind.days * mediaMult)),
    mediaGain: kind.media,
    clashes: matchWeek && rng.random() < 0.35,
    market: Math.round(market * 10) / 10,
  };
}

function dealSummary(offer) {
  const span = offer.years === 1 ? "לשנה" : `ל-${offer.years} שנים`;
  return `${offer.brand} · ${offer.kindHe} · ₪${fmt(offer.amount)} ${span} · ${offer.days} ימי צילומים`;
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
