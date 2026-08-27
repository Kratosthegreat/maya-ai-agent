// ---------------------------------------------------------------------------
// מצב המשחק — פורט מ-football_manager/game.py
// ---------------------------------------------------------------------------

function fmt(n) { return Math.round(n).toLocaleString("en-US"); }

/**
 * מה שנשאר ביד אחרי מס ועמלת סוכן.
 * בלי זה הכסף רק נערם: אחרי עשור בשכר של מקצוען אין שום החלטה
 * כלכלית שבאמת עולה משהו. המדרגות פרוגרסיביות, כמו במציאות.
 */
function netIncome(gross) {
  if (gross <= 0) return 0;
  let rate;
  if (gross <= 3000) rate = 0.14;
  else if (gross <= 20000) rate = 0.28;
  else if (gross <= 80000) rate = 0.39;
  else rate = 0.47;
  rate += 0.05;                      // עמלת הסוכן, גם היא יורדת מהברוטו
  return Math.round(gross * (1 - rate));
}

// בן 13 מתאמן שלוש פעמים בשבוע ועוד הולך לבית ספר — לא עומס של מקצוען
const YOUTH_LOAD = 0.52;

// כמה שינויי דירוג נשמרים לגרף. 200 מכסים כמה עונות של עלייה רצופה,
// והם עולים בשמורה פחות מקילובייט.
const OVERALL_LOG_LIMIT = 200;

class Game {
  constructor() {
    this.seed = 0;
    this.clubs = {}; this.players = {};
    this.meId = ""; this.stage = "youth";
    this.year = 2026; this.week = 1;
    this.fixtures = {}; this.tables = {}; this.cup = {};
    this.money = 0; this.flags = {}; this.honours = []; this.news = [];
    this.firedEvents = []; this.pendingEventId = null; this.pendingEventBody = null;
    this.managedClubId = null;
    this.tactics = { mentality: "balanced", pressing: "medium", formation: "4-3-3", talkBoost: 0 };
    this.trainingFocus = "shooting"; this.intensity = 1.0;
    this.firstClubId = null; this.lastClubId = null;
    this.history = []; this.caps = 0; this.intlGoals = 0;
    this.noStartStreak = 0; this.gameOver = false;
    this.positionLog = [];
    // יומן הדירוג השבועי. הוא קיים רק כאן ולא במנוע הפייתון — כמו
    // `positionLog`, זה יומן תצוגה: הגרף במסך הבית צריך קו, ובלי
    // רישום שבועי הדירוג נראה שטוח עד סוף העונה הראשונה.
    this.overallLog = [];
    this.rng = new Rng(1);
  }

  get me() { return this.players[this.meId]; }

  myClub() {
    if (["manager", "coach", "director", "owner"].includes(this.stage) && this.managedClubId)
      return this.clubs[this.managedClubId] || null;
    return this.me.clubId ? (this.clubs[this.me.clubId] || null) : null;
  }
  myLeague() { const c = this.myClub(); return c ? c.leagueId : null; }
  flag(name, dflt = null) { return name in this.flags ? this.flags[name] : dflt; }
  setFlag(name, value = true) { this.flags[name] = value; }
  log(text) {
    if (!text) return;
    this.news.push(`[${this.year}/ש${this.week}] ${text}`);
    if (this.news.length > 120) this.news = this.news.slice(-120);
  }
  recordHonour(text) {
    this.honours.push(`${this.year}: ${text}`);
    this.me.career.trophies += 1;
    this.log(`🏆 ${text}`);
    return text;
  }
  earn(amount) { this.money += Math.round(amount); return this.money; }
  spend(amount) { this.money = Math.max(0, this.money - Math.round(amount)); return this.money; }

  // ==================================================================
  // משחק חדש
  // ==================================================================

  /** השלב שמתאים לגיל שבו מתחילים. */
  static stageForAge(age) {
    if (age <= 15) return "youth";
    if (age <= 17) return "academy";
    if (age <= 30) return "player";
    return "veteran";
  }

  static newGame(name, position, clubId, age = 15, seed = null, role = "player",
                 identity = null) {
    const g = new Game();
    g.seed = seed ?? Math.floor(Math.random() * 100000000) + 1;
    g.rng = new Rng(g.seed);
    const world = generateWorld(g.seed);
    g.clubs = world.clubs; g.players = world.players;
    const club = g.clubs[clubId];

    if (role === "manager") return g.startAsManager(name, club, age, identity);

    // ככל שמתחילים מבוגר יותר, מתחילים כשחקן מגובש יותר
    const quality = age <= 17
      ? Math.round(clamp(club.reputation * 0.55 + 24, 48, 70))
      : Math.round(clamp(club.reputation * 0.66 + 12 + Math.min(8, (age - 17) * 1.4), 42, 82));
    const me = generatePlayer(g.rng, club, position, { age, quality });
    me.name = name;
    me.isHuman = true;
    if (identity && identity.foot) me.foot = identity.foot;
    // מי שמתחיל צעיר יותר — יש לו יותר לאן לגדול.
    // התקרה נסתרת ורחבה; מה שמוצג הוא הערכה שתתעדכן לפי הביצועים.
    me.ceiling = Math.round(clamp(
      overall(me) + g.rng.randint(14, 34) + Math.max(0, 24 - age) * 1.9,
      overall(me) + 6, 95));
    me.potential = Math.round(clamp(
      overall(me) + (me.ceiling - overall(me)) * 0.45,
      overall(me) + 2, me.ceiling));
    me.clubId = clubId;
    // חוזה שמתאים לגיל ולרמה
    if (age <= 15) me.contract = { wage: 0, yearsLeft: 0 };
    else if (age <= 17)
      me.contract = { wage: Math.max(2500, Math.round(wageForOverall(overall(me)) / 2)),
                      yearsLeft: 3 };
    else
      me.contract = { wage: wageForOverall(overall(me)), yearsLeft: g.rng.randint(2, 4) };

    me.morale = 70;
    me.reputation = age <= 15 ? 3 : age <= 17 ? 8
      : clamp(overall(me) - 28 + (age - 18) * 1.2, 5, 70);

    // מי שמתחיל אחרי גיל 18 — כבר יש לו עבר
    if (age >= 19) {
      const seasons = Math.min(12, age - 17);
      me.career.apps = Math.round(seasons * g.rng.uniform(14, 26));
      const share = D.POSITION_ROLE_SHARE[position].att;
      me.career.goals = Math.round(me.career.apps * share * g.rng.uniform(0.10, 0.34));
      me.career.assists = Math.round(me.career.apps * g.rng.uniform(0.04, 0.13));
      me.career.minutes = me.career.apps * 78;
      me.career.ratingSum = me.career.apps * g.rng.uniform(6.3, 7.0);
      me.coaching = clamp(me.coaching + (age - 18) * 1.1, 0, 60);
    }
    me.traits = [identity && D.TRAITS[identity.trait]
      ? identity.trait : g.rng.choice(Object.keys(D.TRAITS))];
    g.players[me.pid] = me;
    club.squad.push(me.pid);
    const wantedNumber = identity && identity.number;
    assignNumber(club, g.players, me, wantedNumber);
    if (wantedNumber && me.number !== wantedNumber) {
      const owner = club.squad.map(pid => g.players[pid])
        .find(p => p && p.pid !== me.pid && p.number === wantedNumber);
      g.log(owner
        ? `מספר ${wantedNumber} תפוס אצל ${owner.name}. קיבלת את ${me.number}.`
        : `מספר ${wantedNumber} לא היה פנוי. קיבלת את ${me.number}.`);
    }
    g.meId = me.pid;
    g.firstClubId = clubId; g.lastClubId = clubId;
    g.stage = Game.stageForAge(age);
    club.managerTrust = age <= 17 ? 45 : clamp(35 + (overall(me) - 55) * 1.4, 25, 78);

    g.startYear = g.year;
    g.startSeason();
    g.logOverall();                    // נקודת הפתיחה של גרף ההתפתחות
    g.log(`התחלת את הדרך ב${club.name}.`);
    return g;
  }

  /** קריירה שמתחילה מהספסל: מנג'ר ראשי, בלי עבר כשחקן פעיל. */
  startAsManager(name, club, age, identity) {
    const me = generatePlayer(this.rng, club, "CM", { age: Math.min(age, 40), quality: 55 });
    me.name = name;
    me.isHuman = true;
    if (identity && identity.foot) me.foot = identity.foot;
    if (identity && D.TRAITS[identity.trait]) me.traits = [identity.trait];
    me.age = age;
    me.retired = true;
    me.clubId = null;
    me.contract = { wage: 0, yearsLeft: 0 };
    me.coaching = clamp(28 + (age - 32) * 1.9 + this.rng.uniform(0, 12), 20, 92);
    me.badges = Math.min(4, Math.floor(me.coaching / 22));
    me.mediaSkill = clamp(15 + (age - 32) * 0.9, 5, 70);
    me.business = clamp(10 + (age - 32) * 0.8, 5, 60);
    me.reputation = clamp(12 + (age - 32) * 1.1, 5, 60);
    if (this.rng.random() < 0.65) {          // עבר כשחקן — לא לכל מנג'ר יש
      me.career.apps = this.rng.randint(60, 380);
      me.career.goals = Math.round(me.career.apps * this.rng.uniform(0.02, 0.22));
      me.career.assists = Math.round(me.career.apps * this.rng.uniform(0.03, 0.12));
      me.career.ratingSum = me.career.apps * this.rng.uniform(6.2, 6.9);
    }
    this.players[me.pid] = me;
    this.meId = me.pid;

    this.stage = "manager";
    this.managedClubId = club.cid;
    this.firstClubId = club.cid;
    this.lastClubId = club.cid;
    club.managerName = name;
    club.boardConfidence = 58;
    this.tactics.formation = club.formation;
    this.trainingFocus = "tactics";
    this.startYear = this.year;
    this.startSeason();
    this.log(`מונית למנג'ר של ${club.name}.`);
    return this;
  }

  // ==================================================================
  // עונה
  // ==================================================================

  startSeason() {
    this.week = 1;
    this.positionLog = [];
    this.refreshStaffMarket();
    for (const club of Object.values(this.clubs)) club.formLog = [];
    this.fixtures = {}; this.tables = {};
    for (const league of D.LEAGUES) {
      const lid = league.id;
      const clubIds = Object.values(this.clubs).filter(c => c.leagueId === lid).map(c => c.cid);
      this.fixtures[lid] = roundRobin(clubIds, this.rng);
      this.tables[lid] = {};
      for (const cid of clubIds)
        this.tables[lid][cid] = { clubId: cid, played: 0, won: 0, drawn: 0, lost: 0, gf: 0, ga: 0 };
    }
    this.buildCup();
    if (this.year > (this.startYear || 0)) {
      const note = this.refreshRole();
      if (note) this.log(note);
    }
    for (const club of Object.values(this.clubs)) club.seasonExpectation = this.expectation(club);
  }

  buildCup() {
    const top = Object.values(this.clubs).filter(c => c.leagueId === "top").map(c => c.cid);
    const national = Object.values(this.clubs).filter(c => c.leagueId === "national")
      .sort((a, b) => b.reputation - a.reputation).slice(0, 12).map(c => c.cid);
    const teams = this.rng.shuffle(top.concat(national)).slice(0, 32);
    this.cup = { teams, round: "שלב 32 האחרונות", winner: null, log: [] };
  }

  expectation(club) {
    const peers = Object.values(this.clubs).filter(c => c.leagueId === club.leagueId)
      .sort((a, b) => b.reputation - a.reputation);
    const rank = peers.findIndex(c => c.cid === club.cid) + 1;
    if (rank <= 2) return "אליפות";
    if (rank <= 4) return "מקום באירופה";
    if (rank <= peers.length - 3) return "אמצע טבלה";
    return "הישרדות";
  }

