// ---------------------------------------------------------------------------
// נכסים והשקעות — תאום JS של wealth.py
//
// עד עכשיו הכסף רק נערם. כאן הוא יכול לעבוד: דירות, חנויות, מסעדה,
// מתחם פאדל, אקדמיה, קרן מדד ואחזקה במועדון.
// ---------------------------------------------------------------------------

const ASSET_BY_KEY = {};
for (const row of D.ASSETS) ASSET_BY_KEY[row[0]] = row;

function holdings(game) {
  if (!Array.isArray(game.flags.assets)) game.flags.assets = [];
  return game.flags.assets;
}

function assetsAvailable(game) {
  const me = game.me;
  return D.ASSETS.map(([key, name, category, price, yieldPct, vol, minRep, desc]) => ({
    key, name, category, price, yield: yieldPct, volatility: vol, desc,
    min_rep: minRep, locked: me.reputation < minRep,
    affordable: game.money >= price,
  }));
}

function buyAsset(game, key) {
  const row = ASSET_BY_KEY[key];
  if (!row) return "אין נכס כזה.";
  const [, name, category, price, , , minRep] = row;
  if (game.me.reputation < minRep)
    return `${name} — לא פתוח לך עדיין. צריך מוניטין ${minRep}.`;
  if (game.money < price)
    return `אין מספיק. ${name} עולה ₪${fmt(price)}, ויש לך ₪${fmt(Math.trunc(game.money))}.`;
  game.spend(price);
  holdings(game).push({ key, name, category, paid: price, value: price,
                        year: game.year, income: 0 });
  return `🏠 קנית: ${name} תמורת ₪${fmt(price)}.`;
}

function sellAsset(game, index) {
  const items = holdings(game);
  if (index < 0 || index >= items.length) return "אין נכס כזה.";
  const item = items.splice(index, 1)[0];
  const value = Math.trunc(item.value);
  game.earn(value);
  const profit = value - Math.trunc(item.paid);
  const verdict = profit > 0 ? `רווח של ₪${fmt(profit)}`
                : profit < 0 ? `הפסד של ₪${fmt(-profit)}` : "בדיוק מה ששילמת";
  return `💼 מכרת את ${item.name} ב-₪${fmt(value)} — ${verdict}.`;
}

function netWorth(game) {
  return Math.trunc(game.money)
    + holdings(game).reduce((a, i) => a + Math.trunc(i.value), 0);
}

function portfolioYield(game) {
  let total = 0;
  for (const item of holdings(game)) {
    const row = ASSET_BY_KEY[item.key];
    if (row) total += item.value * row[4];
  }
  return Math.trunc(total);
}

/** סוף עונה: תשואה, שינוי שווי, ולפעמים אירוע. */
function assetsSeasonTick(game, rng) {
  const items = holdings(game);
  if (!items.length) return [];
  const lines = [];
  let totalIncome = 0;
  for (const item of items) {
    const row = ASSET_BY_KEY[item.key];
    if (!row) continue;
    const [, , category, price, baseYield, vol] = row;
    let realised = baseYield * (1 + rng.gauss(0, vol));
    if (["restaurant", "academy", "agency_stake"].includes(item.key))
      realised *= 0.55 + game.me.reputation / 90;
    const income = Math.trunc(item.value * Math.max(-0.25, realised));
    item.income = (item.income || 0) + income;
    totalIncome += income;
    const drift = category.includes("נדל") ? 0.028 : 0.012;
    item.value = Math.trunc(Math.max(price * 0.25,
      item.value * (1 + drift + rng.gauss(0, vol * 0.35))));
  }
  if (totalIncome > 0) {
    game.earn(totalIncome);
    lines.push(`🏦 הנכסים שלך הכניסו ₪${fmt(totalIncome)} העונה.`);
  } else if (totalIncome < 0) {
    game.spend(-totalIncome);
    lines.push(`🏦 הנכסים שלך עלו לך ₪${fmt(-totalIncome)} העונה.`);
  }
  if (items.length && rng.random() < 0.45) {
    const item = rng.choice(items);
    const pool = D.ASSET_EVENTS.filter(ev => ev[0] === item.category);
    if (pool.length) {
      const [, text, impact] = rng.choice(pool);
      item.value = Math.trunc(Math.max(1, item.value + item.value * impact * 0.28));
      if (impact > 0) game.earn(Math.max(0, Math.trunc(item.value * impact * 0.10)));
      lines.push(`📌 ${item.name}: ${text}`);
    }
  }
  return lines;
}

function wealthSummary(game) {
  const items = holdings(game);
  return {
    cash: Math.trunc(game.money),
    assets: items.reduce((a, i) => a + Math.trunc(i.value), 0),
    net_worth: netWorth(game),
    yearly: portfolioYield(game),
    count: items.length,
    items: items.map(i => ({ ...i })),
  };
}
