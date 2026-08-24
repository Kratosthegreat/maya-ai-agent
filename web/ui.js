// ---------------------------------------------------------------------------
// ממשק המשתמש
// ---------------------------------------------------------------------------

const SAVE_KEY = "fm_career_save_v1";
let game = null;
let view = "menu";
let viewData = null;

const $ = sel => document.querySelector(sel);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// -- שמירה --------------------------------------------------------------

function saveGame() {
  if (!game) return false;
  try {
    localStorage.setItem(SAVE_KEY, JSON.stringify(game.toJSON()));
    return true;
  } catch (err) { return false; }
}
function loadGame() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return null;
    return Game.fromJSON(JSON.parse(raw));
  } catch (err) { return null; }
}
function hasSave() {
  try { return !!localStorage.getItem(SAVE_KEY); } catch (err) { return false; }
}
function clearSave() { try { localStorage.removeItem(SAVE_KEY); } catch (err) {} }

// -- ניווט --------------------------------------------------------------

function go(next, data = null) {
  view = next;
  viewData = data;
  render();
  window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
}

function render() {
  const app = $("#app");
  if (!document.getElementById("scene-defs")) {
    const holder = document.createElement("div");
    holder.id = "scene-defs";
    holder.innerHTML = sceneDefs();
    document.body.appendChild(holder);
  }
  let html = "";
  if (view === "menu") html = screenMenu();
  else if (view === "new") html = screenNew();
  else if (view === "event") html = screenEvent();
  else if (view === "outcome") html = screenOutcome();
  else if (view === "week") html = screenWeek();
  else if (view === "season") html = screenSeason();
  else if (view === "end") html = screenEnd();
  else html = screenMain();
  app.innerHTML = html;
  bind();
}

// ---------------------------------------------------------------------------
// מסכים
// ---------------------------------------------------------------------------

function screenMenu() {
  const saved = hasSave();
  return `
  <div class="screen menu flush">
    <div class="scene-frame">${SCENES.stadium()}</div>
    <div class="hero" style="padding-top:6px">
      <div class="eyebrow">משחק ניהול כדורגל</div>
      <h1 class="display">קריירה</h1>
      <div class="underline"></div>
      <p class="sub">מנער בקבוצת הנוער ועד המשרד של הבעלים. כל שבוע זו החלטה,
      וכל החלטה נשארת איתך עד סוף הדרך.</p>
    </div>
    <div class="actions">
      ${saved ? `<button class="btn primary" data-act="continue">להמשיך קריירה</button>` : ""}
      <button class="btn ${saved ? "" : "primary"}" data-act="new">
        <span class="k">${saved ? "קריירה חדשה" : "להתחיל קריירה"}</span>
        ${saved ? `<span class="hint">מוחק את השמורה</span>` : ""}
      </button>
    </div>
    <div class="card">
      <div class="eyebrow">מה יש כאן</div>
      <div class="notes">
        <div class="note"><span class="ico">⚽</span><span>3 ליגות, 32 מועדונים, סימולציה מלאה של כל משחק בעונה.</span></div>
        <div class="note"><span class="ico">📖</span><span>28 צמתי עלילה — פציעות, מריבות, הצעות מאירופה, פרישה.</span></div>
        <div class="note"><span class="ico">🎓</span><span>מה שתלמד בזמן הקריירה יקבע מה תעשה אחריה.</span></div>
      </div>
    </div>
    <p class="muted center">המשחק נשמר בדפדפן הזה אוטומטית.</p>
  </div>`;
}

function screenNew() {
  const state = viewData || (viewData = { name: "", position: "ST", club: "hapoel_carmel", age: 15 });
  const clubs = D.CLUBS.filter(c => c[3] !== "euro").sort((a, b) => a[4] - b[4]);
  return `
  <div class="screen">
    <div class="hero" style="padding-top:14px">
      <div class="eyebrow">קריירה חדשה</div>
      <h1 class="display" style="font-size:44px">מי אתה?</h1>
    </div>

    <div class="card">
      <label class="eyebrow" for="pname">שם השחקן</label>
      <input type="text" id="pname" maxlength="24" placeholder="עומר לוי" value="${esc(state.name)}">
    </div>

    <div class="card">
      <div class="eyebrow">עמדה</div>
      <div class="chips">
        ${D.POSITIONS.map(p => `<button class="chip" data-pos="${p}"
          aria-pressed="${state.position === p}">${D.POSITION_NAMES_HE[p]}</button>`).join("")}
      </div>
    </div>

    <div class="card">
      <div class="eyebrow">גיל התחלה</div>
      <div class="chips">
        ${[13, 14, 15, 16, 17, 18].map(a => `<button class="chip" data-age="${a}"
          aria-pressed="${state.age === a}">${a}</button>`).join("")}
      </div>
      <p class="muted">${state.age <= 15
        ? "מתחילים בקבוצת הנוער: בית ספר, מגרש שכונתי, ומאמן שעוד לא יודע איך קוראים לך. הדרך ארוכה — והתקרה גבוהה."
        : "ישר לקבוצת הנוער הבוגרת, עם חוזה ראשון ופחות זמן להתפתח."}</p>
    </div>

    <div class="card">
      <div class="eyebrow">מועדון פתיחה</div>
      <select id="pclub">
        ${clubs.map(c => `<option value="${c[0]}" ${state.club === c[0] ? "selected" : ""}>
          ${esc(c[1])} — מוניטין ${c[4]}</option>`).join("")}
      </select>
      <p class="muted">מועדון חלש = דקות משחק מיד. מועדון חזק = ספסל, אבל במה גדולה יותר.</p>
    </div>

    <div class="actions">
      <button class="btn primary" data-act="start">להתחיל</button>
      <button class="btn ghost" data-act="menu">חזרה</button>
    </div>
  </div>`;
}

