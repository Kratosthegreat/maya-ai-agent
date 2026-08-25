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

/**
 * מצב השמירה האחרונה. כשהדפדפן מסרב לשמור — ואצל חלק מהדפדפנים
 * בטלפון זה קורה — עדיף שתדע מיד ולא שתגלה כשהקריירה נעלמת.
 */
let saveState = { ok: true, at: 0, error: "" };

function saveGame() {
  if (!game) return false;
  // אם יש קובץ מקושר עם הרשאה — לכתוב גם אליו, בשקט וברקע
  if (saveFile.handle && saveFile.permission === "granted") writeCareerFile(true);
  let payload;
  try {
    payload = packSave(game.toJSON());
  } catch (err) {
    saveState = { ok: false, at: saveState.at, error: "הכנת השמורה נכשלה." };
    return false;
  }
  try {
    localStorage.setItem(SAVE_KEY, payload);
    saveState = { ok: true, at: Date.now(), error: "" };
    return true;
  } catch (err) {
    const full = err && (err.name === "QuotaExceededError"
      || err.name === "NS_ERROR_DOM_QUOTA_REACHED" || err.code === 22);
    saveState = {
      ok: false, at: saveState.at,
      error: full
        ? "אין מספיק מקום פנוי בדפדפן כדי לשמור את הקריירה."
        : "הדפדפן חוסם שמירה מקומית בעמוד הזה.",
    };
    return false;
  }
}

function loadGame() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return null;
    return Game.fromJSON(unpackSave(raw));
  } catch (err) { return null; }
}

function hasSave() {
  try { return !!localStorage.getItem(SAVE_KEY); } catch (err) { return false; }
}

function clearSave() {
  try { localStorage.removeItem(SAVE_KEY); } catch (err) {}
  saveState = { ok: true, at: 0, error: "" };
}

/**
 * חיבור לקובץ שמירה קבוע.
 *
 * הרעיון: בוחרים קובץ פעם אחת, ומאותו רגע כל שמירה דורסת אותו —
 * בלי דיאלוג, בלי "(1)", בלי ערימת קבצים בתיקיית ההורדות.
 */
let saveFile = { handle: null, permission: "prompt", at: 0, error: "" };

/** מחזיר את מצב הקובץ בטקסט, לתצוגה. */
function saveFileState() {
  if (!fileSaveSupported()) return "unsupported";
  if (!saveFile.handle) return "none";
  return saveFile.permission === "granted" ? "linked" : "needs-permission";
}

/** טוען את הקובץ שנבחר בעבר, אם יש. נקרא פעם אחת בעלייה. */
async function loadSaveFile() {
  if (!fileSaveSupported()) return;
  const handle = await storedSaveHandle();
  if (!handle) return;
  saveFile.handle = handle;
  saveFile.permission = await saveFilePermission(handle, false);
  render();
}

// כתיבה לדיסק היא יקרה יותר מ-localStorage, ו-saveGame נקרא הרבה.
// כתיבה שקטה מווסתת; לחיצה מפורשת תמיד נכתבת מיד.
const FILE_WRITE_GAP = 10000;
let fileWriteBusy = false;

/** כותב את הקריירה לקובץ המקושר. שקט — בלי הודעות אם הכל תקין. */
async function writeCareerFile(quiet = true) {
  if (!saveFile.handle || !game) return false;
  if (quiet && (fileWriteBusy || Date.now() - saveFile.at < FILE_WRITE_GAP)) return false;
  fileWriteBusy = true;
  try {
    await writeSaveFile(saveFile.handle, packSave(game.toJSON()));
    saveFile.at = Date.now();
    saveFile.error = "";
    if (!quiet) toast(`הקריירה נשמרה ל-${saveFile.handle.name}.`);
    return true;
  } catch (err) {
    saveFile.permission = "prompt";
    saveFile.error = "הכתיבה לקובץ נכשלה. צריך לחדש את החיבור.";
    if (!quiet) toast(saveFile.error);
    return false;
  } finally {
    fileWriteBusy = false;
  }
}

/**
 * הכפתור הראשי: בפעם הראשונה בוחר קובץ, ומכאן ואילך דורס אותו.
 * בדפדפנים שלא תומכים — הורדה רגילה בשם קבוע.
 */
async function backupCareer(pickNew = false) {
  if (!game) return;
  let payload;
  try { payload = packSave(game.toJSON()); }
  catch (err) { toast("לא הצלחתי להכין את הגיבוי."); return; }

  if (fileSaveSupported()) {
    if (pickNew || !saveFile.handle) {
      const handle = await pickSaveFile();
      if (!handle) return;                    // המשתמש ביטל
      saveFile.handle = handle;
      saveFile.permission = "granted";
    } else if (saveFile.permission !== "granted") {
      saveFile.permission = await saveFilePermission(saveFile.handle, true);
      if (saveFile.permission !== "granted") {
        toast("בלי הרשאה לקובץ אי אפשר לשמור אליו.");
        render();
        return;
      }
    }
    const ok = await writeCareerFile(false);
    render();
    if (ok) return;
  }

  // דרך המילוט: הורדה רגילה, בשם קבוע כדי שלפחות יהיה ברור מה מחליף מה
  try {
    const downloads = window.claude && await window.claude.use("downloads");
    if (downloads) {
      await downloads.save({ filename: SAVE_FILENAME, data: payload });
      toast("הקריירה נשמרה לקובץ.");
      return;
    }
  } catch (err) {
    if (err && err.code === "declined") return;
  }

  const blob = new Blob([payload], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = SAVE_FILENAME;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
  toast("הקריירה יורדת כקובץ גיבוי.");
}

/** מנתק את הקובץ המקושר. */
async function unlinkSaveFile() {
  await forgetSaveHandle();
  saveFile = { handle: null, permission: "prompt", at: 0, error: "" };
  toast("הקובץ נותק. הקריירה עדיין נשמרת בדפדפן.");
  render();
}

/** שחזור קריירה מקובץ גיבוי. */
function restoreCareer() {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".txt,text/plain,application/json";
  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onerror = () => toast("לא הצלחתי לקרוא את הקובץ.");
    reader.onload = () => {
      let restored;
      try { restored = Game.fromJSON(unpackSave(String(reader.result).trim())); }
      catch (err) { toast("הקובץ הזה לא נראה כמו גיבוי של קריירה."); return; }
      game = restored;
      saveGame();
      toast(`הקריירה של ${game.me.name} שוחזרה.`);
      go(game.gameOver ? "end" : "main");
    };
    reader.readAsText(file);
  });
  input.click();
}

/** פאנל השמורה: מה נשמר, לאן, ומה אפשר לעשות עם זה. */
function savePanel() {
  const mode = saveFileState();
  const name = saveFile.handle ? saveFile.handle.name : "";
  const body = {
    linked: `הקריירה נכתבת אוטומטית ל־<strong class="fname">${esc(name)}</strong> בכל סוף שבוע.
             כל כתיבה דורסת את אותו קובץ — לא נוצרים עותקים.`,
    "needs-permission": `הקובץ <strong class="fname">${esc(name)}</strong> מקושר, אבל הדפדפן
             מבקש אישור מחדש אחרי שסגרת את הדף. לחיצה אחת והכל חוזר לעבוד.`,
    none: `אפשר לקשר קובץ שמירה קבוע: בוחרים אותו פעם אחת, ומאותו רגע כל
             שמירה דורסת אותו — בלי ערימת קבצים בהורדות.`,
    unsupported: `הדפדפן הזה לא יודע לכתוב חזרה לקובץ קיים, אז גיבוי יורד
             כקובץ רגיל בשם קבוע. במחשב עם כרום או Edge זה יעבוד כדריסה.`,
  }[mode];

  return `
  <div class="panel">
    <div class="panel-head"><span class="t">השמורה</span>
      <span class="r">${saveState.ok ? esc(savedAgo()) : "לא נשמר"}</span></div>
    <div class="panel-body">
      <div class="row">
        <span class="nm">בדפדפן</span>
        <span class="val ${saveState.ok ? "good" : "bad"}">${
          saveState.ok ? "פעיל" : "נכשל"}</span>
      </div>
      <div class="row">
        <span class="nm">קובץ קבוע</span>
        <span class="val ${mode === "linked" ? "good" : ""}">${
          mode === "linked" ? `<span class="fname">${esc(name)}</span>`
          : mode === "needs-permission" ? "ממתין לאישור"
          : mode === "none" ? "לא מקושר" : "לא נתמך"}</span>
      </div>
      <div class="muted">${body}</div>
      ${saveFile.error ? `<div class="muted bad">${esc(saveFile.error)}</div>` : ""}
      <div class="btn-row">
        <button class="btn ${mode === "linked" ? "" : "primary"}" data-act="backup">${
          mode === "linked" ? "לשמור עכשיו"
          : mode === "needs-permission" ? "לחדש את החיבור"
          : mode === "none" ? "לבחור קובץ שמירה" : "להוריד גיבוי"}</button>
        <button class="btn" data-act="restore">לשחזר</button>
      </div>
      ${saveFile.handle ? `<div class="btn-row">
        <button class="mini-btn" data-act="backup-as">לבחור קובץ אחר</button>
        <button class="mini-btn" data-act="unlink-file">לנתק</button>
      </div>` : ""}
    </div>
  </div>`;
}

