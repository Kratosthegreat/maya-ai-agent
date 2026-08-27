// ---------------------------------------------------------------------------
// widgets.js — אבני הבניין של התצוגה
//
// כאן יושבים החלקים החוזרים של המסכים: טבעות דירוג, מדי־כושר, כרטיס
// המשחק הבא, אריחי סטטיסטיקה, תגי מיקום וגרף קו. כולם מחזירים HTML
// כמחרוזת ואף אחד מהם לא נוגע ב-DOM — לכן אפשר לבדוק אותם ב-node בלי
// דפדפן, וזו הסיבה שהם יושבים כאן ולא בתוך `ui.js`.
//
// הטקסט נכנס דרך `wEsc` בתוך הפונקציות עצמן. HTML שכבר נבנה (סמל
// מועדון, אווטאר) מועבר כמו שהוא — לפרמטרים כאלה יש שם שמתחיל ב-html.
// ---------------------------------------------------------------------------

function wEsc(s) {
  return String(s === null || s === undefined ? "" : s)
    .replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

const TONE_VARS = {
  accent: "--accent", accent2: "--accent-2", good: "--good", warn: "--warn",
  bad: "--bad", gold: "--gold", soft: "--neutral",
};

function toneColor(tone) {
  return `var(${TONE_VARS[tone] || TONE_VARS.accent})`;
}

/** גוון לפי אחוז — ירוק בגבוה, ענבר באמצע, אדום בנמוך. */
function toneFor(pct) {
  return pct >= 72 ? "good" : pct >= 45 ? "warn" : "bad";
}

function clampPct(value, max) {
  const m = max || 100;
  return Math.max(0, Math.min(100, (Number(value) || 0) / m * 100));
}

/**
 * טבעת דירוג — מספר גדול עם קשת שמראה כמה זה מתוך המקסימום.
 *
 * מספר לבד לא אומר כלום: "77" הופך למשמעותי רק כשרואים שהקשת מלאה
 * שלושה רבעים. זה הרכיב המרכזי של הממשק החדש.
 */
function ring(value, opts) {
  const o = Object.assign({ max: 100, size: 62, stroke: 5, label: "",
                            text: null, tone: "accent" }, opts || {});
  const pct = clampPct(value, o.max) / 100;
  const r = (o.size - o.stroke) / 2;
  const mid = o.size / 2;
  const circ = 2 * Math.PI * r;
  const shown = o.text === null || o.text === undefined
    ? String(Math.round(Number(value) || 0)) : String(o.text);
  return `<div class="ring-wrap">
    <div class="ring" style="width:${o.size}px;height:${o.size}px">
      <svg viewBox="0 0 ${o.size} ${o.size}" width="${o.size}" height="${o.size}"
        role="img" aria-label="${wEsc(o.label ? o.label + " " + shown : shown)}">
        <circle cx="${mid}" cy="${mid}" r="${r}" fill="none"
          stroke="var(--panel-3)" stroke-width="${o.stroke}"/>
        <circle cx="${mid}" cy="${mid}" r="${r}" fill="none"
          stroke="${toneColor(o.tone)}" stroke-width="${o.stroke}" stroke-linecap="round"
          stroke-dasharray="${(circ * pct).toFixed(2)} ${(circ + 1).toFixed(2)}"
          transform="rotate(-90 ${mid} ${mid})"/>
      </svg>
      <span class="ring-val" style="font-size:${Math.round(o.size * 0.34)}px"
        >${wEsc(shown)}</span>
    </div>
    ${o.label ? `<span class="ring-label">${wEsc(o.label)}</span>` : ""}
  </div>`;
}

/**
 * שורת מד: שם מימין, פס באמצע, ערך משמאל.
 * כשלא נמסר גוון — הצבע נגזר מהאחוז, כך שמסך אדום נראה אדום.
 */
function meter(label, value, opts) {
  const o = Object.assign({ max: 100, tone: null, text: null }, opts || {});
  const pct = clampPct(value, o.max);
  const tone = o.tone || toneFor(pct);
  const shown = o.text === null || o.text === undefined
    ? Math.round(pct) + "%" : String(o.text);
  return `<div class="meter">
    <span class="mk">${wEsc(label)}</span>
    <span class="mbar"><i class="${tone}" style="width:${pct.toFixed(1)}%"></i></span>
    <span class="mval num">${wEsc(shown)}</span>
  </div>`;
}

/** שורת מד שהערך שלה הוא מילה או אימוג'י ולא אחוז — מורל, סיכון פציעה. */
function verdictRow(label, text, tone) {
  return `<div class="meter verdict">
    <span class="mk">${wEsc(label)}</span>
    <span class="mbar hidden"></span>
    <span class="mval ${wEsc(tone || "")}">${wEsc(text)}</span>
  </div>`;
}

/** אריח סטטיסטיקה — אייקון, מספר, תווית. ארבעה בשורה. */
function statTile(icon, value, label) {
  return `<div class="tile">
    <span class="ico">${wEsc(icon)}</span>
    <span class="v num">${wEsc(value)}</span>
    <span class="l">${wEsc(label)}</span>
  </div>`;
}

/**
 * כרטיס המשחק הבא: סמל מול סמל ו-VS באמצע.
 * `home`/`away` הם { html, name, mine } — ה-html הוא הסמל שכבר נבנה.
 */
function matchup(home, away, opts) {
  const o = Object.assign({ meta: "", note: "" }, opts || {});
  const side = (team, cls) => `<div class="mu-side ${cls}">
    ${team.html || ""}
    <span class="mu-name ${team.mine ? "mine" : ""}">${wEsc(team.name)}</span>
  </div>`;
  return `<div class="matchup">
    ${side(home, "home")}
    <div class="mu-vs">VS</div>
    ${side(away, "away")}
    ${o.meta ? `<div class="mu-meta">${wEsc(o.meta)}</div>` : ""}
    ${o.note ? `<div class="mu-meta">${wEsc(o.note)}</div>` : ""}
  </div>`;
}

/** תג מיקום בטבלה — צבוע כשהמיקום אומר משהו (עלייה, ירידה, אתה). */
function rankBadge(pos, tone) {
  return `<span class="rank ${wEsc(tone || "")}">${wEsc(pos)}</span>`;
}

/**
 * גרף קו. `values` הם המספרים, `labels` תוויות ציר ה-x (אפשר לתת רק
 * לקצוות — מה שלא נמסר פשוט לא מצויר).
 *
 * הסקאלה נגזרת מהערכים עצמם ולא מ-0, אחרת עלייה מ-70 ל-80 נראית שטוחה.
 */
function sparkline(values, opts) {
  const o = Object.assign({ labels: [], tone: "accent", alt: "", height: 96,
                            dots: true }, opts || {});
  const nums = (values || []).map(v => Number(v) || 0);
  if (nums.length < 2) return "";
  const W = 300, H = o.height, padT = 12, padB = 20, padL = 26, padR = 12;
  const lo = Math.min(...nums), hi = Math.max(...nums);
  // כשכל הערכים זהים אין טווח לחלק בו — פורשים רצועה קטנה סביבם
  const min = lo === hi ? lo - 1 : lo;
  const max = lo === hi ? hi + 1 : hi;
  const stepX = (W - padL - padR) / (nums.length - 1);
  const x = i => padL + i * stepX;
  const y = v => padT + (1 - (v - min) / (max - min)) * (H - padT - padB);
  const color = toneColor(o.tone);
  const path = nums.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `M${x(0).toFixed(1)},${(H - padB).toFixed(1)} `
    + nums.map((v, i) => `L${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ")
    + ` L${x(nums.length - 1).toFixed(1)},${(H - padB).toFixed(1)} Z`;
  // התווית התחתונה יושבת מעל הקו ולא במרכזו — מתחתיה כבר יש את
  // תוויות ציר ה-x, ושתיהן יחד נראו כמו כתם.
  const ticks = [[max, 3.4], [min, -4]];

  return `<svg viewBox="0 0 ${W} ${H}" class="chart spark" role="img"
    aria-label="${wEsc(o.alt)}">
    ${ticks.map(([t, dy]) => `
      <line x1="${padL}" y1="${y(t).toFixed(1)}" x2="${W - padR}" y2="${y(t).toFixed(1)}"
        stroke="var(--line)" stroke-width="1"/>
      <text x="${padL - 6}" y="${(y(t) + dy).toFixed(1)}" font-size="10" text-anchor="end"
        fill="var(--ink-soft)" font-family="Assistant, sans-serif">${Math.round(t)}</text>`).join("")}
    <path d="${area}" fill="${color}" opacity=".10"/>
    <path d="${path}" fill="none" stroke="${color}" stroke-width="2"
      stroke-linejoin="round" stroke-linecap="round"/>
    ${o.dots ? nums.map((v, i) => `<circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}"
      r="${i === nums.length - 1 ? 4 : 2.6}" fill="${color}"
      stroke="var(--panel)" stroke-width="${i === nums.length - 1 ? 2 : 0}"/>`).join("") : ""}
    ${o.labels.map((lab, i) => lab ? `<text x="${x(i).toFixed(1)}" y="${H - 5}"
      font-size="9.5" text-anchor="middle" fill="var(--ink-soft)"
      font-family="Assistant, sans-serif">${wEsc(lab)}</text>` : "").join("")}
  </svg>`;
}

/** שורת דואר נכנס — סמל, כותרת, תאריך. `html` הוא האייקון שכבר נבנה. */
function inboxRow(icon, title, when, opts) {
  const o = Object.assign({ tone: "", attrs: "" }, opts || {});
  return `<div class="msg ${wEsc(o.tone)}"${o.attrs}>
    <span class="msg-ico">${wEsc(icon)}</span>
    <span class="msg-body"><span class="msg-t">${wEsc(title)}</span></span>
    ${when ? `<span class="msg-when num">${wEsc(when)}</span>` : ""}
  </div>`;
}
