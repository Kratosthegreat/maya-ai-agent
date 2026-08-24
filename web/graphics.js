// ---------------------------------------------------------------------------
// גרפיקה — הכל SVG מחולל, בלי תמונות חיצוניות.
// סמלי מועדונים, צבעי מדים, מגרש עם ההרכב, ציר שערים, חולצה, וגרפים.
// ---------------------------------------------------------------------------

// צבעי המדים נגזרים מהכינוי של כל מועדון (הצהובים, הירוקים, הנחשים...)
const KITS = {
  hapoel_yam:      ["#123A6B", "#FFFFFF", "hoops"],
  maccabi_harel:   ["#F2C230", "#16264A", "solid"],
  bnei_negev:      ["#C87A2E", "#3B2412", "sash"],
  hapoel_carmel:   ["#B4231F", "#FFFFFF", "solid"],
  maccabi_sharon:  ["#1E7A46", "#FFFFFF", "halves"],
  ironi_galil:     ["#1B6F6A", "#EDE8D8", "stripes"],
  beitar_zion:     ["#1A1A1A", "#F2C230", "stripes"],
  hapoel_ayalon:   ["#C0392B", "#F5F5F5", "sash"],
  maccabi_yarden:  ["#1F5FA8", "#2E8B57", "halves"],
  shimshon_ashdod: ["#1FA3A3", "#FFFFFF", "hoops"],
  hakoah_arava:    ["#E2701A", "#1A1A1A", "sash"],
  ironi_kinneret:  ["#5AA9E6", "#FFFFFF", "solid"],

  maccabi_tavor:   ["#6B3FA0", "#FFFFFF", "stripes"],
  hapoel_lachish:  ["#3E7A2E", "#E8C25A", "hoops"],
  ironi_modiin:    ["#20509E", "#FFFFFF", "sash"],
  bnei_hasharon:   ["#E8791E", "#FFFFFF", "halves"],
  maccabi_arad:    ["#7A4B2A", "#E2A03F", "stripes"],
  hapoel_ramla:    ["#7B2233", "#F0E6D2", "solid"],
  shimshon_dan:    ["#16264A", "#C0392B", "halves"],
  ironi_besor:     ["#177C6E", "#FFFFFF", "sash"],
  maccabi_negba:   ["#5E6A70", "#C0392B", "hoops"],
  hapoel_ofakim:   ["#4FA3D1", "#E8791E", "stripes"],
  bnei_zvulun:     ["#14304F", "#D9B44A", "sash"],
  ironi_shomron:   ["#6E7B3A", "#FFFFFF", "solid"],

  real_castilla:   ["#F5F5F0", "#C8A24A", "solid"],
  olympia_munchen: ["#C8102E", "#FFFFFF", "hoops"],
  thames_united:   ["#B4231F", "#1A1A1A", "halves"],
  inter_lazio:     ["#1B2A6B", "#1A1A1A", "stripes"],
  paris_luxe:      ["#16264A", "#C0392B", "sash"],
  ajax_noord:      ["#F5F5F0", "#C8102E", "sash"],
  porto_atlantico: ["#1F63B8", "#FFFFFF", "stripes"],
  galata_bosphorus:["#E8B21E", "#B4231F", "halves"],
};

const FALLBACK_KIT = ["#4A5A50", "#FFFFFF", "solid"];

function kit(cid) { return KITS[cid] || FALLBACK_KIT; }

/** שחור או לבן — מה שקריא יותר מעל הצבע הנתון. */
function inkOn(hex) {
  const c = hex.replace("#", "");
  const r = parseInt(c.slice(0, 2), 16) / 255;
  const g = parseInt(c.slice(2, 4), 16) / 255;
  const b = parseInt(c.slice(4, 6), 16) / 255;
  const lin = v => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
  const L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  return L > 0.42 ? "#14201A" : "#F4F7F2";
}

function shade(hex, amount) {
  const c = hex.replace("#", "");
  const parts = [0, 2, 4].map(i => parseInt(c.slice(i, i + 2), 16));
  const out = parts.map(v => Math.max(0, Math.min(255,
    Math.round(amount < 0 ? v * (1 + amount) : v + (255 - v) * amount))));
  return "#" + out.map(v => v.toString(16).padStart(2, "0")).join("");
}

