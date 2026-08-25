// ---------------------------------------------------------------------------
// בדיקות לגרסת הווב. הרצה:  node web/test.js
// טוען את קבצי המשחק (בלי ה-UI) ומריץ עליהם בדיקות שפיות ואיזון.
// ---------------------------------------------------------------------------

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const HERE = __dirname;
const PARTS = ["data.js", "art.js", "save.js", "engine.js", "matchstats.js", "clubops.js",
               "commercial.js", "scouting.js", "development.js", "wealth.js", "manager.js",
               "story.js", "game.js",
               "graphics.js", "avatars.js", "scenes.js"];
const source = PARTS.map(f => fs.readFileSync(path.join(HERE, f), "utf8")).join("\n");
const ctx = vm.createContext({ console, Math, JSON, Date,
                              TextEncoder, TextDecoder, btoa, atob,
                              Uint8Array, Int32Array });
vm.runInContext(source + "\nthis.API = { D, Rng, Game, STORY, generateWorld, generatePlayer, " +
  "simulateMatch, pickLineup, teamStrength, roundRobin, overall, playerValue, " +
  "wageForOverall, positionFit, avgRating, weeklyTraining, weeklyRecovery, " +
  "endOfSeasonDevelopment, fmt, " +
  "SCENES, sceneFor, crest, kit, playerCard, pitch, goalTimeline, formGuide, " +
  "SEASON_WEEKS, leagueWeeks, " +
  "ART, avatar, avatarChip, SCENE_LABELS, randomIdentity, playerFoot, " +
  "buildOf, FOOT_KEYS, FOOT_NAMES, attendanceFor, matchdayIncome, " +
  "commercialIncome, weeklyFinances, upgradeCost, canUpgrade, tickWorks, " +
  "stadiumExpansion, staffCandidates, medicalCare, staffQuality, ticketPrice, " +
  "packSave, unpackSave, injuryRisk, marketability, sponsorOffer, " +
  "managerStyle, postMatchLine, selectionNote, weeklyDirective, directiveLine, STORY, " +
  "availableNumbers, assignNumber, STORY_CONDITIONS, applyStoryEffects, " +
  "EFFECT_KEYS, " +
  "matchStatLine, statSummary, areaScores, matchPerformance, weakestArea, " +
  "reasonLine, promiseLine, netIncome, " +
  "watchers, interestMap, interestLabel, candidateClubs, scoutsThisWeek, " +
  "topSuitor, foreignAgent, scoutReport, clubCountry, " +
  "SCOUT_NOTICED, SCOUT_COURTED, SCOUT_CHASED, " +
  "planOptionsFor, setPlan, planSummary, milestoneRows, nextTarget, " +
  "recommendedFocus, claimMilestones, " +
  "holdings, assetsAvailable, buyAsset, sellAsset, netWorth, portfolioYield, " +
  "assetsSeasonTick, wealthSummary, " +
  "signDeal, weeklyRetainer, seasonBonuses, tickPortfolio, renewalOffer, " +
  "dealLines, clauseText, portfolioTotal };", ctx);
const A = ctx.API;

let passed = 0, failed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log(`  ✓ ${name}`); }
  catch (err) { failed++; console.log(`  ✗ ${name}\n      ${err.message}`); }
}
function assert(cond, msg) { if (!cond) throw new Error(msg || "assertion failed"); }
function near(value, lo, hi, label) {
  assert(value >= lo && value <= hi, `${label}: ${value} מחוץ לטווח ${lo}–${hi}`);
}

console.log("\nעולם ומודלים");

test("ייצור עולם מלא ועקבי", () => {
  const w1 = A.generateWorld(7), w2 = A.generateWorld(7);
  assert(Object.keys(w1.clubs).length === A.D.CLUBS.length, "מספר מועדונים");
  assert(Object.keys(w1.players).length > 500, "מספר שחקנים");
  const names1 = Object.values(w1.players).map(p => p.name).join();
  const names2 = Object.values(w2.players).map(p => p.name).join();
  assert(names1 === names2, "אותו זרע חייב לייצר אותו עולם");
  for (const club of Object.values(w1.clubs))
    for (const pid of club.squad)
      assert(w1.players[pid].clubId === club.cid, "שיוך שחקן למועדון");
});

test("מועדונים חזקים = סגלים חזקים", () => {
  const { clubs, players } = A.generateWorld(5);
  const avg = cid => clubs[cid].squad.reduce((s, p) => s + A.overall(players[p]), 0) / clubs[cid].squad.length;
  assert(avg("real_castilla") > avg("maccabi_harel"), "אירופה מול ליגת העל");
  assert(avg("maccabi_harel") > avg("ironi_shomron"), "צמרת מול תחתית");
});

test("סולם השכר עולה עם הדירוג", () => {
  const wages = [40, 50, 60, 70, 80, 90].map(A.wageForOverall);
  for (let i = 1; i < wages.length; i++) assert(wages[i] > wages[i - 1], "מונוטוני");
});

test("שווי שחקן מגיע לשיא באמצע שנות ה-20", () => {
  const rng = new A.Rng(11);
  const { clubs } = A.generateWorld(11);
  const young = A.generatePlayer(rng, clubs.maccabi_harel, "ST", { age: 25, quality: 75 });
  const old = A.generatePlayer(rng, clubs.maccabi_harel, "ST", { age: 36, quality: 75 });
  old.attributes = Object.assign({}, young.attributes);
  assert(A.playerValue(young) > A.playerValue(old), "צעיר שווה יותר");
});

console.log("\nמנוע המשחקים");

test("הרכב תקין: 11 שחקנים בלי כפילויות", () => {
  const { clubs, players } = A.generateWorld(2);
  const lineup = A.pickLineup(clubs.bnei_negev, players, "4-3-3");
  assert(lineup.length === 11, `${lineup.length} שחקנים`);
  assert(new Set(lineup).size === 11, "כפילות בהרכב");
});

test("שחקן שנכפה להרכב מוצב במשבצת מתאימה לעמדתו", () => {
  const { clubs, players } = A.generateWorld(31);
  const club = clubs.ironi_shomron;
  for (const pos of ["ST", "CB", "CM", "LW", "GK"]) {
    const me = club.squad.map(p => players[p]).find(p => p.position === pos)
      || players[club.squad[0]];
    me.position = pos;
    for (const formation of Object.keys(A.D.FORMATIONS)) {
      const lineup = A.pickLineup(club, players, formation, [me.pid]);
      const idx = lineup.indexOf(me.pid);
      assert(idx >= 0, `${pos} לא נכנס להרכב ב-${formation}`);
      const slot = A.D.FORMATIONS[formation][idx];
      assert(A.positionFit(pos, slot) >= 0.9,
        `${pos} הוצב כ-${slot} במערך ${formation}`);
    }
  }
});

test("התאמת עמדה מעדיפה את העמדה הטבעית", () => {
  assert(A.positionFit("ST", "ST") === 1, "עמדה טבעית");
  assert(A.positionFit("GK", "ST") < 0.5, "שוער בהתקפה");
});

test("עוצמות הקווים בסולם דירוגים", () => {
  const { clubs, players } = A.generateWorld(4);
  const club = clubs.maccabi_harel;
  const s = A.teamStrength(A.pickLineup(club, players, club.formation), players, club.formation);
  for (const line of ["def", "mid", "att"]) near(s[line], 30, 100, line);
});

test("תוצאת משחק עקבית עם אירועי השערים", () => {
  const { clubs, players } = A.generateWorld(21);
  const rng = new A.Rng(9);
  const top = Object.values(clubs).filter(c => c.leagueId === "top");
  for (let i = 0; i < 300; i++) {
    for (const p of Object.values(players)) { p.fitness = 100; p.injuryWeeks = 0; }
    const s = rng.shuffle(top.slice());
    const r = A.simulateMatch(s[0], s[1], players, rng);
    const goals = r.events.filter(e => e.kind === "goal");
    assert(goals.length === r.homeGoals + r.awayGoals, "סכום השערים");
    assert(goals.filter(e => e.clubId === r.homeId).length === r.homeGoals, "שערי הבית");
    for (const pid of r.homeLineup.concat(r.awayLineup)) {
      assert(pid in r.ratings, "ציון לכל שחקן");
      near(r.ratings[pid], 3, 10, "ציון");
    }
  }
});

test("איזון: שערים ותוצאות בטווח מציאותי", () => {
  for (const seed of [3, 11, 19]) {
    const { clubs, players } = A.generateWorld(seed);
    const rng = new A.Rng(seed * 13);
    const top = Object.values(clubs).filter(c => c.leagueId === "top");
    let goals = 0, home = 0, draw = 0, n = 0;
    for (let i = 0; i < 400; i++) {
      for (const p of Object.values(players)) { p.fitness = 100; p.form = 50; p.morale = 60; p.injuryWeeks = 0; }
      const s = rng.shuffle(top.slice());
      const r = A.simulateMatch(s[0], s[1], players, rng);
      goals += r.homeGoals + r.awayGoals; n++;
      if (r.homeGoals > r.awayGoals) home++;
      else if (r.homeGoals === r.awayGoals) draw++;
    }
    near(goals / n, 2.0, 3.4, `שערים למשחק (זרע ${seed})`);
    near(home / n, 0.34, 0.55, `ניצחונות בית (זרע ${seed})`);
    near(draw / n, 0.13, 0.32, `תיקו (זרע ${seed})`);
  }
});

