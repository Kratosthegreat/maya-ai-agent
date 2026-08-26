// ---------------------------------------------------------------------------
// בדיקת השמירה בדפדפן אמיתי
//
// test.js בודק את הדחיסה; כאן בודקים את מה שבאמת נכשל פעם: קריירה
// שנשמרה, דפדפן שנסגר, ושמורה שלא הייתה שם כשחזרו. את זה אי אפשר
// לבדוק בלי דפדפן — צריך localStorage אמיתי, IndexedDB אמיתי, ואת
// היכולת לשבור כל אחד מהם בנפרד ולראות שהשני מחזיק.
//
//   npm install playwright-core   (או playwright)
//   node web/test_save_browser.js
//
// בלי playwright מותקן הבדיקה מדלגת על עצמה ולא נכשלת.
// ---------------------------------------------------------------------------

let chromium;
try { ({ chromium } = require("playwright")); }
catch (err) {
  try { ({ chromium } = require("playwright-core")); }
  catch (err2) {
    console.log("playwright לא מותקן — מדלגים על בדיקת הדפדפן");
    process.exit(0);
  }
}

const fs = require("fs");
const path = require("path");

const PAGE = "file://" + path.join(__dirname, "index.html");

/** נתיב לכרומיום. משתנה סביבה גובר, אחרת מחפשים איפה ש-playwright שם אותו. */
function chromePath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH, "/opt/pw-browsers"].filter(Boolean);
  for (const root of roots) {
    let names = [];
    try { names = fs.readdirSync(root); } catch (err) { continue; }
    for (const name of names.sort().reverse()) {
      if (!name.startsWith("chromium-")) continue;
      const exe = path.join(root, name, "chrome-linux", "chrome");
      if (fs.existsSync(exe)) return exe;
    }
  }
  return undefined;          // playwright המלא יודע למצוא לבד
}

let failures = 0;
const ok = (name, cond, extra) => {
  if (!cond) failures++;
  console.log(`  ${cond ? "\u2713" : "\u2717"} ${name}` +
              (extra === undefined ? "" : "  " + JSON.stringify(extra)));
};

/** שבוע אחד קדימה, יהיה המסך אשר יהיה. */
const STEP_BUTTONS = ['[data-act="after-week"]', '[data-act="after-outcome"]',
                      '[data-choice="0"]', '[data-act="after-season"]',
                      '[data-act="play"]'];

const step = async p => {
  for (const sel of STEP_BUTTONS) {
    const el = await p.$(sel);
    if (el) { await el.click(); await p.waitForTimeout(50); return true; }
  }
  return false;
};

/** קריירה חדשה שרצה מספר שבועות — נקודת הפתיחה של כל תרחיש. */
const start = async (p, weeks) => {
  await p.click('[data-act="new"]'); await p.waitForTimeout(250);
  await p.click('[data-act="start"]'); await p.waitForTimeout(500);
  for (let i = 0; i < weeks; i++) await step(p);
};