/** ראשי התיבות של שם המועדון — שתי אותיות. */
function initials(name) {
  const words = name.replace(/["']/g, "").split(/\s+/).filter(Boolean);
  if (words.length === 1) return words[0].slice(0, 2);
  return words[0][0] + words[1][0];
}

// ---------------------------------------------------------------------------
// סמל המועדון
// ---------------------------------------------------------------------------

const SHIELD = "M6,6 H94 V64 C94,90 74,106 50,116 C26,106 6,90 6,64 Z";
let crestSeq = 0;

function crest(club, size = 28) {
  const [primary, secondary, pattern] = kit(club.cid);
  const id = "cr" + (++crestSeq);
  const ink = inkOn(primary);
  const bandInk = inkOn(secondary);

  let motif = "";
  if (pattern === "stripes") {
    motif = [18, 42, 66].map(x =>
      `<rect x="${x}" y="0" width="14" height="120" fill="${secondary}"/>`).join("");
  } else if (pattern === "hoops") {
    motif = [22, 52, 82].map(y =>
      `<rect x="0" y="${y}" width="100" height="14" fill="${secondary}"/>`).join("");
  } else if (pattern === "halves") {
    motif = `<rect x="50" y="0" width="50" height="120" fill="${secondary}"/>`;
  } else if (pattern === "sash") {
    motif = `<path d="M0,26 L100,86 L100,108 L0,48 Z" fill="${secondary}"/>`;
  }

  return `<svg class="crest" width="${size}" height="${size * 1.16}" viewBox="0 0 100 120"
    role="img" aria-label="סמל ${escAttr(club.name)}">
    <defs><clipPath id="${id}"><path d="${SHIELD}"/></clipPath></defs>
    <path d="${SHIELD}" fill="${primary}"/>
    <g clip-path="url(#${id})">${motif}
      <rect x="0" y="52" width="100" height="26" fill="${secondary}" opacity=".92"/>
      <text x="50" y="71" text-anchor="middle" font-size="20" font-weight="700"
        fill="${bandInk}" font-family="Assistant, sans-serif">${escAttr(initials(club.name))}</text>
    </g>
    <path d="${SHIELD}" fill="none" stroke="${shade(primary, -0.45)}" stroke-width="5"/>
  </svg>`;
}

function escAttr(s) {
  return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// ---------------------------------------------------------------------------
// חולצה עם מספר
// ---------------------------------------------------------------------------

function shirt(club, number, size = 74) {
  const [primary, secondary, pattern] = club ? kit(club.cid) : FALLBACK_KIT;
  const id = "sh" + (++crestSeq);
  const ink = inkOn(primary);
  const body = "M22,16 L38,8 C42,16 58,16 62,8 L78,16 L86,34 L72,42 L72,92 L28,92 L28,42 L14,34 Z";
  let motif = "";
  if (pattern === "stripes")
    motif = [30, 46, 62].map(x => `<rect x="${x}" y="0" width="9" height="100" fill="${secondary}"/>`).join("");
  else if (pattern === "hoops")
    motif = [30, 52, 74].map(y => `<rect x="0" y="${y}" width="100" height="10" fill="${secondary}"/>`).join("");
  else if (pattern === "halves")
    motif = `<rect x="50" y="0" width="50" height="100" fill="${secondary}"/>`;
  else if (pattern === "sash")
    motif = `<path d="M8,24 L92,66 L92,80 L8,38 Z" fill="${secondary}"/>`;

  return `<svg width="${size}" height="${size}" viewBox="0 0 100 100" role="img"
    aria-label="חולצה מספר ${number}">
    <defs><clipPath id="${id}"><path d="${body}"/></clipPath></defs>
    <path d="${body}" fill="${primary}"/>
    <g clip-path="url(#${id})">${motif}</g>
    <path d="${body}" fill="none" stroke="${shade(primary, -0.4)}" stroke-width="3"/>
    <text x="50" y="76" text-anchor="middle" font-size="38" font-weight="700"
      fill="${ink}" font-family="Assistant, sans-serif">${number}</text>
  </svg>`;
}

// ---------------------------------------------------------------------------
// המגרש וההרכב
// ---------------------------------------------------------------------------

const ROW_OF = { GK: 0, CB: 1, LB: 1, RB: 1, DM: 2, CM: 2, AM: 3, LW: 3, RW: 3, ST: 4 };
const LATERAL = { LB: -2, LW: -2, RB: 2, RW: 2, CB: 0, DM: 0, CM: 0, AM: 0, ST: 0, GK: 0 };
const ROW_Y = [150, 122, 92, 62, 32];

/** מצייר את ההרכב על מגרש. השחקן האנושי מסומן. */
function pitch(lineup, formation, players, meId, club) {
  const slots = D.FORMATIONS[formation] || D.FORMATIONS["4-3-3"];
  const [primary] = club ? kit(club.cid) : FALLBACK_KIT;
  const dotInk = inkOn(primary);

  const rows = [[], [], [], [], []];
  lineup.forEach((pid, idx) => {
    const slot = idx < slots.length ? slots[idx] : (players[pid] || {}).position || "CM";
    rows[ROW_OF[slot] ?? 2].push({ pid, slot });
  });

  let dots = "";
  rows.forEach((row, r) => {
    if (!row.length) return;
    row.sort((a, b) => LATERAL[a.slot] - LATERAL[b.slot]);
    const step = 100 / (row.length + 1);
    row.forEach((entry, i) => {
      const x = step * (i + 1);
      const y = ROW_Y[r];
      const p = players[entry.pid];
      const isMe = entry.pid === meId;
      dots += `
        <g>
          <circle cx="${x}" cy="${y}" r="${isMe ? 7 : 5.4}"
            fill="${isMe ? "var(--accent-fill)" : primary}"
            stroke="${isMe ? "var(--accent-fill)" : shade(primary, -0.4)}" stroke-width="1.4"/>
          <text x="${x}" y="${y + 2.6}" text-anchor="middle" font-size="6.4" font-weight="700"
            fill="${isMe ? "#241803" : dotInk}"
            font-family="Assistant, sans-serif">${p && p.number ? p.number : ""}</text>
          ${isMe ? `<text x="${x}" y="${y - 10}" text-anchor="middle" font-size="7"
            font-weight="700" fill="var(--accent)"
            font-family="Assistant, sans-serif">${escAttr(shortName(p.name))}</text>` : ""}
        </g>`;
    });
  });

  return `<svg viewBox="0 0 100 170" class="pitch" role="img" aria-label="ההרכב על המגרש">
    <rect x="0" y="0" width="100" height="170" fill="var(--pitch-turf)"/>
    ${[0, 1, 2, 3, 4, 5].map(i =>
      `<rect x="0" y="${i * 28.4}" width="100" height="14.2" fill="var(--pitch-stripe)"/>`).join("")}
    <g fill="none" stroke="var(--pitch-line)" stroke-width="0.8">
      <rect x="4" y="4" width="92" height="162"/>
      <line x1="4" y1="85" x2="96" y2="85"/>
      <circle cx="50" cy="85" r="14"/>
      <rect x="28" y="4" width="44" height="20"/>
      <rect x="28" y="146" width="44" height="20"/>
      <rect x="40" y="4" width="20" height="8"/>
      <rect x="40" y="158" width="20" height="8"/>
    </g>
    ${dots}
  </svg>`;
}

function shortName(name) {
  const parts = String(name).split(/\s+/);
  return parts.length > 1 ? parts[parts.length - 1] : name;
}

// ---------------------------------------------------------------------------
// ציר השערים של המשחק
// ---------------------------------------------------------------------------

function goalTimeline(result, homeClub, awayClub, meId) {
  const goals = result.events.filter(e => e.kind === "goal");
  const reds = result.events.filter(e => e.kind === "red");
  const homeColor = kit(homeClub.cid)[0];
  const awayColor = kit(awayClub.cid)[0];
  const W = 300, H = 46, PAD = 14, BASE = 23;
  const x = m => PAD + (Math.min(m, 93) / 93) * (W - PAD * 2);

  const marks = goals.map(g => {
    const home = g.clubId === homeClub.cid;
    const y = home ? 11 : 35;
    const me = g.playerId === meId;
    return `<g>
      <line x1="${x(g.minute)}" y1="${BASE}" x2="${x(g.minute)}" y2="${y}"
        stroke="var(--line)" stroke-width="1"/>
      <circle cx="${x(g.minute)}" cy="${y}" r="${me ? 5.5 : 4.5}"
        fill="${home ? homeColor : awayColor}"
        stroke="${me ? "var(--accent-fill)" : "var(--surface)"}" stroke-width="2">
        <title>${g.minute}' ${escAttr(homeClub.name && "")}</title>
      </circle>
    </g>`;
  }).join("");

  const cards = reds.map(c =>
    `<rect x="${x(c.minute) - 1.6}" y="${BASE - 4}" width="3.2" height="8" rx="0.8"
      fill="var(--loss)"/>`).join("");

  return `<svg viewBox="0 0 ${W} ${H}" class="timeline" role="img"
    aria-label="ציר הזמן של השערים במשחק">
    <line x1="${PAD}" y1="${BASE}" x2="${W - PAD}" y2="${BASE}"
      stroke="var(--line)" stroke-width="1.4"/>
    ${[15, 30, 60, 75].map(m =>
      `<line x1="${x(m)}" y1="${BASE - 3}" x2="${x(m)}" y2="${BASE + 3}"
        stroke="var(--line)" stroke-width="1"/>`).join("")}
    <line x1="${x(45)}" y1="${BASE - 6}" x2="${x(45)}" y2="${BASE + 6}"
      stroke="var(--ink-soft)" stroke-width="1"/>
    ${marks}${cards}
  </svg>`;
}

// ---------------------------------------------------------------------------
// חמישה משחקים אחרונים — צבע ואות יחד, אף פעם לא צבע לבד
// ---------------------------------------------------------------------------

const OUTCOME_HE = { W: "נ", D: "ת", L: "ה" };
const OUTCOME_LABEL = { W: "ניצחון", D: "תיקו", L: "הפסד" };

function formGuide(club) {
  const log = (club.formLog || []).slice(-5);
  if (!log.length) return "";
  return `<span class="form" role="img" aria-label="חמישה משחקים אחרונים: ${
    log.map(o => OUTCOME_LABEL[o]).join(", ")}">${
    log.map(o => `<span class="f f-${o.toLowerCase()}">${OUTCOME_HE[o]}</span>`).join("")}</span>`;
}

// ---------------------------------------------------------------------------
// גרפים — סדרה אחת, סימנים דקים, רשת דקיקה
// ---------------------------------------------------------------------------

/** עמודות: ערך אחד לעונה. מסמן ישירות רק את השיא. */
function columns(data, opts = {}) {
  if (!data.length) return "";
  const w = 300, h = 96, padB = 16, padT = 12;
  const max = Math.max(1, ...data.map(d => d.value));
  const band = w / data.length;
  const barW = Math.min(24, band * 0.56);
  const peak = data.reduce((a, b) => (b.value > a.value ? b : a), data[0]);

  const bars = data.map((d, i) => {
    const x = band * i + (band - barW) / 2;
    const barH = (d.value / max) * (h - padB - padT);
    const y = h - padB - barH;
    const isPeak = d === peak && d.value > 0;
    return `<g>
      <rect x="${x}" y="${y}" width="${barW}" height="${Math.max(barH, 0.6)}"
        rx="4" fill="var(--accent-fill)" opacity="${isPeak ? 1 : 0.62}">
        <title>${escAttr(d.label)}: ${d.value}</title></rect>
      ${isPeak ? `<text x="${x + barW / 2}" y="${y - 4}" text-anchor="middle" font-size="11"
        font-weight="700" fill="var(--ink)" font-family="Assistant, sans-serif">${d.value}</text>` : ""}
      <text x="${x + barW / 2}" y="${h - 4}" text-anchor="middle" font-size="9"
        fill="var(--ink-soft)" font-family="Assistant, sans-serif">${escAttr(d.label)}</text>
    </g>`;
  }).join("");

  return `<svg viewBox="0 0 ${w} ${h}" class="chart" role="img"
    aria-label="${escAttr(opts.alt || "")}">
    <line x1="0" y1="${h - padB}" x2="${w}" y2="${h - padB}"
      stroke="var(--line)" stroke-width="1"/>
    ${bars}
  </svg>`;
}

/** קו: המיקום בטבלה לאורך העונה (ציר הפוך — המקום הראשון למעלה). */
function positionLine(points, teams, opts = {}) {
  if (points.length < 2) return "";
  const W = 300, H = 108, padT = 16, padB = 22, padL = 26, padR = 16;
  const stepX = (W - padL - padR) / Math.max(1, points.length - 1);
  const y = pos => padT + ((pos - 1) / Math.max(1, teams - 1)) * (H - padT - padB);
  const path = points.map((p, i) => `${i ? "L" : "M"}${padL + i * stepX},${y(p)}`).join(" ");
  const last = points[points.length - 1];
  const lastX = padL + (points.length - 1) * stepX;
  const ticks = [...new Set([1, Math.ceil(teams / 2), teams])];

  return `<svg viewBox="0 0 ${W} ${H}" class="chart" role="img"
    aria-label="${escAttr(opts.alt || "")}">
    ${ticks.map(p => `
      <line x1="${padL}" y1="${y(p)}" x2="${W - padR}" y2="${y(p)}"
        stroke="var(--line)" stroke-width="1"/>
      <text x="${padL - 6}" y="${y(p) + 3.4}" font-size="10" text-anchor="end"
        fill="var(--ink-soft)" font-family="Assistant, sans-serif">${p}</text>`).join("")}
    <path d="${path}" fill="none" stroke="var(--accent-fill)" stroke-width="2"
      stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${lastX}" cy="${y(last)}" r="4.5" fill="var(--accent-fill)"
      stroke="var(--surface)" stroke-width="2"/>
    <text x="${lastX - 7}" y="${y(last) - 7}" font-size="11" font-weight="700"
      text-anchor="middle" fill="var(--ink)"
      font-family="Assistant, sans-serif">${last}</text>
    <text x="${padL}" y="${H - 5}" font-size="9.5" fill="var(--ink-soft)"
      font-family="Assistant, sans-serif">מחזור 1</text>
    <text x="${W - padR}" y="${H - 5}" font-size="9.5" text-anchor="end"
      fill="var(--ink-soft)" font-family="Assistant, sans-serif">מחזור ${points.length}</text>
  </svg>`;
}

// ---------------------------------------------------------------------------
// אצטדיון לילה — כותרת מסך הפתיחה
// ---------------------------------------------------------------------------

function stadium() {
  const crowd = [];
  for (let i = 0; i < 150; i++) {
    const x = 4 + Math.random() * 292;
    const y = 30 + Math.random() * 26;
    const r = 0.9 + Math.random() * 1.1;
    crowd.push(`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(1)}"
      fill="var(--ink-soft)" opacity="${(0.18 + Math.random() * 0.3).toFixed(2)}"/>`);
  }
  const beam = (x, dir) => `
    <path d="M${x},18 L${x + dir * 52},74 L${x - dir * 6},74 Z"
      fill="var(--accent-fill)" opacity=".07"/>
    <rect x="${x - 9}" y="10" width="18" height="7" rx="1.4" fill="var(--ink-soft)" opacity=".55"/>
    <rect x="${x - 1.2}" y="17" width="2.4" height="12" fill="var(--ink-soft)" opacity=".4"/>
    ${[-6, 0, 6].map(o => `<circle cx="${x + o}" cy="13.5" r="2.2"
      fill="var(--accent-fill)" opacity=".85"/>`).join("")}`;

  return `<svg viewBox="0 0 300 90" class="stadium" role="img" aria-label="אצטדיון בלילה" aria-hidden="true">
    <rect x="0" y="0" width="300" height="90" fill="none"/>
    ${beam(52, 1)}${beam(248, -1)}
    <path d="M0,58 L300,58 L300,90 L0,90 Z" fill="var(--pitch-turf)"/>
    <path d="M0,58 L300,58 L262,90 L38,90 Z" fill="var(--pitch-stripe)"/>
    <g fill="none" stroke="var(--pitch-line)" stroke-width="0.8" opacity=".8">
      <path d="M38,90 L76,58 L224,58 L262,90"/>
      <line x1="150" y1="58" x2="150" y2="90"/>
      <path d="M112,58 L104,74 L196,74 L188,58"/>
    </g>
    <path d="M0,28 L300,28 L300,58 L0,58 Z" fill="var(--surface-2)" opacity=".65"/>
    ${crowd.join("")}
  </svg>`;
}

// ---------------------------------------------------------------------------
// גביע — לרשימת ההישגים
// ---------------------------------------------------------------------------

function trophy(size = 16) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" class="trophy"
    role="img" aria-label="תואר">
    <path d="M7,3 H17 V9 C17,12.3 14.8,14.6 12,14.6 C9.2,14.6 7,12.3 7,9 Z"
      fill="var(--accent-fill)"/>
    <path d="M7,4 H4.4 V6.4 C4.4,8.6 5.7,10 7.4,10.2" fill="none"
      stroke="var(--accent-fill)" stroke-width="1.5"/>
    <path d="M17,4 H19.6 V6.4 C19.6,8.6 18.3,10 16.6,10.2" fill="none"
      stroke="var(--accent-fill)" stroke-width="1.5"/>
    <rect x="10.6" y="14.2" width="2.8" height="4" fill="var(--accent-fill)"/>
    <rect x="7.6" y="18" width="8.8" height="2.6" rx="0.8" fill="var(--accent-fill)"/>
  </svg>`;
}