test("הקבוצה החזקה מנצחת את רוב המשחקים", () => {
  const { clubs, players } = A.generateWorld(9);
  const rng = new A.Rng(9);
  let wins = 0;
  for (let i = 0; i < 60; i++) {
    for (const p of Object.values(players)) { p.fitness = 100; p.injuryWeeks = 0; }
    const r = A.simulateMatch(clubs.real_castilla, clubs.ironi_shomron, players, rng);
    if (r.homeGoals > r.awayGoals) wins++;
  }
  assert(wins >= 45, `רק ${wins}/60 ניצחונות`);
});

test("לוח המשחקים מכסה כל צמד פעמיים", () => {
  const teams = Array.from({ length: 20 }, (_, i) => "t" + i);
  const rounds = A.roundRobin(teams, new A.Rng(1));
  assert(rounds.length === 38, `${rounds.length} מחזורים`);
  const seen = {};
  for (const rnd of rounds) {
    assert(rnd.length === 10, "משחקים במחזור");
    const inRound = new Set(rnd.flat());
    assert(inRound.size === 20, "כל קבוצה פעם אחת במחזור");
    for (const [h, a] of rnd) seen[h + ">" + a] = (seen[h + ">" + a] || 0) + 1;
  }
  assert(Object.keys(seen).length === 380, "כל הצמדים");
  assert(Object.values(seen).every(v => v === 1), "בלי כפילויות");
});

test("לוח השנה מכיל בדיוק את כל המחזורים", () => {
  const g = A.Game.newGame("בודק", "ST", "maccabi_sharon", 24, 3);
  assert(A.SEASON_WEEKS === 43, `אורך עונה ${A.SEASON_WEEKS}`);
  assert(A.leagueWeeks().length === 38, "שבועות ליגה");
  assert(g.fixtures.top.length === 38, "מחזורי ליגת העל");
  assert(g.cup.teams.length === 32, "קבוצות בגביע");
  assert(g.standings("top").length === 20 && g.standings("national").length === 20,
    "גודל הליגות");
});

console.log("\nהתפתחות");

test("אימון משפר את התכונה שמתאמנים עליה", () => {
  const rng = new A.Rng(12);
  const { clubs } = A.generateWorld(12);
  const p = A.generatePlayer(rng, clubs.maccabi_harel, "ST", { age: 18, quality: 55 });
  p.potential = 85;
  const before = p.attributes.shooting;
  for (let i = 0; i < 25; i++) A.weeklyTraining(p, "shooting", clubs.maccabi_harel, rng);
  assert(p.attributes.shooting > before, "הבעיטה לא עלתה");
});

test("תקרת הפוטנציאל נשמרת", () => {
  const rng = new A.Rng(13);
  const { clubs } = A.generateWorld(13);
  const p = A.generatePlayer(rng, clubs.maccabi_harel, "ST", { age: 20, quality: 60 });
  p.potential = A.overall(p);
  for (let i = 0; i < 60; i++) A.weeklyTraining(p, "shooting", clubs.maccabi_harel, rng);
  assert(A.overall(p) <= p.potential + 4, "פריצה של התקרה");
});

test("ותיקים דועכים לאורך עונות", () => {
  const rng = new A.Rng(15);
  const { clubs } = A.generateWorld(15);
  const p = A.generatePlayer(rng, clubs.maccabi_harel, "LW", { age: 34, quality: 75 });
  const before = A.overall(p);
  for (let i = 0; i < 4; i++) A.endOfSeasonDevelopment(p, rng, 0.8);
  assert(A.overall(p) < before, "לא דעך");
  assert(p.age === 38, "הגיל לא התקדם");
});

test("תעודות אימון דורשות שנים של לימוד", () => {
  const rng = new A.Rng(16);
  const { clubs } = A.generateWorld(16);
  const p = A.generatePlayer(rng, clubs.maccabi_harel, "CM", { age: 24 });
  p.coaching = 0;
  for (let i = 0; i < 22; i++) A.weeklyTraining(p, "badges", clubs.maccabi_harel, rng);
  assert(p.coaching > 0 && p.coaching < 40, `ידע אימון ${p.coaching}`);
  assert(p.badges <= 1, "יותר מדי תעודות בעונה אחת");
});

console.log("\nעלילה");

test("מאגר האירועים תקין", () => {
  const ids = A.STORY.map(e => e.eid);
  assert(new Set(ids).size === ids.length, "מזהה כפול");
  for (const e of A.STORY) {
    assert(e.choices.length > 0, `${e.eid} בלי בחירות`);
    assert(typeof e.body === "function", `${e.eid} בלי טקסט`);
    for (const c of e.choices) assert(c.label && typeof c.apply === "function", `${e.eid} בחירה פגומה`);
    for (const stage of e.stages) assert(stage in A.D.CAREER_STAGES_HE, `${e.eid} שלב לא מוכר`);
  }
});

test("אירוע ממתין עוצר את השבוע עד להחלטה", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 17, 21);
  g.pendingEventId = "youth_mentor";
  const week = g.week;
  const report = g.advanceWeek();
  assert(g.week === week, "השבוע התקדם למרות אירוע פתוח");
  assert(report.eventId === "youth_mentor", "האירוע לא הוחזר");
  assert(g.resolveEvent(0), "אין תוצאה לבחירה");
  assert(g.pendingEventId === null, "האירוע לא נסגר");
});

console.log("\nגרפיקה");

test("לכל סצנה יש תמונה מוטבעת", () => {
  const names = Object.keys(A.SCENES);
  assert(names.length >= 10, `רק ${names.length} סצנות`);
  for (const name of names) {
    const html = A.SCENES[name]();
    assert(html.includes("<img src=\"data:image/jpeg;base64,"), `${name}: אין תמונה מוטבעת`);
    assert(!html.includes("undefined"), `${name}: ערך חסר`);
    const art = A.ART[name];
    assert(art && art.length > 8000, `${name}: התמונה קטנה מדי (${art ? art.length : 0})`);
  }
});

test("כל תמונות הרקע קיימות ותקינות", () => {
  for (const key of Object.keys(A.SCENE_LABELS)) {
    const data = A.ART[key];
    assert(typeof data === "string", `${key}: חסרה תמונה`);
    assert(data.startsWith("data:image/jpeg;base64,"), `${key}: פורמט שגוי`);
  }
});

test("לכל אירוע עלילה יש סצנה", () => {
  for (const event of A.STORY) {
    const html = A.sceneFor(event.eid, event.stages[0] || "player");
    assert(html.includes("data:image/jpeg"), `${event.eid}: אין סצנה`);
  }
});

test("אפשר לבחור זהות, והיא נשמרת עם הקריירה", () => {
  const chosen = { foot: "left", trait: "clutch" };
  const g = A.Game.newGame("עומר לוי", "ST", "hapoel_carmel", 24, 8, "player", chosen);
  assert(g.me.foot === "left", `רגל: ${g.me.foot}`);
  assert(g.me.traits[0] === "clutch", `תכונה: ${g.me.traits[0]}`);
  assert(A.playerFoot(g.me) === "left", "הרגל שנבחרה לא הוחלה");

  // שמירה וטעינה
  const copy = A.Game.fromJSON(JSON.parse(JSON.stringify(g.toJSON())));
  assert(copy.me.foot === "left" && copy.me.traits[0] === "clutch",
    "הזהות לא שרדה שמירה וטעינה");

  // זהות אקראית תמיד חוקית
  for (let i = 0; i < 60; i++) {
    const id = A.randomIdentity();
    assert(A.FOOT_KEYS.includes(id.foot), `רגל לא חוקית: ${id.foot}`);
    assert(A.D.TRAITS[id.trait], `תכונה לא חוקית: ${id.trait}`);
  }

  // שחקן מחשב — רגל יציבה, נגזרת מהמזהה
  const other = g.players[g.myClub().squad.find(p => p !== g.meId)];
  assert(A.FOOT_KEYS.includes(A.playerFoot(other)), "לשחקן מחשב אין רגל חוקית");
  assert(A.playerFoot(other) === A.playerFoot(other), "הרגל של שחקן המחשב משתנה");
});

test("לכל שחקן יש דיוקן במדי המועדון, בלי פנים מומצאות", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 17, 61);
  const club = g.myClub();
  const sample = club.squad.slice(0, 12).map(pid => g.players[pid]);
  const shapes = new Set();
  for (const p of sample) {
    const svg = A.avatar(p, club, 80);
    assert(svg.startsWith("<svg") && svg.trim().endsWith("</svg>"), `${p.name}: לא SVG`);
    assert(!svg.includes("undefined") && !svg.includes("NaN"), `${p.name}: ערך חסר`);
    // אותו שחקן — אותה צללית, תמיד
    const b = A.buildOf(p);
    assert(JSON.stringify(A.buildOf(p)) === JSON.stringify(b), "הצללית משתנה בין קריאות");
    shapes.add([b.frame, b.crop, b.shoulder].join("|"));
  }
  assert(shapes.size >= 5, `רק ${shapes.size} צלליות שונות מתוך ${sample.length}`);
});

