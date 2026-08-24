// ---------------------------------------------------------------------------
// סצנות מאוירות לדפי המעבר. הכל SVG מחולל, בשני מצבי התצוגה.
// לכל אירוע עלילה יש סצנה משלו: חדר הלבשה, חדר טיפולים, אולם עיתונאים...
// ---------------------------------------------------------------------------

const SCENE_W = 320, SCENE_H = 132;

function sceneWrap(inner, label) {
  return `<svg viewBox="0 0 ${SCENE_W} ${SCENE_H}" class="scene" role="img"
    aria-label="${escAttr(label)}">
    <rect width="${SCENE_W}" height="${SCENE_H}" fill="var(--scene-sky)"/>
    ${inner}
    <rect width="${SCENE_W}" height="${SCENE_H}" fill="url(#sceneVignette)"/>
  </svg>`;
}

/** הגדרות משותפות לכל הסצנות — מוזרקות פעם אחת לדף. */
function sceneDefs() {
  return `<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
    <linearGradient id="sceneVignette" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="var(--scene-sky)" stop-opacity="0"/>
      <stop offset="72%" stop-color="var(--scene-sky)" stop-opacity="0"/>
      <stop offset="100%" stop-color="var(--scene-sky)" stop-opacity=".55"/>
    </linearGradient>
    <linearGradient id="beamGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="var(--accent-fill)" stop-opacity=".26"/>
      <stop offset="100%" stop-color="var(--accent-fill)" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="tunnelGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="var(--scene-near)"/>
      <stop offset="100%" stop-color="var(--scene-far)"/>
    </linearGradient>
  </defs></svg>`;
}

// -- עוזרים ---------------------------------------------------------------

function times(count, fn) { return Array.from({ length: count }, (_, i) => fn(i)).join(""); }

/**
 * דמות אנושית פשוטה. (x,y) = הרצפה שעליה היא עומדת, s = קנה מידה.
 * תנוחות: stand | sit | kick | lie
 */
function figure(x, y, s = 1, opts = {}) {
  const color = opts.color || "var(--scene-line)";
  const pose = opts.pose || "stand";
  const shadow = opts.shadow === false ? "" :
    `<ellipse cx="0" cy="1.5" rx="9" ry="2.6" fill="var(--scene-line)" opacity=".28"/>`;
  let body;
  if (pose === "sit") {
    body = `<circle cx="0" cy="-31" r="5.4"/>
      <path d="M-6,-26 h12 l1.5,15 h-15 z"/>
      <path d="M-5,-11 h16 v5 h-16 z"/>
      <path d="M9,-6 h5 v6 h-5 z"/>`;
  } else if (pose === "kick") {
    body = `<circle cx="0" cy="-33" r="5.4"/>
      <path d="M-6,-28 h12 l1,16 h-14 z"/>
      <path d="M-5,-12 l-6,12 h5 l5,-10 z"/>
      <path d="M2,-12 l9,7 l-3,4 l-8,-7 z"/>
      <path d="M6,-26 l9,-6 l2,4 l-9,6 z"/>`;
  } else if (pose === "lie") {
    body = `<circle cx="-18" cy="-6" r="5"/>
      <path d="M-13,-10 h20 l2,9 h-22 z"/>
      <path d="M7,-9 h16 v7 h-16 z"/>`;
  } else {
    body = `<circle cx="0" cy="-33" r="5.4"/>
      <path d="M-6,-28 h12 l1.5,16 h-15 z"/>
      <rect x="-5.5" y="-12" width="4.5" height="12"/>
      <rect x="1" y="-12" width="4.5" height="12"/>
      <path d="M-7,-27 l-4,12 l3,1 l5,-11 z"/>
      <path d="M7,-27 l4,12 l-3,1 l-5,-11 z"/>`;
  }
  return `<g transform="translate(${x},${y}) scale(${s})" fill="${color}">${shadow}${body}</g>`;
}