function strip() {
  const me = game.me;
  const club = game.myClub();
  const stage = D.CAREER_STAGES_HE[game.stage] || game.stage;
  return `
  <div class="strip">
    <span class="who">${esc(me.name)}</span>
    <span class="meta">${stage}${club ? " · " + esc(club.name) : ""}</span>
    <span class="spacer"></span>
    <span class="meta">${game.year}/${game.year + 1} · שבוע ${game.week}/${SEASON_WEEKS}</span>
  </div>`;
}

function dock(showPlay) {
  const items = [["main", "ראשי"], ["profile", "פרופיל"], ["table", "טבלה"],
                 ["squad", "סגל"], ["news", "יומן"]];
  const offer = !!game.flag("pending_offer");
  return `<div class="dock">
    ${showPlay ? `<button class="btn primary" data-act="play">לשחק את השבוע</button>` : ""}
    <nav class="nav">${items.map(([k, l]) =>
      `<button data-go="${k}" aria-current="${view === k}">${l}${
        k === "main" && offer ? '<span class="dot"></span>' : ""}</button>`).join("")}</nav>
  </div>`;
}

function screenMain() {
  if (view === "profile") return strip() + screenProfile() + dock(false);
  if (view === "table") return strip() + screenTable() + dock(false);
  if (view === "squad") return strip() + screenSquad() + dock(false);
  if (view === "news") return strip() + screenNews() + dock(false);
  return strip() + screenHub() + dock(true);
}

function screenHub() {
  const me = game.me;
  const club = game.myClub();
  const isPlayer = ["academy", "player", "veteran"].includes(game.stage);
  const actions = game.availableActions();
  const offer = game.flag("pending_offer");

  let fixture = "";
  const fx = game.myFixture();
  if (fx) {
    const [homeId, awayId] = fx;
    const home = game.clubs[homeId], away = game.clubs[awayId];
    const comp = CUP_WEEKS[game.week] || "ליגה";
    const rival = club && club.cid === homeId ? away : home;
    const where = club && club.cid === homeId ? "בית" : "חוץ";
    fixture = `
      <div class="scoreboard">
        <div class="eyebrow">${esc(comp)} · ${where}</div>
        <div class="scoreline">
          <div class="side">${crest(home, 30)}<span class="nm ${
            club && club.cid === homeId ? "mine" : ""}">${esc(home.name)}</span></div>
          <div class="versus">נגד</div>
          <div class="side away">${crest(away, 30)}<span class="nm ${
            club && club.cid === awayId ? "mine" : ""}">${esc(away.name)}</span></div>
        </div>
        <div class="scoreline" style="font-size:12px">
          <div class="side">${formGuide(home)}</div>
          <div></div>
          <div class="side away">${formGuide(away)}</div>
        </div>
        <div class="muted">${esc(rival.nickname)} · מוניטין ${rival.reputation}</div>
      </div>`;
  } else {
    fixture = `<div class="scoreboard"><div class="eyebrow">השבוע</div>
      <div>אין משחק — שבוע של עבודה.</div></div>`;
  }

  const status = isPlayer ? `
    <div class="stat-grid">
      <div class="stat"><div class="n">${overall(me)}</div><div class="l">כללי</div></div>
      <div class="stat"><div class="n">${Math.round(me.form)}</div><div class="l">כושר</div></div>
      <div class="stat"><div class="n">${Math.round(me.fitness)}</div><div class="l">רעננות</div></div>
    </div>
    ${me.injuryWeeks > 0 ? `<div class="note"><span class="ico">🚑</span><span>${esc(me.injuryName)} — עוד ${me.injuryWeeks} שבועות</span></div>` : ""}
    ${club ? `<div class="attr"><span>אמון המאמן</span><span class="val">${Math.round(club.managerTrust)}</span>
      <span class="bar"><i style="width:${Math.round(club.managerTrust)}%"></i></span></div>` : ""}
  ` : club ? `
    <div class="stat-grid">
      <div class="stat"><div class="n">${game.leaguePosition()}</div><div class="l">מקום</div></div>
      <div class="stat"><div class="n">${Math.round(club.boardConfidence)}</div><div class="l">הנהלה</div></div>
      <div class="stat"><div class="n">${Math.round(club.fanSupport)}</div><div class="l">קהל</div></div>
    </div>
    <div class="muted">ציפיית ההנהלה: ${esc(club.seasonExpectation)}</div>
  ` : `<div class="muted">ידע אימון ${Math.round(me.coaching)} · תקשורת ${Math.round(me.mediaSkill)} · עסקים ${Math.round(me.business)}</div>`;

  return `
  <div class="screen">
    ${fixture}
    <div class="card">
      <div class="eyebrow">המצב שלך</div>
      ${status}
      <div class="muted">בחשבון: ₪${fmt(game.money)}</div>
    </div>

    ${offer ? `
    <div class="card" style="border-color:var(--accent)">
      <div class="eyebrow">הצעת העברה</div>
      <div><strong>${esc(game.clubs[offer.club].name)}</strong> — ₪${fmt(offer.wage)} לשבוע</div>
      <div class="muted">החוזה הנוכחי שלך: ₪${fmt(me.contract.wage)} לשבוע</div>
      <div class="btn-row">
        <button class="btn primary" data-act="accept">לחתום</button>
        <button class="btn" data-act="reject">לדחות</button>
      </div>
    </div>` : ""}

    <div class="card">
      <div class="eyebrow">על מה נעבוד השבוע</div>
      <div class="chips">
        ${actions.map(([k, l]) => `<button class="chip" data-focus="${k}"
          aria-pressed="${game.trainingFocus === k}">${esc(l)}</button>`).join("")}
      </div>
      ${isPlayer ? `
      <hr class="rule">
      <div class="eyebrow">עצימות</div>
      <div class="chips">
        ${[[1.0, "רגילה"], [1.3, "גבוהה"], [0.75, "קלה"]].map(([v, l]) =>
          `<button class="chip" data-int="${v}" aria-pressed="${game.intensity === v}">${l}</button>`).join("")}
      </div>` : ""}
    </div>

    ${["manager", "coach"].includes(game.stage) ? tacticsCard() : ""}

    <button class="btn ghost wide" data-act="menu">תפריט ראשי</button>
  </div>`;
}