console.log("\nמועדון: אצטדיון, תקציב, מתקנים וצוות");

function commercialIncomeOf(g) { return A.commercialIncome(g.myClub()); }

function managedGame(seed = 9, club = "hapoel_carmel") {
  return A.Game.newGame("מנג'ר", "CM", club, 42, seed, "manager");
}

test("לכל מועדון יש אצטדיון, מתקנים וצוות", () => {
  const { clubs } = A.generateWorld(4);
  for (const club of Object.values(clubs)) {
    assert(club.stadiumName, `${club.name}: אין שם אצטדיון`);
    assert(club.capacity >= 1500 && club.capacity <= 42000, `${club.name}: קיבולת ${club.capacity}`);
    assert(club.capacity % 500 === 0, "קיבולת לא מעוגלת");
    assert(club.balance > 0, "אין קופה");
    assert(club.medicalCentre >= 1 && club.medicalCentre <= 99, "מרכז רפואי מחוץ לטווח");
    assert(A.ticketPrice(club) > 0, "מחיר כרטיס לא תקין");
    for (const [role, m] of Object.entries(club.staff)) {
      assert(A.D.STAFF_ROLES[role], `תפקיד לא מוכר: ${role}`);
      assert(m.quality >= 8 && m.quality <= 96, `איכות ${m.quality}`);
      assert(m.wage > 0 && Number.isFinite(m.wage), `שכר ${m.wage}`);
      assert(m.name, "אין שם");
    }
  }
});

test("גודל האצטדיון הולך אחרי גודל המועדון", () => {
  const { clubs } = A.generateWorld(4);
  const ranked = Object.values(clubs).sort((a, b) => b.reputation - a.reputation);
  const big = ranked.slice(0, 6).reduce((s, c) => s + c.capacity, 0) / 6;
  const small = ranked.slice(-6).reduce((s, c) => s + c.capacity, 0) / 6;
  assert(big > small * 4, `${Math.round(big)} מול ${Math.round(small)}`);
});

test("הקהל אף פעם לא עולה על הקיבולת, וגדל עם האהדה", () => {
  const { clubs } = A.generateWorld(4);
  const club = clubs.hapoel_carmel, opponent = clubs.maccabi_harel;
  const rng = new A.Rng(2);
  for (let i = 0; i < 60; i++) {
    const att = A.attendanceFor(club, opponent, rng);
    assert(att > 0 && att <= club.capacity, `קהל ${att} מול קיבולת ${club.capacity}`);
  }
  const loyal = Object.assign({}, club, { fanSupport: 95 });
  const quiet = Object.assign({}, club, { fanSupport: 25 });
  let crowded = 0, empty = 0;
  for (let i = 0; i < 30; i++) {
    crowded += A.attendanceFor(loyal, opponent, new A.Rng(i + 1));
    empty += A.attendanceFor(quiet, opponent, new A.Rng(i + 1));
  }
  assert(crowded > empty, "אהדה לא משפיעה על הקהל");
});

test("המאזן השבועי מסתדר חשבונית", () => {
  const { clubs, players } = A.generateWorld(4);
  const club = clubs.hapoel_carmel;
  const before = club.balance;
  const d = A.weeklyFinances(club, players, 1000000);
  assert(d.net === d.commercial + d.matchday - d.wages - d.staff, "הנטו לא מסתדר");
  assert(club.balance === Math.round(before + d.net), "הקופה לא עודכנה");
});

test("משחקי בית מכניסים כסף לקופה", () => {
  const g = managedGame();
  let homeWeeks = 0;
  for (let i = 0; i < 120; i++) {
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    const r = g.advanceWeek();
    if (r.attendance) {
      homeWeeks++;
      assert(r.finances.matchday > 0, "משחק בית בלי הכנסה");
      assert(r.attendance <= g.myClub().capacity, "קהל מעל הקיבולת");
    } else {
      assert(r.finances.matchday === 0, "הכנסת יום משחק בלי משחק בית");
    }
    if (r.seasonEnded) break;
  }
  assert(homeWeeks >= 14, `רק ${homeWeeks} משחקי בית בעונה`);
});

test("הקופה עובדת גם בשנות הנוער", () => {
  const g = A.Game.newGame("נער", "ST", "hapoel_carmel", 13, 5);
  assert(g.stage === "youth", `שלב ${g.stage}`);
  let homeWeeks = 0, gate = 0;
  for (let i = 0; i < 80; i++) {
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    const r = g.advanceWeek();
    if (r.attendance) { homeWeeks++; assert(r.finances.matchday > 0, "אין הכנסה ממשחק בית"); }
    gate += r.finances ? r.finances.matchday : 0;
    if (r.seasonEnded) break;
  }
  assert(homeWeeks >= 14, `רק ${homeWeeks} משחקי בית נספרו`);
  // מועדון יכול לסיים עונה במינוס — מה שנבדק כאן הוא שהקהל נספר בכלל
  assert(gate > commercialIncomeOf(g) * 4, `הכנסות יום משחק זניחות: ${gate}`);
});

test("שדרוג מתקן עולה כסף, לוקח זמן ונוחת", () => {
  const g = managedGame();
  const club = g.myClub();
  club.balance = 60000000;
  const beforeLevel = club.medicalCentre;
  const beforeBalance = club.balance;
  const cost = A.upgradeCost(club, "medical");

  assert(g.upgradeFacility("medical").includes("אישרת"), "השדרוג לא אושר");
  assert(club.balance === beforeBalance - cost, "הכסף לא ירד");
  assert(club.medicalCentre === beforeLevel, "המתקן השתדרג לפני הזמן");
  assert(g.upgradeFacility("medical").includes("כבר בעיצומן"), "אפשר לשדרג פעמיים במקביל");

  for (let i = 0; i < A.D.FACILITIES.medical.weeks; i++) A.tickWorks(club);
  assert(club.medicalCentre > beforeLevel, "המתקן לא שודרג");
  assert(club.works.length === 0, "העבודות לא הסתיימו");
});

test("הרחבת אצטדיון מוסיפה מקומות", () => {
  const g = managedGame();
  const club = g.myClub();
  club.balance = 200000000;
  const before = club.capacity;
  const added = A.stadiumExpansion(club);
  g.upgradeFacility("stadium");
  for (let i = 0; i < A.D.FACILITIES.stadium.weeks; i++) A.tickWorks(club);
  assert(club.capacity === before + added, `${before} + ${added} ≠ ${club.capacity}`);
});

test("קופה ריקה חוסמת בנייה", () => {
  const g = managedGame();
  const club = g.myClub();
  club.balance = 1000;
  assert(A.canUpgrade(club, "training") === "אין מספיק כסף בקופה.", "לא נחסם");
  assert(g.upgradeFacility("training").includes("אין מספיק כסף"), "השדרוג עבר");
  assert(club.works.length === 0, "נפתחה עבודה בלי כסף");
});

test("גיוס ופיטורי צוות מזיזים כסף ואת הסגל המקצועי", () => {
  const g = managedGame();
  const club = g.myClub();
  club.balance = 20000000;
  const candidate = Object.assign({}, g.staffMarket.analyst[0]);
  let before = club.balance;

  const message = g.hireStaff("analyst", 0);
  assert(message.includes(candidate.name), `הודעה: ${message}`);
  assert(club.staff.analyst.quality === candidate.quality, "האנליסט לא נכנס");
  assert(club.balance === before - candidate.wage * 4, "דמי החתימה לא ירדו");

  const wage = club.staff.analyst.wage;
  before = club.balance;
  assert(g.releaseStaff("analyst").includes("סיים את תפקידו"), "לא פוטר");
  assert(!club.staff.analyst, "עדיין בתפקיד");
  assert(club.balance === before - wage * 8, "הפיצויים לא שולמו");
  assert(g.releaseStaff("analyst") === "המשרה כבר פנויה.", "פיטר משרה ריקה");
});

test("רק מי שמחליט מוציא כסף של המועדון", () => {
  const g = A.Game.newGame("שחקן", "ST", "hapoel_carmel", 24, 9);
  assert(!g.controlsClub(), "שחקן שולט בתקציב");
  const balance = g.myClub().balance;
  assert(g.upgradeFacility("training").includes("לא מחליט"), "שחקן שדרג מתקן");
  assert(g.hireStaff("analyst", 0).includes("לא מגייס"), "שחקן גייס צוות");
  assert(g.releaseStaff("analyst").includes("לא מפטר"), "שחקן פיטר צוות");
  assert(g.myClub().balance === balance, "הקופה השתנתה");
});