/** התראה כשהשמירה האוטומטית לא עובדת — עם דרך מוצא. */
function saveWarning() {
  if (saveState.ok) return "";
  return `
  <div class="panel warn">
    <div class="panel-head"><span class="t">השמירה האוטומטית לא עובדת</span></div>
    <div class="panel-body">
      <div class="muted">${esc(saveState.error)}
        הקריירה תמשיך לרוץ, אבל היא לא תחכה לך אחרי שתסגור את הדף.</div>
      <button class="btn wide" data-act="backup">${
        fileSaveSupported() ? "לקשר קובץ שמירה קבוע" : "להוריד קובץ גיבוי"}</button>
    </div>
  </div>`;
}

/** "לפני רגע" / "לפני 4 דק'" — כדי שיהיה ברור שהשמירה באמת קורית. */
function savedAgo() {
  if (!saveState.at) return "";
  const seconds = Math.round((Date.now() - saveState.at) / 1000);
  if (seconds < 45) return "נשמר עכשיו";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `נשמר לפני ${minutes} דק'`;
  return `נשמר לפני ${Math.round(minutes / 60)} שע'`;
}

// -- ניווט --------------------------------------------------------------

/** הודעה קצרה שנעלמת מעצמה — משוב על פעולה שבוצעה. */
let toastTimer = null;
function toast(message) {
  if (!message) return;
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.className = "toast";
    el.setAttribute("role", "status");
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.classList.add("on");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("on"), 3600);
}

// מחסנית חזרה קצרה — כדי שאפשר יהיה לצלול לתיק של מועדון ולחזור
const navStack = [];

function goDeep(next, data = null) {
  navStack.push([view, viewData]);
  go(next, data);
}