  leagueRoundForWeek(leagueId, week) {
    if (CUP_WEEKS[week]) return null;
    const weeks = leagueWeeks();
    const idx = weeks.indexOf(week);
    if (idx < 0) return null;
    const rounds = this.fixtures[leagueId] || [];
    return idx < rounds.length ? idx : null;
  }

  myFixture(week) {
    week = week || this.week;
    const club = this.myClub();
    if (!club) return null;
    if (CUP_WEEKS[week]) return this.cupFixtureFor(club.cid);
    const rnd = this.leagueRoundForWeek(club.leagueId, week);
    if (rnd === null) return null;
    for (const [home, away] of this.fixtures[club.leagueId][rnd])
      if (home === club.cid || away === club.cid) return [home, away];
    return null;
  }

  cupFixtureFor(cid) {
    const teams = this.cup.teams || [];
    const idx = teams.indexOf(cid);
    if (idx < 0) return null;
    const start = idx - (idx % 2);
    if (start + 1 >= teams.length) return null;
    return [teams[start], teams[start + 1]];
  }

  standings(leagueId) {
    const rows = Object.values(this.tables[leagueId] || {});
    rows.forEach(r => { r.points = r.won * 3 + r.drawn; r.gd = r.gf - r.ga; });
    rows.sort((a, b) => (b.points - a.points) || (b.gd - a.gd) || (b.gf - a.gf));
    return rows;
  }

  leaguePosition() {
    const club = this.myClub();
    if (!club) return 0;
    const rows = this.standings(club.leagueId);
    const idx = rows.findIndex(r => r.clubId === club.cid);
    return idx < 0 ? 0 : idx + 1;
  }

  /**
   * רישום הדירוג לגרף ההתפתחות.
   *
   * נרשם רק כשהמספר זז, אחרת קריירה של 25 שנה מייצרת אלף רשומות זהות
   * בתוך השמורה. `OVERALL_LOG_LIMIT` חותך מלמטה — הגרף מראה את הדרך
   * האחרונה, וההיסטוריה המלאה ממילא יושבת ב-`growthLog` לפי עונות.
   */
  logOverall() {
    if (!this.me) return;
    const value = overall(this.me);
    const last = this.overallLog[this.overallLog.length - 1];
    if (last && last[2] === value) return;
    this.overallLog.push([this.year, this.week, value]);
    if (this.overallLog.length > OVERALL_LOG_LIMIT) this.overallLog.shift();
  }

  leagueName(leagueId) {
    const league = D.LEAGUES.find(l => l.id === leagueId);
    return league ? league.name : leagueId;
  }

  // ==================================================================
  // התקדמות שבועית
  // ==================================================================

  /**
   * על מה אפשר להתאמן — תכונות אמיתיות, לא קטגוריות.
   * לא כל 36, כי זה תפריט בלתי קריא בטלפון: בדיוק מה שרלוונטי עכשיו.
   */
  trainingOptions() {
    const me = this.me;
    const allowed = new Set(attrsFor(me.position));
    const picked = [];
    const add = attr => {
      if (attr && allowed.has(attr) && !picked.includes(attr)) picked.push(attr);
    };
    add(this.flag("directive"));
    add(recommendedFocus(this));
    const row = roleRow(me.role);
    if (row) {
      for (const attr of row[4]) add(attr);
      for (const attr of row[5].slice(0, 2)) add(attr);
    }
    const weakest = [...allowed].sort((a, b) => (me.detail[a] ?? 10) - (me.detail[b] ?? 10));
    for (const attr of weakest.slice(0, 3)) add(attr);
    return picked.slice(0, 12).map(a => [a, D.DETAIL_NAMES_HE[a]]);
  }

  availableActions() {
    if (["youth", "academy", "player", "veteran"].includes(this.stage)) {
      const extra = this.stage === "youth"
        ? ["street", "school", "rest"]
        : ["rest", "badges", "media", "business"];
      return this.trainingOptions()
        .concat(extra.map(k => [k, D.TRAINING_FOCUS_HE[k]]));
    }
    if (["coach", "manager"].includes(this.stage)) {
      return [["tactics", "עבודה טקטית עם הקבוצה"], ["individual", "אימון אישי לצעירים"],
              ["scouting", "סקאוטינג ואיתור שחקנים"], ["media", "עבודה מול התקשורת"],
              ["badges", "השתלמות מקצועית"], ["rest", "לתת לקבוצה לנשום"]];
    }
    if (this.stage === "pundit")
      return [["studio", "אולפן שידור"], ["column", "טור בעיתון"],
              ["badges", "לשמור על תעודות האימון"], ["rest", "חופש"]];
    if (this.stage === "agent")
      return [["clients", "לגייס לקוחות חדשים"], ["deals", "לסגור עסקאות"],
              ["media", "לבנות קשרים בתקשורת"], ["rest", "חופש"]];
    if (["director", "owner"].includes(this.stage))
      return [["squad", "בניית סגל"], ["finance", "ניהול פיננסי"],
              ["academy", "השקעה בנוער"], ["rest", "חופש"]];
    return [["rest", "מנוחה"]];
  }

  setAction(key) { this.trainingFocus = key; }

  /** רושם על מה התאמנת. המנטור קורא את זה כדי לזהות שגרה. */
  noteFocus() {
    if (!Array.isArray(this.flags.focus_log)) this.flags.focus_log = [];
    this.flags.focus_log.push(this.trainingFocus);
    if (this.flags.focus_log.length > 60)
      this.flags.focus_log = this.flags.focus_log.slice(-60);
  }

  advanceWeek() {
    const report = { week: this.week, training: [], notes: [], match: null,
                     personal: null, eventId: null, seasonEnded: false, seasonSummary: null,
                     attendance: 0, finances: null };
    this.weekAttendance = 0;
    if (this.gameOver) { report.notes.push({ icon: "🏁", text: "הקריירה הסתיימה." }); return report; }
    if (this.pendingEventId) { report.eventId = this.pendingEventId; return report; }

    // מה המאמן ביקש ממך השבוע, ומה עשית בפועל
    const directive = this.flag("directive");
    if (directive) {
      const club = this.myClub();
      if (club && this.trainingFocus === directive) {
        trustMove(club, 1.6);
        report.notes.push({ icon: "✅", text: `עשית מה שהמאמן ביקש. ${club.managerName} שם לב.` });
      } else if (club && ["academy", "player", "veteran"].includes(this.stage)) {
        trustMove(club, -0.9);
        report.notes.push({ icon: "↩️", text: `התאמנת על משהו אחר ממה ש${club.managerName} ביקש.` });
      }
    }
    this.noteFocus();
    report.training = this.doWeeklyAction();
    // הליגה הבוגרת רצה גם בשנות הנוער — אתה פשוט צופה בה מבחוץ
    this.simulateWeekMatches(report, this.stage === "youth");
    if (this.stage === "youth") this.youthWeek(report);
    simulateAiWeek(this.players, this.rng, this.clubs, this.meId);

    const event = pickEvent(this, this.rng);
    if (event && this.armEvent(event)) report.eventId = event.eid;

    // סקאוטים ביציע — מי ראה אותך השבוע ומה הוא כתב
    const played = report.match && report.match.result
      && report.match.result.ratings[this.meId] !== undefined;
    const myRating = played ? report.match.result.ratings[this.meId] : null;
    for (const line of scoutsThisWeek(this, this.rng, myRating))
      report.notes.push({ icon: "", text: line });

    // הערכה מחדש לנער: הדירוג שלו גדל מהר מדי מכדי לחכות לקיץ
    if (["youth", "academy", "player"].includes(this.stage)
        && this.week % REASSESS_EVERY === 0) {
      const note = reassessYoungster(this.me, this.rng, this.myClub());
      if (note) report.notes.push({ icon: "", text: note });
    }

    // צופי נוער — מערך שצד ילדים הרבה לפני שהם שחקנים
    if (this.stage === "youth") {
      for (const line of youthScoutsThisWeek(this, this.rng))
        report.notes.push({ icon: "", text: line });
      for (const line of maybeOpenYouthMarket(this, this.rng))
        report.notes.push({ icon: "", text: line });
      for (const line of tickYouthOffers(this))
        report.notes.push({ icon: "", text: line });
    }

    // מה שנכתב עליך — עיתונות, טלוויזיה ושמועות
    for (const line of weeklyPress(this, this.rng))
      report.notes.push({ icon: "", text: line });
    if (report.match)
      for (const line of broadcast(this, report.match, this.rng))
        report.notes.push({ icon: "", text: line });
    for (const line of tickOffers(this))
      report.notes.push({ icon: "", text: line });

    // מה שהשם שלך שווה מחוץ למגרש
    const venture = ventureOffer(this, this.rng);
    if (venture) {
      this.flags.venture = venture;
      report.notes.push({ icon: "💼",
        text: `${venture.title}: ${venture.text} (בתפריט: 'שם')` });
    }

    this.weeklyIncome(report);

    if (this.myClub()) this.positionLog.push(this.leaguePosition());
    // רק כשהערך זז, ותמיד עם השבוע — אחרת אי אפשר לתייג את הציר
    this.logOverall();

    // ההוראה לשבוע הבא
    const next = weeklyDirective(this, this.rng);
    const prev = this.flag("directive");
    this.setFlag("directive", next);
    // הוראה שלא השתנתה היא לא חדשות. חזרה על אותה שורה מילה במילה כל
    // שבוע היא מה שגורם למשחק להרגיש כמו לולאה ולא כמו עונה.
    const onPitch = ["academy", "player", "veteran"].includes(this.stage);
    if (next && next !== prev && onPitch) {
      report.notes.push({ icon: "🎙️",
        text: directiveLine(this.myClub(), next, this.flags.last_stats) });
    } else if (next && onPitch && this.week % 6 === 0) {
      const club = this.myClub();
      report.notes.push({ icon: "🎙️",
        text: `${club ? club.managerName : "המאמן"}: "ממשיכים עם מה שהתחלנו."` });
    }
    if (["youth", "academy", "player", "veteran"].includes(this.stage)) {
      const target = nextTarget(this);
      if (target && this.week % 4 === 0)
        report.notes.push({ icon: "", text: target });
      // המנטור מדבר רק כשיש לו משהו חדש להגיד
      if (this.week % 3 === 0) {
        const tip = mentorLines(this, this.rng);
        if (tip.length) {
          report.notes.push({ icon: "🧭", text: tip[0] });
          for (const line of tip.slice(1)) report.notes.push({ icon: "", text: line });
        }
      }
    }

    this.week += 1;
    if (this.week > SEASON_WEEKS) {
      report.seasonEnded = true;
      report.seasonSummary = this.endSeason();
    }
    return report;
  }