function tacticsCard() {
  const t = game.tactics;
  return `
  <div class="card">
    <div class="eyebrow">טקטיקה</div>
    <div class="chips">
      ${Object.keys(D.FORMATIONS).map(f => `<button class="chip" data-form="${f}"
        aria-pressed="${t.formation === f}">${f}</button>`).join("")}
    </div>
    <div class="chips">
      ${Object.entries(D.MENTALITIES).map(([k, v]) => `<button class="chip" data-ment="${k}"
        aria-pressed="${t.mentality === k}">${esc(v[0])}</button>`).join("")}
    </div>
    <div class="chips">
      ${Object.entries(D.PRESSING).map(([k, v]) => `<button class="chip" data-press="${k}"
        aria-pressed="${t.pressing === k}">${esc(v[0])}</button>`).join("")}
    </div>
  </div>`;
}

function screenWeek() {
  const report = viewData;
  const me = game.me;
  let html = `<div class="screen">`;

  if (report.match) {
    const { result, home, away, competition, penalties } = report.match;
    const club = game.myClub();
    const goals = result.events.filter(e => e.kind === "goal")
      .sort((a, b) => a.minute - b.minute);
    html += `
    <div class="scoreboard result">
      <span class="comp-tag">${esc(competition)}</span>
      <div class="scoreline">
        <div class="side">${crest(home, 34)}<span class="nm ${
          club && club.cid === home.cid ? "mine" : ""}">${esc(home.name)}</span></div>
        <div class="score">${result.homeGoals} : ${result.awayGoals}</div>
        <div class="side away">${crest(away, 34)}<span class="nm ${
          club && club.cid === away.cid ? "mine" : ""}">${esc(away.name)}</span></div>
      </div>
      ${penalties ? `<div class="muted center">הוכרע בפנדלים — ${esc(penalties)}</div>` : ""}
      ${goals.length ? goalTimeline(result, home, away, me.pid) : ""}
      ${goals.length ? `<div class="goals">${goals.map((e, i) => `
        <div class="goal-row ${e.playerId === me.pid ? "mine" : ""}" style="animation-delay:${i * 60}ms">
          <span class="min">${e.minute}'</span>
          <span>${esc(game.players[e.playerId] ? game.players[e.playerId].name : "")}</span>
          <span class="muted">${esc(e.clubId === home.cid ? home.name : away.name)}</span>
        </div>`).join("")}</div>` : ""}
      <div class="muted">${esc(result.commentary[0] || "")}</div>
    </div>`;

    // ההרכב על המגרש — רק כשהייתי בו
    const myLineup = club && club.cid === home.cid ? result.homeLineup : result.awayLineup;
    if (club && myLineup.includes(me.pid)) {
      const formation = club.formation;
      html += `<div class="card">
        <div class="eyebrow">ההרכב · ${esc(formation)}</div>
        ${pitch(myLineup, formation, game.players, me.pid, club)}
      </div>`;
    }
  }

  if (report.match) {
    const mine = report.match.result.events.filter(
      e => e.kind === "goal" && e.playerId === me.pid);
    if (mine.length) {
      html += `<div class="my-goal-flash">
        <span class="big">${mine.length === 1 ? "גול!" : mine.length + " גולים!"}</span>
        <span>${mine.map(e => e.minute + "'").join(" · ")} — ${esc(me.name)}</span>
      </div>`;
    }
  }

  if (report.seniorMatch) {
    const { result, home, away } = report.seniorMatch;
    const club = game.myClub();
    const outcome = club ? resultFor(result, club.cid) : "D";
    const label = { W: "ניצחון", D: "תיקו", L: "הפסד" }[outcome];
    html += `<div class="card">
      <div class="eyebrow">הקבוצה הבוגרת</div>
      <div class="crest-row">
        ${crest(home, 22)}
        <span class="nm">${esc(home.name)} ${result.homeGoals} : ${result.awayGoals} ${esc(away.name)}</span>
        ${crest(away, 22)}
      </div>
      <div class="muted">${esc(label)} — קראת על זה בדרך לאימון.</div>
    </div>`;
  }

  if (report.youth) html += youthCard(report.youth);
  if (report.personal) html += personalCard(report.personal);

  const notes = (report.training || []).concat(report.notes || []);
  if (notes.length) {
    html += `<div class="card"><div class="eyebrow">השבוע</div><div class="notes">
      ${notes.map(n => `<div class="note"><span class="ico">${n.icon}</span><span>${esc(n.text)}</span></div>`).join("")}
    </div></div>`;
  }

  html += `<button class="btn primary wide" data-act="after-week">המשך</button></div>`;
  return strip() + html;
}