test("טיפול רפואי טוב מקצר פציעות", () => {
  const { clubs } = A.generateWorld(4);
  const good = clubs.hapoel_carmel;
  good.medicalCentre = 95;
  good.staff.physio = { name: "טוב", quality: 95, wage: 5000 };
  const poor = clubs.maccabi_sharon;
  poor.medicalCentre = 10;
  delete poor.staff.physio;
  assert(A.medicalCare(good) > 0.9, "טיפול טוב לא נמדד");
  assert(A.medicalCare(poor) < 0.2, "טיפול גרוע לא נמדד");

  const weeksToHeal = (club, seed) => {
    const p = A.generatePlayer(new A.Rng(seed), club, "ST");
    p.injuryWeeks = 6;
    const rng = new A.Rng(seed + 100);
    let weeks = 0;
    while (p.injuryWeeks > 0 && weeks < 40) { A.weeklyRecovery(p, false, rng, club); weeks++; }
    return weeks;
  };
  let fast = 0, slow = 0;
  for (let i = 0; i < 14; i++) { fast += weeksToHeal(good, i); slow += weeksToHeal(poor, i); }
  assert(fast < slow, `${fast} מול ${slow}`);
});

test("עוזר מאמן מאיץ את האימון", () => {
  const { clubs } = A.generateWorld(4);
  const helped = clubs.hapoel_carmel;
  helped.staff.assistant = { name: "טוב", quality: 95, wage: 6000 };
  const alone = clubs.maccabi_sharon;
  alone.trainingFacilities = helped.trainingFacilities;
  delete alone.staff.assistant;

  const gain = (club, seed) => {
    const p = A.generatePlayer(new A.Rng(seed), club, "ST", { age: 19, quality: 55 });
    p.potential = 90;
    const start = p.attributes.shooting;
    const rng = new A.Rng(seed);
    for (let i = 0; i < 40; i++) A.weeklyTraining(p, "shooting", club, rng);
    return p.attributes.shooting - start;
  };
  let withHelp = 0, without = 0;
  for (let s = 0; s < 14; s++) { withHelp += gain(helped, s); without += gain(alone, s); }
  assert(withHelp > without, `${withHelp} מול ${without}`);
});

test("אנליסט נותן יתרון מדיד", () => {
  const { clubs, players } = A.generateWorld(4);
  const home = clubs.hapoel_carmel, away = clubs.maccabi_sharon;
  home.staff.analyst = { name: "מצוין", quality: 95, wage: 6000 };
  delete away.staff.analyst;
  let sharp = 0;
  for (let s = 0; s < 160; s++)
    sharp += A.simulateMatch(home, away, players, new A.Rng(s + 1)).homeGoals;
  delete home.staff.analyst;
  away.staff.analyst = { name: "מצוין", quality: 95, wage: 6000 };
  let blunt = 0;
  for (let s = 0; s < 160; s++)
    blunt += A.simulateMatch(home, away, players, new A.Rng(s + 1)).homeGoals;
  assert(sharp > blunt, `${sharp} מול ${blunt}`);
});

test("בנייה מסתיימת גם אחרי שעברת מועדון", () => {
  const g = managedGame();
  const first = g.myClub();
  first.balance = 60000000;
  const before = first.medicalCentre;
  g.upgradeFacility("medical");

  g.managedClubId = "maccabi_harel";      // עברת מועדון באמצע
  for (let i = 0; i < A.D.FACILITIES.medical.weeks + 1; i++) {
    if (g.pendingEventId) g.resolveEvent(0);
    g.advanceWeek();
  }
  assert(first.medicalCentre > before, `${before} -> ${first.medicalCentre}`);
  assert(first.works.length === 0, "העבודות נתקעו");
});

test("ספרי המועדון שורדים שמירה וטעינה", () => {
  const g = managedGame();
  const club = g.myClub();
  club.balance = 80000000;
  g.upgradeFacility("medical");
  g.hireStaff("assistant", 0);
  for (let i = 0; i < 3; i++) { if (g.pendingEventId) g.resolveEvent(0); g.advanceWeek(); }

  // ייתכן שהמנג'ר עבר מועדון באמצע — משווים את אותו מועדון בשני הצדדים
  const live = g.myClub();
  const copy = A.Game.fromJSON(JSON.parse(JSON.stringify(g.toJSON())));
  const mirror = copy.clubs[live.cid];
  assert(mirror.stadiumName === live.stadiumName, "שם האצטדיון לא נשמר");
  assert(mirror.capacity === live.capacity, "הקיבולת לא נשמרה");
  assert(Math.round(mirror.balance) === Math.round(live.balance), "הקופה לא נשמרה");
  assert(JSON.stringify(mirror.staff) === JSON.stringify(live.staff), "הצוות לא נשמר");
  assert(JSON.stringify(mirror.works) === JSON.stringify(live.works), "העבודות לא נשמרו");
  assert(Object.keys(copy.staffMarket).length === Object.keys(g.staffMarket).length,
    "שוק הצוות לא נשמר");
});

test("סמל, מגרש וכרטיס שחקן נבנים לכל מועדון", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 17, 55);
  for (const club of Object.values(g.clubs)) {
    const c = A.crest(club, 28);
    assert(c.includes("<svg") && !c.includes("undefined"), `סמל ${club.name}`);
    const [primary] = A.kit(club.cid);
    assert(/^#[0-9A-Fa-f]{6}$/.test(primary), `צבע לא תקין ל-${club.name}`);
  }
  const card = A.playerCard(g.me, g.myClub(), g.stage);
  assert(card.includes("pcard") && !card.includes("undefined"), "כרטיס שחקן");
  assert(card.includes("avatar"), "אין דיוקן בכרטיס");
  const club = g.myClub();
  const lineup = A.pickLineup(club, g.players, club.formation);
  const svg = A.pitch(lineup, club.formation, g.players, g.meId, club);
  assert(svg.includes("<svg") && !svg.includes("NaN"), "מגרש");
});

console.log("\nשמירה");

test("שמורה נדחסת בלי לאבד ולו סיבית", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 15, 7);
  for (let i = 0; i < 20; i++) { if (g.pendingEventId) g.resolveEvent(0); g.advanceWeek(); }
  const state = JSON.parse(JSON.stringify(g.toJSON()));
  const packed = A.packSave(state);
  assert(packed.startsWith("fm2:"), "אין תג פורמט");
  assert(packed.length < JSON.stringify(state).length / 2,
    `הדחיסה חלשה מדי: ${packed.length} מול ${JSON.stringify(state).length}`);
  assert(JSON.stringify(A.unpackSave(packed)) === JSON.stringify(state), "השמורה לא זהה");
});

test("קריירה שנטענה ממשיכה בדיוק לאותו עתיד", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 15, 7);
  for (let i = 0; i < 15; i++) { if (g.pendingEventId) g.resolveEvent(0); g.advanceWeek(); }
  const copy = A.Game.fromJSON(A.unpackSave(A.packSave(g.toJSON())));

  const walk = state => {
    const out = [];
    for (let i = 0; i < 12; i++) {
      if (state.pendingEventId) state.resolveEvent(0);
      const r = state.advanceWeek();
      out.push([r.week, r.attendance, r.finances && r.finances.net,
                r.match ? r.match.result.homeGoals + ":" + r.match.result.awayGoals : ""].join("|"));
    }
    return out.join(";");
  };
  assert(walk(g) === walk(copy), "העתיד השתנה אחרי טעינה");
});

test("שמורות בפורמט הישן עדיין נטענות", () => {
  const g = A.Game.newGame("ותיק", "CM", "hapoel_carmel", 22, 3);
  g.advanceWeek();
  const legacy = JSON.stringify(g.toJSON());       // כך זה נשמר לפני הדחיסה
  const restored = A.Game.fromJSON(A.unpackSave(legacy));
  assert(restored.me.name === "ותיק", "שם לא שוחזר");
  assert(restored.week === g.week, "שבוע לא שוחזר");
});

test("דחיסה עומדת בטקסט עברי, אימוג'י ותווים חריגים", () => {
  const cases = ["", "a", "שלום עולם", "🏟️⚽🎓", "\u0000\u001f\uffff",
                 JSON.stringify({ a: [1.5, -2.25e-7, null, true], ב: "מכבי \"הראל\"" }),
                 "ab".repeat(50000)];
  for (const text of cases) {
    const value = { text };
    assert(JSON.stringify(A.unpackSave(A.packSave(value))) === JSON.stringify(value),
      `נשבר על: ${text.slice(0, 24)}`);
  }
});

console.log("\nהתפתחות, פציעות ומסחר");

test("שחקן ממשיך להשתפר גם אחרי גיל 18", () => {
  const g = A.Game.newGame("צעיר", "ST", "hapoel_carmel", 17, 4);
  const marks = {};
  while (g.me.age <= 24 && !g.gameOver) {
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    g.advanceWeek();
    marks[g.me.age] = A.overall(g.me);
  }
  const at18 = marks[18], at22 = marks[22], at24 = marks[24];
  assert(at22 > at18 + 3, `18→22 עלה רק ${at22 - at18}`);
  assert(at24 >= at22, `24 (${at24}) נמוך מ-22 (${at22})`);
});

test("הפוטנציאל זז לפי מה שקרה במגרש, והתקרה נשארת חסם", () => {
  const g = A.Game.newGame("צעיר", "ST", "hapoel_carmel", 16, 8);
  const first = g.me.potential;
  assert(g.me.ceiling >= first, "התקרה נמוכה מההערכה");
  for (let i = 0; i < 260 && g.me.age <= 22 && !g.gameOver; i++) {
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    g.advanceWeek();
    assert(g.me.potential <= g.me.ceiling, "הפוטנציאל עבר את התקרה");
  }
  assert(g.me.potential !== first, "ההערכה לא זזה בכלל");
});

