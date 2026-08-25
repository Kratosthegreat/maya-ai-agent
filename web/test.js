// ---------------------------------------------------------------------------
// בדיקות לגרסת הווב. הרצה:  node web/test.js
// טוען את קבצי המשחק (בלי ה-UI) ומריץ עליהם בדיקות שפיות ואיזון.
// ---------------------------------------------------------------------------

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const HERE = __dirname;
const PARTS = ["data.js", "art.js", "save.js", "engine.js", "clubops.js", "commercial.js", "manager.js",
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
  "managerStyle, postMatchLine, selectionNote, weeklyDirective, STORY };", ctx);
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

console.log(`\n${passed} עברו, ${failed} נכשלו\n`);
process.exit(failed ? 1 : 0);