function youthCard(y) {
  const club = game.myClub();
  const rival = game.clubs[y.rivalCid];
  const label = { W: "ניצחון", D: "תיקו", L: "הפסד" }[y.outcome];
  const cls = { W: "w", D: "d", L: "l" }[y.outcome];
  const bits = [];
  if (y.goals) bits.push(y.goals === 1 ? "שער אחד" : `${y.goals} שערים`);
  if (y.assists) bits.push(y.assists === 1 ? "בישול אחד" : `${y.assists} בישולים`);
  const ratingCls = y.rating >= 7.5 ? "good" : y.rating < 5.5 ? "bad" : "";
  return `<div class="card youth-card">
    <div class="scene-frame inset">${SCENES.youthpitch()}</div>
    <span class="comp-tag">ליגת הנוער</span>
    <div class="youth-score">
      ${club ? crest(club, 26) : ""}
      <span>${y.teamGoals} : ${y.oppGoals}</span>
      ${rival ? crest(rival, 26) : ""}
      <span class="vs">מול ${esc(y.rival)}</span>
    </div>
    <div class="perf">
      <div class="rating ${ratingCls}">${y.rating.toFixed(1)}</div>
      <div class="detail">
        <strong>${label}</strong>
        <span>${bits.length ? esc(bits.join(" · ")) : "עוד משחק בדרך."}</span>
      </div>
    </div>
  </div>`;
}

function personalCard(p) {
  if (p.status === "manager") {
    const label = { W: "ניצחון", D: "תיקו", L: "הפסד" }[p.outcome];
    const cls = { W: "w", D: "d", L: "l" }[p.outcome];
    return `<div class="card">
      <div class="eyebrow">מהספסל</div>
      <div><span class="pill ${cls}">${label}</span></div>
      <div class="muted">אמון ההנהלה ${p.board}% · אהדת הקהל ${p.fans}%</div>
    </div>`;
  }
  if (p.status === "bench")
    return `<div class="card"><div class="eyebrow">אתה</div>
      <div class="note"><span class="ico">🪑</span><span>ישבת 90 דקות על הספסל.</span></div>
      <div class="muted">${game.noStartStreak === 1 ? "משחק אחד" :
        game.noStartStreak + " משחקים"} ברצף בלי להתחיל.</div></div>`;
  if (p.status === "injured")
    return `<div class="card"><div class="eyebrow">אתה</div>
      <div class="note"><span class="ico">🚑</span><span>${esc(p.injuryName)} — עוד ${p.weeks} שבועות.</span></div></div>`;

  const cls = p.rating >= 7.5 ? "good" : p.rating < 5.5 ? "bad" : "";
  const bits = [];
  if (p.goals) bits.push(p.goals === 1 ? "שער אחד" : `${p.goals} שערים`);
  if (p.assists) bits.push(p.assists === 1 ? "בישול אחד" : `${p.assists} בישולים`);
  if (p.motm) bits.push("⭐ מצטיין המשחק");
  return `<div class="card">
    <div class="eyebrow">${p.status === "sub" ? "נכנסת מהספסל" : "ההופעה שלך"}</div>
    <div class="perf">
      <div class="rating ${cls}">${p.rating.toFixed(1)}</div>
      <div class="detail">
        <strong>${p.status === "sub" ? p.minutes + " דקות" : "90 דקות"}</strong>
        <span>${bits.length ? esc(bits.join(" · ")) : "משחק שקט."}</span>
      </div>
    </div>
  </div>`;
}