  doWeeklyAction() {
    const focus = this.trainingFocus;
    const me = this.me;
    const club = this.myClub();

    if (this.stage === "youth") {
      if (focus === "school") {
        me.attributes.mental = Math.round(clamp((me.attributes.mental ?? 50) +
          (this.rng.random() < 0.35 ? 1 : 0), 10, 97));
        this.flags.school = (this.flag("school", 0)) + 1;
        me.fitness = clamp(me.fitness + 14, 0, 100);
        return [{ icon: "📚", text: "שבוע של בית ספר. ההורים מרוצים, המאמן פחות." }];
      }
      if (focus === "street") {
        const attr = this.rng.choice(["dribbling", "shooting", "pace"]);
        const lines = weeklyTraining(me, attr, club, this.rng, 1.15);
        me.morale = clamp(me.morale + 4, 5, 99);
        return [{ icon: "🧱", text: "שיחקת עד שהחשיך במגרש השכונתי." }].concat(lines);
      }
      return weeklyTraining(me, focus, club, this.rng, this.intensity);
    }
    if (["academy", "player", "veteran"].includes(this.stage))
      return weeklyTraining(me, focus, club, this.rng, this.intensity);

    const lines = [];
    if (["coach", "manager"].includes(this.stage)) {
      if (focus === "tactics") {
        this.tactics.talkBoost = clamp((this.tactics.talkBoost || 0) + 0.25, 0, 0.6);
        me.coaching = clamp(me.coaching + 0.6, 0, 100);
        lines.push({ icon: "🧠", text: "עבדתם על תבניות. הקבוצה נכנסת מוכנה יותר למשחק." });
      } else if (focus === "individual" && club) {
        const young = club.squad.map(p => this.players[p]).filter(p => p && p.age <= 22);
        if (young.length) {
          const target = this.rng.choice(young);
          weeklyTraining(target, this.rng.choice(D.ATTRIBUTES), club, this.rng, 1.2);
          lines.push({ icon: "🎯", text: `עבודה אישית עם ${target.name} (${target.age}).` });
        }
      } else if (focus === "scouting" && club) {
        this.setFlag("scouted", true);
        lines.push({ icon: "🔍", text: "הצוות סרק שחקנים — בחלון ההעברות יהיו לך יעדים." });
      } else if (focus === "media") {
        me.mediaSkill = clamp(me.mediaSkill + 1.1, 0, 100);
        if (club) club.fanSupport = clamp(club.fanSupport + 1.2, 0, 100);
        lines.push({ icon: "🎤", text: "מסיבת עיתונאים טובה. הקהל נרגע." });
      } else if (focus === "badges") {
        me.coaching = clamp(me.coaching + 1.4, 0, 100);
        lines.push({ icon: "📚", text: "השתלמות מקצועית — ידע האימון עלה." });
      } else if (focus === "rest" && club) {
        for (const pid of club.squad) {
          const p = this.players[pid];
          if (p) { p.fitness = clamp(p.fitness + 14, 0, 100); p.morale = clamp(p.morale + 1.5, 0, 100); }
        }
        lines.push({ icon: "😌", text: "שבוע קליל. הסגל רענן." });
      }
      return lines;
    }

    if (this.stage === "pundit") {
      if (focus === "studio") {
        const fee = Math.round(6000 + me.mediaSkill * 260 + me.reputation * 190);
        this.earn(fee);
        me.mediaSkill = clamp(me.mediaSkill + 1.4, 0, 100);
        me.reputation = clamp(me.reputation + 0.3, 0, 99);
        lines.push({ icon: "📺", text: `שידור באולפן. ₪${fmt(fee)}.` });
      } else if (focus === "column") {
        const fee = Math.round(3000 + me.mediaSkill * 120);
        this.earn(fee);
        me.mediaSkill = clamp(me.mediaSkill + 1.0, 0, 100);
        lines.push({ icon: "📰", text: `טור שבועי. ₪${fmt(fee)}.` });
      } else if (focus === "badges") {
        me.coaching = clamp(me.coaching + 1.6, 0, 100);
        lines.push({ icon: "📚", text: "שמרת על הכשרת האימון שלך." });
      } else lines.push({ icon: "🌴", text: "שבוע חופש." });
      return lines;
    }

    if (this.stage === "agent") {
      if (focus === "clients") {
        const gained = this.rng.random() < 0.35 + me.business / 220 ? 1 : 0;
        this.flags.clients = (this.flag("clients", 0)) + gained;
        me.business = clamp(me.business + 1.2, 0, 100);
        lines.push({ icon: "🤝", text: gained ? "חתמת לקוח חדש." : "שיחות. בלי חתימות השבוע." });
      } else if (focus === "deals") {
        const clients = this.flag("clients", 0);
        const fee = Math.round(clients * (3000 + me.business * 220) * this.rng.uniform(0.5, 1.5));
        this.earn(fee);
        lines.push({ icon: "💼", text: fee ? `עמלות מעסקאות: ₪${fmt(fee)}.` : "אין לקוחות — אין עמלות." });
      } else if (focus === "media") {
        me.mediaSkill = clamp(me.mediaSkill + 1.3, 0, 100);
        lines.push({ icon: "🎤", text: "בנית קשרים. השם שלך חוזר בכתבות." });
      } else lines.push({ icon: "🌴", text: "שבוע חופש." });
      return lines;
    }

    if (["director", "owner"].includes(this.stage) && club) {
      if (focus === "squad") {
        club.reputation = Math.round(clamp(club.reputation + 0.3, 1, 99));
        lines.push({ icon: "📋", text: "עבודת סגל. המועדון נראה מסודר יותר." });
      } else if (focus === "finance") {
        const income = Math.round(club.reputation * 9000 * this.rng.uniform(0.7, 1.4));
        club.budget += income / 1000000;
        if (this.stage === "owner") this.earn(Math.round(income * 0.15));
        lines.push({ icon: "💰", text: `הכנסות: ₪${fmt(income)} לקופת המועדון.` });
      } else if (focus === "academy") {
        club.youthAcademy = Math.round(clamp(club.youthAcademy + 1.2, 1, 99));
        lines.push({ icon: "🌱", text: "השקעה בנוער. הדור הבא יהיה טוב יותר." });
      } else lines.push({ icon: "🌴", text: "שבוע חופש." });
      return lines;
    }
    return lines;
  }

  // -- משחקים -----------------------------------------------------------

  simulateWeekMatches(report, spectator = false) {
    if (CUP_WEEKS[this.week]) { this.playCupRound(report, spectator); return; }
    const myClub = this.myClub();
    for (const league of D.LEAGUES) {
      const lid = league.id;
      const rnd = this.leagueRoundForWeek(lid, this.week);
      if (rnd === null) continue;
      for (const [homeId, awayId] of this.fixtures[lid][rnd]) {
        const home = this.clubs[homeId], away = this.clubs[awayId];
        const involvesMe = myClub && (myClub.cid === homeId || myClub.cid === awayId);
        const isMine = involvesMe && !spectator;
        const result = this.simulateOne(home, away, isMine, "ליגה");
        this.registerResult(lid, result);
        if (isMine) {
          report.match = { result, home, away, competition: "ליגה" };
          this.myMatchLines(result, report);
        } else if (involvesMe && spectator) {
          // הקבוצה הבוגרת של המועדון שלך שיחקה — אתה קראת על זה בעיתון
          report.seniorMatch = { result, home, away };
        }
      }
    }
    if (myClub && !spectator && !report.match) this.idleWeek(report);
  }

  /** שבוע בקבוצת הנוער — משחק מול קבוצת נוער אחרת, בלי טבלה ובלי קהל. */
  youthWeek(report) {
    const me = this.me;
    const club = this.myClub();
    if (this.week % 2 === 0) {
      report.notes.push({ icon: "🏃", text: "שבוע אימונים בקבוצת הנוער." });
      weeklyRecovery(me, false, this.rng);
      return;
    }
    if (!isAvailable(me)) {
      report.personal = { status: "injured", injuryName: me.injuryName, weeks: me.injuryWeeks };
      return;
    }
    const rivalClub = this.rng.choice(Object.values(this.clubs).filter(c => c.cid !== (club && club.cid)));
    const oppStrength = clamp((club ? club.youthAcademy : 45) * 0.42 + 16 + this.rng.gauss(0, 5), 18, 72);
    const mine = effective(me);
    const edge = (mine - oppStrength) / 10;

    const teamGoals = poisson(this.rng, clamp(1.3 + edge * 0.35, 0.15, 6));
    const oppGoals = poisson(this.rng, clamp(1.4 - edge * 0.30, 0.15, 6));
    const goals = poisson(this.rng, clamp(
      0.18 + Math.max(0, edge) * 0.22 + (me.attributes.shooting ?? 40) / 260, 0.02, 3));
    const assists = poisson(this.rng, clamp(0.12 + (me.attributes.passing ?? 40) / 320, 0.02, 2));

    me.season.goals += goals;
    me.season.assists += assists;
    let rating = 6.0 + edge * 0.16 + goals * 1.0 + assists * 0.5 + this.rng.gauss(0, 0.5);
    rating = Math.round(clamp(rating, 3, 10) * 10) / 10;
    me.season.apps += 1;
    me.season.minutes += 70;
    me.season.ratingSum += rating;
    me.fitness = clamp(me.fitness - 16, 8, 100);
    me.morale = clamp(me.morale + (rating - 6.3) * 2, 5, 99);
    me.form = clamp(me.form * 0.84 + (rating - 6) * 14 + 9, 5, 99);

    report.youth = {
      rival: rivalClub.name + " נוער",
      rivalCid: rivalClub.cid,
      teamGoals, oppGoals, goals, assists, rating,
      outcome: teamGoals > oppGoals ? "W" : teamGoals === oppGoals ? "D" : "L",
    };
    if (club) club.managerTrust = clamp(club.managerTrust + (rating - 6.4) * 0.8, 0, 100);
  }

  simulateOne(home, away, isMine, competition, neutral = false) {
    let homeTac = {}, awayTac = {};
    if (isMine) {
      const myClub = this.myClub();
      let mine = ["manager", "coach"].includes(this.stage) ? Object.assign({}, this.tactics) : {};
      if (["academy", "player", "veteran"].includes(this.stage) && this.selected())
        mine = { forced: [this.meId] };
      if (myClub && myClub.cid === home.cid) homeTac = mine; else awayTac = mine;
    }
    const focusPid = (isMine && ["academy", "player", "veteran"].includes(this.stage))
      ? this.meId : null;
    const focusMods = focusPid ? tacticModifiers(this.myClub(), this.me) : null;
    const result = simulateMatch(home, away, this.players, this.rng,
      { homeTactics: homeTac, awayTactics: awayTac, competition, neutral,
        focusPid, focusMods });
    // הקהל נספר בכל משחק בית של המועדון שלי — גם בשנות הנוער,
    // כשאתה צופה בקבוצה הבוגרת מהיציע ולא משחק בה
    const myHomeClub = this.myClub();
    if (!neutral && myHomeClub && myHomeClub.cid === home.cid)
      this.registerAttendance(home, away);
    if (["manager", "coach"].includes(this.stage)) this.tactics.talkBoost = 0;
    return result;
  }

  /** כמה קהל הגיע למשחק הבית, לפי מיקום בטבלה, יריבה וכושר. */
  registerAttendance(home, away) {
    const order = this.standings(home.leagueId);
    const table = this.tables[home.leagueId] || {};
    const idx = order.findIndex(row => row.clubId === home.cid);
    const position = idx >= 0 ? idx + 1 : Math.max(1, Math.round(order.length / 2));
    const row = table[home.cid];
    const form = row && row.played
      ? clamp((row.won * 3 + row.drawn) / (row.played * 3), 0, 1) : 0.5;
    const attendance = attendanceFor(home, away, this.rng, position,
                                     Math.max(2, order.length), form);
    home.lastAttendance = attendance;
    this.weekAttendance = attendance;
    return attendance;
  }

  selected() {
    const me = this.me, club = this.myClub();
    if (!club || !isAvailable(me)) return false;
    const rivals = club.squad.map(p => this.players[p])
      .filter(p => p && p.pid !== this.meId && isAvailable(p) && p.position === me.position);
    let myScore = effective(me) + (club.managerTrust - 50) * 0.14;
    if (this.flag("captain")) myScore += 4;
    const bestRival = rivals.reduce((m, p) => Math.max(m, effective(p)), 0);
    return myScore >= bestRival - 1.0;
  }