(async () => {
  const b = await chromium.launch({ executablePath: chromePath(), args: ["--no-sandbox"] });

  // -- 1. מסלול רגיל: משחקים, סוגרים בלי אזהרה, חוזרים ---------------
  {
    const ctx = await b.newContext({ viewport: { width: 420, height: 900 } });
    const p = await ctx.newPage();
    p.on("pageerror", e => console.log("PAGEERROR", String(e)));
    await p.goto(PAGE);
    await start(p, 40);
    const before = await p.evaluate(() => ({ year: game.year, week: game.week, name: game.me.name,
      store: saveState.store, localKB: Math.round((localStorage.getItem('fm_career_save_v1')||'').length*2/1024) }));
    // סגירת דף אלימה — בלי pagehide ובלי זמן ל-IndexedDB
    const p2 = await ctx.newPage();
    await p.close({ runBeforeUnload: false });
    await p2.goto(PAGE);
    await p2.waitForTimeout(100);
    const cont = await p2.$('[data-act="continue"]');
    ok('כפתור המשך מופיע מיד אחרי סגירה פתאומית', !!cont, before);
    if (cont) {
      await cont.click(); await p2.waitForTimeout(600);
      const after = await p2.evaluate(() => ({ year: game && game.year, week: game && game.week, name: game && game.me.name }));
      ok('הקריירה חזרה באותו שבוע', after.year === before.year && after.week === before.week && after.name === before.name, after);
    }
    await ctx.close();
  }

  // -- 2. IndexedDB תקוע לגמרי: open לא עונה לעולם --------------------
  {
    const ctx = await b.newContext({ viewport: { width: 420, height: 900 } });
    await ctx.addInitScript(() => {
      indexedDB.open = () => ({ set onsuccess(v){}, set onerror(v){}, set onupgradeneeded(v){}, set onblocked(v){} });
    });
    const p = await ctx.newPage();
    p.on("pageerror", e => console.log("PAGEERROR", String(e)));
    await p.goto(PAGE);
    await start(p, 30);
    const before = await p.evaluate(() => ({ year: game.year, week: game.week, name: game.me.name,
      store: saveState.store, ok: saveState.ok }));
    ok('שמירה עובדת גם כש-IndexedDB תקוע', before.ok && before.store === 'local', before);
    await p.reload(); await p.waitForTimeout(200);
    const cont = await p.$('[data-act="continue"]');
    ok('כפתור המשך מופיע גם כש-IndexedDB תקוע', !!cont);
    if (cont) {
      await cont.click(); await p.waitForTimeout(600);
      const after = await p.evaluate(() => ({ year: game && game.year, week: game && game.week }));
      ok('הקריירה חזרה למרות IndexedDB התקוע', after.year === before.year && after.week === before.week, after);
    }
    await ctx.close();
  }

  // -- 3. IndexedDB זורק מיד (גלישה פרטית) ----------------------------
  {
    const ctx = await b.newContext({ viewport: { width: 420, height: 900 } });
    await ctx.addInitScript(() => { indexedDB.open = () => { throw new DOMException('blocked', 'SecurityError'); }; });
    const p = await ctx.newPage();
    p.on("pageerror", e => console.log("PAGEERROR", String(e)));
    await p.goto(PAGE);
    await start(p, 20);
    const before = await p.evaluate(() => ({ week: game.week, year: game.year, ok: saveState.ok, store: saveState.store }));
    ok('שמירה עובדת כשהאחסון המורחב זורק', before.ok, before);
    await p.reload(); await p.waitForTimeout(200);
    ok('יש שמורה אחרי רענון בגלישה פרטית', !!(await p.$('[data-act="continue"]')));
    await ctx.close();
  }

  // -- 4. localStorage מלא: IndexedDB חייב להחזיק, וגם לנצח בטעינה ---
  {
    const ctx = await b.newContext({ viewport: { width: 420, height: 900 } });
    const p = await ctx.newPage();
    p.on("pageerror", e => console.log("PAGEERROR", String(e)));
    await p.goto(PAGE);
    await start(p, 20);
    const early = await p.evaluate(() => ({ week: game.week, year: game.year }));
    // מכאן והלאה localStorage מסרב לקבל את השמורה הגדולה
    await p.evaluate(() => {
      const real = Storage.prototype.setItem;
      Storage.prototype.setItem = function (key, value) {
        if (String(value).length > 4096) throw new DOMException('full', 'QuotaExceededError');
        return real.call(this, key, value);
      };
    });
    for (let i = 0; i < 20; i++) await step(p);
    const late = await p.evaluate(() => ({ week: game.week, year: game.year,
      ok: saveState.ok, store: saveState.store, stale: !!localStorage.getItem('fm_career_save_stale') }));
    ok('IndexedDB מחזיק כשהאחסון המהיר מלא', late.ok && late.store === 'idb' && late.stale, late);
    ok('המשחק באמת התקדם מאז הכתיבה האחרונה שהצליחה', late.week !== early.week || late.year !== early.year, { early, late });
    await p.reload(); await p.waitForTimeout(1200);
    const cont = await p.$('[data-act="continue"]');
    ok('יש כפתור המשך גם כשהמהיר מיושן', !!cont);
    if (cont) {
      await cont.click(); await p.waitForTimeout(1500);
      const after = await p.evaluate(() => ({ week: game && game.week, year: game && game.year }));
      ok('נטענה השמורה החדשה מ-IndexedDB ולא המיושנת',
        after.week === late.week && after.year === late.year, { after, late, early });
    }
    await ctx.close();
  }

  // -- 5. קריירה ארוכה: השמורה חייבת להישאר בתוך המכסה ---------------
  //
  // המכסה של localStorage היא בערך 5MB, והיא נמדדת בתווים של UTF-16.
  // קריירה גדלה עם השנים, ולכן הבדיקה כאן היא לא של רגע אחד אלא של
  // מגמה: גם אחרי חמש עונות צריך להישאר מרווח אמיתי.
  {
    const ctx = await b.newContext({ viewport: { width: 420, height: 900 } });
    const p = await ctx.newPage();
    p.on("pageerror", e => console.log("PAGEERROR", String(e)));
    await p.goto(PAGE);
    await start(p, 30);
    let last = null;
    for (const weeks of [120, 200, 300]) {
      for (let i = 0; i < weeks; i++) await step(p);
      last = await p.evaluate(() => {
        const raw = localStorage.getItem("fm_career_save_v1") || "";
        const t0 = performance.now(); saveGame(); const t1 = performance.now();
        return { year: game.year, week: game.week, format: raw.slice(0, 4),
                 quotaKB: Math.round(raw.length * 2 / 1024),
                 saveMs: Math.round(t1 - t0), store: saveState.store };
      });
      ok(`עונת ${last.year}: השמורה בתוך המכסה`, last.quotaKB < 2560, last);
    }
    ok("הקידוד הצפוף נבחר", last && last.format === "fm3:", last);
    ok("שמירה נשארת מהירה מספיק לשבוע", last && last.saveMs < 800, last);
    await ctx.close();
  }

  await b.close();
  console.log(`\n${failures ? failures + " נכשלו" : "הכל עבר"}\n`);
  process.exit(failures ? 1 : 0);
})();