function screenEvent() {
  const event = game.pendingEvent();
  if (!event) { go("main"); return ""; }
  return `
  <div class="takeover flush">
    <div class="scene-frame">${sceneFor(event.eid, game.stage)}</div>
    <div class="kicker">${esc(D.CAREER_STAGES_HE[game.stage] || "")} · שבוע ${game.week}</div>
    <h2 class="display">${esc(event.title)}</h2>
    <hr class="rule">
    <div class="body">${esc(game.pendingEventText())}</div>
    ${contextStrip()}
    <div class="actions" style="margin-top:auto">
      ${event.choices.map((c, i) => `<button class="btn" data-choice="${i}">
        <span class="k">${esc(c.label)}</span>
        ${c.hint ? `<span class="hint">${esc(c.hint)}</span>` : ""}
      </button>`).join("")}
    </div>
  </div>`;
}

/** רצועה קצרה עם המצב שלך — כדי שההחלטה תתקבל עם הנתונים מול העיניים. */
function contextStrip() {
  const me = game.me;
  const club = game.myClub();
  const isPlayer = ["youth", "academy", "player", "veteran"].includes(game.stage);
  const pills = [];
  pills.push(`<span class="cpill">גיל <b>${me.age}</b></span>`);
  if (isPlayer) {
    pills.push(`<span class="cpill">כללי <b>${overall(me)}</b></span>`);
    pills.push(`<span class="cpill">מורל <b>${Math.round(me.morale)}</b></span>`);
    if (club) pills.push(`<span class="cpill">אמון המאמן <b>${Math.round(club.managerTrust)}</b></span>`);
    if (me.injuryWeeks > 0)
      pills.push(`<span class="cpill accent">פצוע <b>${me.injuryWeeks}ש</b></span>`);
  } else {
    pills.push(`<span class="cpill">ידע אימון <b>${Math.round(me.coaching)}</b></span>`);
    if (club) pills.push(`<span class="cpill">הנהלה <b>${Math.round(club.boardConfidence)}</b></span>`);
  }
  if (game.money > 0) pills.push(`<span class="cpill">₪<b>${fmt(game.money)}</b></span>`);
  return `<div class="context-strip">${pills.join("")}</div>`;
}

function screenOutcome() {
  return `
  <div class="takeover${viewData.scene ? " flush" : ""}">
    ${viewData.scene ? `<div class="scene-frame">${viewData.scene}</div>` : ""}
    <div class="kicker">מה שקרה</div>
    <h2 class="display">${esc(viewData.title)}</h2>
    <hr class="rule">
    <div class="outcome">${esc(viewData.text)}</div>
    <div class="actions" style="margin-top:auto">
      <button class="btn primary" data-act="after-outcome">להמשיך</button>
    </div>
  </div>`;
}

function screenSeason() {
  const s = viewData;
  return `
  <div class="screen flush">
    <div class="scene-frame season-hero">
      ${SCENES.trophy()}
      <span class="season-title">${esc(s.title)}</span>
    </div>
    <div class="card"><div class="notes">
      ${s.lines.map(l => `<div class="note ${l.strong ? "strong" : ""}">
        <span class="ico">${l.icon}</span><span>${esc(l.text)}</span></div>`).join("")}
    </div></div>
    <button class="btn primary wide" data-act="after-season">לעונה הבאה</button>
  </div>`;
}

