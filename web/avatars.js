// ---------------------------------------------------------------------------
// דיוקנאות בסגנון פוטבול מנג'ר: אין פנים מזויפות — יש צללית במדי המועדון.
// מה שמזהה שחקן הוא המדים, המספר, המבנה והרגל — בדיוק כמו במשחק האמיתי.
// ---------------------------------------------------------------------------

const FOOT_KEYS = ["right", "left", "both"];
const FOOT_NAMES = { right: "ימין", left: "שמאל", both: "דו-רגלי" };

function hashOf(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h);
}

/** מבנה גוף לצללית — משתנה בין שחקנים כדי שרשימת הסגל לא תיראה משוכפלת. */
function buildOf(player) {
  const h = hashOf((player.pid || "") + (player.name || ""));
  return {
    frame: h % 3,                    // רזה / רגיל / חסון
    crop: Math.floor(h / 3) % 4,     // נפח שיער בקו הצללית
    shoulder: Math.floor(h / 12) % 3,
  };
}

/** רגל חזקה: מה שהשחקן בחר, ואם לא בחר — נגזר מהמזהה. */
function playerFoot(player) {
  if (player && FOOT_KEYS.includes(player.foot)) return player.foot;
  const h = hashOf((player && player.pid) || "x");
  const r = (h % 100) / 100;
  return r < 0.70 ? "right" : r < 0.92 ? "left" : "both";
}

/** זהות אקראית לכפתור "הגרל" בבורר. */
function randomIdentity(rand) {
  const r = rand || Math.random;
  const traitKeys = Object.keys(D.TRAITS);
  return {
    foot: FOOT_KEYS[Math.floor(r() * FOOT_KEYS.length)],
    trait: traitKeys[Math.floor(r() * traitKeys.length)],
  };
}

const FALLBACK_SILHOUETTE = ["#39405A", "#1B2030"];

/**
 * דיוקן שחקן: רקע בצבעי המועדון, צללית ניטרלית במדים.
 * opts: { background, number, ring }
 */