  myMatchLines(result, report) {
    const me = this.me;
    if (["academy", "player", "veteran"].includes(this.stage)) {
      if (me.pid in result.ratings) {
        this.noStartStreak = 0;
        report.personal = {
          status: "started",
          rating: result.ratings[me.pid],
          goals: result.events.filter(e => e.kind === "goal" && e.playerId === me.pid).length,
          assists: result.events.filter(e => e.kind === "assist" && e.playerId === me.pid).length,
          motm: result.motm === me.pid,
        };
        const stats = result.statLines ? result.statLines[me.pid] : null;
        if (stats) {
          this.flags.last_stats = stats;
          report.personal.stats = stats;
          report.personal.statLines = statSummary(stats, me.position);
        }
        const club = this.myClub();
        const note = postMatchLine(this, report.personal.rating,
          club ? resultFor(result, club.cid) : "D", true, this.rng);
        if (note) report.personal.managerNote = note;
      } else if (isAvailable(me)) {
        this.noStartStreak += 1;
        if (this.rng.random() < 0.4) report.personal = this.subAppearance(result);
        else {
          me.morale = clamp(me.morale - 2.5, 5, 99);
          report.personal = { status: "bench" };
          const note = postMatchLine(this, null, "D", false, this.rng);
          if (note) report.personal.managerNote = note;
        }
      } else {
        report.personal = { status: "injured", injuryName: me.injuryName, weeks: me.injuryWeeks };
      }
    } else {
      const club = this.myClub();
      if (club) {
        const outcome = resultFor(result, club.cid);
        const delta = { W: 4.0, D: -0.5, L: -4.0 }[outcome];
        club.boardConfidence = clamp(club.boardConfidence + delta, 0, 100);
        club.fanSupport = clamp(club.fanSupport + delta * 0.7, 0, 100);
        report.personal = { status: "manager", outcome,
          board: Math.round(club.boardConfidence), fans: Math.round(club.fanSupport) };
      }
    }
  }

  subAppearance(result) {
    const me = this.me, club = this.myClub();
    const minutes = this.rng.randint(8, 32);
    let rating = Math.round(clamp(5.9 + this.rng.gauss(0.25, 0.5) + (effective(me) - 60) * 0.012, 3, 10) * 10) / 10;
    let scored = false;
    if (this.rng.random() < 0.06 * ((me.attributes.shooting ?? 40) / 55) && club) {
      scored = true;
      me.season.goals += 1;
      rating = Math.round(Math.min(10, rating + 1.2) * 10) / 10;
      const minute = 90 - this.rng.randint(1, Math.max(1, minutes - 1));
      result.events.push({ minute, kind: "goal", clubId: club.cid, playerId: me.pid,
                           text: `${minute}' ${me.name}` });
      if (club.cid === result.homeId) result.homeGoals += 1; else result.awayGoals += 1;
      // התוצאה השתנתה — הפרשנות צריכה להיכתב מחדש
      result.commentary = buildCommentary(result, this.clubs[result.homeId],
                                          this.clubs[result.awayId], this.players);
    }
    me.season.apps += 1;
    me.season.minutes += minutes;
    me.season.ratingSum += rating;
    result.ratings[me.pid] = rating;
    me.fitness = clamp(me.fitness - minutes * 0.12, 8, 100);
    me.morale = clamp(me.morale + (rating - 6.2), 5, 99);
    // גם עשרים דקות מייצרות מספרים. מי שיושב על הספסל צריך לדעת
    // על מה לעבוד לא פחות ממי שמשחק תשעים.
    const stats = matchStatLine(me, minutes, scored ? 1 : 0, 0, this.rng);
    if (result.statLines) result.statLines[me.pid] = stats;
    this.flags.last_stats = stats;
    return { status: "sub", minutes, rating, goals: scored ? 1 : 0, assists: 0,
             motm: false, stats, statLines: statSummary(stats, me.position) };
  }

  registerResult(leagueId, result) {
    const table = this.tables[leagueId];
    if (!table) return;
    const reg = (row, scored, conceded) => {
      row.played += 1; row.gf += scored; row.ga += conceded;
      if (scored > conceded) row.won += 1;
      else if (scored === conceded) row.drawn += 1;
      else row.lost += 1;
    };
    reg(table[result.homeId], result.homeGoals, result.awayGoals);
    reg(table[result.awayId], result.awayGoals, result.homeGoals);
    for (const cid of [result.homeId, result.awayId]) {
      const club = this.clubs[cid];
      if (!club) continue;
      club.formLog = (club.formLog || []).concat(resultFor(result, cid)).slice(-5);
    }
  }

  playCupRound(report, spectator = false) {
    const teams = this.cup.teams || [];
    const roundName = CUP_WEEKS[this.week];
    if (!teams.length || this.cup.winner) {
      report.notes.push({ icon: "🏆", text: "הגביע כבר הוכרע — שבוע חופשי." });
      this.idleWeek(report);
      return;
    }
    this.cup.round = roundName;
    const winners = [];
    const myClub = this.myClub();
    const neutral = roundName === "גמר הגביע";
    for (let i = 0; i + 1 < teams.length; i += 2) {
      const home = this.clubs[teams[i]], away = this.clubs[teams[i + 1]];
      const involvesMe = myClub && (myClub.cid === home.cid || myClub.cid === away.cid);
      const isMine = involvesMe && !spectator;
      const result = this.simulateOne(home, away, isMine, roundName, neutral);
      let winner, penalties = null;
      if (result.homeGoals === result.awayGoals) {
        winner = this.rng.random() < 0.5 ? home.cid : away.cid;
        penalties = this.clubs[winner].name;
      } else {
        winner = result.homeGoals > result.awayGoals ? result.homeId : result.awayId;
      }
      winners.push(winner);
      if (isMine) {
        report.match = { result, home, away, competition: roundName, penalties };
        this.myMatchLines(result, report);
      } else if (involvesMe && spectator) {
        report.seniorMatch = { result, home, away };
      }
    }
    this.cup.teams = winners;
    if (winners.length === 1) {
      this.cup.winner = winners[0];
      const champ = this.clubs[winners[0]];
      report.notes.push({ icon: "🏆", text: `${champ.name} זוכים בגביע המדינה!` });
      if (myClub && myClub.cid === winners[0]) this.recordHonour("גביע המדינה");
    }
    if (!spectator && myClub && !winners.includes(myClub.cid) && !report.match)
      report.notes.push({ icon: "📅", text: "אין לך משחק גביע השבוע." });
    if (!spectator && myClub && !report.match) this.idleWeek(report);
  }

  idleWeek(report) {
    weeklyRecovery(this.me, false, this.rng);
    report.notes.push({ icon: "📅", text: "שבוע בלי משחק — התאוששות ואימונים." });
  }

  weeklyIncome(report) {
    const me = this.me;
    if (this.stage === "youth") { /* בלי שכר — אתה עוד בבית ספר */ }
    else if (["academy", "player", "veteran"].includes(this.stage))
      this.earn(netIncome(me.contract.wage));
    else if (["coach", "manager", "director"].includes(this.stage)) {
      const club = this.myClub();
      let base = this.stage === "coach" ? 4000 : 12000;
      if (club) base += Math.round(club.reputation * (this.stage === "coach" ? 60 : 260));
      this.earn(netIncome(base));
    }

    // חסויות משלמות כל שבוע כל עוד החוזה בתוקף — לא פעם אחת ונגמר
    const retainer = weeklyRetainer(this.deals(), SEASON_WEEKS);
    if (retainer) {
      report.sponsorIncome = netIncome(retainer);
      this.earn(report.sponsorIncome);
    }

    const club = this.myClub();
    if (club) {
      report.attendance = this.weekAttendance || 0;
      const gate = report.attendance ? matchdayIncome(club, report.attendance) : 0;
      this.finances = weeklyFinances(club, this.players, gate);
      report.finances = this.finances;
      this.boardFinancePressure(report, club);
    }

    // בנייה שהתחלת ממשיכה גם אם עברת מועדון — פשוט לא תיהנה ממנה
    for (const other of Object.values(this.clubs)) {
      if (!other.works || !other.works.length) continue;
      for (const line of tickWorks(other)) {
        if (club && other.cid === club.cid) {
          report.notes.push({ icon: "🏗️", text: line });
          this.log(line);
        }
      }
    }

    const played = !!(report.match && me.pid in report.match.result.ratings);
    weeklyRecovery(me, played, this.rng, club);
  }

  // ==================================================================
  // ניהול המועדון: מתקנים, אצטדיון וצוות
  // ==================================================================

  /** המספרים שאפשר לבחור מהם במועדון הנוכחי. */
  freeNumbers() {
    const club = this.myClub();
    return club ? availableNumbers(club, this.players, this.meId) : [];
  }

  /** מחליף מספר חולצה. מחזיר הודעה למשתמש. */
  chooseNumber(number) {
    const club = this.myClub();
    if (!club) return "אתה לא משויך לסגל כרגע.";
    const taken = takenNumbers(club, this.players, this.meId);
    if (taken.has(number)) {
      const owner = club.squad.map(p => this.players[p])
        .find(p => p && p.pid !== this.meId && p.number === number);
      return owner ? `${owner.name} לובש את ${number}.` : "המספר תפוס.";
    }
    if (number < 1 || number > SQUAD_NUMBER_MAX) return "מספר לא חוקי.";
    this.me.number = number;
    this.log(`קיבלת את חולצה מספר ${number}.`);
    return `מעכשיו אתה מספר ${number}.`;
  }

  /** האם אני בעמדה שמאפשרת להוציא כסף של המועדון. */
  controlsClub() {
    return ["manager", "director", "owner"].includes(this.stage) && !!this.myClub();
  }

  /** מרענן את רשימת המועמדים. נקרא בתחילת עונה ואחרי כל גיוס. */
  refreshStaffMarket(role = null) {
    const club = this.myClub();
    if (!club) { this.staffMarket = {}; return; }
    if (!this.staffMarket) this.staffMarket = {};
    for (const key of role ? [role] : Object.keys(D.STAFF_ROLES))
      this.staffMarket[key] = staffCandidates(this.rng, club, key);
  }

  /** מצב כל מתקן: רמה נוכחית, מחיר השדרוג ומה חוסם אותו. */
  facilityOptions() {
    const club = this.myClub();
    if (!club) return [];
    return Object.entries(D.FACILITIES).map(([kind, spec]) => {
      const work = workInProgress(club, kind);
      return {
        kind, name: spec.name, effect: spec.effect,
        level: Math.round(kind === "stadium" ? club.capacity : facilityLevel(club, kind)),
        cost: upgradeCost(club, kind),
        weeks: spec.weeks,
        added: kind === "stadium" ? stadiumExpansion(club) : 0,
        building: work ? work.weeksLeft : 0,
        blocked: canUpgrade(club, kind),
      };
    });
  }

  upgradeFacility(kind) {
    if (!D.FACILITIES[kind]) return "אין מתקן כזה.";
    if (!this.controlsClub()) return "בתפקיד הנוכחי אתה לא מחליט על תקציב המועדון.";
    const club = this.myClub();
    const message = startUpgrade(club, kind);
    if (!workInProgress(club, kind)) return message;
    this.log(message);
    return message;
  }

  hireStaff(role, index) {
    if (!D.STAFF_ROLES[role]) return "אין תפקיד כזה.";
    if (!this.controlsClub()) return "בתפקיד הנוכחי אתה לא מגייס צוות.";
    const candidates = (this.staffMarket && this.staffMarket[role]) || [];
    if (index < 0 || index >= candidates.length) return "המועמד כבר לא זמין.";
    const message = hireStaffMember(this.myClub(), role, candidates[index]);
    if (message.includes("אין מספיק כסף")) return message;
    this.refreshStaffMarket(role);
    this.log(message);
    return message;
  }

  releaseStaff(role) {
    if (!this.controlsClub()) return "בתפקיד הנוכחי אתה לא מפטר צוות.";
    const message = fireStaffMember(this.myClub(), role);
    if (message !== "המשרה כבר פנויה.") {
      this.refreshStaffMarket(role);
      this.log(message);
    }
    return message;
  }