function screenProfile() {
  const me = game.me;
  const club = game.myClub();
  const isPlayer = ["academy", "player", "veteran"].includes(game.stage);
  const s = me.season, c = me.career;
  return `
  <div class="screen">
    ${isPlayer ? playerCard(me, club, game.stage) : `
    <div class="card">
      <div class="eyebrow">${esc(D.CAREER_STAGES_HE[game.stage] || game.stage)}</div>
      <div class="kit-row">
        ${club ? crest(club, 58) : ""}
        <div class="kit-meta">
          <span class="display big">${esc(me.name)}</span>
          <span class="muted">בן ${me.age} · ${esc(positionHe(me))} · ${esc(me.nationality)}</span>
          ${club ? `<span class="muted">${esc(club.name)}</span>` : ""}
        </div>
      </div>
    </div>`}
    ${me.traits.length ? `<div class="card">
      <div class="eyebrow">אופי</div>
      <div class="chips">${me.traits.map(t =>
        `<span class="chip" style="cursor:default">${esc(D.TRAITS[t] ? D.TRAITS[t].name : t)}</span>`).join("")}</div>
      <div class="muted">${me.traits.map(t => D.TRAITS[t] ? esc(D.TRAITS[t].desc) : "").join(" ")}</div>
    </div>` : ""}

    ${isPlayer ? `
    <div class="card">
      <div class="eyebrow">דירוג ${overall(me)} · פוטנציאל ${me.potential}</div>
      <div class="attrs">
        ${D.ATTRIBUTES.map(a => `<div class="attr">
          <span>${D.ATTRIBUTE_NAMES_HE[a]}</span>
          <span class="val">${me.attributes[a]}</span>
          <span class="bar"><i style="width:${me.attributes[a]}%"></i></span>
        </div>`).join("")}
      </div>
      <hr class="rule">
      <div class="attr"><span>מורל</span><span class="val">${Math.round(me.morale)}</span>
        <span class="bar soft"><i style="width:${Math.round(me.morale)}%"></i></span></div>
      <div class="attr"><span>מוניטין</span><span class="val">${Math.round(me.reputation)}</span>
        <span class="bar soft"><i style="width:${Math.round(me.reputation)}%"></i></span></div>
    </div>

    <div class="card">
      <div class="eyebrow">העונה</div>
      <div class="stat-grid">
        <div class="stat"><div class="n">${s.apps}</div><div class="l">משחקים</div></div>
        <div class="stat"><div class="n">${s.goals}</div><div class="l">שערים</div></div>
        <div class="stat"><div class="n">${avgRating(s).toFixed(1)}</div><div class="l">ציון</div></div>
      </div>
      <div class="eyebrow">בקריירה</div>
      <div class="stat-grid">
        <div class="stat"><div class="n">${c.apps}</div><div class="l">משחקים</div></div>
        <div class="stat"><div class="n">${c.goals}</div><div class="l">שערים</div></div>
        <div class="stat"><div class="n">${c.assists}</div><div class="l">בישולים</div></div>
      </div>
    </div>

    ${game.history.length ? `
    <div class="card">
      <div class="eyebrow">שערים לפי עונה</div>
      ${columns(seasonGoalsData(), { alt: "שערים בכל עונה" })}
    </div>` : ""}

    <div class="card">
      <div class="eyebrow">חוזה</div>
      <div>₪${fmt(me.contract.wage)} לשבוע · ${me.contract.yearsLeft} עונות</div>
      <div class="muted">שווי שוק מוערך: ₪${fmt(playerValue(me))}</div>
    </div>` : `
    <div class="card">
      <div class="eyebrow">הכישורים שלך</div>
      <div class="attrs">
        <div class="attr"><span>ידע אימון</span><span class="val">${Math.round(me.coaching)}</span>
          <span class="bar"><i style="width:${Math.round(me.coaching)}%"></i></span></div>
        <div class="attr"><span>תקשורת</span><span class="val">${Math.round(me.mediaSkill)}</span>
          <span class="bar"><i style="width:${Math.round(me.mediaSkill)}%"></i></span></div>
        <div class="attr"><span>עסקים</span><span class="val">${Math.round(me.business)}</span>
          <span class="bar"><i style="width:${Math.round(me.business)}%"></i></span></div>
      </div>
      <div class="muted">תעודות אימון: ${me.badges}/4</div>
      <hr class="rule">
      <div class="eyebrow">קריירת השחקן</div>
      <div class="stat-grid">
        <div class="stat"><div class="n">${c.apps}</div><div class="l">משחקים</div></div>
        <div class="stat"><div class="n">${c.goals}</div><div class="l">שערים</div></div>
        <div class="stat"><div class="n">${game.caps}</div><div class="l">נבחרת</div></div>
      </div>
    </div>`}

    ${isPlayer ? `
    <div class="card">
      <div class="eyebrow">הכישורים לקריירה שאחרי</div>
      <div class="attrs">
        <div class="attr"><span>ידע אימון</span><span class="val">${Math.round(me.coaching)}</span>
          <span class="bar soft"><i style="width:${Math.round(me.coaching)}%"></i></span></div>
        <div class="attr"><span>תקשורת</span><span class="val">${Math.round(me.mediaSkill)}</span>
          <span class="bar soft"><i style="width:${Math.round(me.mediaSkill)}%"></i></span></div>
        <div class="attr"><span>עסקים</span><span class="val">${Math.round(me.business)}</span>
          <span class="bar soft"><i style="width:${Math.round(me.business)}%"></i></span></div>
      </div>
      <div class="muted">תעודות אימון: ${me.badges}/4 — פותחות את מסלול האימון והניהול.</div>
    </div>` : ""}
  </div>`;
}

function seasonGoalsData() {
  const rows = [];
  let previous = 0;
  for (const h of game.history) {
    rows.push({ label: String(h.year).slice(2), value: Math.max(0, h.goals - previous) });
    previous = h.goals;
  }
  const current = game.me.season.goals;
  if (["academy", "player", "veteran"].includes(game.stage))
    rows.push({ label: String(game.year).slice(2), value: current });
  return rows.slice(-8);
}