function avatar(player, club, size = 96, opts = {}) {
  const b = buildOf(player || {});
  const [kitPrimary, kitSecondary] = club ? kit(club.cid) : FALLBACK_KIT;
  const id = "av" + (++crestSeq);
  const showBg = opts.background !== false;
  const [silLight, silDark] = FALLBACK_SILHOUETTE;

  // רוחב כתפיים ומבנה ראש לפי המבנה
  const shoulderW = [56, 64, 72][b.shoulder];
  const headRx = [34, 36, 38][b.frame];
  const headRy = headRx + 4;
  // קו הקודקוד: נפח שיער כחלק מהצללית, בלי לרמוז על פנים
  const crown = [
    `M${100 - headRx},86 a${headRx},${headRy} 0 1,1 ${headRx * 2},0 Z`,
    `M${100 - headRx - 3},88 q0,-${headRy + 8} ${headRx + 3},-${headRy + 8}
       q${headRx + 3},0 ${headRx + 3},${headRy + 8} Z`,
    `M${100 - headRx - 6},84 a${headRx + 6},${headRy + 2} 0 1,1 ${(headRx + 6) * 2},0 Z`,
    `M${100 - headRx},90 q2,-${headRy + 14} ${headRx},-${headRy + 12}
       q${headRx - 2},-2 ${headRx},${headRy + 12} Z`,
  ][b.crop];

  const number = opts.number != null ? opts.number : null;
  const showNumber = number != null && size >= 56;
  // במצב "שבב" (רשימות ארוכות) הרקע ניטרלי, וצבע המועדון נשאר רק בטבעת
  const chip = opts.chip === true;

  return `<svg viewBox="0 0 200 200" width="${size}" height="${size}" class="avatar"
    role="img" aria-label="${escAttr((player && player.name) || "שחקן")}">
    <defs>
      <linearGradient id="${id}bg" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="${chip ? "#2A2740" : shade(kitPrimary, 0.34)}"/>
        <stop offset="52%" stop-color="${chip ? "#1E1B2E" : shade(kitPrimary, -0.10)}"/>
        <stop offset="100%" stop-color="${chip ? "#14121F" : shade(kitPrimary, -0.62)}"/>
      </linearGradient>
      <linearGradient id="${id}kit" x1="12%" y1="0%" x2="88%" y2="100%">
        <stop offset="0%" stop-color="${shade(kitPrimary, 0.20)}"/>
        <stop offset="100%" stop-color="${shade(kitPrimary, -0.34)}"/>
      </linearGradient>
      <linearGradient id="${id}sil" x1="24%" y1="6%" x2="82%" y2="100%">
        <stop offset="0%" stop-color="${silLight}"/>
        <stop offset="100%" stop-color="${silDark}"/>
      </linearGradient>
      <clipPath id="${id}clip"><circle cx="100" cy="100" r="99"/></clipPath>
    </defs>

    <g clip-path="url(#${id}clip)">
      ${showBg ? `<rect width="200" height="200" fill="url(#${id}bg)"/>
      <g opacity=".13" fill="${kitSecondary}">
        <rect x="0" y="0" width="200" height="10"/>
        <rect x="0" y="26" width="200" height="6"/>
      </g>
      <circle cx="100" cy="78" r="72" fill="#fff" opacity=".06"/>` : ""}

      <!-- כתפיים במדי המועדון -->
      <path d="M${100 - shoulderW - 22},200
        C${100 - shoulderW - 18},156 ${100 - shoulderW + 6},137 ${100 - shoulderW + 26},131
        L${100 + shoulderW - 26},131
        C${100 + shoulderW - 6},137 ${100 + shoulderW + 18},156 ${100 + shoulderW + 22},200 Z"
        fill="url(#${id}kit)" stroke="#000" stroke-opacity=".28" stroke-width="3"/>
      <path d="M${100 - shoulderW - 22},200 C${100 - shoulderW - 18},166
        ${100 - shoulderW - 4},148 ${100 - shoulderW + 12},140 L${100 - shoulderW + 22},200 Z"
        fill="${kitSecondary}" opacity=".34"/>
      <path d="M${100 + shoulderW + 22},200 C${100 + shoulderW + 18},166
        ${100 + shoulderW + 4},148 ${100 + shoulderW - 12},140 L${100 + shoulderW - 22},200 Z"
        fill="${kitSecondary}" opacity=".34"/>
      <path d="M${100 - 20},133 L100,152 L${100 + 20},133 L${100 + 13},130 L100,143 L${100 - 13},130 Z"
        fill="${kitSecondary}" opacity=".9"/>

      <!-- צללית: צוואר וראש, בלי תווי פנים -->
      <path d="M86,104 h28 v26 c0,11 -28,11 -28,0 Z" fill="${silDark}"/>
      <path d="${crown}" fill="url(#${id}sil)"/>
      <ellipse cx="100" cy="86" rx="${headRx}" ry="${headRy}" fill="url(#${id}sil)"/>
      <ellipse cx="100" cy="86" rx="${headRx}" ry="${headRy}" fill="none"
        stroke="#fff" stroke-width="1.6" opacity=".13"/>
      <ellipse cx="${100 - headRx * 0.42}" cy="76" rx="${headRx * 0.32}" ry="${headRy * 0.34}"
        fill="#fff" opacity=".06"/>
      <path d="M100,50 a${headRx},${headRy} 0 0,1 0,${headRy * 2} Z" fill="#000" opacity=".16"/>
      <ellipse cx="100" cy="134" rx="${headRx * 0.95}" ry="8" fill="#000" opacity=".26"/>
    </g>
    ${showNumber ? `<g>
      <circle cx="156" cy="156" r="27" fill="#0C0A14" opacity=".85"/>
      <circle cx="156" cy="156" r="27" fill="none" stroke="${kitSecondary}"
        stroke-width="3" opacity=".7"/>
      <text x="156" y="166" text-anchor="middle" font-size="29" font-weight="700"
        fill="#fff" style="direction:ltr">${number}</text>
    </g>` : ""}
    <circle cx="100" cy="100" r="97" fill="none" stroke="${shade(kitPrimary, -0.5)}"
      stroke-width="4" opacity=".85"/>
  </svg>`;
}

/** דיוקן קטן לרשימות. */
function avatarChip(player, club, size = 34) {
  return avatar(player, club, size, { chip: true });
}