test("אימון מפזר על כמה תכונות, לא רק על אחת", () => {
  const { clubs } = A.generateWorld(4);
  const club = clubs.hapoel_carmel;
  const p = A.generatePlayer(new A.Rng(3), club, "ST", { age: 19, quality: 50 });
  p.potential = 90; p.ceiling = 90;
  const before = Object.assign({}, p.attributes);
  const rng = new A.Rng(3);
  for (let i = 0; i < 43; i++) A.weeklyTraining(p, "shooting", club, rng);
  const moved = D_ATTRS().filter(a => p.attributes[a] > before[a]);
  assert(moved.length >= 4, `רק ${moved.length} תכונות זזו`);
  assert(p.attributes.shooting > before.shooting, "התכונה שנבחרה לא עלתה");
});

function D_ATTRS() { return A.D.ATTRIBUTES; }

test("כוח פיזי ועמידות מורידים סיכון פציעה", () => {
  const { clubs } = A.generateWorld(4);
  const club = clubs.hapoel_carmel;
  const tough = A.generatePlayer(new A.Rng(5), club, "CB", { age: 24, quality: 60 });
  const frail = A.generatePlayer(new A.Rng(5), club, "CB", { age: 24, quality: 60 });
  tough.resilience = 92; tough.attributes.physical = 88; tough.sharpness = 85;
  frail.resilience = 15; frail.attributes.physical = 35; frail.sharpness = 30;
  assert(A.injuryRisk(tough) < A.injuryRisk(frail) * 0.6,
    `${A.injuryRisk(tough).toFixed(2)} מול ${A.injuryRisk(frail).toFixed(2)}`);
  assert(A.injuryRisk(tough) < 1, "שחקן חסון עדיין בסיכון רגיל");
});

test("לכל שחקן יש גובה, משקל ועמידות סבירים לעמדה", () => {
  const { players } = A.generateWorld(4);
  const keepers = [], wingers = [];
  for (const p of Object.values(players)) {
    assert(p.height >= 150 && p.height <= 210, `גובה ${p.height}`);
    assert(p.weight >= 45 && p.weight <= 110, `משקל ${p.weight}`);
    assert(p.resilience >= 0 && p.resilience <= 100, "עמידות מחוץ לטווח");
    if (p.position === "GK" && p.age >= 20) keepers.push(p.height);
    if (p.position === "LW" && p.age >= 20) wingers.push(p.height);
  }
  const avg = a => a.reduce((x, y) => x + y, 0) / a.length;
  assert(avg(keepers) > avg(wingers) + 6,
    `שוערים ${avg(keepers).toFixed(0)} מול כנפיים ${avg(wingers).toFixed(0)}`);
});

test("הצעות חסות מתכיילות למי שאתה", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 24, 2);
  const rng = new A.Rng(9);
  const sample = (rep, media, goals) => {
    g.me.reputation = rep; g.me.mediaSkill = media; g.me.career.goals = goals;
    let total = 0, n = 60;
    for (let i = 0; i < n; i++) {
      const o = A.sponsorOffer(g.me, rng, 67);
      total += o ? o.amount : 0;
    }
    return total / n;
  };
  const young = sample(18, 8, 2);
  const star = sample(88, 72, 210);
  assert(star > young * 8, `כוכב ${Math.round(star)} מול צעיר ${Math.round(young)}`);
  assert(A.marketability(g.me, 67) > 50, "ערך מסחרי של כוכב נמוך מדי");
});

test("למאמן יש אופי קבוע והוא מגיב אחרי משחק", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 24, 5);
  const club = g.myClub();
  const style = A.managerStyle(club);
  assert(style && style[1], "אין אופי למאמן");
  assert(JSON.stringify(A.managerStyle(club)) === JSON.stringify(style), "האופי משתנה");
  const rng = new A.Rng(1);
  assert(A.postMatchLine(g, 8.6, "W", true, rng).includes(club.managerName), "אין תגובה לציון גבוה");
  assert(A.selectionNote(g), "אין הסבר על מצב ההרכב");
  const directive = A.weeklyDirective(g, rng);
  assert(A.D.ATTRIBUTES.includes(directive) || directive === "rest", `הוראה לא חוקית: ${directive}`);
});

test("אירוע חוזר לא קופץ שוב בשבוע הבא", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 24, 6);
  const seen = {};
  let lastWeekOf = {};
  for (let i = 0; i < 220 && !g.gameOver; i++) {
    if (g.pendingEventId) {
      const eid = g.pendingEventId;
      const stamp = g.year * 43 + g.week;
      const event = A.STORY.find(e => e.eid === eid);
      if (event && !event.once && lastWeekOf[eid] !== undefined) {
        const gap = stamp - lastWeekOf[eid];
        assert(gap >= (event.cooldown ?? 30),
          `${eid} חזר אחרי ${gap} שבועות במקום ${event.cooldown ?? 30}`);
      }
      lastWeekOf[eid] = stamp;
      seen[eid] = (seen[eid] || 0) + 1;
      g.resolveEvent(0);
      continue;
    }
    g.advanceWeek();
  }
  assert(Object.keys(seen).length > 5, "כמעט לא נורו אירועים");
});

test("מספרי חולצה ייחודיים, וניתן לבחור אותם", () => {
  const { clubs, players } = A.generateWorld(4);
  const club = clubs.hapoel_carmel;
  const numbers = club.squad.map(pid => players[pid].number);
  assert(numbers.every(n => n >= 1 && n <= 45), "מספר מחוץ לטווח");
  assert(new Set(numbers).size === numbers.length, "יש כפילות במספרים");

  const free = A.availableNumbers(club, players);
  assert(free.length > 0, "אין מספרים פנויים");
  assert(free.every(n => !numbers.includes(n)), "מספר תפוס הוצע כפנוי");

  // מספר מבוקש שפנוי — מתקבל
  const wanted = free[0];
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 22, 5, "player",
                           { foot: "right", trait: "leader", number: wanted });
  assert(g.me.number === wanted, `ביקשתי ${wanted} וקיבלתי ${g.me.number}`);
  const squadNumbers = g.myClub().squad.map(pid => g.players[pid].number);
  assert(new Set(squadNumbers).size === squadNumbers.length, "כפילות אחרי הצטרפות");
});

test("מספר תפוס לא נגנב, ומוסבר למי הוא שייך", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 22, 5);
  const club = g.myClub();
  const other = club.squad.map(pid => g.players[pid])
    .find(p => p && p.pid !== g.meId && p.number);
  const before = g.me.number;
  const message = g.chooseNumber(other.number);
  assert(message.includes(other.name), `הודעה: ${message}`);
  assert(g.me.number === before, "המספר הוחלף למרות שהיה תפוס");

  const free = g.freeNumbers().find(n => n !== before);
  assert(g.chooseNumber(free).includes(String(free)), "החלפה למספר פנוי נכשלה");
  assert(g.me.number === free, "המספר לא התעדכן");
  const squadNumbers = club.squad.map(pid => g.players[pid].number);
  assert(new Set(squadNumbers).size === squadNumbers.length, "כפילות אחרי החלפה");
});

console.log("\nספריית העלילה");

test("החבילה מונחת-הנתונים תקינה ותואמת בין המנועים", () => {
  const pack = A.D.STORY_PACK;
  assert(pack.length >= 140, `רק ${pack.length} אירועים בחבילה`);
  const ids = new Set();
  const stages = new Set(["youth", "academy", "player", "veteran", "retired",
                          "coach", "manager", "director", "pundit", "agent",
                          "owner", "legend"]);
  for (const row of pack) {
    assert(row.eid && !ids.has(row.eid), `מזהה כפול: ${row.eid}`);
    ids.add(row.eid);
    assert(row.title && row.body, `${row.eid}: חסר כותרת או טקסט`);
    assert(row.choices && row.choices.length >= 2, `${row.eid}: פחות משתי בחירות`);
    for (const st of (row.stages || []))
      assert(stages.has(st), `${row.eid}: שלב לא מוכר ${st}`);
    for (const choice of row.choices) {
      assert(choice.label, `${row.eid}: בחירה בלי תווית`);
      assert(choice.text, `${row.eid}: בחירה בלי תוצאה`);
    }
    for (const key of Object.keys(row.when || {}))
      assert(key in A.STORY_CONDITIONS, `${row.eid}: תנאי לא מוכר ${key}`);
    for (const choice of row.choices)
      for (const key of Object.keys(choice.fx || {}))
        assert(A.EFFECT_KEYS.has(key), `${row.eid}: אפקט לא מוכר ${key}`);
  }
  // כל אירוע בחבילה נרשם במנוע
  const registered = new Set(A.STORY.map(e => e.eid));
  for (const row of pack) assert(registered.has(row.eid), `${row.eid} לא נרשם`);
});