function screenTable() {
  const club = game.myClub();
  const leagueId = (viewData && viewData.league) || game.myLeague() || "top";
  const rows = game.standings(leagueId);
  const isDomestic = leagueId !== "euro";
  return `
  <div class="screen">
    <div class="card">
      <div class="chips">
        ${D.LEAGUES.map(l => `<button class="chip" data-league="${l.id}"
          aria-pressed="${leagueId === l.id}">${esc(l.name)}</button>`).join("")}
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>#</th><th style="text-align:right">קבוצה</th><th>מש</th>
            <th>הפרש</th><th>נק</th><th>טופס</th></tr></thead>
          <tbody>
            ${rows.map((r, i) => {
              const c = game.clubs[r.clubId];
              const mine = club && c.cid === club.cid;
              const cls = [mine ? "me" : "",
                isDomestic && leagueId === "national" && i < 2 ? "up" : "",
                isDomestic && leagueId === "top" && i >= rows.length - 2 ? "down" : ""].join(" ");
              return `<tr class="${cls}"><td>${i + 1}</td>
                <td class="club"><span class="crest-row">${crest(c, 20)}<span class="nm">${esc(c.name)}</span></span></td>
                <td>${r.played}</td>
                <td><span class="num">${r.gd > 0 ? "+" : ""}${r.gd}</span></td>
                <td class="pts">${r.points}</td>
                <td class="form-cell">${formGuide(c)}</td></tr>`;
            }).join("")}
          </tbody>
        </table>
      </div>
      ${leagueId === "top" ? `<div class="muted">שתי האחרונות יורדות לליגה הלאומית.</div>` : ""}
      ${leagueId === "national" ? `<div class="muted">שתי הראשונות עולות לליגת העל.</div>` : ""}
    </div>
    ${club && club.leagueId === leagueId && game.positionLog.length > 2 ? `
    <div class="card">
      <div class="eyebrow">המיקום שלך לאורך העונה</div>
      ${positionLine(game.positionLog, rows.length, { alt: "מיקום בטבלה לפי מחזור" })}
    </div>` : ""}
    ${game.cup && game.cup.teams ? `<div class="card">
      <div class="eyebrow">גביע המדינה</div>
      <div class="muted">${game.cup.winner
        ? "זוכה: " + esc(game.clubs[game.cup.winner].name)
        : "שלב: " + esc(game.cup.round) + " · " + game.cup.teams.length + " קבוצות נותרו"}</div>
    </div>` : ""}
  </div>`;
}

function screenSquad() {
  const club = game.myClub();
  if (!club) return `<div class="screen"><div class="card">אין לך מועדון כרגע.</div></div>`;
  const squad = club.squad.map(p => game.players[p]).filter(Boolean)
    .sort((a, b) => overall(b) - overall(a));
  return `
  <div class="screen">
    <div class="card">
      <div class="crest-row">${crest(club, 38)}<span class="nm">
        <strong>${esc(club.name)}</strong><br><span class="muted">${esc(club.nickname)}</span></span></div>
      <div class="muted">מאמן: ${esc(club.managerName)} · מערך: ${esc(club.formation)}
        · מתקנים ${club.trainingFacilities}</div>
      ${formGuide(club) ? `<div>${formGuide(club)}</div>` : ""}
      <hr class="rule">
      ${squad.map(p => `<div class="squad-row ${p.pid === game.meId ? "me" : ""}">
        <span><span class="num">${p.number || ""}</span> ${esc(p.name)}${
          p.injuryWeeks > 0 ? ` <span class="muted">🚑${p.injuryWeeks}ש</span>` : ""}</span>
        <span class="pos">${esc(positionHe(p))} · ${p.age}</span>
        <span class="ovr">${overall(p)}</span>
      </div>`).join("")}
    </div>
  </div>`;
}

function screenNews() {
  return `
  <div class="screen">
    ${game.honours.length ? `<div class="card">
      <div class="eyebrow">הישגים</div>
      ${game.honours.slice().reverse().map(h => {
        const [yr, ...rest] = h.split(": ");
        return `<div class="honour"><span class="yr">${esc(yr)}</span><span>${trophy()} ${esc(rest.join(": "))}</span></div>`;
      }).join("")}
    </div>` : ""}
    ${game.history.length ? `<div class="card">
      <div class="eyebrow">עונות</div>
      ${game.history.slice().reverse().map(h => `<div class="honour">
        <span class="yr">${h.year}</span>
        <span>${esc(D.CAREER_STAGES_HE[h.stage] || h.stage)} · ${esc(h.club)} — ${h.apps} משחקים, ${h.goals} שערים</span>
      </div>`).join("")}
    </div>` : ""}
    <div class="card">
      <div class="eyebrow">יומן</div>
      <div class="notes">
        ${game.news.slice(-25).reverse().map(n =>
          `<div class="note"><span class="ico">·</span><span>${esc(n)}</span></div>`).join("")
          || '<div class="muted">עוד לא קרה כלום. זה יגיע.</div>'}
      </div>
    </div>
  </div>`;
}

function screenEnd() {
  const me = game.me;
  const score = game.honours.length * 2 + me.career.apps / 100 + game.caps / 10;
  const verdict = score > 18 ? "אגדה. ילדים ייוולדו עם השם שלך על הגב."
    : score > 10 ? "קריירה גדולה. האוהדים יזכרו כל אחד מהתארים."
    : score > 5 ? "קריירה מכובדת מאוד. עשית את זה כמו שצריך."
    : score > 2 ? "קריירה יפה. לא כולם מגיעים עד לשם."
    : "לא הכל הלך. אבל שיחקת כדורגל בשביל להתפרנס — וזה משהו.";
  return `
  <div class="screen">
    <div class="hero">
      <div class="eyebrow">סוף הדרך</div>
      <h1 class="display" style="font-size:52px">${esc(me.name)}</h1>
      <p class="sub">${esc(verdict)}</p>
    </div>
    <div class="card">
      <div class="stat-grid">
        <div class="stat"><div class="n">${me.career.apps}</div><div class="l">משחקים</div></div>
        <div class="stat"><div class="n">${me.career.goals}</div><div class="l">שערים</div></div>
        <div class="stat"><div class="n">${game.honours.length}</div><div class="l">הישגים</div></div>
      </div>
      <div class="muted center">הון: ₪${fmt(game.money)} · ${game.caps} הופעות בנבחרת</div>
    </div>
    ${game.honours.length ? `<div class="card"><div class="eyebrow">ארון התארים</div>
      ${game.honours.map(h => {
        const [yr, ...rest] = h.split(": ");
        return `<div class="honour"><span class="yr">${esc(yr)}</span><span>${trophy()} ${esc(rest.join(": "))}</span></div>`;
      }).join("")}</div>` : ""}
    <button class="btn primary wide" data-act="restart">קריירה חדשה</button>
  </div>`;
}