  /** תמונת המצב הכספית של המועדון שלי. */
  clubFinanceSummary() {
    const club = this.myClub();
    if (!club) return null;
    return {
      balance: Math.round(club.balance),
      commercial: commercialIncome(club),
      wages: wageBill(club, this.players),
      staffWages: staffWageBill(club),
      capacity: club.capacity,
      stadium: club.stadiumName,
      attendance: club.lastAttendance,
      ticket: ticketPrice(club),
      lastWeek: this.finances || null,
    };
  }

  /** קופה בגירעון שוחקת את אמון ההנהלה במאמן. */
  // -- חסויות ------------------------------------------------------------

  /** תיק החסויות הפעיל. חי בדגלים, ולכן נשמר עם הקריירה. */
  deals() {
    if (!Array.isArray(this.flags.deals)) this.flags.deals = [];
    return this.flags.deals;
  }

  /** בונוסים לפי הביצועים, ואז שנה קדימה בכל חוזה. */
  commercialSeasonEnd() {
    const portfolio = this.deals();
    if (!portfolio.length) return [];
    const lines = [];
    const payouts = seasonBonuses(portfolio, this.me, this.honours.length, this.caps);
    const total = payouts.reduce((a, pair) => a + pair[1], 0);
    if (total) {
      this.earn(total);
      lines.push(`💰 בונוסים מחסויות: ₪${fmt(total)}`);
      for (const [label, amount] of payouts.slice(0, 4))
        lines.push(`   • ${label} — ₪${fmt(amount)}`);
    }
    const expiring = portfolio.filter(d => d.yearsLeft <= 1);
    lines.push(...tickPortfolio(portfolio));
    // מותג שהחוזה איתו נגמר חוזר עם הצעה חדשה, לפי מי שנעשית
    for (const deal of expiring) {
      if (this.rng.random() < 0.55) {
        const club = this.myClub();
        const offer = renewalOffer(deal, this.me, this.rng, club ? club.reputation : 30);
        this.flags.pending_renewal = offer;
        lines.push(`📞 ${deal.brand} רוצים לחדש — ₪${fmt(offer.annual)} לעונה.`);
        break;
      }
    }
    return lines;
  }

  boardFinancePressure(report, club) {
    if (!["manager", "director", "owner"].includes(this.stage)) return;
    if (club.balance < 0) {
      club.boardConfidence = clamp(club.boardConfidence - 0.8, 0, 100);
      if (this.week % 4 === 0)
        report.notes.push({ icon: "💸",
          text: `הקופה במינוס ₪${fmt(Math.abs(club.balance))}. ההנהלה לא אוהבת את זה.` });
    } else if (club.balance > commercialIncome(club) * 26) {
      club.boardConfidence = clamp(club.boardConfidence + 0.2, 0, 100);
    }
  }

  // ==================================================================
  // אירועי עלילה
  // ==================================================================

  armEvent(event) {
    let body;
    try { body = event.body(this); } catch (err) { return false; }
    if (!body) return false;
    noteFired(this, event.eid);
    this.pendingEventId = event.eid;
    this.pendingEventBody = body;
    return true;
  }

  pendingEvent() {
    if (!this.pendingEventId) return null;
    const event = findEvent(this.pendingEventId);
    if (!event) { this.pendingEventId = null; this.pendingEventBody = null; }
    return event;
  }

  pendingEventText() {
    if (this.pendingEventBody) return this.pendingEventBody;
    const event = this.pendingEvent();
    if (!event) return "";
    try { return event.body(this); } catch (err) { return ""; }
  }

  resolveEvent(index) {
    const event = this.pendingEvent();
    if (!event) return "";
    const choice = event.choices[Math.max(0, Math.min(index, event.choices.length - 1))];
    const outcome = choice.apply(this) || "";
    if (!this.firedEvents.includes(event.eid)) this.firedEvents.push(event.eid);
    this.pendingEventId = null;
    this.pendingEventBody = null;
    this.log(`${event.title} — ${choice.label}`);
    return outcome;
  }

  // ==================================================================
  // שאילתות לעלילה
  // ==================================================================

  minutesShare() {
    const weeks = Math.max(1, this.week - 1);
    return clamp(this.me.season.minutes / (weeks * 90), 0, 1);
  }

  /** מועדון עם מחלקת נוער חזקה שמעוניין בי. */
  youthAcademySuitor() {
    const club = this.myClub();
    if (!club) return null;
    const pool = Object.values(this.clubs).filter(c =>
      c.cid !== club.cid && c.youthAcademy > club.youthAcademy + 12 &&
      c.leagueId !== "euro");
    if (!pool.length) return null;
    return pool.reduce((a, b) => (a.youthAcademy >= b.youthAcademy ? a : b));
  }

  joinBigAcademy() {
    const target = this.youthAcademySuitor();
    if (!target) return "ההזדמנות נסגרה.";
    this.transferMe(target.cid, 0, 0);
    target.managerTrust = 40;
    this.me.morale = clamp(this.me.morale - 4, 5, 99);
    this.me.potential = Math.round(clamp(this.me.potential + this.rng.randint(1, 5),
                                        40, this.me.ceiling));
    this.setFlag("big_academy", true);
    return `עברת ל${target.name}. מתקנים שלא הכרת, וילדים שכולם היו הכי טובים במועדון שלהם.`;
  }

  showOff() {
    if (this.rng.random() < 0.5) {
      this.me.reputation = clamp(this.me.reputation + 6, 1, 99);
      addGrowth(this.me, "dribbling", 1.0);
      this.setFlag("scouted_wow", true);
      return "הורדת שניים בתנועה אחת והנחת כדור בזווית. הוא הפסיק לכתוב והסתכל.";
    }
    const club = this.myClub();
    if (club) club.managerTrust = clamp(club.managerTrust - 8, 0, 100);
    this.me.morale = clamp(this.me.morale - 6, 5, 99);
    return "ניסית סובב מיותר באמצע המגרש, איבדת כדור, וספגתם. הצופה כבר לא הסתכל.";
  }

  askWhy() {
    const club = this.myClub();
    const trust = club ? club.managerTrust : 50;
    if (trust >= 45 || this.rng.random() < 0.4) {
      if (club) club.managerTrust = clamp(club.managerTrust + 6, 0, 100);
      addGrowth(this.me, "mental", 1.2);
      return 'הוא ענה בכנות: "אתה טוב עם הכדור וגרוע בלעדיו." ' +
             'זו הייתה הביקורת הכי שימושית שקיבלת.';
    }
    this.me.morale = clamp(this.me.morale - 7, 5, 99);
    return 'הוא אמר "יש עוד טורנירים" והמשיך לסדר קונוסים. לא קיבלת תשובה.';
  }

  loanTargetName() {
    const options = Object.values(this.clubs).filter(c => c.leagueId === "national");
    return options.length ? this.rng.choice(options).name : "מועדון מהליגה הלאומית";
  }

  bigClubSuitor() {
    const me = this.me;
    const candidates = Object.values(this.clubs).filter(c =>
      c.cid !== me.clubId && c.reputation > me.reputation + 12 && c.reputation < me.reputation + 45);
    if (!candidates.length) return null;
    return candidates.reduce((a, b) => (a.reputation >= b.reputation ? a : b));
  }

  managerSuitor() {
    const club = this.myClub();
    if (!club || club.boardConfidence < 55) return null;
    const candidates = Object.values(this.clubs)
      .filter(c => c.reputation > club.reputation + 10 && c.cid !== club.cid);
    if (!candidates.length) return null;
    return candidates.reduce((a, b) => (a.reputation <= b.reputation ? a : b));
  }

  managerJobTarget() {
    const pool = Object.values(this.clubs).filter(c =>
      ["top", "national"].includes(c.leagueId) && c.reputation <= 30 + this.me.coaching * 0.7);
    if (!pool.length) return null;
    return pool.reduce((a, b) => (a.reputation >= b.reputation ? a : b));
  }
  managerJobOfferName() { const c = this.managerJobTarget(); return c ? c.name : "מועדון מהליגה"; }

  squadStar() {
    const club = this.myClub();
    if (!club) return null;
    const squad = club.squad.map(p => this.players[p]).filter(p => p && p.pid !== this.meId);
    if (!squad.length) return null;
    return squad.reduce((a, b) => (overall(a) >= overall(b) ? a : b));
  }

  rivalYoungster() {
    const club = this.myClub();
    if (!club) return null;
    const rivals = club.squad.map(p => this.players[p]).filter(p =>
      p && p.pid !== this.meId && p.position === this.me.position && p.age <= 21);
    if (!rivals.length) return null;
    return rivals.reduce((a, b) => (a.potential >= b.potential ? a : b));
  }

  retirementReady() {
    return retirementPressure(this.me) > 0.45 && !this.flag("retired_announced") && this.week >= 18;
  }

  lastClubName() { const c = this.clubs[this.lastClubId]; return c ? c.name : "המועדון שלך"; }
  firstClubName() { const c = this.clubs[this.firstClubId]; return c ? c.name : "מועדון הילדות"; }

  renewalOffer() {
    const club = this.myClub(), me = this.me;
    let target = wageForOverall(overall(me));
    target = Math.round(target * (0.85 + me.reputation / 200));
    if (club) target = Math.round(Math.min(target, club.wageBudget * 0.30));
    return Math.round(Math.max(me.contract.wage * 0.9, target));
  }

  careerOptionsSummary() {
    const me = this.me;
    return `תעודות אימון: ${me.badges}/4 · ידע אימון ${Math.round(me.coaching)}\n` +
      `כריזמה תקשורתית: ${Math.round(me.mediaSkill)} · ראש עסקי: ${Math.round(me.business)}\n` +
      `מוניטין: ${Math.round(me.reputation)} · בחשבון: ₪${fmt(this.money)}`;
  }

  // ==================================================================
  // אפקטים
  // ==================================================================

  goOnLoan() {
    const target = Object.values(this.clubs).filter(c => c.leagueId === "national")
      .reduce((a, b) => (a.reputation >= b.reputation ? a : b));
    this.transferMe(target.cid, Math.round(this.me.contract.wage * 0.8), 1, true);
    this.me.reputation = clamp(this.me.reputation - 2, 1, 99);
    return `יצאת בהשאלה ל${target.name}. שם תשחק כל שבוע — וזה בדיוק מה שהקריירה שלך צריכה.`;
  }

  confrontManager() {
    const club = this.myClub();
    const roll = this.rng.random() + (effective(this.me) - 62) * 0.012;
    if (roll > 0.55) {
      if (club) club.managerTrust = clamp(club.managerTrust + 14, 0, 100);
      this.me.morale = clamp(this.me.morale + 6, 5, 99);
      return 'צעקת. הוא צעק חזרה. ואז אמר: "תהיה מוכן ביום ראשון." אתה בהרכב.';
    }
    if (club) club.managerTrust = clamp(club.managerTrust - 18, 0, 100);
    this.me.morale = clamp(this.me.morale - 8, 5, 99);
    this.setFlag("frozen_out", true);
    return 'הוא הקשיב בשקט ואז אמר: "תודה שבאת." מאז אתה אפילו לא בסגל.';
  }

  denyScandal() {
    if (this.rng.random() < 0.45) {
      this.me.reputation = clamp(this.me.reputation - 12, 1, 99);
      const club = this.myClub();
      if (club) {
        club.managerTrust = clamp(club.managerTrust - 12, 0, 100);
        club.fanSupport = clamp(club.fanSupport - 10, 0, 100);
      }
      this.me.morale = clamp(this.me.morale - 10, 5, 99);
      return "יומיים אחרי ההכחשה פורסם סרטון נוסף. עכשיו זה לא הבילוי — זה השקר.";
    }
    this.me.reputation = clamp(this.me.reputation + 1, 1, 99);
    return "הכחשת בתוקף והסיפור דעך. הפעם יצאת מזה.";
  }

