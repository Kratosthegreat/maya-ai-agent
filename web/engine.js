// ---------------------------------------------------------------------------
// מנוע המשחק — פורט מ-football_manager (פייתון). ללא תלות ב-DOM.
// ---------------------------------------------------------------------------

const SEASON_WEEKS = 43;
const CUP_WEEKS = { 6: "שלב 32 האחרונות", 13: "שמינית הגמר", 21: "רבע הגמר",
                    29: "חצי הגמר", 37: "גמר הגביע" };
const SQUAD_MIN = 16;

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

// -- מחולל מספרים אקראיים עם זרע (כדי ששמירה וטעינה יחזירו בדיוק אותו עולם) --
class Rng {
  constructor(seed) { this.s = (seed >>> 0) || 1; this.spare = null; }
  random() {
    this.s = (this.s + 0x6D2B79F5) >>> 0;
    let t = this.s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  uniform(a, b) { return a + (b - a) * this.random(); }
  randint(a, b) { return a + Math.floor(this.random() * (b - a + 1)); }
  gauss(mu, sigma) {
    if (this.spare !== null) { const v = this.spare; this.spare = null; return mu + sigma * v; }
    let u = 0, v = 0, s = 0;
    do { u = this.random() * 2 - 1; v = this.random() * 2 - 1; s = u * u + v * v; }
    while (s >= 1 || s === 0);
    const mul = Math.sqrt(-2 * Math.log(s) / s);
    this.spare = v * mul;
    return mu + sigma * u * mul;
  }
  choice(arr) { return arr[Math.floor(this.random() * arr.length)]; }
  shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(this.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }
  weighted(pairs) {                       // [[value, weight], ...]
    const total = pairs.reduce((a, p) => a + p[1], 0);
    let roll = this.random() * total, upto = 0;
    for (const [value, weight] of pairs) { upto += weight; if (roll <= upto) return value; }
    return pairs[pairs.length - 1][0];
  }
  state() { return [this.s, this.spare]; }
  static fromState(st) { const r = new Rng(1); r.s = st[0] >>> 0; r.spare = st[1]; return r; }
}

// ---------------------------------------------------------------------------
// סטטיסטיקה
// ---------------------------------------------------------------------------

function newStats() {
  return { apps: 0, goals: 0, assists: 0, cleanSheets: 0, yellow: 0, red: 0,
           minutes: 0, ratingSum: 0, motm: 0, trophies: 0 };
}
function avgRating(s) { return s.apps ? Math.round((s.ratingSum / s.apps) * 100) / 100 : 0; }
function mergeStats(target, other) {
  for (const k of ["apps", "goals", "assists", "cleanSheets", "yellow", "red",
                   "minutes", "ratingSum", "motm"]) target[k] += other[k];
}

// ---------------------------------------------------------------------------
// שחקן
// ---------------------------------------------------------------------------

function overall(p) {
  const w = D.POSITION_WEIGHTS[p.position];
  let total = 0;
  for (const attr of D.ATTRIBUTES) total += (p.attributes[attr] ?? 50) * w[attr];
  return Math.round(total);
}

function effective(p) {
  let base = overall(p);
  base += (p.form - 50) * 0.12;
  base += (p.morale - 50) * 0.05;
  base *= 0.85 + 0.15 * (p.fitness / 100);
  return clamp(base, 20, 99);
}

function playerValue(p) {
  const ovr = overall(p);
  const base = Math.pow(Math.max(0, ovr - 40), 3) * 55;
  let ageMod;
  if (p.age <= 20) ageMod = 1.35;
  else if (p.age <= 23) ageMod = 1.25;
  else if (p.age <= 27) ageMod = 1.0;
  else if (p.age <= 30) ageMod = 0.7;
  else if (p.age <= 33) ageMod = 0.4;
  else ageMod = 0.18;
  const potMod = 1 + Math.max(0, p.potential - ovr) * 0.02;
  const repMod = 0.8 + p.reputation / 250;
  return Math.round(base * ageMod * potMod * repMod);
}

function wageForOverall(ovr) {
  return Math.round(clamp(8000 * Math.pow(Math.max(20, ovr) / 50, 6.85), 700, 1200000));
}

function isAvailable(p) { return p.injuryWeeks <= 0 && !p.retired; }
function positionHe(p) { return D.POSITION_NAMES_HE[p.position]; }
function hasTrait(p, t) { return p.traits.includes(t); }

function generateAttributes(rng, position, target) {
  const w = D.POSITION_WEIGHTS[position];
  const attrs = {};
  for (const attr of D.ATTRIBUTES) {
    const spread = rng.gauss(0, 7);
    attrs[attr] = Math.round(clamp(target + (w[attr] - 0.15) * 45 + spread, 15, 96));
  }
  const heaviest = D.ATTRIBUTES.reduce((a, b) => (w[a] >= w[b] ? a : b));
  for (let i = 0; i < 40; i++) {
    let current = 0;
    for (const attr of D.ATTRIBUTES) current += attrs[attr] * w[attr];
    const diff = target - current;
    if (Math.abs(diff) < 0.6) break;
    attrs[heaviest] = Math.round(clamp(attrs[heaviest] + (diff > 0 ? 1 : -1), 15, 96));
  }
  return attrs;
}

let PID_COUNTER = 0;
function generatePlayer(rng, club, position, opts = {}) {
  const usedNames = opts.usedNames || null;
  const age = opts.age ?? rng.randint(17, 35);
  const rep = club ? club.reputation : 40;
  let quality = opts.quality;
  if (quality === undefined) quality = Math.round(clamp(rng.gauss(rep * 0.70 + 20, 6), 28, 92));
  if (age < 21) quality = Math.round(quality - (21 - age) * 2.5);
  const potential = Math.round(clamp(
    quality + Math.max(0, 26 - age) * rng.uniform(0.4, 1.6) + rng.gauss(0, 3), quality, 95));

  let name = null;
  for (let i = 0; i < 60 && name === null; i++) {
    const candidate = `${rng.choice(D.FIRST_NAMES)} ${rng.choice(D.LAST_NAMES)}`;
    if (!usedNames || !usedNames.has(candidate)) { name = candidate; if (usedNames) usedNames.add(candidate); }
  }
  if (name === null) name = `${rng.choice(D.FIRST_NAMES)} ${rng.choice(D.LAST_NAMES)} ${rng.randint(2, 99)}`;

  const p = {
    pid: "p" + (++PID_COUNTER),
    name, age, position,
    nationality: rng.weighted(D.NATIONALITIES),
    attributes: generateAttributes(rng, position, quality),
    growth: {},
    potential,
    clubId: club ? club.cid : null,
    contract: { wage: 0, yearsLeft: rng.randint(1, 4) },
    form: rng.uniform(40, 60),
    morale: rng.uniform(45, 75),
    fitness: 100,
    injuryWeeks: 0,
    injuryName: "",
    reputation: clamp(quality - 25 + rng.gauss(0, 6), 1, 95),
    traits: [],
    isHuman: false,
    coaching: clamp(rng.gauss(10, 6), 0, 40),
    mediaSkill: clamp(rng.gauss(10, 6), 0, 40),
    business: clamp(rng.gauss(8, 5), 0, 40),
    badges: 0,
    season: newStats(),
    career: newStats(),
    retired: false,
  };
  p.contract.wage = wageForOverall(overall(p));
  if (rng.random() < 0.35) p.traits.push(rng.choice(Object.keys(D.TRAITS)));
  return p;
}

// מספרי חולצה — לכל עמדה יש את המספרים המסורתיים שלה
const NUMBER_PREF = {
  GK: [1, 12, 23], CB: [4, 5, 2, 3, 6], LB: [3, 15], RB: [2, 14],
  DM: [6, 16, 4], CM: [8, 18, 20], AM: [10, 7, 21],
  LW: [11, 17], RW: [7, 17, 22], ST: [9, 19, 29],
};

/** נותן לשחקן מספר חולצה פנוי במועדון, בעדיפות למספר המסורתי של העמדה. */
function assignNumber(club, players, player) {
  const taken = new Set(club.squad
    .map(pid => players[pid])
    .filter(p => p && p !== player && p.number)
    .map(p => p.number));
  for (const n of (NUMBER_PREF[player.position] || [])) {
    if (!taken.has(n)) { player.number = n; return n; }
  }
  for (let n = 2; n <= 45; n++) {
    if (!taken.has(n)) { player.number = n; return n; }
  }
  player.number = 0;
  return 0;
}

function generateWorld(seed) {
  const rng = new Rng(seed);
  const clubs = {}, players = {}, usedNames = new Set();
  for (const [cid, name, nickname, leagueId, rep, budget] of D.CLUBS) {
    const club = {
      cid, name, nickname, leagueId, reputation: rep, budget,
      wageBudget: Math.round(budget * 1000000 / 10),
      trainingFacilities: Math.round(clamp(rep + rng.gauss(0, 8), 15, 99)),
      youthAcademy: Math.round(clamp(rep + rng.gauss(0, 12), 15, 99)),
      managerName: rng.choice(D.MANAGER_NAMES),
      managerTrust: 50,
      boardConfidence: 60,
      fanSupport: clamp(rep + rng.gauss(0, 10), 20, 99),
      formation: rng.choice(Object.keys(D.FORMATIONS)),
      squad: [],
      seasonExpectation: "אמצע טבלה",
      trophies: [],
    };
    for (const position of D.SQUAD_TEMPLATE) {
      const p = generatePlayer(rng, club, position, { usedNames });
      players[p.pid] = p;
      club.squad.push(p.pid);
      assignNumber(club, players, p);
    }
    clubs[cid] = club;
  }
  return { clubs, players };
}

// ---------------------------------------------------------------------------
// מנוע המשחקים
// ---------------------------------------------------------------------------

const FIT_GROUPS = [["CB"], ["LB", "RB"], ["DM", "CM"], ["CM", "AM"],
                    ["LW", "RW", "AM"], ["ST", "LW", "RW"]];

function positionFit(playerPos, slot) {
  if (playerPos === slot) return 1.0;
  if ((playerPos === "GK") !== (slot === "GK")) return 0.35;
  for (const group of FIT_GROUPS) {
    if (group.includes(playerPos) && group.includes(slot)) return 0.90;
  }
  return 0.72;
}

function pickLineup(club, players, formation, forced) {
  formation = formation || club.formation;
  const slots = D.FORMATIONS[formation] || D.FORMATIONS["4-3-3"];
  const available = club.squad.map(pid => players[pid]).filter(p => p && isAvailable(p));
  const lineup = new Array(slots.length).fill(null);
  const used = new Set();
  const claim = (idx, p) => { lineup[idx] = p.pid; used.add(p.pid); };

  // מי שנכפה להרכב תופס ראשון את המשבצת הכי מתאימה לו
  for (const pid of (forced || [])) {
    const p = players[pid];
    if (!p || used.has(pid) || !available.includes(p)) continue;
    let bestIdx = -1, bestFit = 0;
    slots.forEach((slot, idx) => {
      if (lineup[idx]) return;
      const fit = positionFit(p.position, slot);
      if (fit > bestFit) { bestFit = fit; bestIdx = idx; }
    });
    if (bestIdx >= 0) claim(bestIdx, p);
  }

  // מעבר ראשון: רק שחקנים בעמדתם הטבעית. מעבר שני: מי שנשאר.
  for (const minFit of [0.9, 0]) {
    for (let idx = 0; idx < slots.length; idx++) {
      if (lineup[idx]) continue;
      const slot = slots[idx];
      const candidates = available.filter(p =>
        !used.has(p.pid) && positionFit(p.position, slot) >= minFit);
      if (!candidates.length) continue;
      claim(idx, candidates.reduce((a, b) =>
        effective(a) * positionFit(a.position, slot) >=
        effective(b) * positionFit(b.position, slot) ? a : b));
    }
  }
  return lineup.filter(Boolean);
}

function teamStrength(lineup, players, formation) {
  const slots = D.FORMATIONS[formation] || D.FORMATIONS["4-3-3"];
  const sums = { def: 0, mid: 0, att: 0 };
  const shares = { def: 0, mid: 0, att: 0 };
  lineup.forEach((pid, idx) => {
    const p = players[pid];
    if (!p) return;
    const slot = idx < slots.length ? slots[idx] : p.position;
    const fit = positionFit(p.position, slot);
    const power = effective(p) * (0.62 + 0.38 * fit);
    const share = D.POSITION_ROLE_SHARE[slot];
    for (const line of ["def", "mid", "att"]) {
      sums[line] += power * share[line];
      shares[line] += share[line];
    }
  });
  const baselines = { def: 5.05, mid: 3.10, att: 2.85 };
  const out = {};
  for (const line of ["def", "mid", "att"]) {
    const average = shares[line] > 0.01 ? sums[line] / shares[line] : 40;
    out[line] = average * Math.pow(Math.max(0.4, shares[line]) / baselines[line], 0.4);
  }
  return out;
}

function poisson(rng, lam) {
  lam = Math.max(0.02, lam);
  const limit = Math.exp(-lam);
  let k = 0, prod = rng.random();
  while (prod > limit && k < 12) { k++; prod *= rng.random(); }
  return k;
}

function simulateMatch(home, away, players, rng, opts = {}) {
  const homeTac = opts.homeTactics || {};
  const awayTac = opts.awayTactics || {};
  const competition = opts.competition || "ליגה";
  const neutral = !!opts.neutral;

  const homeForm = homeTac.formation || home.formation;
  const awayForm = awayTac.formation || away.formation;
  const homeLineup = pickLineup(home, players, homeForm, homeTac.forced);
  const awayLineup = pickLineup(away, players, awayForm, awayTac.forced);

  const hs = teamStrength(homeLineup, players, homeForm);
  const as = teamStrength(awayLineup, players, awayForm);

  const hMent = D.MENTALITIES[homeTac.mentality || "balanced"];
  const aMent = D.MENTALITIES[awayTac.mentality || "balanced"];
  const hPress = D.PRESSING[homeTac.pressing || "medium"];
  const aPress = D.PRESSING[awayTac.pressing || "medium"];

  let ha = hs.att * hMent[1] * (1 + hPress[1]);
  let hd = hs.def * hMent[2] * (1 + hPress[2]);
  let hm = hs.mid;
  let aa = as.att * aMent[1] * (1 + aPress[1]);
  let ad = as.def * aMent[2] * (1 + aPress[2]);
  const am = as.mid;

  if (!neutral) {
    ha *= 1 + home.fanSupport / 640;
    hd *= 1.02;
    hm *= 1.03;
  }

  const totalMid = hm + am;
  const hControl = totalMid ? hm / totalMid : 0.5;
  const aControl = 1 - hControl;

  const expected = (attack, defence, control, talk) => {
    const edge = (attack - defence) / 11;
    let base = 1.26 * Math.exp(edge * 0.34);
    base *= 0.55 + 0.9 * control;
    base *= 0.9 + talk * 0.2;
    return clamp(base, 0.12, 4.6);
  };

  const homeGoals = poisson(rng, expected(ha, ad, hControl, homeTac.talkBoost || 0));
  const awayGoals = poisson(rng, expected(aa, hd, aControl, awayTac.talkBoost || 0));

  const result = {
    homeId: home.cid, awayId: away.cid, homeGoals, awayGoals,
    events: [], ratings: {}, motm: null,
    homeLineup, awayLineup, commentary: [], competition,
  };

  const total = homeGoals + awayGoals;
  const minutes = [];
  while (minutes.length < total) {
    const m = rng.randint(1, 93);
    if (!minutes.includes(m)) minutes.push(m);
  }
  minutes.sort((a, b) => a - b);

  const queue = [];
  for (let i = 0; i < homeGoals; i++) queue.push(home.cid);
  for (let i = 0; i < awayGoals; i++) queue.push(away.cid);
  rng.shuffle(queue);

  queue.forEach((clubId, idx) => {
    const minute = minutes[idx] ?? rng.randint(1, 93);
    const lineup = clubId === home.cid ? homeLineup : awayLineup;
    const scorer = pickScorer(lineup, players, rng);
    if (!scorer) return;
    players[scorer].season.goals += 1;
    result.events.push({ minute, kind: "goal", clubId, playerId: scorer,
                         text: `${minute}' ${players[scorer].name}` });
    const assister = pickAssister(lineup, players, rng, scorer);
    if (assister) {
      players[assister].season.assists += 1;
      result.events.push({ minute, kind: "assist", clubId, playerId: assister,
                           text: `בישול: ${players[assister].name}` });
    }
  });

  applyDiscipline(result, homeLineup, home.cid, players, rng, hPress[3]);
  applyDiscipline(result, awayLineup, away.cid, players, rng, aPress[3]);
  applyInjuries(result, homeLineup, home.cid, players, rng);
  applyInjuries(result, awayLineup, away.cid, players, rng);
  ratePlayers(result, homeLineup, home.cid, players, rng);
  ratePlayers(result, awayLineup, away.cid, players, rng);

  const rated = Object.keys(result.ratings);
  if (rated.length) {
    result.motm = rated.reduce((a, b) => (result.ratings[a] >= result.ratings[b] ? a : b));
    players[result.motm].season.motm += 1;
  }
  if (awayGoals === 0 && homeLineup.length) players[homeLineup[0]].season.cleanSheets += 1;
  if (homeGoals === 0 && awayLineup.length) players[awayLineup[0]].season.cleanSheets += 1;

  result.commentary = buildCommentary(result, home, away, players);
  return result;
}

function resultFor(result, clubId) {
  if (result.homeGoals === result.awayGoals) return "D";
  if (clubId === result.homeId) return result.homeGoals > result.awayGoals ? "W" : "L";
  return result.awayGoals > result.homeGoals ? "W" : "L";
}
function goalsFor(result, clubId) { return clubId === result.homeId ? result.homeGoals : result.awayGoals; }
function goalsAgainst(result, clubId) { return clubId === result.homeId ? result.awayGoals : result.homeGoals; }

function pickScorer(lineup, players, rng) {
  const weights = [];
  for (const pid of lineup) {
    const p = players[pid];
    if (!p) continue;
    const share = D.POSITION_ROLE_SHARE[p.position];
    let w = share.att * 3.0 + share.mid * 0.7 + share.def * 0.12;
    w *= Math.pow((p.attributes.shooting ?? 40) / 55, 1.5);
    w *= 0.7 + p.form / 140;
    weights.push([pid, Math.max(0.001, w)]);
  }
  return weights.length ? rng.weighted(weights) : null;
}

function pickAssister(lineup, players, rng, scorer) {
  if (rng.random() < 0.26) return null;
  const weights = [];
  for (const pid of lineup) {
    if (pid === scorer) continue;
    const p = players[pid];
    if (!p) continue;
    const share = D.POSITION_ROLE_SHARE[p.position];
    let w = share.att * 1.6 + share.mid * 1.8 + share.def * 0.2;
    w *= Math.pow((p.attributes.passing ?? 40) / 55, 1.4);
    weights.push([pid, Math.max(0.001, w)]);
  }
  return weights.length ? rng.weighted(weights) : null;
}

function applyDiscipline(result, lineup, clubId, players, rng, pressFactor) {
  for (const pid of lineup) {
    const p = players[pid];
    if (!p) continue;
    let chance = 0.055 * pressFactor;
    if (hasTrait(p, "hothead")) chance *= 2.4;
    chance *= 1 + D.POSITION_ROLE_SHARE[p.position].def * 0.6;
    if (rng.random() < chance) {
      const minute = rng.randint(5, 92);
      if (rng.random() < 0.09) {
        p.season.red += 1;
        result.events.push({ minute, kind: "red", clubId, playerId: pid, text: `${minute}' ${p.name}` });
      } else {
        p.season.yellow += 1;
        result.events.push({ minute, kind: "yellow", clubId, playerId: pid, text: `${minute}' ${p.name}` });
      }
    }
  }
}

function applyInjuries(result, lineup, clubId, players, rng) {
  for (const pid of lineup) {
    const p = players[pid];
    if (!p) continue;
    let chance = 0.016;
    chance *= 1 + Math.max(0, 70 - p.fitness) / 90;
    chance *= 1 + Math.max(0, p.age - 30) * 0.09;
    if (hasTrait(p, "glass")) chance *= 2.2;
    if (rng.random() < chance) {
      const [name, low, high] = rng.choice(D.INJURY_TYPES);
      const weeks = rng.randint(low, high);
      p.injuryWeeks = weeks;
      p.injuryName = name;
      p.fitness = Math.min(p.fitness, 55);
      result.events.push({ minute: rng.randint(3, 90), kind: "injury", clubId, playerId: pid,
                           text: `${p.name} — ${name} (${weeks} שבועות)` });
    }
  }
}

function ratePlayers(result, lineup, clubId, players, rng) {
  const conceded = goalsAgainst(result, clubId);
  const outcome = resultFor(result, clubId);
  const teamMod = { W: 0.45, D: 0, L: -0.35 }[outcome];
  const goalsBy = {}, assistsBy = {}, cards = {};
  for (const ev of result.events) {
    if (ev.clubId !== clubId) continue;
    if (ev.kind === "goal") goalsBy[ev.playerId] = (goalsBy[ev.playerId] || 0) + 1;
    else if (ev.kind === "assist") assistsBy[ev.playerId] = (assistsBy[ev.playerId] || 0) + 1;
    else if (ev.kind === "yellow" || ev.kind === "red")
      cards[ev.playerId] = (cards[ev.playerId] || 0) + (ev.kind === "yellow" ? 1 : 3);
  }
  for (const pid of lineup) {
    const p = players[pid];
    if (!p) continue;
    let rating = 6.0 + teamMod + rng.gauss(0, 0.55);
    rating += (effective(p) - 60) * 0.017;
    rating += (goalsBy[pid] || 0) * 1.05;
    rating += (assistsBy[pid] || 0) * 0.65;
    rating -= (cards[pid] || 0) * 0.28;
    const share = D.POSITION_ROLE_SHARE[p.position];
    rating -= conceded * 0.24 * share.def;
    if (conceded === 0) rating += 0.45 * share.def;
    if (hasTrait(p, "clutch") && rng.random() < 0.4) rating += 0.4;
    rating = Math.round(clamp(rating, 3, 10) * 10) / 10;
    result.ratings[pid] = rating;

    const minutes = rng.random() > 0.18 ? 90 : rng.randint(55, 89);
    p.season.apps += 1;
    p.season.minutes += minutes;
    p.season.ratingSum += rating;
    p.fitness = clamp(p.fitness - minutes * 0.13 - rng.uniform(0, 6), 8, 100);
    p.form = clamp(p.form * 0.82 + (rating - 6.0) * 14 + 9, 5, 99);
    p.morale = clamp(p.morale + (outcome === "W" ? 2.5 : outcome === "L" ? -2.0 : 0.3)
                     + (rating - 6.5) * 1.6, 5, 99);
  }
}

function buildCommentary(result, home, away, players) {
  const lines = [];
  const diff = result.homeGoals - result.awayGoals;
  const total = result.homeGoals + result.awayGoals;
  if (total === 0) lines.push("שני שוערים מצוינים, אפס דרמה. 0:0 שאף אחד לא יזכור.");
  else if (Math.abs(diff) >= 3)
    lines.push(`${diff > 0 ? home.name : away.name} פשוט דרסו. הקהל התחיל לצאת ברבע שעה האחרונה.`);
  else if (diff === 0) lines.push("תיקו שמשאיר את שתי הקבוצות עם טעם מריר.");
  else lines.push(`${diff > 0 ? home.name : away.name} לקחו את זה בשיניים. משחק צמוד עד השריקה האחרונה.`);
  return lines;
}

// ---------------------------------------------------------------------------
// התפתחות
// ---------------------------------------------------------------------------

const OFF_PITCH = ["rest", "badges", "media", "business"];

function ageFactor(age) {
  if (age < 16) return 1.7;
  if (age > 38) return -1.1;
  return D.AGE_CURVE[String(age)];
}

function addGrowth(p, attr, delta) {
  p.growth[attr] = (p.growth[attr] || 0) + delta;
  const whole = Math.trunc(p.growth[attr]);
  if (whole) {
    p.attributes[attr] = Math.round(clamp((p.attributes[attr] ?? 50) + whole, 10, 97));
    p.growth[attr] -= whole;
  }
}

function weeklyTraining(p, focus, club, rng, intensity = 1.0) {
  const messages = [];
  const facilities = club ? club.trainingFacilities : 45;

  if (focus === "rest") {
    p.fitness = clamp(p.fitness + 26, 0, 100);
    p.morale = clamp(p.morale + 1.5, 0, 100);
    if (p.injuryWeeks > 0) {
      p.injuryWeeks = Math.max(0, p.injuryWeeks - 1);
      if (rng.random() < 0.3) {
        p.injuryWeeks = Math.max(0, p.injuryWeeks - 1);
        messages.push({ icon: "🏥", text: "השיקום מתקדם מהר מהצפוי." });
      }
    }
    return messages;
  }

  if (focus === "badges") {
    let gain = (0.55 + (p.attributes.mental ?? 50) / 200) * intensity;
    if (hasTrait(p, "student")) gain *= 1.4;
    p.coaching = clamp(p.coaching + gain, 0, 100);
    p.fitness = clamp(p.fitness + 10, 0, 100);
    const newBadges = Math.min(4, Math.floor(p.coaching / 22));
    if (newBadges > p.badges) {
      p.badges = newBadges;
      messages.push({ icon: "🎓", text: `השלמת תעודת אימון רמה ${p.badges}!` });
    }
    return messages;
  }

  if (focus === "media") {
    p.mediaSkill = clamp(p.mediaSkill + 0.9 * intensity, 0, 100);
    p.reputation = clamp(p.reputation + 0.25, 0, 100);
    p.fitness = clamp(p.fitness + 9, 0, 100);
    return messages;
  }

  if (focus === "business") {
    p.business = clamp(p.business + 0.85 * intensity, 0, 100);
    p.fitness = clamp(p.fitness + 9, 0, 100);
    return messages;
  }

  p.fitness = clamp(p.fitness + 12 - 6 * intensity, 0, 100);
  if (p.injuryWeeks > 0) {
    p.injuryWeeks = Math.max(0, p.injuryWeeks - 1);
    return [{ icon: "🩹", text: "אתה בשיקום — האימון היה קל בהרבה." }];
  }

  const gap = p.potential - overall(p);
  const curve = ageFactor(p.age);
  let base = 0.30 * intensity;
  base *= 0.55 + facilities / 110;
  base *= Math.max(0.15, curve);
  base *= 1 + clamp(gap, -10, 25) * 0.05;
  if (hasTrait(p, "workhorse")) base *= 1.30;
  base *= 0.75 + p.morale / 200;
  base *= rng.uniform(0.7, 1.35);

  const headroom = p.potential - overall(p);
  if (headroom <= 0) base *= 0.08;
  else if (headroom < 4) base *= 0.25 + headroom * 0.18;

  let current = (p.growth[focus] || 0) + base;
  let gained = 0;
  while (current >= 1.0 && (p.attributes[focus] ?? 50) < 97) {
    p.attributes[focus] = (p.attributes[focus] ?? 50) + 1;
    current -= 1;
    gained += 1;
  }
  p.growth[focus] = current;
  if (gained) {
    messages.push({ icon: "📈", text:
      `${D.ATTRIBUTE_NAMES_HE[focus]} עלתה ב-${gained} (עכשיו ${p.attributes[focus]}).` });
  }
  if (intensity > 1.15 && rng.random() < 0.035 * intensity) {
    const weeks = rng.randint(1, 3);
    p.injuryWeeks = weeks;
    p.injuryName = "עומס יתר באימון";
    messages.push({ icon: "🚑", text: `נמתחת באימון — ${weeks} שבועות בחוץ.` });
  }
  return messages;
}

function weeklyRecovery(p, played, rng) {
  if (p.injuryWeeks > 0) {
    p.injuryWeeks -= 1;
    if (p.injuryWeeks === 0) { p.injuryName = ""; p.fitness = clamp(p.fitness + 15, 0, 100); }
  }
  if (!played) p.fitness = clamp(p.fitness + 9, 0, 100);
  p.form = clamp(p.form + (played ? 0 : rng.uniform(-1.5, 1.5)), 5, 99);
}

function simulateAiWeek(players, rng, clubs, skip) {
  for (const pid in players) {
    const p = players[pid];
    if (pid === skip || p.retired) continue;
    const club = p.clubId ? clubs[p.clubId] : null;
    if (p.injuryWeeks > 0) {
      p.injuryWeeks -= 1;
      if (p.injuryWeeks === 0) p.injuryName = "";
      continue;
    }
    p.fitness = clamp(p.fitness + rng.uniform(6, 16), 0, 100);
    if (rng.random() < 0.55) weeklyTraining(p, rng.choice(D.ATTRIBUTES), club, rng, 0.85);
  }
}

function endOfSeasonDevelopment(p, rng, minutesShare = 0.5) {
  p.age += 1;
  const curve = ageFactor(p.age);
  const exposure = 0.45 + minutesShare * 1.1;
  for (const attr of D.ATTRIBUTES) {
    const sensitivity = D.DECLINE_SENSITIVITY[attr];
    let delta;
    if (curve > 0) {
      delta = curve * exposure * rng.uniform(0.4, 1.5);
      if (overall(p) >= p.potential) delta *= 0.08;
    } else {
      delta = curve * Math.max(0.2, sensitivity) * rng.uniform(0.5, 1.5);
    }
    addGrowth(p, attr, delta);
  }
  const s = p.season;
  if (s.apps) {
    const contribution = (s.goals + s.assists) / Math.max(1, s.apps);
    p.reputation = clamp(p.reputation + (avgRating(s) - 6.6) * 4 + contribution * 6, 1, 99);
  }
  mergeStats(p.career, s);
  p.season = newStats();
  p.fitness = 100;
  p.form = 50;
  if (p.contract.yearsLeft > 0) p.contract.yearsLeft -= 1;
}

function shouldRetire(p, rng) {
  if (p.age < 32) return false;
  let chance = (p.age - 31) * 0.16;
  if (overall(p) < 55) chance += 0.18;
  if (p.injuryWeeks > 12) chance += 0.25;
  return rng.random() < clamp(chance, 0, 0.95);
}

function retirementPressure(p) {
  let pressure = 0;
  pressure += Math.max(0, p.age - 31) * 0.13;
  pressure += Math.max(0, 62 - overall(p)) * 0.012;
  if (p.injuryWeeks >= 10) pressure += 0.25;
  if (p.contract.yearsLeft === 0 && p.age > 33) pressure += 0.15;
  return clamp(pressure, 0, 1);
}

// ---------------------------------------------------------------------------
// לוח משחקים
// ---------------------------------------------------------------------------

function roundRobin(teams, rng) {
  teams = rng.shuffle(teams.slice());
  if (teams.length % 2) teams.push("__bye__");
  const n = teams.length;
  const rounds = [];
  for (let r = 0; r < n - 1; r++) {
    const pairs = [];
    for (let i = 0; i < n / 2; i++) {
      const home = teams[i], away = teams[n - 1 - i];
      if (home === "__bye__" || away === "__bye__") continue;
      pairs.push(r % 2 === 0 ? [home, away] : [away, home]);
    }
    rounds.push(pairs);
    teams = [teams[0], teams[n - 1], ...teams.slice(1, n - 1)];
  }
  return rounds.concat(rounds.map(rnd => rnd.map(([h, a]) => [a, h])));
}

function leagueWeeks() {
  const out = [];
  for (let w = 1; w <= SEASON_WEEKS; w++) if (!CUP_WEEKS[w]) out.push(w);
  return out;
}