// ---------------------------------------------------------------------------
// אירועי לחיצה
// ---------------------------------------------------------------------------

function bind() {
  const app = $("#app");
  app.querySelectorAll("[data-go]").forEach(el =>
    el.addEventListener("click", () => go(el.dataset.go)));
  app.querySelectorAll("[data-choice]").forEach(el =>
    el.addEventListener("click", () => resolveChoice(+el.dataset.choice)));
  app.querySelectorAll("[data-focus]").forEach(el =>
    el.addEventListener("click", () => { game.setAction(el.dataset.focus); render(); }));
  app.querySelectorAll("[data-int]").forEach(el =>
    el.addEventListener("click", () => { game.intensity = +el.dataset.int; render(); }));
  app.querySelectorAll("[data-pos]").forEach(el =>
    el.addEventListener("click", () => { viewData.position = el.dataset.pos; render(); }));
  app.querySelectorAll("[data-age]").forEach(el =>
    el.addEventListener("click", () => { viewData.age = +el.dataset.age; render(); }));
  app.querySelectorAll("[data-league]").forEach(el =>
    el.addEventListener("click", () => go("table", { league: el.dataset.league })));
  app.querySelectorAll("[data-form]").forEach(el =>
    el.addEventListener("click", () => { game.tactics.formation = el.dataset.form; render(); }));
  app.querySelectorAll("[data-ment]").forEach(el =>
    el.addEventListener("click", () => { game.tactics.mentality = el.dataset.ment; render(); }));
  app.querySelectorAll("[data-press]").forEach(el =>
    el.addEventListener("click", () => { game.tactics.pressing = el.dataset.press; render(); }));

  const nameInput = $("#pname");
  if (nameInput) nameInput.addEventListener("input", e => { viewData.name = e.target.value; });
  const clubSelect = $("#pclub");
  if (clubSelect) clubSelect.addEventListener("change", e => { viewData.club = e.target.value; });

  app.querySelectorAll("[data-act]").forEach(el =>
    el.addEventListener("click", () => act(el.dataset.act)));
}

function act(what) {
  if (what === "new") { go("new", { name: "", position: "ST", club: "hapoel_carmel", age: 15 }); }
  else if (what === "menu") { if (game) saveGame(); go("menu"); }
  else if (what === "continue") {
    const loaded = loadGame();
    if (!loaded) { alert("לא נמצאה שמורה תקינה."); return; }
    game = loaded;
    go(game.gameOver ? "end" : "main");
  }
  else if (what === "start") {
    const name = (viewData.name || "").trim() || "עומר לוי";
    game = Game.newGame(name, viewData.position, viewData.club, viewData.age);
    saveGame();
    go("main");
  }
  else if (what === "play") playWeek();
  else if (what === "after-week") afterWeek();
  else if (what === "after-outcome") afterOutcome();
  else if (what === "after-season") { saveGame(); go(game.gameOver ? "end" : "main"); }
  else if (what === "accept") { showOutcome("הצעת העברה", game.acceptOffer()); }
  else if (what === "reject") { showOutcome("הצעת העברה", game.rejectOffer()); }
  else if (what === "restart") { clearSave(); game = null; go("menu"); }
}

let pendingSeason = null;

function playWeek() {
  const report = game.advanceWeek();
  window.lastReport = report;
  pendingSeason = report.seasonEnded ? report.seasonSummary : null;
  saveGame();
  go("week", report);
}

function afterWeek() {
  if (game.pendingEventId) { go("event"); return; }
  if (pendingSeason) { const s = pendingSeason; pendingSeason = null; go("season", s); return; }
  if (game.gameOver) { go("end"); return; }
  go("main");
}

function resolveChoice(index) {
  const event = game.pendingEvent();
  const title = event.title;
  const scene = sceneFor(event.eid, game.stage);
  const text = game.resolveEvent(index);
  saveGame();
  go("outcome", { title, text: text || "…", scene });
}

function showOutcome(title, text) { go("outcome", { title, text }); }

function afterOutcome() {
  saveGame();
  if (game.pendingEventId) { go("event"); return; }
  if (pendingSeason) { const s = pendingSeason; pendingSeason = null; go("season", s); return; }
  if (game.gameOver) { go("end"); return; }
  go("main");
}

// ---------------------------------------------------------------------------

function boot() {
  const saved = hasSave();
  if (saved) {
    const loaded = loadGame();
    if (loaded) { game = loaded; }
  }
  go("menu");
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();