function floorAndWall(floorY = 96) {
  return `<rect y="0" width="${SCENE_W}" height="${floorY}" fill="var(--scene-far)"/>
    <rect y="${floorY}" width="${SCENE_W}" height="${SCENE_H - floorY}" fill="var(--scene-near)"/>
    <line x1="0" y1="${floorY}" x2="${SCENE_W}" y2="${floorY}"
      stroke="var(--scene-line)" stroke-width="1" opacity=".5"/>`;
}

// -- הסצנות ---------------------------------------------------------------

const SCENES = {

  // חדר הלבשה: תאים, חולצה תלויה, ספסל, נעליים
  dressing: () => sceneWrap(`
    ${floorAndWall(100)}
    ${times(6, i => `
      <rect x="${8 + i * 52}" y="14" width="46" height="74" rx="2"
        fill="var(--scene-mid)" stroke="var(--scene-line)" stroke-width="1"/>
      <rect x="${8 + i * 52}" y="14" width="46" height="9" fill="var(--scene-near)"/>
      <circle cx="${31 + i * 52}" cy="30" r="1.6" fill="var(--scene-line)"/>`)}
    <g>
      <rect x="138" y="30" width="30" height="40" rx="3" fill="var(--accent-fill)"/>
      <path d="M138,30 L146,26 L160,26 L168,30 L172,40 L166,43 L166,70 L140,70 L140,43 L134,40 Z"
        fill="var(--accent-fill)"/>
      <text x="153" y="58" text-anchor="middle" font-size="15" font-weight="700"
        fill="var(--accent-ink)" font-family="Assistant, sans-serif">10</text>
    </g>
    ${figure(64, 100, 1.25, { pose: "sit", color: "var(--scene-near)", shadow: false })}
    <rect x="20" y="100" width="280" height="7" rx="2" fill="var(--scene-mid)"/>
    ${times(4, i => `<rect x="${34 + i * 74}" y="107" width="6" height="14" fill="var(--scene-line)"/>`)}
    ${times(2, i => `
      <ellipse cx="${212 + i * 46}" cy="126" rx="12" ry="4.5" fill="var(--scene-line)" opacity=".75"/>`)}
  `, "חדר הלבשה"),

  // חדר טיפולים: מיטה, רגל חבושה, פיזיותרפיסט
  physio: () => sceneWrap(`
    ${floorAndWall(104)}
    <rect x="18" y="22" width="66" height="48" rx="3" fill="var(--scene-mid)"
      stroke="var(--scene-line)" stroke-width="1"/>
    ${times(3, i => `<line x1="${28 + i * 20}" y1="22" x2="${28 + i * 20}" y2="70"
      stroke="var(--scene-line)" stroke-width="1" opacity=".45"/>`)}
    <rect x="104" y="74" width="164" height="12" rx="4" fill="var(--scene-near)"/>
    <rect x="112" y="86" width="8" height="18" fill="var(--scene-line)"/>
    <rect x="252" y="86" width="8" height="18" fill="var(--scene-line)"/>
    ${figure(146, 74, 1.05, { pose: "lie", color: "var(--scene-mid)", shadow: false })}
    <g>
      <path d="M176,66 l30,-2 l4,10 l-30,4 z" fill="var(--scene-mid)"/>
      <path d="M206,64 l26,10 l-5,10 l-25,-12 z" fill="var(--accent-fill)"/>
      ${times(4, i => `<line x1="${208 + i * 7}" y1="${64 + i * 2.6}" x2="${204 + i * 7}" y2="${76 + i * 2.6}"
        stroke="var(--scene-sky)" stroke-width="1.6" opacity=".6"/>`)}
      <ellipse cx="234" cy="80" rx="6" ry="4.5" fill="var(--accent-fill)"/>
    </g>
    ${figure(258, 104, 1.15, { color: "var(--scene-line)" })}
    <path d="M296,44 L296,100 M290,48 L302,48 M296,100 L290,116 M296,100 L302,116"
      stroke="var(--scene-line)" stroke-width="3" fill="none" stroke-linecap="round"/>
  `, "חדר טיפולים"),

  // אולם מסיבות עיתונאים
  press: () => sceneWrap(`
    ${floorAndWall(112)}
    <rect x="0" y="0" width="${SCENE_W}" height="92" fill="var(--scene-mid)"/>
    ${times(10, i => `<rect x="${(i % 5) * 64 + 8}" y="${Math.floor(i / 5) * 42 + 12}"
      width="34" height="11" rx="2" fill="var(--scene-near)" opacity=".6"/>`)}
    ${figure(160, 96, 1.55, { pose: "sit", color: "var(--scene-far)", shadow: false })}
    <rect x="88" y="90" width="146" height="22" rx="2" fill="var(--scene-near)"/>
    <rect x="88" y="90" width="146" height="4" fill="var(--accent-fill)" opacity=".8"/>
    ${times(3, i => `
      <line x1="${132 + i * 30}" y1="90" x2="${136 + i * 30}" y2="70"
        stroke="var(--scene-line)" stroke-width="2.4"/>
      <ellipse cx="${136 + i * 30}" cy="64" rx="6" ry="8"
        fill="${i === 1 ? "var(--accent-fill)" : "var(--scene-line)"}"/>`)}
    ${times(9, i => `<circle cx="${14 + i * 36}" cy="${120 + (i % 3) * 5}" r="${2.4 + (i % 3)}"
      fill="var(--accent-fill)" opacity=".${4 + (i % 5)}"/>`)}
    ${times(4, i => `<rect x="${28 + i * 78}" y="118" width="18" height="10" rx="2"
      fill="var(--scene-line)" opacity=".7"/>`)}
  `, "מסיבת עיתונאים"),

  // אצטדיון לילה
  stadium: () => sceneWrap(`
    <rect width="${SCENE_W}" height="70" fill="var(--scene-far)"/>
    ${[54, 266].map(x => `
      <path d="M${x},16 L${x + (x < 160 ? 60 : -60)},96 L${x + (x < 160 ? -10 : 10)},96 Z"
        fill="url(#beamGrad)"/>
      <rect x="${x - 12}" y="8" width="24" height="8" rx="1.5" fill="var(--scene-line)"/>
      <rect x="${x - 1.5}" y="16" width="3" height="16" fill="var(--scene-line)"/>
      ${times(3, i => `<circle cx="${x - 8 + i * 8}" cy="12" r="2.6"
        fill="var(--accent-fill)"/>`)}`).join("")}
    <rect y="34" width="${SCENE_W}" height="36" fill="var(--scene-mid)"/>
    ${times(90, i => `<circle cx="${(i * 37) % 316 + 2}" cy="${38 + (i * 13) % 30}"
      r="${1 + (i % 3) * 0.5}" fill="var(--scene-line)" opacity=".${3 + (i % 5)}"/>`)}
    <path d="M0,70 L320,70 L320,132 L0,132 Z" fill="var(--pitch-turf)"/>
    <path d="M0,70 L320,70 L282,132 L38,132 Z" fill="var(--pitch-stripe)"/>
    <g fill="none" stroke="var(--pitch-line)" stroke-width="1" opacity=".85">
      <path d="M38,132 L76,70 L244,70 L282,132"/>
      <line x1="160" y1="70" x2="160" y2="132"/>
      <path d="M120,70 L110,100 L210,100 L200,70"/>
    </g>
  `, "אצטדיון בלילה"),

  // חדר ישיבות
  boardroom: () => sceneWrap(`
    ${floorAndWall(100)}
    <rect x="176" y="12" width="132" height="72" rx="2" fill="var(--scene-mid)"/>
    ${times(8, i => `<line x1="176" y1="${16 + i * 9}" x2="308" y2="${16 + i * 9}"
      stroke="var(--scene-near)" stroke-width="3" opacity=".8"/>`)}
    <ellipse cx="130" cy="98" rx="112" ry="22" fill="var(--scene-near)"/>
    <ellipse cx="130" cy="94" rx="112" ry="22" fill="var(--scene-mid)"/>
    ${times(3, i => figure(46 + i * 62, 92, 1.15, { pose: "sit", color: "var(--scene-near)", shadow: false }))}
    ${times(3, i => `
      <rect x="${34 + i * 62}" y="66" width="26" height="20" rx="4" fill="var(--scene-mid)" opacity=".7"/>`)}
    <rect x="96" y="84" width="34" height="24" rx="2" fill="var(--accent-fill)" opacity=".92"/>
    ${times(3, i => `<line x1="102" y1="${90 + i * 6}" x2="124" y2="${90 + i * 6}"
      stroke="var(--accent-ink)" stroke-width="1.4" opacity=".6"/>`)}
  `, "חדר ישיבות"),

  // מגרש אימונים
  training: () => sceneWrap(`
    <rect width="${SCENE_W}" height="44" fill="var(--scene-far)"/>
    <rect y="44" width="${SCENE_W}" height="88" fill="var(--pitch-turf)"/>
    ${times(5, i => `<rect y="${44 + i * 18}" width="${SCENE_W}" height="9"
      fill="var(--pitch-stripe)"/>`)}
    <g fill="none" stroke="var(--pitch-line)" stroke-width="1.4" opacity=".75">
      <rect x="206" y="26" width="92" height="32" rx="1"/>
      ${times(6, i => `<line x1="${212 + i * 14}" y1="26" x2="${212 + i * 14}" y2="58"/>`)}
      ${times(3, i => `<line x1="206" y1="${34 + i * 9}" x2="298" y2="${34 + i * 9}"/>`)}
    </g>
    ${times(5, i => `<path d="M${18 + i * 22},${122 - i * 5} l7,0 l-3.5,-11 z"
      fill="var(--accent-fill)" opacity=".9"/>`)}
    ${figure(112, 118, 1.5, { pose: "kick", color: "var(--scene-line)" })}
    <circle cx="146" cy="116" r="7" fill="var(--scene-sky)"
      stroke="var(--scene-line)" stroke-width="1.4"/>
    ${figure(246, 96, 1.15, { color: "var(--scene-near)" })}
    <rect x="240" y="70" width="12" height="4" rx="2" fill="var(--scene-near)"/>
  `, "מגרש אימונים"),

  // ארון התארים
  trophy: () => sceneWrap(`
    ${floorAndWall(106)}
    ${[92, 160, 228].map((x, i) => `
      <path d="M${x - 26},20 L${x + 26},20 L${x + 14},${34 + i * 6} L${x - 14},${34 + i * 6} Z"
        fill="url(#beamGrad)"/>`).join("")}
    <rect x="118" y="86" width="84" height="20" rx="2" fill="var(--scene-near)"/>
    <rect x="128" y="78" width="64" height="10" rx="2" fill="var(--scene-mid)"/>
    <g>
      <path d="M138,34 H182 V56 C182,68 172,76 160,76 C148,76 138,68 138,34 Z"
        fill="var(--accent-fill)"/>
      <path d="M138,38 H126 V48 C126,57 132,62 140,63" fill="none"
        stroke="var(--accent-fill)" stroke-width="5"/>
      <path d="M182,38 H194 V48 C194,57 188,62 180,63" fill="none"
        stroke="var(--accent-fill)" stroke-width="5"/>
      <rect x="154" y="76" width="12" height="6" fill="var(--accent-fill)"/>
    </g>
    ${times(16, i => `<rect x="${12 + i * 20}" y="${14 + (i * 29) % 80}" width="4" height="7"
      rx="1" fill="${i % 3 ? "var(--accent-fill)" : "var(--scene-line)"}"
      opacity=".${4 + (i % 5)}" transform="rotate(${(i * 37) % 90 - 45} ${14 + i * 20} ${18 + (i * 29) % 80})"/>`)}
  `, "ארון התארים"),

  // שדה תעופה
  airport: () => sceneWrap(`
    <rect width="${SCENE_W}" height="82" fill="var(--scene-far)"/>
    <rect y="82" width="${SCENE_W}" height="50" fill="var(--scene-near)"/>
    <g opacity=".95">
      <path d="M150,44 L236,26 L246,32 L196,58 Z" fill="var(--accent-fill)"/>
      <path d="M188,44 L172,20 L182,18 L206,38 Z" fill="var(--accent-fill)" opacity=".8"/>
      <path d="M196,58 L214,66 L222,60 L212,54 Z" fill="var(--accent-fill)" opacity=".7"/>
    </g>
    ${times(3, i => `<line x1="${60 + i * 18}" y1="${64 + i * 4}" x2="${104 + i * 18}" y2="${56 + i * 4}"
      stroke="var(--scene-line)" stroke-width="1.5" opacity=".5"/>`)}
    <rect x="14" y="88" width="46" height="34" rx="4" fill="var(--scene-mid)"
      stroke="var(--scene-line)" stroke-width="1.5"/>
    <rect x="30" y="80" width="14" height="8" rx="3" fill="var(--scene-line)"/>
    <rect x="14" y="100" width="46" height="4" fill="var(--scene-line)" opacity=".6"/>
    <rect x="230" y="86" width="76" height="30" rx="2" fill="var(--scene-mid)"/>
    ${times(4, i => `<rect x="236" y="${90 + i * 7}" width="${58 - i * 9}" height="3.4"
      fill="${i === 0 ? "var(--accent-fill)" : "var(--scene-line)"}" opacity=".8"/>`)}
    ${times(9, i => `<rect x="${i * 40}" y="126" width="24" height="3" fill="var(--scene-sky)" opacity=".5"/>`)}
  `, "שדה תעופה"),

  // אולפן טלוויזיה
  studio: () => sceneWrap(`
    ${floorAndWall(104)}
    <rect x="0" y="0" width="${SCENE_W}" height="90" fill="var(--scene-mid)"/>
    <rect x="20" y="14" width="108" height="60" rx="3" fill="var(--pitch-turf)"
      stroke="var(--scene-line)" stroke-width="1.5"/>
    ${times(4, i => `<rect x="20" y="${18 + i * 15}" width="108" height="7"
      fill="var(--pitch-stripe)"/>`)}
    <g fill="none" stroke="var(--pitch-line)" stroke-width="1" opacity=".9">
      <line x1="74" y1="14" x2="74" y2="74"/>
      <circle cx="74" cy="44" r="12"/>
    </g>
    ${times(4, i => `<circle cx="${44 + i * 20}" cy="${34 + (i % 2) * 20}" r="3"
      fill="var(--accent-fill)"/>`)}
    ${figure(206, 90, 1.4, { pose: "sit", color: "var(--scene-near)", shadow: false })}
    <rect x="150" y="88" width="130" height="24" rx="3" fill="var(--scene-near)"/>
    <rect x="150" y="88" width="130" height="5" fill="var(--accent-fill)" opacity=".9"/>
    <g>
      <rect x="262" y="16" width="32" height="21" rx="3" fill="var(--scene-line)"/>
      <path d="M294,22 L310,14 L310,39 L294,31 Z" fill="var(--scene-line)"/>
      <circle cx="271" cy="12" r="3.4" fill="var(--loss)"/>
    </g>
    ${times(2, i => `<path d="M${140 + i * 130},8 l14,0 l7,14 l-28,0 z"
      fill="var(--accent-fill)" opacity=".5"/>`)}
  `, "אולפן טלוויזיה"),

  // מנהרת השחקנים
  tunnel: () => sceneWrap(`
    <rect width="${SCENE_W}" height="${SCENE_H}" fill="url(#tunnelGrad)"/>
    <path d="M0,0 L96,26 L96,110 L0,132 Z" fill="var(--scene-near)"/>
    <path d="M320,0 L224,26 L224,110 L320,132 Z" fill="var(--scene-near)"/>
    <path d="M96,26 L224,26 L224,14 L96,14 Z" fill="var(--scene-mid)"/>
    <rect x="96" y="26" width="128" height="84" fill="var(--scene-sky)" opacity=".16"/>
    <rect x="112" y="34" width="96" height="70" fill="var(--pitch-turf)"/>
    ${times(4, i => `<rect x="112" y="${34 + i * 18}" width="96" height="9" fill="var(--pitch-stripe)"/>`)}
    <path d="M112,34 L208,34 L208,104 L112,104 Z" fill="none"
      stroke="var(--pitch-line)" stroke-width="1.2" opacity=".7"/>
    ${times(2, i => `
      <g fill="var(--scene-line)" opacity=".95">
        <circle cx="${132 + i * 56}" cy="${58 + i * 4}" r="7"/>
        <path d="M${125 + i * 56},${66 + i * 4} h14 l3,26 h-20 z"/>
      </g>`)}
    <rect x="96" y="104" width="128" height="28" fill="var(--scene-near)"/>
    ${[104, 216].map(x => `<rect x="${x}" y="14" width="6" height="96"
      fill="var(--accent-fill)" opacity=".35"/>`).join("")}
  `, "מנהרת השחקנים"),

  // סלון בבית
  home: () => sceneWrap(`
    ${floorAndWall(98)}
    <rect x="18" y="16" width="86" height="56" rx="3" fill="var(--scene-mid)"
      stroke="var(--scene-line)" stroke-width="1.5"/>
    <line x1="61" y1="16" x2="61" y2="72" stroke="var(--scene-line)" stroke-width="1.5"/>
    <circle cx="86" cy="32" r="9" fill="var(--accent-fill)" opacity=".55"/>
    ${figure(176, 92, 1.3, { pose: "sit", color: "var(--scene-line)", shadow: false })}
    <rect x="130" y="76" width="150" height="30" rx="6" fill="var(--scene-near)"/>
    <rect x="138" y="60" width="134" height="20" rx="6" fill="var(--scene-mid)"/>
    ${times(3, i => `<rect x="${146 + i * 44}" y="62" width="36" height="16" rx="4"
      fill="var(--scene-near)" opacity=".8"/>`)}
    <path d="M292,44 L308,44 L304,64 L296,64 Z" fill="var(--accent-fill)" opacity=".8"/>
    <rect x="298" y="64" width="4" height="34" fill="var(--scene-line)"/>
    <rect x="288" y="98" width="24" height="4" rx="2" fill="var(--scene-line)"/>
    <ellipse cx="300" cy="56" rx="30" ry="22" fill="var(--accent-fill)" opacity=".10"/>
  `, "בבית"),

  // מגרש שכונתי
  youthpitch: () => sceneWrap(`
    <rect width="${SCENE_W}" height="54" fill="var(--scene-far)"/>
    <rect y="54" width="${SCENE_W}" height="78" fill="var(--pitch-turf)"/>
    ${times(16, i => `<line x1="${i * 21}" y1="10" x2="${i * 21}" y2="54"
      stroke="var(--scene-line)" stroke-width="1" opacity=".25"/>`)}
    ${times(3, i => `<line x1="0" y1="${14 + i * 14}" x2="320" y2="${14 + i * 14}"
      stroke="var(--scene-line)" stroke-width="1" opacity=".25"/>`)}
    <rect y="6" width="${SCENE_W}" height="4" fill="var(--scene-line)" opacity=".5"/>
    <g fill="none" stroke="var(--scene-sky)" stroke-width="2.6" opacity=".92">
      <path d="M28,54 L28,22 L118,22 L118,54"/>
      ${times(5, i => `<line x1="${38 + i * 18}" y1="22" x2="${38 + i * 18}" y2="54" stroke-width="1"/>`)}
      ${times(2, i => `<line x1="28" y1="${32 + i * 12}" x2="118" y2="${32 + i * 12}" stroke-width="1"/>`)}
    </g>
    ${times(4, i => `<rect y="${62 + i * 18}" width="${SCENE_W}" height="8"
      fill="var(--pitch-stripe)"/>`)}
    ${figure(214, 120, 1.45, { pose: "kick", color: "var(--accent-fill)" })}
    <circle cx="248" cy="118" r="8" fill="var(--scene-sky)"
      stroke="var(--scene-line)" stroke-width="1.5"/>
    <path d="M248,110 l4.5,6.5 l-2,7.5 h-5 l-2,-7.5 z" fill="var(--scene-line)" opacity=".75"/>
    ${figure(96, 96, 1.0, { color: "var(--scene-near)" })}
  `, "מגרש שכונתי"),

};