  nationalDebut() {
    this.caps += 1;
    this.setFlag("national_debut", true);
    this.me.reputation = clamp(this.me.reputation + 9, 1, 99);
    this.me.morale = clamp(this.me.morale + 8, 5, 99);
    this.recordHonour("בכורה בנבחרת");
    if (this.rng.random() < 0.25) {
      this.intlGoals += 1;
      return "נכנסת בדקה 71 וכבשת בנגיעה הראשונה שלך בנבחרת. אין דבר כזה.";
    }
    return "המנון, 90 דקות, וחולצה ממוסגרת אצל ההורים.";
  }

  becomeCaptain() {
    this.setFlag("captain", true);
    const club = this.myClub();
    if (club) {
      club.managerTrust = clamp(club.managerTrust + 10, 0, 100);
      club.fanSupport = clamp(club.fanSupport + 8, 0, 100);
    }
    this.me.morale = clamp(this.me.morale + 6, 5, 99);
    this.me.reputation = clamp(this.me.reputation + 4, 1, 99);
    if (!this.me.traits.includes("leader")) this.me.traits.push("leader");
    this.me.coaching = clamp(this.me.coaching + 6, 0, 100);
    return "אתה הקפטן. עכשיו כל הפסד הוא גם שלך.";
  }

  rushRehab() {
    if (this.rng.random() < 0.42) {
      this.me.injuryWeeks = Math.max(1, Math.floor(this.me.injuryWeeks / 2));
      this.me.morale = clamp(this.me.morale + 5, 5, 99);
      const club = this.myClub();
      if (club) club.managerTrust = clamp(club.managerTrust + 8, 0, 100);
      return "חזרת חודש לפני הזמן והחזקת. המאמן לא שכח את זה.";
    }
    const extra = this.rng.randint(6, 14);
    this.me.injuryWeeks += extra;
    this.me.attributes.pace = Math.round(clamp((this.me.attributes.pace ?? 50) - 3, 10, 97));
    this.me.morale = clamp(this.me.morale - 12, 5, 99);
    return `נכנסת מוקדם מדי. הפציעה חזרה, ועוד ${extra} שבועות. המהירות שלך לא תחזור לגמרי.`;
  }

  studyDuringInjury() {
    this.me.coaching = clamp(this.me.coaching + 5, 0, 100);
    const newBadges = Math.min(4, Math.floor(this.me.coaching / 22));
    let extra = "";
    if (newBadges > this.me.badges) {
      this.me.badges = newBadges;
      extra = ` השלמת תעודת אימון רמה ${this.me.badges}.`;
    }
    return "במקום להסתובב במסדרונות, ישבת עם הצוות המקצועי על ניתוחי משחק." + extra;
  }

  signRenewal(multiplier) {
    const offer = Math.round(this.renewalOffer() * multiplier);
    this.me.contract = { wage: offer, yearsLeft: 3 };
    const club = this.myClub();
    if (club) {
      club.managerTrust = clamp(club.managerTrust + 6, 0, 100);
      club.fanSupport = clamp(club.fanSupport + 5, 0, 100);
    }
    this.me.morale = clamp(this.me.morale + 5, 5, 99);
    return `חתמת לשלוש עונות על ₪${fmt(offer)} לשבוע.`;
  }

  demandRaise() {
    const club = this.myClub();
    const leverage = (this.me.reputation + overall(this.me)) / 2 - 50;
    if (this.rng.random() * 100 < 45 + leverage) return this.signRenewal(1.45);
    if (club) club.managerTrust = clamp(club.managerTrust - 10, 0, 100);
    this.setFlag("contract_stalled", true);
    this.me.morale = clamp(this.me.morale - 6, 5, 99);
    return "ההנהלה משכה את ההצעה מהשולחן. עכשיו אתה משחק על החוזה שלך כל שבוע.";
  }

  joinRevolt() {
    const club = this.myClub();
    if (!club) return "";
    if (this.rng.random() < 0.5) {
      club.managerName = this.rng.choice(D.MANAGER_NAMES);
      club.managerTrust = 50;
      return `המאמן הודח. ${club.managerName} נכנס במקומו — ואתה מתחיל מאפס מול מישהו שיודע בדיוק מי הדליף.`;
    }
    club.managerTrust = clamp(club.managerTrust - 25, 0, 100);
    this.setFlag("frozen_out", true);
    return "המאמן שרד. אתה הוצאת מהסגל עד סוף העונה.";
  }

  mentorYoungster() {
    const kid = this.rivalYoungster();
    this.me.coaching = clamp(this.me.coaching + 4, 0, 100);
    const club = this.myClub();
    if (club) club.managerTrust = clamp(club.managerTrust + 6, 0, 100);
    if (kid) {
      kid.potential = Math.round(clamp(kid.potential + 2, 40, 95));
      this.setFlag("protege", kid.pid);
      return `לקחת את ${kid.name} תחת חסותך. הוא ייקח את המקום שלך — אבל הוא ייקח אותו כשאתה תלמד אותו איך.`;
    }
    return "התחלת להעביר ידע לצעירים.";
  }

  changePosition() {
    const me = this.me;
    const moves = { ST: "AM", LW: "AM", RW: "AM", AM: "CM", CM: "DM",
                    DM: "CB", LB: "CB", RB: "CB", CB: "CB", GK: "GK" };
    const old = positionHe(me);
    me.position = moves[me.position] || "CM";
    me.attributes.mental = Math.round(clamp((me.attributes.mental ?? 50) + 4, 10, 97));
    return `עברת מ${old} ל${positionHe(me)}. פחות ריצה, יותר ראש — ועוד כמה שנים בקריירה.`;
  }

  painkillers() {
    if (this.rng.random() < 0.55) {
      this.me.form = clamp(this.me.form + 12, 5, 99);
      return "הזריקות עובדות. שיחקת עונה שלמה כאילו אתה בן 26.";
    }
    const weeks = this.rng.randint(8, 16);
    this.me.injuryWeeks = weeks;
    this.me.attributes.physical = Math.round(clamp((this.me.attributes.physical ?? 50) - 4, 10, 97));
    return `הגוף אמר די. ${weeks} שבועות, והפעם זה כואב גם כשאתה יושב.`;
  }

  announceRetirement() {
    this.setFlag("retired_announced", true);
    this.me.reputation = clamp(this.me.reputation + 4, 1, 99);
    this.log("הודעת על פרישה בסוף העונה.");
    return "עמדת מול המצלמות ואמרת את המשפט. בסוף העונה אתה תולה את הנעליים.";
  }

  startCoaching() {
    if (this.me.badges < 1) {
      this.me.coaching = clamp(this.me.coaching + 8, 0, 100);
      return "אין לך אפילו תעודה אחת. שלחו אותך לקורס מאמנים בסיסי — תחזור לזה בעוד קצת.";
    }
    let club = this.clubs[this.lastClubId] || this.clubs[this.firstClubId];
    if (!club) club = this.rng.choice(Object.values(this.clubs));
    this.stage = "coach";
    this.managedClubId = club.cid;
    this.me.clubId = null;
    this.trainingFocus = "tactics";
    this.log(`התחלת לאמן — עוזר מאמן ב${club.name}.`);
    return `אתה עוזר מאמן ב${club.name}. שעה לפני כולם במגרש, שעתיים אחרי כולם בחדר וידאו.`;
  }

  startPunditry() {
    this.stage = "pundit";
    this.managedClubId = null;
    this.me.clubId = null;
    this.trainingFocus = "studio";
    const bonus = Math.round(200000 + this.me.reputation * 12000);
    this.earn(bonus);
    this.log("חתמת בערוץ הספורט כפרשן.");
    return `חתמת כפרשן. מקדמה של ₪${fmt(bonus)}, ואור אדום שנדלק בדיוק כשאתה באמצע משפט.`;
  }

  startAgency() {
    this.stage = "agent";
    this.managedClubId = null;
    this.me.clubId = null;
    this.trainingFocus = "clients";
    this.flags.clients = 1;
    this.log("פתחת סוכנות שחקנים.");
    return "פתחת משרד עם שולחן אחד ולקוח אחד — ילד בן 16 שאף אחד עוד לא שמע עליו.";
  }

  takeManagerJob() {
    const club = this.managerJobTarget();
    if (!club) return "לא נמצא מועדון מתאים כרגע.";
    this.stage = "manager";
    this.managedClubId = club.cid;
    club.managerName = this.me.name;
    club.boardConfidence = 55;
    this.trainingFocus = "tactics";
    this.tactics.formation = club.formation;
    this.log(`מונית למנג'ר של ${club.name}.`);
    return `אתה המנג'ר של ${club.name}. הציפייה: ${club.seasonExpectation}. הסבלנות: קצרה.`;
  }

  moveManagerJob() {
    const target = this.managerSuitor();
    if (!target) return "ההצעה נעלמה.";
    const old = this.myClub();
    if (old) { old.managerName = this.rng.choice(D.MANAGER_NAMES); old.boardConfidence = 55; }
    this.managedClubId = target.cid;
    target.managerName = this.me.name;
    target.boardConfidence = 60;
    this.me.reputation = clamp(this.me.reputation + 6, 1, 99);
    this.log(`עברת לאמן את ${target.name}.`);
    return `אתה המנג'ר של ${target.name}. ליגה אחרת, לחץ אחר.`;
  }

  board(delta) {
    const club = this.myClub();
    if (club) club.boardConfidence = clamp(club.boardConfidence + delta, 0, 100);
    return "";
  }

  demandBudget() {
    const club = this.myClub();
    if (!club) return "";
    if (club.boardConfidence > 55) {
      club.budget += 6;
      club.boardConfidence = clamp(club.boardConfidence - 4, 0, 100);
      return "קיבלת ₪6,000,000 להעברות. עכשיו זה עליך.";
    }
    club.boardConfidence = clamp(club.boardConfidence - 12, 0, 100);
    return 'היו"ר צחק. "תעשה קודם תוצאות." אמון ההנהלה ירד.';
  }

  sellStar() {
    const star = this.squadStar(), club = this.myClub();
    if (!star || !club) return "";
    const fee = playerValue(star);
    club.budget += fee / 1000000;
    club.squad = club.squad.filter(p => p !== star.pid);
    const buyer = Object.values(this.clubs).filter(c => c.cid !== club.cid)
      .reduce((a, b) => (a.reputation >= b.reputation ? a : b));
    buyer.squad.push(star.pid);
    star.clubId = buyer.cid;
    assignNumber(buyer, this.players, star);
    club.boardConfidence = clamp(club.boardConfidence + 5, 0, 100);
    club.fanSupport = clamp(club.fanSupport - 12, 0, 100);
    return `מכרת את ${star.name} ל${buyer.name} תמורת ₪${fmt(fee)}. האוהדים בטראומה.`;
  }

  keepStar() {
    const star = this.squadStar(), club = this.myClub();
    if (!star || !club) return "";
    star.morale = clamp(star.morale - 25, 5, 99);
    club.fanSupport = clamp(club.fanSupport + 8, 0, 100);
    this.setFlag("unhappy_star", star.pid);
    return `${star.name} נשאר — ומצב הרוח שלו ייראה על המגרש.`;
  }

  promoteStar() {
    const star = this.squadStar(), club = this.myClub();
    if (!star || !club) return "";
    const cost = Math.round(star.contract.wage * 0.6);
    star.contract.wage += cost;
    star.morale = clamp(star.morale + 20, 5, 99);
    club.budget -= cost * 40 / 1000000;
    return `נתת ל${star.name} את הסרט ותוספת של ₪${fmt(cost)} לשבוע. הוא נשאר, והשכר מכביד על התקציב.`;
  }