function goBack() {
  const previous = navStack.pop();
  if (previous) { view = previous[0]; viewData = previous[1]; render(); }
  else go("main");
}

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
      <button class="btn ghost" data-act="restore">
        <span class="k">לשחזר מקובץ גיבוי</span>
        <span class="hint">להעביר קריירה ממכשיר אחר</span>
      </button>
    </div>
    <div class="card">
      <div class="eyebrow">מה יש כאן</div>
      <div class="notes">
        <div class="note"><span class="ico">⚽</span><span>3 ליגות, 32 מועדונים, סימולציה מלאה של כל משחק בעונה.</span></div>
        <div class="note"><span class="ico">📖</span><span>${STORY.length} צמתי עלילה — מהנעליים הראשונות ועד הפסל מחוץ לאצטדיון.</span></div>
        <div class="note"><span class="ico">🎓</span><span>מה שתלמד בזמן הקריירה יקבע מה תעשה אחריה.</span></div>
      </div>
    </div>
    <p class="muted center">המשחק נשמר בדפדפן הזה אוטומטית. כדי להעביר קריירה
    למכשיר אחר — או לשמור אותה לפני ניקוי הדפדפן — יש כפתור גיבוי בתוך המשחק.</p>
  </div>`;
}

function ageBlurb(age, role) {
  if (role === "manager")
    return age <= 38 ? "מנג'ר צעיר שרק קיבל תעודות. ההנהלה תיתן לך זמן — לא הרבה."
      : age <= 50 ? "מנג'ר בשיא הדרך: מספיק ניסיון כדי שיקשיבו לך."
      : "מנג'ר ותיק. השם שלך מקדים אותך, וגם הציפיות.";
  if (age <= 15) return "מתחילים בקבוצת הנוער: בית ספר, מגרש שכונתי, ומאמן שעוד לא יודע איך קוראים לך. הדרך ארוכה — והתקרה הכי גבוהה.";
  if (age <= 17) return "קבוצת הנוער הבוגרת, חוזה ראשון, וספסל של קבוצה בוגרת שנראה רחוק.";
  if (age <= 23) return "שחקן צעיר בסגל הבוגרים. יש עוד לאן להתפתח, ויש כבר מה להפסיד.";
  if (age <= 29) return "בשיא. הדירוג כמעט סופי, אבל אלה השנים שבהן נקבעים התארים.";
  if (age <= 33) return "ותיק. הרגליים כבר לא מה שהיו, הראש דווקא כן — וכדאי להתחיל לחשוב על היום שאחרי.";
  return "בסוף הדרך. עוד עונה או שתיים, ואז ההחלטה הגדולה.";
}

const PREVIEW_CLUB = { cid: "__preview__" };

/**
 * רשת מספרי חולצה. מסמנת את המסורתיים לעמדה, ואת התפוסים היא לא מציעה.
 * field מגדיר איזה data-attribute ייצא, כדי שאותה רשת תשמש גם בפתיחה
 * וגם בהחלפת מספר באמצע הקריירה.
 */
const ALL_NUMBERS = Array.from({ length: SQUAD_NUMBER_MAX }, (unused, i) => i + 1);

function numberGrid(free, current, position, attr) {
  const preferred = new Set(NUMBER_PREF[position] || []);
  return `<div class="numbers">${free.map(n => `
    <button class="num-pick ${preferred.has(n) ? "pref" : ""}"
      ${attr}="${n}" aria-pressed="${current === n}">${n}</button>`).join("")}</div>`;
}

/** שחקן דמה לתצוגה מקדימה בכרטיס הזהות. */
function identityPreviewPlayer(identity) {
  return { pid: "preview", name: "preview", age: 25,
           number: identity.number || 9, foot: identity.foot };
}


/**
 * כרטיס הזהות: רגל חזקה ותכונת אופי.
 * שתיהן משפיעות על המשחק עצמו — הן לא קישוט.
 */
function identityPicker(identity, club, position) {
  const previewClub = club || PREVIEW_CLUB;
  const preview = identityPreviewPlayer(identity);


  return `
  <div class="panel">
    <div class="panel-head"><span class="t">הזהות שלך</span>
      <span class="r"><button class="mini-btn" data-act="random-identity">הגרל</button></span></div>
    <div class="panel-body">
      <div class="ident-preview">${avatar(preview, previewClub, 132, { number: null })}</div>
      <div class="muted center">כמו בפוטבול מנג'ר — בלי תמונות שחקנים. מה שמזהה אותך זה המדים, המספר והנתונים.</div>

      <div class="ident-group">
        <div class="muted">רגל חזקה</div>
        <div class="chips">
          ${FOOT_KEYS.map(k => `<button class="chip" data-ident="foot" data-val="${k}"
            aria-pressed="${identity.foot === k}">${FOOT_NAMES[k]}</button>`).join("")}
        </div>
      </div>

      <div class="ident-group">
        <div class="muted">מספר חולצה מבוקש${identity.number
          ? "" : " — אם לא תבחר, תקבל את המסורתי של העמדה"}</div>
        ${numberGrid(ALL_NUMBERS, identity.number, position, "data-shirt")}
        <div class="muted small">אם המספר תפוס בסגל, תקבל אחר — ותוכל להחליף
        אותו בכל רגע מהפרופיל, מתוך מה שבאמת פנוי.</div>
      </div>

      <div class="ident-group">
        <div class="muted">תכונת אופי</div>
        <div class="trait-list">
          ${Object.entries(D.TRAITS).map(([key, t]) => `
            <button class="trait-opt" data-ident="trait" data-val="${key}"
              aria-pressed="${identity.trait === key}">
              <span class="tn">${esc(t.name)}</span>
              <span class="td">${esc(t.desc)}</span>
            </button>`).join("")}
        </div>
      </div>
    </div>
  </div>`;
}

/** מסך פתיחה: תפקיד, גיל, עמדה, מועדון וזהות. */
function screenNew() {
  const state = viewData || (viewData = { name: "", position: "ST",
    club: "hapoel_carmel", age: 15, role: "player", identity: randomIdentity() });
  if (!state.identity) state.identity = randomIdentity();
  const isManager = state.role === "manager";
  const clubs = D.CLUBS.filter(c => c[3] !== "euro").sort((a, b) => a[4] - b[4]);
  const minAge = isManager ? 32 : 13;
  const maxAge = isManager ? 62 : 38;
  const age = Math.max(minAge, Math.min(maxAge, state.age));

  return `
  <div class="screen">
    <div class="hero" style="padding-top:10px">
      <div class="eyebrow">קריירה חדשה</div>
      <h1 class="display" style="font-size:40px">מי אתה?</h1>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">מסלול</span></div>
      <div class="panel-body">
        <div class="chips">
          <button class="chip" data-role="player" aria-pressed="${!isManager}">שחקן</button>
          <button class="chip" data-role="manager" aria-pressed="${isManager}">מנג'ר</button>
        </div>
        <div class="muted">${isManager
          ? "מתחילים ישר על הקו: אתה בוחר מערך, הרכב וטקטיקה, וההנהלה סופרת נקודות."
          : "מתחילים על המגרש: מתאמנים, נלחמים על מקום בהרכב, ובסוף מחליטים מה עושים אחרי הפרישה."}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">שם</span></div>
      <div class="panel-body">
        <input type="text" id="pname" maxlength="24" placeholder="עומר לוי" value="${esc(state.name)}">
      </div>
    </div>

    ${identityPicker(state.identity, { cid: state.club }, state.position)}

    ${isManager ? "" : `
    <div class="panel">
      <div class="panel-head"><span class="t">עמדה</span></div>
      <div class="panel-body">
        <div class="chips">
          ${D.POSITIONS.map(p => `<button class="chip" data-pos="${p}"
            aria-pressed="${state.position === p}">${D.POSITION_NAMES_HE[p]}</button>`).join("")}
        </div>
      </div>
    </div>`}

    <div class="panel">
      <div class="panel-head"><span class="t">גיל</span>
        <span class="r"><span class="num">${age}</span></span></div>
      <div class="panel-body">
        <input type="range" id="page" min="${minAge}" max="${maxAge}" step="1" value="${age}">
        <div class="row" style="padding:0;border:0">
          <span class="muted">${minAge}</span><span class="grow"></span>
          <span class="muted">${maxAge}</span>
        </div>
        <div class="muted">${esc(ageBlurb(age, state.role))}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">מועדון</span></div>
      <div class="panel-body">
        <select id="pclub">
          ${clubs.map(c => `<option value="${c[0]}" ${state.club === c[0] ? "selected" : ""}>
            ${esc(c[1])} — מוניטין ${c[4]}</option>`).join("")}
        </select>
        <div class="muted">${isManager
          ? "מועדון חלש = ציפיות נמוכות ומקום לטעות. מועדון חזק = אפס סבלנות."
          : "מועדון חלש = דקות משחק מיד. מועדון חזק = ספסל, אבל במה גדולה יותר."}</div>
      </div>
    </div>

    <div class="actions">
      <button class="btn primary" data-act="start">להתחיל</button>
      <button class="btn ghost" data-act="menu">חזרה</button>
    </div>
  </div>`;
}

const SEASON_MONTHS = ["אוג", "ספט", "אוק", "נוב", "דצמ", "ינו", "פבר", "מרץ", "אפר", "מאי"];

/** התאריך המשוער של השבוע — נותן תחושה של לוח שנה אמיתי. */
function weekDate() {
  const w = Math.min(SEASON_WEEKS, Math.max(1, game.week));
  const perMonth = SEASON_WEEKS / SEASON_MONTHS.length;
  const month = SEASON_MONTHS[Math.min(SEASON_MONTHS.length - 1,
    Math.floor((w - 1) / perMonth))];
  const inMonth = ((w - 1) % perMonth) / perMonth;
  const day = 1 + Math.floor(inMonth * 28);
  return { d: `${day} ${month}`, w: `שבוע ${w}/${SEASON_WEEKS}` };
}

function appbar() {
  const me = game.me;
  const club = game.myClub();
  const stage = D.CAREER_STAGES_HE[game.stage] || game.stage;
  const date = weekDate();
  return `
  <header class="appbar">
    <div class="appbar-top">
      <div class="brand">
        ${club ? crest(club, 30) : avatar(me, null, 30)}
        <span class="who">
          <span class="nm">${esc(club ? club.name : me.name)}</span>
          <span class="sub">${esc(stage)}${club ? " · " + esc(me.name) : ""}</span>
        </span>
      </div>
      <span class="spacer"></span>
      <div class="date">
        <div class="d">${date.d}</div>
        <div class="w">${game.year}/${game.year + 1}</div>
      </div>
      <button class="btn-continue" data-act="play">
        המשך <span class="chev">‹</span>
      </button>
    </div>
    ${tabsBar()}
  </header>`;
}

function tabsBar() {
  const items = [["main", "סקירה"], ["squad", "סגל"], ["table", "ליגה"],
                 ["profile", "פרופיל"], ["news", "יומן"], ["editor", "עורך"]];
  if (game.myClub()) items.splice(2, 0, ["club", "מועדון"]);
  if (["youth", "academy", "player", "veteran"].includes(game.stage))
    items.splice(1, 0, ["plan", "מסלול"]);
  items.splice(items.length - 1, 0, ["money", "כסף"]);
  if (["manager", "coach"].includes(game.stage)) items.splice(2, 0, ["tactics", "טקטיקה"]);
  const offers = game.flag("pending_offer") ? 1 : 0;
  return `<nav class="tabs">${items.map(([k, l]) =>
    `<button class="tab" data-go="${k}" aria-current="${view === k}">${l}${
      k === "main" && offers ? `<span class="badge">${offers}</span>` : ""}</button>`).join("")}</nav>`;
}

function dock(showPlay) {
  if (!showPlay) return "";
  return `<div class="dock">
    <button class="btn primary" data-act="play">לשחק את השבוע</button>
  </div>`;
}

function screenMain() {
  if (view === "profile") return appbar() + screenProfile();
  if (view === "table") return appbar() + screenTable();
  if (view === "squad") return appbar() + screenSquad();
  if (view === "news") return appbar() + screenNews();
  if (view === "tactics") return appbar() + screenTactics();
  if (view === "club") return appbar() + screenClub();
  if (view === "clubinfo") return appbar() + screenClubInfo();
  if (view === "player") return appbar() + screenPlayer();
  if (view === "editor") return appbar() + screenEditor();
  if (view === "plan") return appbar() + screenPlan();
  if (view === "money") return appbar() + screenMoney();
  if (view === "scouts") return appbar() + screenScouts();
  return appbar() + screenHub() + dock(true);
}

/** תיאור עמידות/חדות במילים — מספר גולמי לא אומר כלום. */
function bandLabel(value, labels) {
  const index = Math.min(labels.length - 1, Math.floor(value / (100 / labels.length)));
  return labels[index];
}

const RESILIENCE_WORDS = ["זכוכית", "שביר", "רגיל", "חסון", "ברזל"];
const SHARPNESS_WORDS = ["חלוד", "לא בקצב", "בסדר", "חד", "בשיא"];

/** תעודת זהות מלאה של שחקן — מה שחסר כשרואים רק גיל ורגל. */
function screenPlayer() {
  if (!viewData) viewData = {};
  const pid = viewData.pid || game.meId;
  const p = game.players[pid];
  if (!p) return `<div class="screen"><div class="card">שחקן לא נמצא.</div></div>`;
  const club = p.clubId ? game.clubs[p.clubId] : null;
  const mine = pid === game.meId;
  const s = p.season, c = p.career;

  return `
  <div class="screen">
    ${playerCard(p, club, mine ? game.stage : "player")}

    <div class="panel">
      <div class="panel-head"><span class="t">תעודת זהות</span>
        <span class="r">${esc(positionHe(p))}</span></div>
      <div class="panel-body tight">
        <div class="row"><span class="nm">גיל</span><span class="val num">${p.age}</span></div>
        <div class="row"><span class="nm">גובה</span>
          <span class="val num">${p.height} ס"מ</span></div>
        <div class="row"><span class="nm">משקל</span>
          <span class="val num">${p.weight} ק"ג</span></div>
        <div class="row"><span class="nm">רגל חזקה</span>
          <span class="val">${esc(FOOT_NAMES[playerFoot(p)])}</span></div>
        <div class="row"><span class="nm">לאום</span>
          <span class="val">${esc(p.nationality)}</span></div>
        <div class="row"><span class="nm">מספר חולצה</span>
          <span class="val num">${p.number || "—"}</span>
          ${mine && game.myClub() ? `<button class="mini-btn" data-act="pick-number">${
            viewData.pickNumber ? "סגור" : "להחליף"}</button>` : ""}</div>
        ${mine && viewData.pickNumber && game.myClub() ? `
          <div class="number-picker">
            ${numberGrid(game.freeNumbers(), p.number, p.position, "data-newshirt")}
            <div class="muted small">רק מספרים שאף אחד בסגל לא לובש.</div>
          </div>` : ""}
        ${club ? `<div class="row"><span class="nm">מועדון</span>
          <span class="val"><button class="link-btn" data-club="${club.cid}">${esc(club.name)}</button></span></div>` : ""}
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">מצב גופני</span>
        <span class="r">${p.injuryWeeks ? esc(p.injuryName) : "כשיר"}</span></div>
      <div class="panel-body">
        <div class="attr"><span>עמידות לפציעות</span>
          <span class="val">${esc(bandLabel(p.resilience, RESILIENCE_WORDS))}</span>
          <span class="bar"><i style="width:${Math.round(p.resilience)}%"></i></span></div>
        <div class="attr"><span>חדות משחק</span>
          <span class="val">${esc(bandLabel(p.sharpness, SHARPNESS_WORDS))}</span>
          <span class="bar"><i style="width:${Math.round(p.sharpness)}%"></i></span></div>
        <div class="attr"><span>כושר</span>
          <span class="val">${Math.round(p.fitness)}</span>
          <span class="bar soft"><i style="width:${Math.round(p.fitness)}%"></i></span></div>
        <div class="muted">סיכון פציעה: <span class="num">${
          Math.round(injuryRisk(p) * 100)}%</span> מהרגיל.
          ${mine ? "אימוני כוח ומנוחה מורידים אותו; דקות משחק מעלות חדות." : ""}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">תכונות</span>
        <span class="r num">${overall(p)}${mine ? ` · תקרה ${p.potential}` : ""}</span></div>
      <div class="panel-body">
        <div class="attrs">
          ${D.ATTRIBUTES.map(a => `<div class="attr">
            <span>${D.ATTRIBUTE_NAMES_HE[a]}</span>
            <span class="val">${p.attributes[a]}</span>
            <span class="bar"><i style="width:${p.attributes[a]}%"></i></span>
          </div>`).join("")}
        </div>
      </div>
    </div>

    ${p.traits.length ? `<div class="panel">
      <div class="panel-head"><span class="t">אופי</span></div>
      <div class="panel-body">
        <div class="chips">${p.traits.map(t =>
          `<span class="chip" style="cursor:default">${esc(D.TRAITS[t] ? D.TRAITS[t].name : t)}</span>`).join("")}</div>
        <div class="muted">${p.traits.map(t => D.TRAITS[t] ? esc(D.TRAITS[t].desc) : "").join(" ")}</div>
      </div>
    </div>` : ""}

    <div class="panel">
      <div class="panel-head"><span class="t">מספרים</span></div>
      <div class="panel-body">
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
    </div>

    <button class="btn ghost wide" data-act="back">חזרה</button>
  </div>`;
}

/**
 * תיק על מועדון אחר: מיקום, כושר, מוניטין, אצטדיון, מתקנים וסגל מלא.
 * נפתח מכל מקום שבו מוזכר מועדון — הצעת העברה, המשחק הבא, הטבלה.
 */
function screenClubInfo() {
  const cid = viewData && viewData.cid;
  const club = cid ? game.clubs[cid] : null;
  if (!club) return `<div class="screen"><div class="card">מועדון לא נמצא.</div></div>`;

  const league = D.LEAGUES.find(l => l.id === club.leagueId);
  const table = game.standings(club.leagueId);
  const index = table.findIndex(r => r.clubId === club.cid);
  const row = index >= 0 ? table[index] : null;
  const squad = club.squad.map(pid => game.players[pid]).filter(Boolean)
    .sort((a, b) => overall(b) - overall(a));
  const best = squad.slice(0, 5);
  const avg = squad.length
    ? Math.round(squad.reduce((sum, p) => sum + overall(p), 0) / squad.length) : 0;
  const mine = game.myClub();
  const isMine = mine && mine.cid === club.cid;

  return `
  <div class="screen">
    <div class="panel">
      <div class="panel-head"><span class="t">${esc(club.name)}</span>
        <span class="r">${esc(league ? league.name : "")}</span></div>
      <div class="panel-body">
        <div class="crest-row">${crest(club, 52)}
          <div class="kit-meta">
            <span class="nm">${esc(club.nickname)}</span>
            <span class="muted">🏟️ ${esc(club.stadiumName)} · ${fmt(club.capacity)} מקומות</span>
            <span class="muted">מאמן: ${esc(club.managerName)} · ${
              esc(managerStyle(club)[1])}</span>
          </div>
        </div>
        <div class="stat-grid">
          <div class="stat"><div class="n">${index >= 0 ? index + 1 : "—"}</div>
            <div class="l">בטבלה</div></div>
          <div class="stat"><div class="n">${row ? row.points : "—"}</div>
            <div class="l">נקודות</div></div>
          <div class="stat"><div class="n">${club.reputation}</div>
            <div class="l">מוניטין</div></div>
        </div>
        ${club.formLog && club.formLog.length ? `<div class="muted">כושר אחרון</div>
          ${formGuide(club)}` : ""}
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">איך זה בפנים</span>
        <span class="r num">סגל ${avg}</span></div>
      <div class="panel-body tight">
        <div class="row"><span class="nm">מתקני אימון</span>
          <span class="val num">${Math.round(club.trainingFacilities)}</span></div>
        <div class="row"><span class="nm">מחלקת נוער</span>
          <span class="val num">${Math.round(club.youthAcademy)}</span></div>
        <div class="row"><span class="nm">מרכז רפואי</span>
          <span class="val num">${Math.round(club.medicalCentre)}</span></div>
        <div class="row"><span class="nm">אהדת קהל</span>
          <span class="val num">${Math.round(club.fanSupport)}</span></div>
        <div class="row"><span class="nm">צוות מקצועי</span>
          <span class="val num">${Object.keys(club.staff || {}).length}/5</span></div>
        ${isMine ? "" : `<div class="row"><span class="nm">שכר טיפוסי לשחקן ברמה שלך</span>
          <span class="val num">₪${fmt(wageForOverall(
            Math.round(club.reputation * 0.8 + 18)))}</span></div>`}
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">מי משחק שם</span>
        <span class="r">${squad.length} שחקנים</span></div>
      <div class="panel-body tight">
        ${best.map(p => `<div class="row">
          ${avatarChip(p, club, 26)}
          <button class="link-btn grow" data-player="${p.pid}">${esc(p.name)}</button>
          <span class="muted">${esc(positionHe(p))} · ${p.age}</span>
          <span class="val num">${overall(p)}</span>
        </div>`).join("")}
        ${squad.length > 5 ? `<button class="mini-btn wide" data-act="club-squad">
          ${viewData.full ? "להראות רק את החמישייה" : `כל הסגל (${squad.length})`}</button>` : ""}
        ${viewData.full ? squad.slice(5).map(p => `<div class="row">
          ${avatarChip(p, club, 26)}
          <button class="link-btn grow" data-player="${p.pid}">${esc(p.name)}</button>
          <span class="muted">${esc(positionHe(p))} · ${p.age}</span>
          <span class="val num">${overall(p)}</span>
        </div>`).join("") : ""}
      </div>
    </div>

    <button class="btn ghost wide" data-act="back">חזרה</button>
  </div>`;
}

/** שורת כסף: תווית, סכום וסימן. */
function moneyRow(label, amount, kind) {
  const sign = amount > 0 ? "+" : amount < 0 ? "−" : "";
  if (!amount) kind = "";
  return `<div class="row money ${kind || ""}">
    <span class="nm">${esc(label)}</span>
    <span class="val num">${sign}₪${fmt(Math.abs(amount))}</span>
  </div>`;
}

/**
 * מסך המועדון: אצטדיון, קופה, מתקנים וצוות מקצועי.
 * כשאתה שחקן אתה רואה הכל אבל לא נוגע; כמנג'ר, מנהל או בעלים — אתה מחליט.
 */
function screenClub() {
  const club = game.myClub();
  if (!club) return `<div class="screen"><div class="card">אתה לא משויך למועדון כרגע.</div></div>`;
  const money = game.clubFinanceSummary();
  const boss = game.controlsClub();
  const last = money.lastWeek;
  if (!viewData) viewData = {};
  const openRole = viewData.staffRole;

  return `
  <div class="screen">
    <div class="panel">
      <div class="panel-head"><span class="t">${esc(club.name)}</span>
        <span class="r">${esc(D.LEAGUES.find(l => l.id === club.leagueId).name)}</span></div>
      <div class="panel-body">
        <div class="crest-row">${crest(club, 46)}
          <div class="kit-meta">
            <span class="nm">🏟️ ${esc(club.stadiumName)}</span>
            <span class="muted">${fmt(club.capacity)} מקומות · כרטיס ₪${fmt(money.ticket)}</span>
          </div>
        </div>
        <div class="stat-grid">
          <div class="stat"><div class="n">${fmt(money.attendance)}</div><div class="l">קהל אחרון</div></div>
          <div class="stat"><div class="n">${money.attendance
            ? Math.round(money.attendance / club.capacity * 100) + "%" : "—"}</div>
            <div class="l">תפוסה</div></div>
          <div class="stat"><div class="n">${Math.round(club.fanSupport)}</div><div class="l">אהדה</div></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">הקופה</span>
        <span class="r num ${money.balance < 0 ? "bad" : ""}">₪${fmt(money.balance)}</span></div>
      <div class="panel-body tight">
        ${last ? `
          ${moneyRow("שידורים וחסויות", last.commercial, "in")}
          ${moneyRow("יום משחק", last.matchday, "in")}
          ${moneyRow("שכר שחקנים", -last.wages, "out")}
          ${moneyRow("שכר צוות", -last.staff, "out")}
          <hr class="rule">
          ${moneyRow("מאזן השבוע", last.net, last.net >= 0 ? "in" : "out")}
        ` : `<div class="muted">המאזן הראשון יופיע אחרי השבוע הבא.</div>`}
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">מתקנים</span>
        <span class="r">${boss ? "אתה מחליט" : "החלטה של ההנהלה"}</span></div>
      <div class="panel-body">
        ${game.facilityOptions().map(f => `
          <div class="facility">
            <div class="facility-top">
              <span class="nm">${esc(f.name)}</span>
              <span class="val num">${f.kind === "stadium" ? fmt(f.level) : f.level}</span>
            </div>
            ${f.kind === "stadium" ? "" :
              `<span class="bar"><i style="width:${f.level}%"></i></span>`}
            <div class="muted">${esc(f.effect)}</div>
            ${f.building
              ? `<div class="build">🏗️ בבנייה — עוד ${f.building} שבועות</div>`
              : boss
                ? `<button class="mini-btn wide" data-upgrade="${f.kind}"
                     ${f.blocked ? "disabled" : ""}>
                     ${f.kind === "stadium"
                       ? `<span class="num">+${fmt(f.added)}</span> מקומות`
                       : `<span class="num">+${D.FACILITIES[f.kind].unit}</span>`}
                     · <span class="num">₪${fmt(f.cost)}</span>
                     · <span class="num">${f.weeks}</span> שב'
                   </button>
                   ${f.blocked ? `<div class="blocked">${esc(f.blocked)}${
                     f.blocked === "אין מספיק כסף בקופה."
                       ? ` חסר ₪${fmt(f.cost - money.balance)}.` : ""}</div>` : ""}`
                : `<div class="muted">שדרוג: ₪${fmt(f.cost)} · ${f.weeks} שבועות</div>`}
          </div>`).join("")}
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">הצוות המקצועי</span>
        <span class="r num">₪${fmt(money.staffWages)}/שבוע</span></div>
      <div class="panel-body">
        ${Object.entries(D.STAFF_ROLES).map(([role, spec]) => {
          const member = club.staff[role];
          const open = openRole === role;
          const candidates = (game.staffMarket && game.staffMarket[role]) || [];
          return `
          <div class="staff">
            <div class="staff-top">
              <span class="nm">${esc(spec.name)}</span>
              ${member
                ? `<span class="val num">${member.quality}</span>`
                : `<span class="val muted">פנוי</span>`}
            </div>
            <div class="muted">${member
              ? `${esc(member.name)} · ₪${fmt(member.wage)}/שבוע`
              : "אין מי שממלא את התפקיד."}</div>
            <div class="muted small">${esc(spec.effect)}</div>
            ${boss ? `
              <div class="staff-actions">
                <button class="mini-btn" data-staffrole="${role}">
                  ${open ? "סגור" : member ? "להחליף" : "לגייס"}</button>
                ${member ? `<button class="mini-btn danger" data-fire="${role}">לפטר</button>` : ""}
              </div>
              ${open ? `<div class="candidates">
                ${candidates.length ? candidates.map((c, i) => `
                  <button class="candidate" data-hire="${role}" data-idx="${i}">
                    <span class="nm">${esc(c.name)}</span>
                    <span class="q num">${c.quality}</span>
                    <span class="w num">₪${fmt(c.wage)}/שב'</span>
                    <span class="fee">חתימה ₪${fmt(c.wage * 4)}</span>
                  </button>`).join("")
                  : `<div class="muted">אין מועמדים כרגע.</div>`}
              </div>` : ""}
            ` : ""}
          </div>`;
        }).join("")}
      </div>
    </div>
  </div>`;
}

/** מסך טקטיקה — מגרש עם ההרכב ובחירות המנג'ר. */
function screenTactics() {
  const club = game.myClub();
  if (!club) return `<div class="screen"><div class="card">אין לך קבוצה לאמן.</div></div>`;
  const formation = game.tactics.formation || club.formation;
  const lineup = pickLineup(club, game.players, formation, null);
  const slots = D.FORMATIONS[formation] || D.FORMATIONS["4-3-3"];
  return `
  <div class="screen">
    <div class="panel">
      <div class="panel-head"><span class="t">מערך</span><span class="r">${esc(formation)}</span></div>
      <div class="panel-body">
        ${pitch(lineup, formation, game.players, game.meId, club)}
        <div class="chips">
          ${Object.keys(D.FORMATIONS).map(f => `<button class="chip" data-form="${f}"
            aria-pressed="${formation === f}">${f}</button>`).join("")}
        </div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><span class="t">גישה</span></div>
      <div class="panel-body">
        <div class="muted">מנטליות</div>
        <div class="chips">
          ${Object.entries(D.MENTALITIES).map(([k, v]) => `<button class="chip" data-ment="${k}"
            aria-pressed="${game.tactics.mentality === k}">${esc(v[0])}</button>`).join("")}
        </div>
        <div class="muted">לחץ</div>
        <div class="chips">
          ${Object.entries(D.PRESSING).map(([k, v]) => `<button class="chip" data-press="${k}"
            aria-pressed="${game.tactics.pressing === k}">${esc(v[0])}</button>`).join("")}
        </div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><span class="t">ההרכב הפותח</span><span class="r">11 שחקנים</span></div>
      <div class="panel-body tight">
        ${lineup.map((pid, i) => {
          const p = game.players[pid];
          if (!p) return "";
          return `<div class="row ${pid === game.meId ? "me" : ""}">
            ${avatarChip(p, club, 28)}
            <span class="grow"><span class="nm">${esc(p.name)}</span>
              <span class="sub">${esc(D.POSITION_NAMES_HE[slots[i]] || "")} · בן ${p.age}</span></span>
            <span class="val">${overall(p)}</span>
          </div>`;
        }).join("")}
      </div>
    </div>
  </div>`;
}

function screenHub() {
  const me = game.me;
  const club = game.myClub();
  const isPlayer = ["youth", "academy", "player", "veteran"].includes(game.stage);
  const actions = game.availableActions();
  const offer = game.flag("pending_offer");
  const fx = game.myFixture();

  // --- פאנל המשחק הבא ---
  let nextMatch = "";
  if (game.stage === "youth") {
    const isMatchWeek = game.week % 2 === 1;
    nextMatch = `
      <div class="panel">
        <div class="panel-head"><span class="t">השבוע</span>
          <span class="r">${isMatchWeek ? "ליגת הנוער" : "אימונים"}</span></div>
        <div class="panel-body">
          <div class="avatar-row">${avatar(me, club, 44)}
            <span class="grow">${isMatchWeek
              ? "משחק נוער השבוע. המאמן מסתכל."
              : "בלי משחק — שבוע אימונים."}</span></div>
          ${fx ? `<div class="muted">הקבוצה הבוגרת: ${esc(game.clubs[fx[0]].name)}
            נגד ${esc(game.clubs[fx[1]].name)}</div>` : ""}
        </div>
      </div>`;
  } else if (fx) {
    const [homeId, awayId] = fx;
    const home = game.clubs[homeId], away = game.clubs[awayId];
    const comp = CUP_WEEKS[game.week] || "ליגה";
    const rival = club && club.cid === homeId ? away : home;
    const where = club && club.cid === homeId ? "בית" : "חוץ";
    nextMatch = `
      <div class="panel">
        <div class="panel-head"><span class="t">המשחק הבא</span>
          <span class="r">${esc(comp)} · ${where}</span></div>
        <div class="panel-body">
          <div class="scoreline">
            <div class="side">${crest(home, 34)}<span class="nm ${
              club && club.cid === homeId ? "mine" : ""}">${esc(home.name)}</span></div>
            <div class="versus">נגד</div>
            <div class="side away">${crest(away, 34)}<span class="nm ${
              club && club.cid === awayId ? "mine" : ""}">${esc(away.name)}</span></div>
          </div>
          <div class="scoreline" style="font-size:12px">
            <div class="side">${formGuide(home)}</div><div></div>
            <div class="side away">${formGuide(away)}</div>
          </div>
          <div class="muted">${esc(rival.nickname)} · מוניטין ${rival.reputation}${
            club ? " · מקום " + game.leaguePosition() : ""}</div>
          <button class="mini-btn wide" data-club="${rival.cid}">
            תיק על ${esc(rival.name)}</button>
        </div>
      </div>`;
  } else {
    nextMatch = `<div class="panel"><div class="panel-head"><span class="t">השבוע</span></div>
      <div class="panel-body"><div class="muted">אין משחק — שבוע של עבודה.</div></div></div>`;
  }

  // --- פאנל המצב ---
  const statusBody = isPlayer ? `
      <div class="avatar-row">${avatar(me, club, 46)}
        <span class="grow"><span class="nm"><strong>${esc(me.name)}</strong></span>
          <span class="sub">${esc(positionHe(me))} · בן ${me.age}${
            me.number ? " · מספר " + me.number : ""}</span></span>
        <span class="val" style="font-size:22px">${overall(me)}</span></div>
      <div class="stat-grid">
        <div class="stat"><div class="n">${Math.round(me.form)}</div><div class="l">כושר</div></div>
        <div class="stat"><div class="n">${Math.round(me.fitness)}</div><div class="l">רעננות</div></div>
        <div class="stat"><div class="n">${Math.round(me.morale)}</div><div class="l">מורל</div></div>
      </div>
      ${me.injuryWeeks > 0 ? `<div class="note"><span class="ico">🚑</span>
        <span>${esc(me.injuryName)} — עוד ${me.injuryWeeks} שבועות</span></div>` : ""}
      ${club ? `<div class="attr"><span>אמון המאמן</span>
        <span class="val">${Math.round(club.managerTrust)}</span>
        <span class="bar"><i style="width:${Math.round(club.managerTrust)}%"></i></span></div>` : ""}`
    : club ? `
      <div class="stat-grid">
        <div class="stat"><div class="n">${game.leaguePosition()}</div><div class="l">מקום</div></div>
        <div class="stat"><div class="n">${Math.round(club.boardConfidence)}</div><div class="l">הנהלה</div></div>
        <div class="stat"><div class="n">${Math.round(club.fanSupport)}</div><div class="l">קהל</div></div>
      </div>
      <div class="muted">ציפיית ההנהלה: ${esc(club.seasonExpectation)}</div>`
    : `<div class="muted">ידע אימון ${Math.round(me.coaching)} ·
       תקשורת ${Math.round(me.mediaSkill)} · עסקים ${Math.round(me.business)}</div>`;

  // --- טבלה מקוצרת ---
  let tableSnip = "";
  if (club && game.tables[club.leagueId]) {
    const rows = game.standings(club.leagueId);
    const idx = rows.findIndex(r => r.clubId === club.cid);
    const from = Math.max(0, Math.min(idx - 2, rows.length - 5));
    tableSnip = `
      <div class="panel">
        <div class="panel-head"><span class="t">${esc(game.leagueName(club.leagueId))}</span>
          <span class="r">מחזור ${Math.max(0, game.week - 1)}</span></div>
        <div class="panel-body tight">
          ${rows.slice(from, from + 5).map((r, i) => {
            const c = game.clubs[r.clubId];
            return `<div class="row ${c.cid === club.cid ? "me" : ""}">
              <span class="val" style="min-width:18px">${from + i + 1}</span>
              ${crest(c, 22)}
              <span class="grow"><span class="nm">${esc(c.name)}</span></span>
              ${formGuide(c)}
              <span class="val">${r.points}</span>
            </div>`;
          }).join("")}
        </div>
      </div>`;
  }

  // --- הודעות ---
  const news = game.news.slice(-4).reverse();
  const messages = news.length ? `
    <div class="panel">
      <div class="panel-head"><span class="t">הודעות</span>
        <span class="r">${news.length}</span></div>
      <div class="panel-body tight">
        ${news.map(n => {
          const text = n.replace(/^\[[^\]]+\]\s*/, "");
          const when = (n.match(/^\[([^\]]+)\]/) || ["", ""])[1];
          return `<div class="row">
            ${avatarChip(me, club, 26)}
            <span class="grow"><span class="nm">${esc(text)}</span>
              <span class="sub">${esc(when)}</span></span>
          </div>`;
        }).join("")}
      </div>
    </div>` : "";

  return `
  <div class="screen">
    ${saveWarning()}
    ${nextMatch}

    ${offer ? `
    <div class="panel" style="border-color:var(--accent)">
      <div class="panel-head"><span class="t">הצעת העברה</span></div>
      <div class="panel-body">
        <div class="crest-row">${crest(game.clubs[offer.club], 30)}
          <span class="nm"><strong>${esc(game.clubs[offer.club].name)}</strong><br>
          <span class="muted">₪${fmt(offer.wage)} לשבוע · עכשיו ₪${fmt(me.contract.wage)}</span></span>
        </div>
        <button class="mini-btn wide" data-club="${offer.club}">
          לבדוק את המועדון לפני שמחליטים</button>
        <div class="btn-row">
          <button class="btn primary" data-act="accept">לחתום</button>
          <button class="btn" data-act="reject">לדחות</button>
        </div>
      </div>
    </div>` : ""}

    <div class="panel">
      <div class="panel-head"><span class="t">המצב שלך</span>
        <span class="r">₪${fmt(game.money)}</span></div>
      <div class="panel-body">${statusBody}
        ${(() => { const note = selectionNote(game);
          return note ? `<div class="muted selection">${esc(note)}</div>` : ""; })()}
        ${game.flag("directive") && club ? `<div class="directive">🎙️ ${
          esc(directiveLine(club, game.flag("directive"), game.flags.last_stats))
            .replace(/\n/g, "<br>")}</div>` : ""}
        ${(() => { const t = nextTarget(game);
          return t ? `<div class="muted selection">${esc(t)}</div>` : ""; })()}
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">תוכנית השבוע</span>
        <span class="r">${esc((actions.find(a => a[0] === game.trainingFocus) || ["", ""])[1])}</span></div>
      <div class="panel-body">
        <div class="chips">
          ${actions.map(([k, l]) => `<button class="chip" data-focus="${k}"
            aria-pressed="${game.trainingFocus === k}">${esc(l)}</button>`).join("")}
        </div>
        ${isPlayer ? `<hr class="rule">
        <div class="muted">עצימות</div>
        <div class="chips">
          ${[[1.0, "רגילה"], [1.3, "גבוהה"], [0.75, "קלה"]].map(([v, l]) =>
            `<button class="chip" data-int="${v}" aria-pressed="${game.intensity === v}">${l}</button>`).join("")}
        </div>` : ""}
      </div>
    </div>

    ${scoutSnip()}
    ${clubSnip()}
    ${tableSnip}
    ${messages}

    ${savePanel()}

    <button class="btn ghost wide" data-act="menu">תפריט ראשי</button>
  </div>`;
}

/**
 * מסלול הפיתוח — ההכוונה שהייתה חסרה.
 * במקום "תתאמן על משהו", כאן כתוב בדיוק מה צריך להיות לך ומתי.
 */
function screenPlan() {
  const info = planSummary(game);
  if (!info.chosen) {
    return `
    <div class="screen">
      <div class="panel">
        <div class="panel-head"><span class="t">איזה שחקן אתה רוצה להיות?</span></div>
        <div class="panel-body">
          <div class="muted">מסלול הוא דגם שחקן אמיתי עם יעדים לפי גיל.
            בלי מסלול אתה מתאמן בלי לדעת לאן.</div>
        </div>
      </div>
      ${info.options.map(row => `
      <div class="panel">
        <div class="panel-head"><span class="t">${esc(row.name)}</span>
          <span class="r">${esc(row.attrs.join(" · "))}</span></div>
        <div class="panel-body">
          <div class="muted">${esc(row.desc)}</div>
          <button class="btn primary wide" data-plan="${row.key}">לבחור את המסלול הזה</button>
        </div>
      </div>`).join("")}
    </div>`;
  }
  const focusName = info.focus ? D.ATTRIBUTE_NAMES_HE[info.focus] : "";
  return `
  <div class="screen">
    <div class="panel" ${info.breakthrough ? 'style="border-color:var(--accent)"' : ""}>
      <div class="panel-head"><span class="t">${esc(info.name)}</span>
        <span class="r">${info.done}/${info.total}</span></div>
      <div class="panel-body">
        <div class="muted">${esc(info.desc)}</div>
        ${info.breakthrough
          ? `<div class="note"><span class="ico">💎</span><span>הפריצה הושלמה —
             ${esc(info.trait)}.</span></div>`
          : `<div class="muted">השלמת המסלול תיתן לך: ${esc(info.trait)}.</div>`}
        ${info.next ? `<div class="directive">${esc(info.next)}</div>` : ""}
        ${focusName ? `<button class="btn wide" data-focus="${info.focus}">
          להתאמן השבוע על ${esc(focusName)}</button>` : ""}
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">אבני דרך</span></div>
      <div class="panel-body tight">
        ${info.milestones.map(row => `
        <div class="row">
          <span class="val" style="min-width:26px">${
            row.claimed ? "✅" : row.met ? "🟡" : row.late ? "⛔" : "▫️"}</span>
          <span class="grow">
            <span class="nm">גיל ${row.age}</span>
            <span class="sub">${row.needs.map(pt =>
              `${esc(pt.name)} ${pt.have}/${pt.need}`).join(" · ")}</span>
          </span>
        </div>
        ${row.needs.map(pt => `<div class="attr">
          <span>${esc(pt.name)}</span>
          <span class="val">${pt.have}/${pt.need}</span>
          <span class="bar"><i style="width:${Math.min(100,
            Math.round(pt.have / pt.need * 100))}%"></i></span>
        </div>`).join("")}`).join("")}
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">להחליף מסלול</span></div>
      <div class="panel-body">
        <div class="muted">החלפה מאפסת את אבני הדרך שנצברו.</div>
        <div class="chips">
          ${planOptionsFor(game.me.position).map(row =>
            `<button class="chip" data-plan="${row[0]}"
              aria-pressed="${row[0] === info.key}">${esc(row[1])}</button>`).join("")}
        </div>
      </div>
    </div>
  </div>`;
}

/** מי עוקב אחריך — סקאוטינג כתהליך, לא כהטלת מטבע. */
function screenScouts() {
  const ranked = watchers(game);
  if (!ranked.length) {
    return `<div class="screen"><div class="panel">
      <div class="panel-head"><span class="t">מי עוקב אחריך</span></div>
      <div class="panel-body"><div class="muted">אף אחד עדיין לא פתח עליך תיק.
        צופים מגיעים למשחקים — תמשיך לשחק.</div></div>
    </div></div>`;
  }
  return `
  <div class="screen">
    <div class="panel">
      <div class="panel-head"><span class="t">מי עוקב אחריך</span>
        <span class="r">${ranked.length}</span></div>
      <div class="panel-body tight">
        ${ranked.slice(0, 10).map(([club, score]) => `
        <div class="row" data-club="${club.cid}">
          ${crest(club, 24)}
          <span class="grow"><span class="nm">${esc(club.name)}</span>
            <span class="sub">${esc(clubCountry(club.cid))} ·
              ${esc(interestLabel(score))}</span></span>
          <span class="val num">${Math.round(score)}</span>
        </div>
        <div class="attr"><span></span><span class="val"></span>
          <span class="bar"><i style="width:${Math.round(score)}%"></i></span></div>`).join("")}
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><span class="t">התיק שלך אצל ${
        esc(ranked[0][0].name)}</span></div>
      <div class="panel-body">
        ${scoutReport(game, ranked[0][0]).map(line =>
          `<div class="muted">${esc(line)}</div>`).join("")}
      </div>
    </div>
  </div>`;
}

/** כסף: תיק החסויות והנכסים. */
function screenMoney() {
  const portfolio = game.deals();
  const info = wealthSummary(game);
  const market = marketability(game.me,
    game.myClub() ? game.myClub().reputation : 30);
  return `
  <div class="screen">
    <div class="panel">
      <div class="panel-head"><span class="t">שווי נטו</span>
        <span class="r">₪${fmt(info.net_worth)}</span></div>
      <div class="panel-body">
        <div class="stat-grid">
          <div class="stat"><div class="n num">₪${fmt(info.cash)}</div><div class="l">מזומן</div></div>
          <div class="stat"><div class="n num">₪${fmt(info.assets)}</div><div class="l">נכסים</div></div>
          <div class="stat"><div class="n num">₪${fmt(info.yearly)}</div><div class="l">תשואה/שנה</div></div>
        </div>
        <div class="muted">ערך מסחרי: ${Math.round(market)}/100 —
          זה מה שקובע איזה מותגים בכלל מתקשרים אליך.</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">חסויות</span>
        <span class="r">₪${fmt(portfolioTotal(portfolio))} לעונה</span></div>
      <div class="panel-body tight">
        ${portfolio.length ? portfolio.map(deal => `
        <div class="row">
          <span class="grow"><span class="nm">${esc(deal.brand)}</span>
            <span class="sub">${esc(deal.tierHe)} · ${esc(deal.kindHe)} ·
              נותרו ${deal.yearsLeft} שנים</span></span>
          <span class="val num">₪${fmt(deal.annual)}</span>
        </div>
        ${(deal.clauses || []).map(key => {
          const text = clauseText(key, deal.annual);
          return text ? `<div class="muted" style="padding-inline-start:8px">• ${
            esc(text)}</div>` : "";
        }).join("")}`).join("")
        : `<div class="muted">אין לך חסויות פעילות. הן מגיעות לפי הערך המסחרי.</div>`}
      </div>
    </div>

    ${info.items.length ? `
    <div class="panel">
      <div class="panel-head"><span class="t">הנכסים שלך</span>
        <span class="r">${info.count}</span></div>
      <div class="panel-body tight">
        ${info.items.map((item, index) => {
          const delta = item.value - item.paid;
          return `<div class="row">
            <span class="grow"><span class="nm">${esc(item.name)}</span>
              <span class="sub">${esc(item.category)} · נקנה ב-${item.year} ·
                ${delta >= 0 ? "+" : "−"}₪${fmt(Math.abs(delta))}</span></span>
            <span class="val num">₪${fmt(item.value)}</span>
            <button class="mini-btn" data-sell="${index}">למכור</button>
          </div>`;
        }).join("")}
      </div>
    </div>` : ""}

    <div class="panel">
      <div class="panel-head"><span class="t">להשקיע</span></div>
      <div class="panel-body tight">
        ${assetsAvailable(game).map(row => `
        <div class="row">
          <span class="grow"><span class="nm">${
            row.locked ? "🔒 " : ""}${esc(row.name)}</span>
            <span class="sub">${esc(row.category)} ·
              ${(row.yield * 100).toFixed(1)}% לשנה${
              row.locked ? ` · צריך מוניטין ${row.min_rep}` : ""}</span></span>
          <span class="val num">₪${fmt(row.price)}</span>
          ${row.locked || !row.affordable
            ? `<span class="mini-btn" style="opacity:.4">${
                row.locked ? "נעול" : "אין מספיק"}</span>`
            : `<button class="mini-btn" data-buy="${row.key}">לקנות</button>`}
        </div>
        <div class="muted" style="padding-inline-start:8px">${esc(row.desc)}</div>`).join("")}
      </div>
    </div>
  </div>`;
}

/** תקציר הסקאוטינג בסקירה — מי היה ביציע ומי כבר פתח עליך תיק. */
function scoutSnip() {
  if (!["academy", "player", "veteran"].includes(game.stage)) return "";
  const ranked = watchers(game);
  if (!ranked.length) return "";
  return `
  <div class="panel">
    <div class="panel-head"><span class="t">מי עוקב אחריך</span>
      <span class="r"><button class="mini-btn" data-go="scouts">לפרטים</button></span></div>
    <div class="panel-body tight">
      ${ranked.slice(0, 3).map(([club, score]) => `
      <div class="row">
        ${crest(club, 22)}
        <span class="grow"><span class="nm">${esc(club.name)}</span>
          <span class="sub">${esc(clubCountry(club.cid))} ·
            ${esc(interestLabel(score))}</span></span>
        <span class="val num">${Math.round(score)}</span>
      </div>`).join("")}
    </div>
  </div>`;
}

/** תקציר המועדון בסקירה: קופה, קהל ובנייה בתהליך. */
function clubSnip() {
  const club = game.myClub();
  if (!club) return "";
  const money = game.clubFinanceSummary();
  const works = club.works || [];
  const last = money.lastWeek;
  return `
  <div class="panel">
    <div class="panel-head"><span class="t">המועדון</span>
      <span class="r"><button class="mini-btn" data-go="club">לפרטים</button></span></div>
    <div class="panel-body tight">
      <div class="row">
        <span class="nm">🏟️ ${esc(club.stadiumName)}</span>
        <span class="val num">${fmt(club.capacity)}</span>
      </div>
      <div class="row">
        <span class="nm">קופת המועדון</span>
        <span class="val num ${money.balance < 0 ? "bad" : ""}">₪${fmt(money.balance)}</span>
      </div>
      ${last ? `<div class="row">
        <span class="nm">מאזן השבוע</span>
        <span class="val num ${last.net < 0 ? "bad" : "good"}">${
          last.net < 0 ? "−" : "+"}₪${fmt(Math.abs(last.net))}</span>
      </div>` : ""}
      ${works.length ? works.map(w => `<div class="row">
        <span class="nm">🏗️ ${esc(D.FACILITIES[w.kind].name)}</span>
        <span class="val num">${w.weeksLeft} שב'</span>
      </div>`).join("") : ""}
    </div>
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
      ${report.attendance ? `<div class="muted center">🏟️ <span class="num">${
        fmt(report.attendance)}</span> צופים · הכנסות <span class="num">₪${
        fmt(report.finances ? report.finances.matchday : 0)}</span></div>` : ""}
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
  return appbar() + html;
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
      ${avatar(game.me, game.myClub(), 54)}
      <div class="rating ${cls}">${p.rating.toFixed(1)}</div>
      <div class="detail">
        <strong>${p.status === "sub" ? p.minutes + " דקות" : "90 דקות"}</strong>
        <span>${bits.length ? esc(bits.join(" · ")) : "משחק שקט."}</span>
      </div>
    </div>
    ${p.statLines ? `<hr class="rule">
    <div class="statline">${p.statLines.map(line =>
      `<div class="muted">${esc(line)}</div>`).join("")}</div>` : ""}
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
  const isPlayer = ["youth", "academy", "player", "veteran"].includes(game.stage);
  const s = me.season, c = me.career;
  return `
  <div class="screen">
    ${isPlayer ? playerCard(me, club, game.stage)
      + `<button class="mini-btn wide" data-player="${me.pid}">תעודת זהות מלאה</button>` : `
    <div class="card">
      <div class="eyebrow">${esc(D.CAREER_STAGES_HE[game.stage] || game.stage)}</div>
      <div class="kit-row">
        ${club ? crest(club, 58) : ""}
        <div class="kit-meta">
          <span class="display big">${esc(me.name)}</span>
          <span class="muted">בן ${me.age} · ${esc(positionHe(me))} · ${esc(me.nationality)}
            · רגל ${esc(FOOT_NAMES[playerFoot(me)])}</span>
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
  if (["youth", "academy", "player", "veteran"].includes(game.stage))
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
        <span class="avatar-row">${avatarChip(p, club, 30)}
          <span class="num">${p.number || ""}</span> <span class="nm">${esc(p.name)}</span>${
          p.injuryWeeks > 0 ? ` <span class="muted">🚑${p.injuryWeeks}ש</span>` : ""}</span>
        <span class="pos">${esc(positionHe(p))} · ${p.age}</span>
        <span class="ovr">${overall(p)}</span>
      </div>`).join("")}
    </div>
  </div>`;
}