// -- מיפוי אירוע → סצנה ---------------------------------------------------

const EVENT_SCENE = {
  first_boots: "home", school_or_football: "youthpitch", growth_spurt: "training",
  scout_in_stands: "youthpitch", left_out: "dressing", academy_offer: "training",
  first_call_up: "tunnel", youth_mentor: "dressing", loan_offer: "airport",
  bench_frustration: "dressing", derby_week: "stadium", scandal_night: "press",
  national_call: "tunnel", big_club_interest: "airport", captain_armband: "dressing",
  serious_injury: "physio", sponsor_deal: "studio", contract_talks: "boardroom",
  dressing_room_split: "dressing", youngster_threat: "training",
  body_signals: "physio", retirement_call: "home", farewell_match: "stadium",
  next_chapter: "home", first_manager_offer: "boardroom", board_meeting: "boardroom",
  star_wants_out: "boardroom", wonderkid: "training", sack_race: "press",
  bigger_job: "boardroom", director_offer: "boardroom", buy_childhood_club: "stadium",
  hall_of_fame: "trophy", child_debut: "youthpitch",
};

function sceneFor(eid, stage) {
  const key = EVENT_SCENE[eid] ||
    (stage === "youth" ? "youthpitch" : stage === "manager" ? "boardroom" :
     stage === "pundit" ? "studio" : "dressing");
  return (SCENES[key] || SCENES.dressing)();
}