test("ספריית העלילה גדולה ומכסה את כל שלבי הקריירה", () => {
  assert(A.STORY.length >= 170, `רק ${A.STORY.length} אירועים`);
  const byStage = {};
  for (const e of A.STORY)
    for (const st of (e.stages.length ? e.stages : ["כללי"]))
      byStage[st] = (byStage[st] || 0) + 1;
  for (const st of ["youth", "academy", "player", "veteran", "manager",
                    "coach", "director", "owner", "pundit", "agent", "legend"])
    assert((byStage[st] || 0) >= 5, `${st}: רק ${byStage[st] || 0} אירועים`);
});

test("כל אירוע שנורה מייצר טקסט מלא בלי מקומות ריקים", () => {
  const seen = new Set();
  for (const seed of [3, 9, 17]) {
    const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 13, seed);
    for (let i = 0; i < 700 && !g.gameOver; i++) {
      if (g.pendingEventId) {
        const body = g.pendingEventBody || "";
        assert(body.trim(), `${g.pendingEventId}: טקסט ריק`);
        assert(!body.includes("{"), `${g.pendingEventId}: מקום שלא מולא — ${body.slice(0, 40)}`);
        seen.add(g.pendingEventId);
        const event = A.STORY.find(e => e.eid === g.pendingEventId);
        g.resolveEvent(g.rng.randint(0, event.choices.length - 1));
        continue;
      }
      g.advanceWeek();
    }
  }
  assert(seen.size >= 60, `רק ${seen.size} אירועים שונים נורו בשלוש קריירות`);
});

test("אפקטים של בחירה באמת משנים את המצב", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 24, 4);
  const before = { morale: g.me.morale, money: g.money, rep: g.me.reputation };
  A.applyStoryEffects(g, { morale: 9, money: 50000, rep: 4, attr: ["shooting", 1.0] });
  assert(g.me.morale > before.morale, "מורל לא השתנה");
  assert(g.money === before.money + 50000, "כסף לא השתנה");
  assert(g.me.reputation > before.rep, "מוניטין לא השתנה");

  const club = g.myClub();
  const trust = club.managerTrust;
  A.applyStoryEffects(g, { trust: -10, flag: "test_flag", trait: "leader" });
  assert(club.managerTrust < trust, "אמון לא ירד");
  assert(g.flag("test_flag") === true, "דגל לא נדלק");
  assert(g.me.traits.includes("leader"), "תכונה לא נוספה");
});

console.log("\nמצב המשחק");

test("משחק חדש מציב את השחקן בסגל", () => {
  const g = A.Game.newGame("עומר לוי", "ST", "hapoel_carmel", 17, 31);
  assert(g.me.name === "עומר לוי", "שם");
  assert(g.myClub().squad.includes(g.meId), "לא בסגל");
  assert(g.stage === "academy", "שלב פתיחה");
  assert(A.overall(g.me) < g.me.potential, "אין לאן להתפתח");
});

test("אפשר להתחיל קריירה בכל גיל", () => {
  const expected = { 13: "youth", 15: "youth", 16: "academy", 17: "academy",
                     18: "player", 25: "player", 30: "player", 31: "veteran", 36: "veteran" };
  for (const [ageStr, stage] of Object.entries(expected)) {
    const age = +ageStr;
    const g = A.Game.newGame("בודק", "ST", "maccabi_sharon", age, 5);
    assert(g.stage === stage, `גיל ${age}: ${g.stage} במקום ${stage}`);
    assert(g.me.age === age, "הגיל לא נשמר");
    assert(g.me.potential >= A.overall(g.me), "פוטנציאל נמוך מהדירוג");
    if (age >= 19) {
      assert(g.me.career.apps > 0, `גיל ${age} בלי עבר`);
      assert(g.me.contract.wage > 0, `גיל ${age} בלי חוזה`);
    }
    if (age <= 15) assert(g.me.contract.wage === 0, "ילד עם חוזה");
  }
});

test("אפשר להתחיל קריירה כמנג'ר", () => {
  const g = A.Game.newGame("דני מנג'ר", "CM", "hapoel_carmel", 45, 11, "manager");
  assert(g.stage === "manager", `שלב ${g.stage}`);
  assert(g.me.retired && g.me.clubId === null, "מנג'ר לא אמור להיות בסגל");
  assert(g.myClub() && g.myClub().managerName === "דני מנג'ר", "לא מונה למועדון");
  assert(g.me.coaching > 20, "בלי ידע אימון");
  g.setAction("tactics");
  const r = g.advanceWeek();
  assert(g.week === 2, "השבוע לא התקדם");
  assert(r.match || r.notes.length, "לא קרה כלום בשבוע");
});

test("קריירה שמתחילה בגיל 13 עוברת דרך שלב הנוער", () => {
  const g = A.Game.newGame("ילד מהשכונה", "ST", "hapoel_carmel", 13, 77);
  assert(g.stage === "youth", `שלב פתיחה ${g.stage}`);
  assert(g.me.contract.wage === 0, "ילד בן 13 לא מקבל שכר");
  const startOverall = A.overall(g.me);
  assert(g.me.potential > startOverall + 15, "אין מספיק לאן לגדול");

  let youthMatches = 0, seasons = 0;
  while (seasons < 4) {
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    g.setAction(g.availableActions()[0][0]);
    const r = g.advanceWeek();
    if (r.youth) {
      youthMatches++;
      assert(r.youth.rival && r.youth.rating >= 3, "משחק נוער לא תקין");
    }
    if (r.seasonEnded) seasons++;
    if (g.stage !== "youth") break;
  }
  assert(youthMatches > 10, `רק ${youthMatches} משחקי נוער`);
  assert(g.me.age === 16, `הגיל בזמן המעבר: ${g.me.age}`);
  assert(g.stage === "academy", `השלב אחרי הנוער: ${g.stage}`);
  assert(g.me.contract.wage > 0, "אין חוזה ראשון");
  assert(A.overall(g.me) > startOverall, "לא התפתח בשנות הנוער");
});

test("הליגה הבוגרת ממשיכה לרוץ בזמן שנות הנוער", () => {
  const g = A.Game.newGame("ילד", "ST", "hapoel_carmel", 13, 42);
  let summary = null;
  while (!summary) {
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    g.setAction("shooting");
    const r = g.advanceWeek();
    if (r.seasonEnded) summary = r.seasonSummary;
  }
  const champion = summary.lines.find(l => l.text.includes("אלוף ליגת העל"));
  assert(champion, "אין אלוף");
  const points = parseInt(champion.text.match(/\((\d+) נק/)[1], 10);
  assert(points > 30, `האלוף סיים עם ${points} נקודות — הליגה לא שוחקה`);
  const scorer = summary.lines.find(l => l.text.includes("מלך השערים"));
  assert(scorer && !scorer.text.includes("ילד"), "ילד בן 13 לא אמור להיות מלך השערים של ליגת העל");
});

test("טבלת הליגה מסתדרת חשבונית", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 17, 33);
  for (let i = 0; i < 8; i++) {
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    g.setAction("rest"); g.advanceWeek();
  }
  for (const lid of ["top", "national"]) {
    const rows = g.standings(lid);
    const gf = rows.reduce((s, r) => s + r.gf, 0), ga = rows.reduce((s, r) => s + r.ga, 0);
    assert(gf === ga, `${lid}: שערים ${gf} מול ${ga}`);
    for (const r of rows) {
      assert(r.played === r.won + r.drawn + r.lost, "משחקים");
      assert(r.points === r.won * 3 + r.drawn, "נקודות");
    }
  }
});

test("עונה מתגלגלת ומאפסת טבלאות", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 17, 34);
  const year = g.year;
  for (let i = 0; i < 200; i++) {
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    g.setAction("shooting");
    if (g.advanceWeek().seasonEnded) break;
  }
  assert(g.year === year + 1, "השנה לא התקדמה");
  assert(g.week === 1, "השבוע לא אופס");
  assert(g.history.length === 1, "אין רישום עונה");
  assert(g.standings("top").every(r => r.played === 0), "הטבלה לא אופסה");
  assert(Object.values(g.clubs).filter(c => c.leagueId === "top").length === 20, "20 בליגת העל");
});

test("שמירה וטעינה משחזרות את המצב ואת ההגרלה", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 17, 41);
  for (let i = 0; i < 6; i++) {
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    g.setAction("passing"); g.advanceWeek();
  }
  const copy = A.Game.fromJSON(JSON.parse(JSON.stringify(g.toJSON())));
  assert(copy.week === g.week && copy.year === g.year, "שבוע/שנה");
  assert(copy.money === g.money, "כסף");
  assert(JSON.stringify(copy.me.attributes) === JSON.stringify(g.me.attributes), "תכונות");
  for (const state of [g, copy]) {
    if (state.pendingEventId) state.resolveEvent(0);
    state.setAction("passing"); state.advanceWeek();
  }
  assert(copy.money === g.money && A.overall(copy.me) === A.overall(g.me),
    "ההמשך אחרי טעינה שונה מהמקור");
});

