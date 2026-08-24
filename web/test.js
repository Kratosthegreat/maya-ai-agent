// ---------------------------------------------------------------------------
// בדיקות לגרסת הווב. הרצה:  node web/test.js
// טוען את קבצי המשחק (בלי ה-UI) ומריץ עליהם בדיקות שפיות ואיזון.
// ---------------------------------------------------------------------------

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const HERE = __dirname;
const PARTS = ["data.js", "engine.js", "story.js", "game.js", "graphics.js", "scenes.js"];
const source = PARTS.map(f => fs.readFileSync(path.join(HERE, f), "utf8")).join("\n");
const ctx = vm.createContext({ console, Math, JSON, Date });
vm.runInContext(source + "\nthis.API = { D, Rng, Game, STORY, generateWorld, generatePlayer, " +
  "simulateMatch, pickLineup, teamStrength, roundRobin, overall, playerValue, " +
  "wageForOverall, positionFit, avgRating, weeklyTraining, endOfSeasonDevelopment, fmt, " +
  "SCENES, sceneFor, crest, kit, playerCard, pitch, goalTimeline, formGuide };", ctx);
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
  const teams = Array.from({ length: 12 }, (_, i) => "t" + i);
  const rounds = A.roundRobin(teams, new A.Rng(1));
  assert(rounds.length === 22, `${rounds.length} מחזורים`);
  const seen = {};
  for (const rnd of rounds) {
    assert(rnd.length === 6, "משחקים במחזור");
    const inRound = new Set(rnd.flat());
    assert(inRound.size === 12, "כל קבוצה פעם אחת במחזור");
    for (const [h, a] of rnd) seen[h + ">" + a] = (seen[h + ">" + a] || 0) + 1;
  }
  assert(Object.keys(seen).length === 132, "כל הצמדים");
  assert(Object.values(seen).every(v => v === 1), "בלי כפילויות");
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

test("כל הסצנות מייצרות SVG תקין", () => {
  const names = Object.keys(A.SCENES);
  assert(names.length >= 10, `רק ${names.length} סצנות`);
  for (const name of names) {
    const svg = A.SCENES[name]();
    assert(svg.startsWith("<svg") && svg.trim().endsWith("</svg>"), `${name}: לא SVG`);
    assert(!svg.includes("undefined") && !svg.includes("NaN"), `${name}: ערך חסר`);
    assert((svg.match(/</g) || []).length === (svg.match(/>/g) || []).length,
      `${name}: תגיות לא מאוזנות`);
  }
});

test("לכל אירוע עלילה יש סצנה", () => {
  for (const event of A.STORY) {
    const svg = A.sceneFor(event.eid, event.stages[0] || "player");
    assert(svg.startsWith("<svg"), `${event.eid}: אין סצנה`);
  }
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
  const club = g.myClub();
  const lineup = A.pickLineup(club, g.players, club.formation);
  const svg = A.pitch(lineup, club.formation, g.players, g.meId, club);
  assert(svg.includes("<svg") && !svg.includes("NaN"), "מגרש");
});

console.log("\nמצב המשחק");

test("משחק חדש מציב את השחקן בסגל", () => {
  const g = A.Game.newGame("עומר לוי", "ST", "hapoel_carmel", 17, 31);
  assert(g.me.name === "עומר לוי", "שם");
  assert(g.myClub().squad.includes(g.meId), "לא בסגל");
  assert(g.stage === "academy", "שלב פתיחה");
  assert(A.overall(g.me) < g.me.potential, "אין לאן להתפתח");
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
  assert(Object.values(g.clubs).filter(c => c.leagueId === "top").length === 12, "12 בליגת העל");
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