  promoteYouth() {
    const club = this.myClub();
    if (!club) return "";
    const kid = generatePlayer(this.rng, club, this.rng.choice(D.POSITIONS),
      { age: 17, quality: Math.round(clamp(club.youthAcademy * 0.5 + 20, 35, 60)) });
    kid.potential = Math.round(clamp(overall(kid) + this.rng.randint(10, 32), 60, 93));
    this.players[kid.pid] = kid;
    club.squad.push(kid.pid);
    assignNumber(club, this.players, kid);
    this.setFlag("wonderkid", kid.pid);
    return `העלית את ${kid.name} (${kid.age}) לסגל. פוטנציאל מוערך: ${kid.potential}. עכשיו תתפלל.`;
  }

  radicalChange() {
    const club = this.myClub();
    if (!club) return "";
    this.tactics.formation = this.rng.choice(Object.keys(D.FORMATIONS));
    this.tactics.mentality = this.rng.choice(Object.keys(D.MENTALITIES));
    if (this.rng.random() < 0.5) {
      club.boardConfidence = clamp(club.boardConfidence + 14, 0, 100);
      for (const pid of club.squad) {
        const p = this.players[pid];
        if (p) p.morale = clamp(p.morale + 10, 5, 99);
      }
      return `שינית הכל למערך ${this.tactics.formation} ובמנטליות ` +
             `${D.MENTALITIES[this.tactics.mentality][0]}. הקבוצה נדלקה.`;
    }
    club.boardConfidence = clamp(club.boardConfidence - 8, 0, 100);
    return "שינית הכל והקבוצה נראתה אבודה. לפעמים תזוזה היא הפסד.";
  }

  resign() {
    const club = this.myClub();
    if (club) { club.managerName = this.rng.choice(D.MANAGER_NAMES); club.boardConfidence = 55; }
    this.managedClubId = null;
    this.stage = "coach";
    this.log("התפטרת מתפקיד המנג'ר.");
    return "התפטרת לפני שהדיחו אותך. בעולם הזה זה נחשב ניצחון קטן. עכשיו אתה מחכה לטלפון הבא.";
  }

  becomeDirector() {
    const club = this.myClub();
    if (!club) return "";
    this.stage = "director";
    club.managerName = this.rng.choice(D.MANAGER_NAMES);
    this.trainingFocus = "squad";
    this.log(`מונית למנהל ספורטיבי ב${club.name}.`);
    return `אתה מנהל ספורטיבי ב${club.name}. עכשיו אתה זה שמפטר מאמנים.`;
  }

  buyClub() {
    const club = this.clubs[this.firstClubId];
    if (!club) return "";
    this.spend(4000000);
    this.stage = "owner";
    this.managedClubId = club.cid;
    club.budget += 2;
    this.setFlag("owner_of", club.cid);
    this.log(`רכשת את ${club.name}.`);
    return `קנית את ${club.name}. הילד שהתאמן פה בגיל 12 מחזיק עכשיו את המפתחות.`;
  }

  /** המאמן מחלק תפקידים מחדש — בהעברה, בתחילת עונה, ובהחלפת מאמן. */
  refreshRole() {
    const me = this.me;
    if (!["academy", "player", "veteran"].includes(this.stage)) return null;
    const club = this.myClub();
    const before = me.role;
    me.role = assignRole(me, club, this.rng);
    me.duty = dutyFor(me.role, club, this.rng);
    if (me.role === before || !me.role) return null;
    const row = roleRow(me.role);
    if (!row) return null;
    return `📋 התפקיד שלך: ${row[1]} (${D.DUTY_NAMES_HE[me.duty] || ""}). ${row[6]}`;
  }

  transferMe(clubId, wage, years, loan = false) {
    const me = this.me;
    const old = this.clubs[me.clubId];
    if (old) old.squad = old.squad.filter(p => p !== me.pid);
    const next = this.clubs[clubId];
    next.squad.push(me.pid);
    me.clubId = clubId;
    assignNumber(next, this.players, me);
    me.contract = { wage, yearsLeft: years };
    next.managerTrust = loan ? 65 : 55;
    this.lastClubId = clubId;
    this.noStartStreak = 0;
    // מאמן חדש, מערכת חדשה — התפקיד שלך נקבע מאפס
    const note = this.refreshRole();
    if (note) this.log(note);
    this.log(`${loan ? "הושאלת ל" : "עברת ל"}${next.name}.`);
    return next.name;
  }

  // ==================================================================
  // סוף עונה
  // ==================================================================

  endSeason() {
    const summary = { title: `סיכום עונת ${this.year}/${this.year + 1}`, lines: [] };
    const add = (icon, text, strong) => summary.lines.push({ icon, text, strong: !!strong });
    const myClub = this.myClub();

    for (const league of D.LEAGUES) {
      const table = this.standings(league.id);
      if (!table.length) continue;
      const champ = this.clubs[table[0].clubId];
      champ.trophies.push(`${league.name} ${this.year}`);
      add("🥇", `אלוף ${league.name}: ${champ.name} (${table[0].points} נק')`);
      if (myClub && myClub.cid === champ.cid) {
        this.recordHonour(`אליפות ${league.name}`);
        add("🎉", "אתה אלוף!", true);
      }
    }
    if (this.cup.winner) add("🏆", `זוכת גביע המדינה: ${this.clubs[this.cup.winner].name}`);

    this.seasonAwards(add);
    this.personalSummary(add);
    this.promotionRelegation(add);
    const beforeDetail = Object.assign({}, this.me.detail);
    for (const note of this.developEveryone()) add(note.icon || "", note.text || note);
    for (const note of this.growthReport(beforeDetail)) add(note.icon, note.text);
    this.processRetirements();
    this.transferWindow(add);
    // מסלול הפיתוח — מה נחתם העונה
    for (const line of claimMilestones(this)) add("", line);
    // חסויות: בונוסים לפי מה שבאמת עשית, ואז שנה קדימה בחוזים
    for (const line of this.commercialSeasonEnd()) add("", line);
    // נכסים והשקעות
    for (const line of assetsSeasonTick(this, this.rng)) add("", line);
    this.advanceCareerStage(add);

    // תמונת מצב שנתית של השחקן — הבסיס למסך "איך התפתחתי"
    if (["youth", "academy", "player", "veteran"].includes(this.stage)) {
      if (!Array.isArray(this.flags.growth_log)) this.flags.growth_log = [];
      this.flags.growth_log.push(
        playerSnapshot(this.me, this.year, myClub ? myClub.name : ""));
      if (this.flags.growth_log.length > 30)
        this.flags.growth_log = this.flags.growth_log.slice(-30);
    }

    this.history.push({
      year: this.year, stage: this.stage,
      club: myClub ? myClub.name : "-",
      apps: this.me.career.apps, goals: this.me.career.goals,
      honours: this.honours.length,
    });

    this.year += 1;
    this.startSeason();
    return summary;
  }

  seasonAwards(add) {
    const leagueId = this.myLeague() || "top";
    const clubIds = new Set(Object.values(this.clubs).filter(c => c.leagueId === leagueId).map(c => c.cid));
    const squad = Object.values(this.players).filter(p =>
      clubIds.has(p.clubId) && p.season.apps > 0 &&
      !(this.stage === "youth" && p.pid === this.meId));
    if (!squad.length) return;
    const scorer = squad.reduce((a, b) =>
      (a.season.goals > b.season.goals || (a.season.goals === b.season.goals && a.season.assists >= b.season.assists)) ? a : b);
    add("👑", `מלך השערים: ${scorer.name} — ${scorer.season.goals} שערים`);
    const best = squad.reduce((a, b) =>
      (avgRating(a.season) > avgRating(b.season) || (avgRating(a.season) === avgRating(b.season) && a.season.apps >= b.season.apps)) ? a : b);
    add("⭐", `שחקן העונה: ${best.name} (ציון ${avgRating(best.season).toFixed(1)})`);
    if (scorer.pid === this.meId) { this.recordHonour("מלך השערים"); add("🎉", "מלך השערים — אתה!", true); }
    if (best.pid === this.meId) { this.recordHonour("שחקן העונה"); add("🎉", "שחקן העונה — אתה!", true); }
  }

  personalSummary(add) {
    const me = this.me;
    if (["youth", "academy", "player", "veteran"].includes(this.stage)) {
      const s = me.season;
      add("📊", `העונה שלך: ${s.apps} משחקים · ${s.goals} שערים · ${s.assists} בישולים · ציון ${avgRating(s).toFixed(1)}`);
      add("📈", `דירוג ${overall(me)} (פוטנציאל ${me.potential}) · מוניטין ${Math.round(me.reputation)} · שווי ₪${fmt(playerValue(me))}`);
    } else {
      const club = this.myClub();
      if (club) {
        add("📊", `${club.name} — מקום ${this.leaguePosition()} ב${this.leagueName(club.leagueId)}`);
        add("🏛️", `אמון ההנהלה ${Math.round(club.boardConfidence)}% · אהדת הקהל ${Math.round(club.fanSupport)}%`);
      }
    }
    add("💰", `בחשבון: ₪${fmt(this.money)}`);
  }

  promotionRelegation(add) {
    const topTable = this.standings("top");
    const natTable = this.standings("national");
    if (topTable.length < 4 || natTable.length < 4) return;
    const relegated = topTable.slice(-3).map(r => r.clubId);
    const promoted = natTable.slice(0, 3).map(r => r.clubId);
    for (const cid of relegated) {
      this.clubs[cid].leagueId = "national";
      this.clubs[cid].reputation = Math.round(clamp(this.clubs[cid].reputation - 6, 5, 99));
    }
    for (const cid of promoted) {
      this.clubs[cid].leagueId = "top";
      this.clubs[cid].reputation = Math.round(clamp(this.clubs[cid].reputation + 6, 5, 99));
    }
    add("⬇️", `יורדות: ${relegated.map(c => this.clubs[c].name).join(", ")}`);
    add("⬆️", `עולות: ${promoted.map(c => this.clubs[c].name).join(", ")}`);
    const myClub = this.myClub();
    if (myClub && relegated.includes(myClub.cid)) {
      add("💔", "ירדת ליגה. העונה הבאה תיראה אחרת לגמרי.", true);
      this.me.morale = clamp(this.me.morale - 12, 5, 99);
    }
    if (myClub && promoted.includes(myClub.cid)) {
      add("🎊", "עלית ליגה!", true);
      this.recordHonour("עלייה לליגת העל");
    }
  }

  /** מפתח את כל העולם, ומחזיר את מה שקרה *לך* — כי זה מה שרצית לדעת. */
  developEveryone() {
    const mine = [];
    for (const p of Object.values(this.players)) {
      if (p.retired) { if (p.pid === this.meId) p.age += 1; continue; }
      const share = clamp(p.season.minutes / (SEASON_WEEKS * 90), 0, 1);
      const notes = endOfSeasonDevelopment(p, this.rng, share, this.clubs[p.clubId]);
      if (p.pid === this.meId) mine.push(...notes);
    }
    return mine;
  }

  /**
   * מה בדיוק השתנה בך העונה, תכונה־תכונה.
   * "הכול כאילו מתפתח אבל לא ברור איך ולא מובן עד כמה" — עכשיו כתוב.
   */
  growthReport(before) {
    if (!["youth", "academy", "player", "veteran"].includes(this.stage)) return [];
    const moved = [];
    for (const attr of attrsFor(this.me.position)) {
      const delta = (this.me.detail[attr] ?? 10) - (before[attr] ?? 10);
      if (delta) moved.push([delta, attr]);
    }
    if (!moved.length)
      return [{ icon: "", text: "שום תכונה לא זזה העונה. שנה תקועה." }];
    moved.sort((a, b) => b[0] - a[0]);
    const label = ([, a]) => `${D.DETAIL_NAMES_HE[a]} ${before[a]}→${this.me.detail[a]}`;
    const out = [];
    const ups = moved.filter(pair => pair[0] > 0).map(label);
    const downs = moved.filter(pair => pair[0] < 0).map(label);
    if (ups.length) out.push({ icon: "📈", text: "עלו: " + ups.join(", ") });
    if (downs.length) out.push({ icon: "📉", text: "ירדו: " + downs.join(", ") });
    return out;
  }