test("קריירה ארוכה רצה עד הסוף בלי שגיאות", () => {
  for (const seed of [101, 202]) {
    const g = A.Game.newGame("מרתון לוי", "ST", "hapoel_ayalon", 17, seed);
    const rng = new A.Rng(seed);
    let picks = 0, seasons = 0;
    while (!g.gameOver && seasons < 25) {
      if (g.pendingEventId) {
        assert(g.pendingEventText(), "טקסט אירוע ריק");
        g.resolveEvent(picks++ % g.pendingEvent().choices.length);
        continue;
      }
      g.setAction(rng.choice(g.availableActions().map(a => a[0])));
      const r = g.advanceWeek();
      if (r.match) {
        const goals = r.match.result.events.filter(e => e.kind === "goal").length;
        assert(goals === r.match.result.homeGoals + r.match.result.awayGoals,
          "אי-התאמה בין התוצאה לשערים");
        assert(r.match.result.commentary[0], "אין פרשנות");
      }
      if (r.seasonEnded) {
        seasons++;
        for (const club of Object.values(g.clubs))
          assert(club.squad.length >= 16, `סגל קטן מדי: ${club.name}`);
      }
    }
    assert(picks >= 12, `רק ${picks} החלטות עלילה`);
    assert(g.history.length === seasons, "רישום העונות");
  }
});

test("שליש מהעלילה לפחות נורה בקריירות שונות", () => {
  const fired = new Set();
  for (const seed of [11, 22, 33]) {
    const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 17, seed);
    const rng = new A.Rng(seed);
    let picks = 0;
    for (let i = 0; i < 26 * 22 && !g.gameOver; i++) {
      if (g.pendingEventId) { g.resolveEvent(picks++ % g.pendingEvent().choices.length); continue; }
      g.setAction(rng.choice(g.availableActions().map(a => a[0])));
      g.advanceWeek();
    }
    g.firedEvents.forEach(e => fired.add(e));
  }
  assert(fired.size >= Math.floor(A.STORY.length / 3),
    `רק ${fired.size} אירועים מתוך ${A.STORY.length}`);
});


// ---------------------------------------------------------------------------
// שורת הסטטיסטיקה: החוט בין האימון למגרש
// ---------------------------------------------------------------------------

function striker(rng, overrides) {
  const p = A.generatePlayer(rng, null, "ST", { age: 24, quality: 65 });
  for (const attr of A.D.ATTRIBUTES) p.attributes[attr] = 60;
  Object.assign(p.attributes, overrides || {});
  p.fitness = 90; p.sharpness = 85;
  return p;
}

function meanStats(player, rng, n = 250) {
  const totals = {};
  for (let i = 0; i < n; i++) {
    const stats = A.matchStatLine(player, 90, 0, 0, rng);
    for (const key in stats)
      if (typeof stats[key] === "number") totals[key] = (totals[key] || 0) + stats[key];
  }
  for (const key in totals) totals[key] /= n;
  return totals;
}

test("אימון נראה במגרש", () => {
  const rng = new A.Rng(11);
  const weak = meanStats(striker(rng, { shooting: 45 }), rng);
  const strong = meanStats(striker(rng, { shooting: 90 }), rng);
  assert(strong.on_target > weak.on_target * 1.5,
    `בעיטה 45→90 העלתה למסגרת רק מ-${weak.on_target.toFixed(2)} ל-${strong.on_target.toFixed(2)}`);
  const sloppy = meanStats(striker(rng, { passing: 40 }), rng);
  const tidy = meanStats(striker(rng, { passing: 88 }), rng);
  assert(tidy.pass_pct > sloppy.pass_pct + 8, "אחוז המסירה לא הגיב לאימון");
  assert(tidy.losses < sloppy.losses, "איבודי הכדור לא ירדו");
});

test("ציון המשחק ממורכז על הרמה של השחקן עצמו", () => {
  const rng = new A.Rng(5);
  for (const position of ["ST", "CM", "CB", "LW", "GK"]) {
    for (const level of [45, 85]) {
      const p = A.generatePlayer(rng, null, position, { age: 24, quality: level });
      for (const attr of A.D.ATTRIBUTES) p.attributes[attr] = level;
      p.fitness = 88; p.sharpness = 80;
      let sum = 0;
      for (let i = 0; i < 120; i++)
        sum += A.matchPerformance(A.matchStatLine(p, 90, 0, 0, rng), position);
      const mean = sum / 120;
      assert(mean >= 55 && mean <= 80, `${position}/${level}: ממוצע ${mean.toFixed(1)}`);
    }
  }
});

test("המאמן מבקש מחלוץ משהו שחלוץ באמת עושה", () => {
  const rng = new A.Rng(7);
  const p = striker(rng);
  const asks = {};
  for (let i = 0; i < 300; i++) {
    const area = A.weakestArea(A.matchStatLine(p, 90, 0, 0, rng), "ST", p.attributes);
    asks[area] = (asks[area] || 0) + 1;
  }
  assert((asks.defending || 0) <= 15, `דרש הגנה ${asks.defending} פעמים`);
  for (const key in asks) assert(A.D.ATTRIBUTES.includes(key), `תחום לא מוכר: ${key}`);
});

test("מנוחה היא לא ברירת המחדל של המאמן", () => {
  const counts = {};
  for (const seed of [11, 24]) {
    const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 18, seed);
    for (let i = 0; i < 260; i++) {
      if (g.gameOver || g.me.age > 22) break;
      if (g.pendingEventId) { g.resolveEvent(0); continue; }
      g.advanceWeek();
      const focus = g.flag("directive");
      if (focus) counts[focus] = (counts[focus] || 0) + 1;
    }
  }
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  assert(total > 100, `רק ${total} הוראות`);
  const top = Object.keys(counts).reduce((a, b) => counts[a] >= counts[b] ? a : b);
  assert(top !== "rest", `מנוחה היא עדיין ההוראה הנפוצה ביותר (${JSON.stringify(counts)})`);
  // כמה מנוחה תידרש תלוי גם במאמן הכושר של המועדון — אבל לא רוב השבועות
  assert((counts.rest || 0) / total < 0.30,
    `מנוחה נדרשה ב-${counts.rest}/${total} מהשבועות`);
});

test("ההוראה מצטטת את המשחק האחרון", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 22, 6);
  for (let i = 0; i < 80; i++) {
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    g.advanceWeek();
    if (g.flags.last_stats && g.flag("directive")) break;
  }
  assert(g.flags.last_stats, "לא נשמרה שורת סטטיסטיקה");
  const line = A.directiveLine(g.myClub(), g.flag("directive"), g.flags.last_stats);
  assert(line.includes("\n"), "ההוראה לא כוללת סיבה מהמשחק");
  assert(!line.includes("{"), "מקום שלא מולא בהוראה");
});

test("הכושר לא קורס לאורך עונה", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 22, 9);
  const readings = [];
  for (let i = 0; i < 120; i++) {
    if (g.gameOver) break;
    if (g.pendingEventId) { g.resolveEvent(0); continue; }
    g.advanceWeek();
    readings.push(g.me.fitness);
  }
  const mean = readings.reduce((a, b) => a + b, 0) / readings.length;
  assert(mean > 70, `כושר ממוצע ${Math.round(mean)} — הגוף לא מתאושש`);
  assert(Math.min(...readings) < 95, "הכושר לא זז בכלל — אין מחיר לעומס");
});

// ---------------------------------------------------------------------------
// סקאוטינג
// ---------------------------------------------------------------------------

test("צופים בונים עניין לאורך עונה", () => {
  let found = 0;
  for (const seed of [8, 21, 33, 44]) {
    const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 19, seed);
    for (let i = 0; i < 300; i++) {
      if (g.gameOver || g.me.age > 25) break;
      if (g.pendingEventId) { g.resolveEvent(0); continue; }
      g.advanceWeek();
    }
    if (A.watchers(g).length) found++;
  }
  assert(found >= 3, `רק ${found} מתוך 4 קריירות משכו צופים`);
});

test("הסקאוטינג מגיע גם מחוץ לישראל", () => {
  let abroad = false;
  for (const seed of [33, 44, 52, 61]) {
    const g = A.Game.newGame("בודק", "ST", "maccabi_harel", 20, seed);
    for (let i = 0; i < 320; i++) {
      if (g.gameOver || g.me.age > 27) break;
      if (g.pendingEventId) { g.resolveEvent(0); continue; }
      g.advanceWeek();
    }
    for (const [club] of A.watchers(g))
      if (A.clubCountry(club.cid) !== "ישראל") abroad = true;
  }
  assert(abroad, 'אף מועדון מחו"ל לא עקב אחרי אף אחת מהקריירות');
});

test("קבוצה קטנה לא רודפת אחרי כוכב", () => {
  const g = A.Game.newGame("בודק", "ST", "maccabi_harel", 26, 4);
  for (const attr of A.D.ATTRIBUTES) g.me.attributes[attr] = 88;
  const pool = A.candidateClubs(g);
  assert(pool.length, "אין בכלל יעדים");
  for (const club of pool)
    assert(club.reputation >= A.overall(g.me) - 24, `${club.name} קטן מדי`);
});

test("עניין נשחק כשאף אחד לא צופה", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 24, 2);
  A.interestMap(g).real_castilla = 60;
  for (let i = 0; i < 40; i++) A.scoutsThisWeek(g, g.rng, null);
  assert((A.interestMap(g).real_castilla || 0) < 55, "העניין לא נשחק");
});