/**
 * עורך מסד הנתונים — שינוי שמות מועדונים ושחקנים, ייצוא וייבוא.
 * מה שנשמר כאן נשמר רק בדפדפן שלך.
 */
function screenEditor() {
  const club = game.myClub();
  const leagues = D.LEAGUES.map(l => l.id);
  const editingLeague = (viewData && viewData.editLeague) || (club ? club.leagueId : "top");
  const clubs = Object.values(game.clubs)
    .filter(c => c.leagueId === editingLeague)
    .sort((a, b) => b.reputation - a.reputation);
  const squad = club ? club.squad.map(p => game.players[p]).filter(Boolean)
    .sort((a, b) => overall(b) - overall(a)) : [];

  return `
  <div class="screen">
    <div class="panel">
      <div class="panel-head"><span class="t">עורך מסד הנתונים</span></div>
      <div class="panel-body">
        <div class="muted">כאן אפשר לתת לכל מועדון ולכל שחקן את השם שאתה רוצה.
        השינויים נשמרים בדפדפן הזה בלבד, יחד עם הקריירה שלך.</div>
        <div class="btn-row">
          <button class="btn" data-act="export-db">ייצוא לקובץ</button>
          <button class="btn" data-act="import-db">ייבוא מקובץ</button>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><span class="t">מועדונים</span>
        <span class="r">${clubs.length}</span></div>
      <div class="panel-body">
        <div class="chips">
          ${leagues.map(id => `<button class="chip" data-editleague="${id}"
            aria-pressed="${editingLeague === id}">${esc(game.leagueName(id))}</button>`).join("")}
        </div>
      </div>
      <div class="panel-body tight">
        ${clubs.map(c => `<div class="row">
          ${crest(c, 26)}
          <input type="text" class="edit-in" data-club="${c.cid}" value="${esc(c.name)}"
            maxlength="26" aria-label="שם המועדון">
          <span class="val">${c.reputation}</span>
        </div>`).join("")}
      </div>
    </div>

    ${identityPicker({ foot: playerFoot(game.me), trait: game.me.traits[0],
                       number: game.me.number }, club, game.me.position)}

    ${squad.length ? `
    <div class="panel">
      <div class="panel-head"><span class="t">הסגל שלך</span>
        <span class="r">${esc(club.name)}</span></div>
      <div class="panel-body tight">
        ${squad.map(p => `<div class="row ${p.pid === game.meId ? "me" : ""}">
          ${avatarChip(p, club, 26)}
          <input type="text" class="edit-in" data-player="${p.pid}" value="${esc(p.name)}"
            maxlength="26" aria-label="שם השחקן">
          <span class="val">${overall(p)}</span>
        </div>`).join("")}
      </div>
    </div>` : ""}
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
  app.querySelectorAll("[data-shirt]").forEach(el =>
    el.addEventListener("click", () => {
      const wanted = +el.dataset.shirt;
      viewData.identity = Object.assign({}, viewData.identity,
        { number: viewData.identity && viewData.identity.number === wanted ? null : wanted });
      render();
    }));
  app.querySelectorAll("[data-newshirt]").forEach(el =>
    el.addEventListener("click", () => {
      toast(game.chooseNumber(+el.dataset.newshirt));
      viewData.pickNumber = false;
      saveGame();
      render();
    }));
  app.querySelectorAll("[data-ident]").forEach(el =>
    el.addEventListener("click", () => {
      const field = el.dataset.ident;
      const value = el.dataset.val;
      if (view === "editor") {
        if (field === "foot") game.me.foot = value;
        else game.me.traits = [value].concat(
          game.me.traits.slice(1).filter(t => t !== value));
        saveGame();
      } else {
        viewData.identity = Object.assign({}, viewData.identity, { [field]: value });
      }
      render();
    }));
  app.querySelectorAll("[data-role]").forEach(el =>
    el.addEventListener("click", () => {
      viewData.role = el.dataset.role;
      viewData.age = el.dataset.role === "manager" ? 42 : 15;
      render();
    }));
  const ageInput = $("#page");
  if (ageInput) {
    ageInput.addEventListener("input", e => {
      viewData.age = +e.target.value;
      const head = app.querySelector(".panel-head .r .num");
      if (head) head.textContent = viewData.age;
      const blurb = ageInput.closest(".panel-body").querySelector(".muted:last-child");
      if (blurb) blurb.textContent = ageBlurb(viewData.age, viewData.role);
    });
  }
  app.querySelectorAll("[data-editleague]").forEach(el =>
    el.addEventListener("click", () => go("editor", { editLeague: el.dataset.editleague })));
  app.querySelectorAll("input.edit-in").forEach(el => {
    el.addEventListener("change", () => {
      const value = el.value.trim();
      if (!value) { el.value = el.dataset.club
        ? game.clubs[el.dataset.club].name : game.players[el.dataset.player].name; return; }
      if (el.dataset.club) game.clubs[el.dataset.club].name = value;
      else if (el.dataset.player) game.players[el.dataset.player].name = value;
      saveGame();
    });
  });
  app.querySelectorAll("[data-league]").forEach(el =>
    el.addEventListener("click", () => go("table", { league: el.dataset.league })));
  app.querySelectorAll("[data-form]").forEach(el =>
    el.addEventListener("click", () => { game.tactics.formation = el.dataset.form; render(); }));
  app.querySelectorAll("[data-ment]").forEach(el =>
    el.addEventListener("click", () => { game.tactics.mentality = el.dataset.ment; render(); }));
  app.querySelectorAll("[data-press]").forEach(el =>
    el.addEventListener("click", () => { game.tactics.pressing = el.dataset.press; render(); }));
  app.querySelectorAll("[data-club]").forEach(el =>
    el.addEventListener("click", () => goDeep("clubinfo", { cid: el.dataset.club })));
  app.querySelectorAll("[data-player]:not(input)").forEach(el =>
    el.addEventListener("click", () => goDeep("player", { pid: el.dataset.player })));
  app.querySelectorAll("[data-plan]").forEach(el =>
    el.addEventListener("click", () => {
      const message = setPlan(game, el.dataset.plan);
      saveGame();
      toast(message);
      render();
    }));
  app.querySelectorAll("[data-buy]").forEach(el =>
    el.addEventListener("click", () => {
      const message = buyAsset(game, el.dataset.buy);
      saveGame();
      toast(message);
      render();
    }));
  app.querySelectorAll("[data-sell]").forEach(el =>
    el.addEventListener("click", () => {
      const message = sellAsset(game, +el.dataset.sell);
      saveGame();
      toast(message);
      render();
    }));
  app.querySelectorAll("[data-upgrade]").forEach(el =>
    el.addEventListener("click", () => {
      const message = game.upgradeFacility(el.dataset.upgrade);
      saveGame();
      toast(message);
      render();
    }));
  app.querySelectorAll("[data-staffrole]").forEach(el =>
    el.addEventListener("click", () => {
      viewData.staffRole = viewData.staffRole === el.dataset.staffrole
        ? null : el.dataset.staffrole;
      render();
    }));
  app.querySelectorAll("[data-hire]").forEach(el =>
    el.addEventListener("click", () => {
      const message = game.hireStaff(el.dataset.hire, +el.dataset.idx);
      viewData.staffRole = null;
      saveGame();
      toast(message);
      render();
    }));
  app.querySelectorAll("[data-fire]").forEach(el =>
    el.addEventListener("click", () => {
      const message = game.releaseStaff(el.dataset.fire);
      saveGame();
      toast(message);
      render();
    }));

  const nameInput = $("#pname");
  if (nameInput) nameInput.addEventListener("input", e => { viewData.name = e.target.value; });
  const clubSelect = $("#pclub");
  if (clubSelect) clubSelect.addEventListener("change", e => { viewData.club = e.target.value; });

  app.querySelectorAll("[data-act]").forEach(el =>
    el.addEventListener("click", () => act(el.dataset.act)));
}

function act(what) {
  if (what === "new") { go("new", { name: "", position: "ST", club: "hapoel_carmel", age: 15,
      role: "player", identity: randomIdentity() }); }
  else if (what === "menu") { if (game) saveGame(); go("menu"); }
  else if (what === "continue") {
    const loaded = loadGame();
    if (!loaded) { alert("לא נמצאה שמורה תקינה."); return; }
    game = loaded;
    go(game.gameOver ? "end" : "main");
  }
  else if (what === "start") {
    const name = (viewData.name || "").trim() || (viewData.role === "manager" ? "דני מנג'ר" : "עומר לוי");
    game = Game.newGame(name, viewData.position, viewData.club, viewData.age,
                        null, viewData.role, viewData.identity);
    saveGame();
    go("main");
  }
  else if (what === "play") playWeek();
  else if (what === "after-week") afterWeek();
  else if (what === "after-outcome") afterOutcome();
  else if (what === "after-season") {
    saveGame();
    saveFile.at = 0;              // סוף עונה הוא נקודת ציון — לכתוב לקובץ בלי ויסות
    writeCareerFile(true);
    go(game.gameOver ? "end" : "main");
  }
  else if (what === "accept") { showOutcome("הצעת העברה", game.acceptOffer()); }
  else if (what === "reject") { showOutcome("הצעת העברה", game.rejectOffer()); }
  else if (what === "restart") { clearSave(); game = null; go("menu"); }
  else if (what === "random-identity") {
    const next = randomIdentity();
    if (view === "editor") {
      game.me.foot = next.foot;
      game.me.traits = [next.trait].concat(
        game.me.traits.slice(1).filter(t => t !== next.trait));
      saveGame();
    } else viewData.identity = next;
    render();
  }
  else if (what === "back") goBack();
  else if (what === "pick-number") { viewData.pickNumber = !viewData.pickNumber; render(); }
  else if (what === "club-squad") { viewData.full = !viewData.full; render(); }
  else if (what === "backup") backupCareer(false);
  else if (what === "backup-as") backupCareer(true);
  else if (what === "unlink-file") unlinkSaveFile();
  else if (what === "restore") restoreCareer();
  else if (what === "export-db") exportDatabase();
  else if (what === "import-db") importDatabase();
}

let pendingSeason = null;

/** מוריד את השמות שערכת כקובץ, כדי שאפשר יהיה לשמור ולשתף אותם. */
function exportDatabase() {
  const data = {
    v: 1,
    clubs: Object.fromEntries(Object.values(game.clubs).map(c => [c.cid, c.name])),
    players: Object.fromEntries(Object.values(game.players)
      .filter(p => p.clubId || p.pid === game.meId).map(p => [p.pid, p.name])),
  };
  const text = JSON.stringify(data, null, 1);
  navigator.clipboard && navigator.clipboard.writeText(text).then(
    () => alert("מסד הנתונים הועתק ללוח. אפשר להדביק אותו לקובץ ולשמור."),
    () => window.prompt("העתק את מסד הנתונים:", text));
  if (!navigator.clipboard) window.prompt("העתק את מסד הנתונים:", text);
}

/** מדביק בחזרה מסד נתונים שערכת. */
function importDatabase() {
  const text = window.prompt("הדבק כאן מסד נתונים שייצאת:");
  if (!text) return;
  let data;
  try { data = JSON.parse(text); } catch (err) {
    alert("הקובץ לא תקין — צריך להדביק בדיוק את מה שיוצא בייצוא.");
    return;
  }
  let changed = 0;
  for (const [cid, name] of Object.entries(data.clubs || {}))
    if (game.clubs[cid] && typeof name === "string" && name.trim()) {
      game.clubs[cid].name = name.trim().slice(0, 26); changed++;
    }
  for (const [pid, name] of Object.entries(data.players || {}))
    if (game.players[pid] && typeof name === "string" && name.trim()) {
      game.players[pid].name = name.trim().slice(0, 26); changed++;
    }
  saveGame();
  alert(changed ? `עודכנו ${changed} שמות.` : "לא נמצא מה לעדכן.");
  render();
}

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
  // סגירת הדף באמצע שבוע לא אמורה למחוק את השבוע
  const saveNow = () => { if (game) saveGame(); };
  loadSaveFile();
  window.addEventListener("pagehide", saveNow);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") saveNow();
  });
  go("menu");
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();