  processRetirements() {
    for (const p of Object.values(this.players)) {
      if (p.pid === this.meId || p.retired) continue;
      if (shouldRetire(p, this.rng)) {
        p.retired = true;
        const club = this.clubs[p.clubId];
        if (club) club.squad = club.squad.filter(x => x !== p.pid);
        p.clubId = null;
      }
    }
    for (const club of Object.values(this.clubs)) {
      while (club.squad.length < 20) {
        const kid = generatePlayer(this.rng, club, this.rng.choice(D.POSITIONS),
          { age: this.rng.randint(16, 19) });
        kid.potential = Math.round(clamp(overall(kid) + this.rng.randint(6, 28), 45, 94));
        this.players[kid.pid] = kid;
        club.squad.push(kid.pid);
        assignNumber(club, this.players, kid);
      }
    }
  }

  transferWindow(add) {
    const me = this.me;
    const movers = Object.values(this.players).filter(p =>
      p.pid !== this.meId && !p.retired && p.contract.yearsLeft <= 0 && p.clubId).slice(0, 40);
    for (const p of movers) {
      if (this.rng.random() < 0.35) {
        const target = this.rng.choice(Object.values(this.clubs));
        const old = this.clubs[p.clubId];
        if (old && old.squad.includes(p.pid) && old.squad.length > 16) {
          old.squad = old.squad.filter(x => x !== p.pid);
          target.squad.push(p.pid);
          p.clubId = target.cid;
          assignNumber(target, this.players, p);
        }
      }
      p.contract.yearsLeft = this.rng.randint(1, 4);
    }
    if (["player", "veteran"].includes(this.stage)) {
      this.openTransferMarket(add);
    }
  }

  /**
   * פותח חלון העברות: כל מי שרוצה אותך מניח חבילה על השולחן.
   *
   * הצעה אחת היא לא שוק. מה שהופך העברה להחלטה הוא בדיוק זה שיש עם
   * מה להשוות, ושמי שרוצה אותך יותר יודע שיש לו מתחרים.
   */
  openTransferMarket(add) {
    const suitors = this.transferSuitors();
    if (!suitors.length) return;
    setOffers(this, suitors.map(c => buildOffer(this, c, this.rng)));
    const live = liveOffers(this);
    add("📨", `חלון ההעברות נפתח — ${live.length} `
            + `${live.length > 1 ? "הצעות" : "הצעה"} על השולחן`, true);
    for (const offer of live) {
      const club = this.clubs[offer.cid];
      add("", `   • ${offerClubTag(this, club.cid)} ${club.name} — `
            + `₪${fmt(offer.wage)} לשבוע, ${offer.years} שנים `
            + `(${interestWord(offer)})`);
    }
    // פנייה מחו"ל היא לא עוד שורה ברשימה — זה הרגע שכל שחקן מחכה לו
    const abroad = live.filter(o => isForeign(o.cid));
    if (abroad.length)
      add("", `   🌍 מחו"ל: ${abroad.map(o => this.clubs[o.cid].name).join(", ")}. `
            + `זה כבר לא אותו משחק.`);
    add("", "   אפשר לנהל משא ומתן על כל סעיף. (בתפריט: 'הצעות')");
  }

  /** מי מניח הצעה השנה. אחד לפחות, ולפעמים מרוץ שלם. */
  transferSuitors() {
    const me = this.me;
    const picked = [], seen = new Set();
    const add = club => {
      if (club && !seen.has(club.cid) && club.cid !== me.clubId) {
        seen.add(club.cid);
        picked.push(club);
      }
    };
    // מי שבאמת עקב אחריך כל העונה קודם — הצעה היא סוף של תהליך
    for (const [club] of watchers(this, SCOUT_CHASED)) add(club);
    const target = this.flag("agent_target");
    if (target && this.clubs[target] && this.rng.random() < 0.7) {
      delete this.flags.agent_target;
      add(this.clubs[target]);
    }
    for (const [club] of watchers(this, SCOUT_COURTED))
      if (this.rng.random() < 0.55) add(club);

    // ככל שאתה גדול יותר, כך יותר שמות עולים בישיבות שלא ראית
    let pool = candidateClubs(this).filter(c => !seen.has(c.cid));
    let extra = me.reputation >= 55 ? 1 : 0;
    if (me.reputation >= 75) extra += 1;
    for (let i = 0; i < extra; i++) {
      if (pool.length && this.rng.random() < 0.55) {
        const club = pool.reduce((a, b) => (a.reputation >= b.reputation ? a : b));
        pool = pool.filter(c => c !== club);
        add(club);
      }
    }
    if (!picked.length && pool.length && this.rng.random() < 0.35)
      add(pool.reduce((a, b) => (a.reputation >= b.reputation ? a : b)));
    return picked.slice(0, 5);
  }

  /** חותם על אחת ההצעות שעל השולחן. */
  acceptOffer(cid = null) {
    const live = liveOffers(this);
    if (!live.length) return "אין הצעה פתוחה.";
    const offer = cid ? offerFor(this, cid) : live[0];
    if (!offer || !["open", "improved", "final"].includes(offer.state))
      return "ההצעה הזאת כבר לא על השולחן.";
    const club = this.clubs[offer.cid];
    this.transferMe(club.cid, offer.wage, offer.years);
    if (offer.bonus) this.money += offer.bonus;
    this.flags.squad_role = offer.role;
    if (offer.clause) this.flags.release_clause = offer.clause;
    if (offer.image) this.flags.image_share = offer.image;
    clearOffers(this);
    delete this.flags.wants_transfer;
    this.me.morale = clamp(this.me.morale + 8, 5, 99);
    const extra = offer.bonus ? ` ומענק ₪${fmt(offer.bonus)}` : "";
    return `חתמת ב${club.name} על ₪${fmt(offer.wage)} לשבוע${extra}. `
         + `הובטח לך תפקיד: ${ROLE_NAMES[offer.role] || offer.role}.`;
  }

  /** מבקש שיפור בסעיף אחד בהצעה של מועדון מסוים. */
  negotiateOffer(cid, term) {
    return negotiate(this, cid, term, this.rng).text;
  }

  /** דוחה הצעה אחת, או את כולן אם לא צוין מועדון. */
  rejectOffer(cid = null) {
    const offers = openOffers(this);
    if (!offers.length) return "אין הצעה פתוחה.";
    if (cid) {
      const offer = offerFor(this, cid);
      if (!offer) return "אין הצעה כזאת.";
      offer.state = "withdrawn";
      setOffers(this, offers);
      const club = this.clubs[cid];
      if (liveOffers(this).length)
        return `אמרת לא ל${club ? club.name : "מועדון"}. נשארו הצעות אחרות.`;
    } else {
      clearOffers(this);
    }
    const club = this.myClub();
    if (club) {
      club.fanSupport = clamp(club.fanSupport + 6, 0, 100);
      club.managerTrust = clamp(club.managerTrust + 5, 0, 100);
    }
    return "דחית ונשארת. במועדון שמעו על זה.";
  }

  advanceCareerStage(add) {
    const me = this.me;
    const club = this.myClub();

    if (this.stage === "youth") {
      if (me.age >= 16) {
        this.stage = "academy";
        me.contract = { wage: Math.max(1800, Math.round(wageForOverall(overall(me)) / 3)), yearsLeft: 2 };
        add("📈", "עלית לקבוצת הנוער הבוגרת — ועם החוזה הראשון שלך.", true);
      }
    } else if (this.stage === "academy") {
      if (me.age >= 18 || (club && club.managerTrust >= 55)) {
        this.stage = "player";
        add("📈", "אתה כבר לא נער — אתה שחקן בסגל הבוגרים.", true);
      }
    } else if (this.stage === "player" && me.age >= 31) {
      this.stage = "veteran";
      add("🧓", "עברת לשלב הוותיקים. הניסיון מחליף את הרגליים.", true);
    } else if (this.stage === "veteran") {
      const forced = me.age >= 40 || overall(me) < 45;
      if (this.flag("retired_announced") || forced) {
        this.stage = "retired";
        me.retired = true;
        if (me.clubId) {
          const old = this.clubs[me.clubId];
          if (old) old.squad = old.squad.filter(p => p !== me.pid);
          this.lastClubId = me.clubId;
          me.clubId = null;
        }
        add("🎬", "תלית את הנעליים.", true);
        add("📖", `סה"כ: ${me.career.apps} משחקים, ${me.career.goals} שערים, ` +
                  `${me.career.assists} בישולים, ${this.honours.length} הישגים.`);
        this.setFlag("retired_announced", true);
      }
    }

    if (["coach", "manager", "director", "pundit", "agent", "owner"].includes(this.stage)) {
      if (me.age >= 68) {
        this.stage = "legend";
        this.gameOver = true;
        add("🕰️", "הגיע הזמן לרדת מהבמה. הקריירה הושלמה.", true);
      }
    }

    if (this.stage === "manager" && club && club.boardConfidence <= 12) {
      club.managerName = this.rng.choice(D.MANAGER_NAMES);
      this.managedClubId = null;
      this.stage = "coach";
      add("📉", "פוטרת. ההנהלה איבדה סבלנות.", true);
    }
  }

  // ==================================================================
  // שמירה וטעינה
  // ==================================================================

  toJSON() {
    return {
      v: 1, seed: this.seed, clubs: this.clubs, players: this.players,
      meId: this.meId, stage: this.stage, year: this.year, week: this.week,
      fixtures: this.fixtures, tables: this.tables, cup: this.cup,
      money: this.money, flags: this.flags, honours: this.honours,
      news: this.news.slice(-60), firedEvents: this.firedEvents,
      pendingEventId: this.pendingEventId, pendingEventBody: this.pendingEventBody,
      managedClubId: this.managedClubId, tactics: this.tactics,
      trainingFocus: this.trainingFocus, intensity: this.intensity,
      firstClubId: this.firstClubId, lastClubId: this.lastClubId,
      history: this.history, caps: this.caps, intlGoals: this.intlGoals,
      noStartStreak: this.noStartStreak, gameOver: this.gameOver,
      positionLog: this.positionLog, overallLog: this.overallLog,
      startYear: this.startYear,
      staffMarket: this.staffMarket, finances: this.finances,
      rngState: this.rng.state(), pidCounter: PID_COUNTER,
    };
  }

  static fromJSON(raw) {
    const g = new Game();
    Object.assign(g, {
      seed: raw.seed, clubs: raw.clubs, players: raw.players, meId: raw.meId,
      stage: raw.stage, year: raw.year, week: raw.week, fixtures: raw.fixtures,
      tables: raw.tables, cup: raw.cup, money: raw.money, flags: raw.flags,
      honours: raw.honours, news: raw.news, firedEvents: raw.firedEvents,
      pendingEventId: raw.pendingEventId, pendingEventBody: raw.pendingEventBody,
      managedClubId: raw.managedClubId, tactics: raw.tactics,
      trainingFocus: raw.trainingFocus, intensity: raw.intensity,
      firstClubId: raw.firstClubId, lastClubId: raw.lastClubId,
      history: raw.history, caps: raw.caps, intlGoals: raw.intlGoals,
      noStartStreak: raw.noStartStreak, gameOver: raw.gameOver,
      positionLog: raw.positionLog || [], overallLog: raw.overallLog || [],
      startYear: raw.startYear,
      staffMarket: raw.staffMarket || {}, finances: raw.finances || null,
    });
    g.rng = Rng.fromState(raw.rngState);
    PID_COUNTER = Math.max(PID_COUNTER, raw.pidCounter || 0);
    return g;
  }
}