// ---------------------------------------------------------------------------
// כרטיס שחקן
// ---------------------------------------------------------------------------

const ATTR_SHORT = {
  pace: "מהי", shooting: "בעי", passing: "מסי",
  dribbling: "כדר", defending: "הגנ", physical: "כוח",
};

function playerCard(player, club, stage) {
  const [primary, secondary] = club ? kit(club.cid) : FALLBACK_KIT;
  const ink = inkOn(primary);
  const ovr = overall(player);
  return `
  <div class="pcard" style="--card-a:${primary};--card-b:${shade(primary, -0.35)};--card-ink:${ink}">
    <div class="pcard-top">
      <div class="pcard-rating">
        <span class="n">${ovr}</span>
        <span class="pos">${escAttr(positionHe(player))}</span>
        <span class="rule"></span>
        <span class="nat">${escAttr(player.nationality)}</span>
      </div>
      <div class="pcard-art">${shirt(club, player.number || 0, 92)}</div>
    </div>
    <div class="pcard-name">${escAttr(player.name)}</div>
    <div class="pcard-attrs">
      ${Object.keys(ATTR_SHORT).map(a => `
        <div class="pa"><span class="v">${player.attributes[a]}</span>
          <span class="k">${ATTR_SHORT[a]}</span></div>`).join("")}
    </div>
    <div class="pcard-foot">
      ${club ? crest(club, 20) : ""}
      <span>${club ? escAttr(club.name) : "ללא מועדון"}</span>
      <span class="spacer"></span>
      <span>${escAttr(D.CAREER_STAGES_HE[stage] || "")}</span>
    </div>
  </div>`;
}