// ---------------------------------------------------------------------------
// מסלול הפיתוח
// ---------------------------------------------------------------------------

test("לכל עמדה יש מסלול", () => {
  for (const position of A.D.POSITIONS) {
    const options = A.planOptionsFor(position);
    assert(options.length, position);
    for (const row of options)
      assert(row[4].length >= 3, `${row[0]}: פחות משלוש אבני דרך`);
  }
});

test("המסלול אומר מה חסר", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 15, 3);
  assert(A.nextTarget(g) === null, "יש יעד בלי מסלול");
  A.setPlan(g, "poacher");
  const target = A.nextTarget(g);
  assert(target && target.includes("🎯"), "אין יעד אחרי בחירת מסלול");
  assert(A.D.ATTRIBUTES.includes(A.recommendedFocus(g)), "המלצת אימון לא תקינה");
});

test("אבני דרך משלמות, ומסלול מלא נותן פריצה", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 24, 3);
  A.setPlan(g, "poacher");
  g.me.ceiling = 99; g.me.potential = 60;
  for (const attr of A.D.ATTRIBUTES) g.me.attributes[attr] = 90;
  const before = g.me.potential;
  const lines = A.claimMilestones(g);
  assert(lines.length >= 5, `רק ${lines.length} שורות`);
  assert(lines.some(l => l.includes("💎")), "בלי פריצה");
  assert(g.me.potential > before, "הפוטנציאל לא זז");
  assert(g.flag("breakthrough") === true, "דגל הפריצה לא נדלק");
  assert(g.me.traits.includes("clutch"), "לא ניתנה תכונת אופי");
  assert(A.claimMilestones(g).length === 0, "שולם פעמיים");
});

test("החלפת מסלול מאפסת את ההתקדמות", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 20, 3);
  A.setPlan(g, "poacher");
  g.flags.plan_done = [0, 1];
  A.setPlan(g, "target_man");
  assert(g.flags.plan_done.length === 0, "ההתקדמות לא אופסה");
});

test("אבן דרך לא דוחפת פוטנציאל מעל התקרה", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 24, 3);
  A.setPlan(g, "poacher");
  g.me.ceiling = 70; g.me.potential = 69;
  for (const attr of A.D.ATTRIBUTES) g.me.attributes[attr] = 92;
  A.claimMilestones(g);
  assert(g.me.potential <= g.me.ceiling, "הפוטנציאל עבר את התקרה");
});

// ---------------------------------------------------------------------------
// חסויות כתיק, לא כתשלום חד־פעמי
// ---------------------------------------------------------------------------

test("חוזה חסות ממשיך לשלם כל שבוע", () => {
  const rng = new A.Rng(2);
  const p = A.generatePlayer(rng, null, "ST", { age: 26, quality: 82 });
  p.reputation = 78; p.mediaSkill = 65;
  const offer = A.sponsorOffer(p, rng, 80, false, 2);
  assert(offer && offer.annual > 0, "אין הצעה");
  const portfolio = [];
  A.signDeal(portfolio, offer, 2030);
  const weekly = A.weeklyRetainer(portfolio, 43);
  assert(weekly > 0, "אין תשלום שבועי");
  assert(Math.abs(weekly * 43 - offer.annual) < offer.annual * 0.05, "התשלום לא מסתדר");
});

test("סעיפי בונוס משלמים על עונה אמיתית", () => {
  const rng = new A.Rng(2);
  const p = A.generatePlayer(rng, null, "ST", { age: 26, quality: 82 });
  const portfolio = [];
  const deal = A.signDeal(portfolio, {
    brand: "מותג", tier: "global", tierHe: "עולמי", kindHe: "נעליים",
    annual: 1000000, years: 3, clauses: ["per_goal", "trophy"] }, 2030);
  assert(A.seasonBonuses(portfolio, p, 0, 0).length === 0, "שילם בלי סיבה");
  p.season.goals = 20;
  const payouts = A.seasonBonuses(portfolio, p, 1, 0);
  assert(payouts.length === 2, `${payouts.length} תשלומים`);
  assert(payouts.reduce((a, x) => a + x[1], 0) > 800000, "בונוס זעום");
  assert(deal.earned > 0, "לא נרשם לחוזה");
});

test("חוזה נגמר, והחידוש משקף את מי שנעשית", () => {
  const rng = new A.Rng(2);
  const p = A.generatePlayer(rng, null, "ST", { age: 27, quality: 88 });
  p.reputation = 90; p.mediaSkill = 80;
  const portfolio = [];
  A.signDeal(portfolio, { brand: "מותג", tier: "national", tierHe: "ארצי",
    kindHe: "ביגוד", annual: 200000, years: 2, clauses: [] }, 2030);
  assert(A.tickPortfolio(portfolio).length === 0, "נמחק מוקדם");
  assert(portfolio[0].yearsLeft === 1, "השנים לא ירדו");
  const renewal = A.renewalOffer(portfolio[0], p, rng, 85);
  assert(renewal.annual > 200000, "החידוש לא משקף כוכב");
  assert(A.tickPortfolio(portfolio).length === 1 && portfolio.length === 0, "לא פג");
});

test("מותגים גדולים נפתחים לקריירה גדולה", () => {
  const rng = new A.Rng(2);
  const kid = A.generatePlayer(rng, null, "ST", { age: 17, quality: 55 });
  kid.reputation = 18; kid.mediaSkill = 10;
  const star = A.generatePlayer(rng, null, "ST", { age: 27, quality: 90 });
  star.reputation = 88; star.mediaSkill = 75; star.career.goals = 180;
  const kidTiers = A.D.SPONSOR_TIERS.filter(t => A.marketability(kid, 40) >= t[2]);
  const starTiers = A.D.SPONSOR_TIERS.filter(t => A.marketability(star, 90) >= t[2]);
  assert(kidTiers.length === 1 && kidTiers[0][0] === "local", "לנער נפתח יותר מדי");
  assert(starTiers.some(t => t[0] === "global"), "לכוכב לא נפתח דרג עולמי");
});

test("כסף מחסויות באמת מגיע לבנק", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 25, 5);
  g.deals().push({ brand: "מותג", tier: "global", tierHe: "עולמי", kindHe: "נעליים",
    annual: 4300000, yearsLeft: 3, clauses: [], signed: g.year, earned: 0 });
  const before = g.money;
  g.advanceWeek();
  assert(g.money > before + 40000, "התיק המסחרי לא שילם השבוע");
});

// ---------------------------------------------------------------------------
// נכסים והשקעות
// ---------------------------------------------------------------------------

test("אי אפשר לקנות מה שאין עליו כסף או מוניטין", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 20, 5);
  g.money = 2000000; g.me.reputation = 10;
  assert(A.buyAsset(g, "club_shares").includes("מוניטין"), "נמכר בלי מוניטין");
  g.me.reputation = 95;
  assert(A.buyAsset(g, "club_shares").includes("אין מספיק"), "נמכר בלי כסף");
  assert(A.holdings(g).length === 0, "נרשם נכס שלא נקנה");
  assert(A.buyAsset(g, "studio_flat").includes("קנית"), "לא נקנה");
  assert(g.money < 2000000, "הכסף לא ירד");
  assert(A.holdings(g).length === 1, "הנכס לא נרשם");
});

test("נכסים משלמים תשואה, ואפשר למכור אותם", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 26, 5);
  g.money = 20000000; g.me.reputation = 60;
  A.buyAsset(g, "padel");
  assert(A.portfolioYield(g) > 0, "אין תשואה");
  const before = A.netWorth(g);
  const lines = A.assetsSeasonTick(g, g.rng);
  assert(lines.length, "עונה שלמה בלי שום תנועה בנכסים");
  assert(A.netWorth(g) !== before, "השווי לא זז");
  const cash = g.money;
  assert(A.sellAsset(g, 0).includes("מכרת"), "לא נמכר");
  assert(g.money > cash, "הכסף לא חזר");
  assert(A.holdings(g).length === 0, "הנכס נשאר");
});

test("שווי נטו סופר מזומן ונכסים", () => {
  const g = A.Game.newGame("בודק", "ST", "hapoel_carmel", 26, 5);
  g.money = 10000000; g.me.reputation = 60;
  A.buyAsset(g, "restaurant");
  const info = A.wealthSummary(g);
  assert(info.net_worth === info.cash + info.assets, "החשבון לא מסתדר");
  assert(info.assets === 5000000, `שווי ${info.assets}`);
  assert(info.count === 1, "מספר נכסים");
});

test("מס משאיר פחות מהברוטו, ובמדרגות", () => {
  assert(A.netIncome(0) === 0, "מס על אפס");
  assert(A.netIncome(2000) < 2000 && A.netIncome(2000) > 0, "נטו לא הגיוני");
  assert(A.netIncome(2000) / 2000 > A.netIncome(200000) / 200000, "המדרגות לא פרוגרסיביות");
});

console.log(`\n${passed} עברו, ${failed} נכשלו\n`);
process.exit(failed ? 1 : 0);
