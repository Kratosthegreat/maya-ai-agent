// ---------------------------------------------------------------------------
// דמויות — דיוקן מצויר לכל שחקן, נגזר מהמזהה שלו כך שהפנים תמיד אותן פנים.
// ---------------------------------------------------------------------------

const SKIN = [
  ["#F6D3B0", "#E3B489", "#C08C63"],
  ["#EDBE93", "#D69C6D", "#B0774B"],
  ["#D79A6B", "#B87A4E", "#8F5A34"],
  ["#B87A50", "#965C38", "#6F4126"],
  ["#8D5A38", "#6E4126", "#4E2C18"],
  ["#5E3A24", "#472A18", "#301B0E"],
];

const HAIR_COLORS = ["#171310", "#2C1D14", "#4A2E1B", "#7A4A22", "#B98842", "#D8C79A", "#8C8C8C"];
const EYES = ["#3E2B18", "#5B4326", "#2F4A5C", "#3F5F45", "#1F1B18"];

function hashOf(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h);
}

const FACE_FIELDS = {
  skin: SKIN.length,
  hairStyle: 8,
  hairColor: HAIR_COLORS.length,
  eye: EYES.length,
  facial: 4,
  brow: 3,
  jaw: 3,
};

/** דמות אקראית — משמשת גם ככפתור "הגרל" בבורר. */
function randomFace(rand) {
  const r = rand || Math.random;
  const face = {};
  for (const [key, count] of Object.entries(FACE_FIELDS))
    face[key] = Math.floor(r() * count);
  return face;
}

/** דמות שנגזרת מהמזהה — לשחקני המחשב, שתמיד ייראו אותו דבר. */
function faceFromId(player) {
  const h = hashOf(player.pid + player.name);
  const pickIndex = (count, shift) => Math.floor(h / Math.pow(7, shift)) % count;
  return {
    skin: pickIndex(SKIN.length, 1),
    hairColor: player.age >= 34 && Math.floor(h / 19683) % 3 === 0
      ? HAIR_COLORS.length - 1
      : pickIndex(HAIR_COLORS.length, 2),
    hairStyle: pickIndex(8, 3),
    eye: pickIndex(EYES.length, 4),
    brow: pickIndex(3, 5),
    facial: player.age >= 20 ? pickIndex(4, 6) : 0,
    jaw: pickIndex(3, 7),
  };
}

/** מאפייני הדמות: מה שהשחקן בחר, ואם לא בחר — לפי המזהה. */
function faceTraits(player) {
  const chosen = player.face || null;
  const base = chosen ? Object.assign(faceFromId(player), chosen) : faceFromId(player);
  const clampIndex = (v, count) => Math.max(0, Math.min(count - 1, v | 0));
  return {
    skin: SKIN[clampIndex(base.skin, SKIN.length)],
    hairColor: HAIR_COLORS[clampIndex(base.hairColor, HAIR_COLORS.length)],
    hairStyle: clampIndex(base.hairStyle, 8),
    eye: EYES[clampIndex(base.eye, EYES.length)],
    brow: clampIndex(base.brow, 3),
    facial: clampIndex(base.facial, 4),
    jaw: clampIndex(base.jaw, 3),
    ear: 1,
  };
}

// שמות התצוגה של האפשרויות בבורר הדמות
const HAIR_STYLE_NAMES = ["קצר", "מכונה", "מתולתל", "אפרו", "ארוך", "קוקו", "קרחת", "בלורית"];
const FACIAL_NAMES = ["מגולח", "זיפים", "זקן", "שפם"];

/**
 * שיער בשתי שכבות: מסה מאחורי הראש, ובלורית מעליו.
 * הפרדה כזו מונעת מהשיער לכסות את הפנים.
 */
function hairBack(style, color) {
  const dark = shade(color, -0.3);
  switch (style) {
    case 2: // מתולתל
      return `<g fill="${color}">${
        [[68, 56, 17], [88, 44, 19], [112, 44, 19], [132, 56, 17], [60, 76, 14], [140, 76, 14]]
          .map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}"/>`).join("")}</g>`;
    case 3: // אפרו
      return `<ellipse cx="100" cy="66" rx="56" ry="46" fill="${color}"/>
        <ellipse cx="100" cy="62" rx="44" ry="34" fill="${dark}" opacity=".28"/>`;
    case 4: // ארוך
      return `<path d="M50,94 C50,50 72,30 100,30 C128,30 150,50 150,94
        L150,148 L132,148 L132,92 C132,70 120,58 100,58 C80,58 68,70 68,92 L68,148 L50,148 Z"
        fill="${color}"/>`;
    case 5: // קוקו
      return `<circle cx="100" cy="34" r="20" fill="${color}"/>
        <circle cx="100" cy="34" r="12" fill="${dark}" opacity=".4"/>`;
    default:
      return "";
  }
}

/** בלורית — נעצרת תמיד מעל הגבות. */
function hairFront(style, color) {
  const dark = shade(color, -0.28);
  const CROWN = `M58,80 C58,48 78,34 100,34 C122,34 142,48 142,80`;
  switch (style) {
    case 0: // תספורת קצרה
      return `<path d="${CROWN} C142,66 130,58 100,58 C70,58 58,66 58,80 Z" fill="${color}"/>
        <path d="M64,70 C74,56 86,50 100,50 C114,50 126,56 136,70
          C126,60 114,56 100,56 C86,56 74,60 64,70 Z" fill="${dark}" opacity=".45"/>`;
    case 1: // מכונה
      return `<path d="M60,80 C60,52 78,40 100,40 C122,40 140,52 140,80
        C140,70 128,64 100,64 C72,64 60,70 60,80 Z" fill="${color}" opacity=".9"/>`;
    case 2: // מתולתל
      return `<path d="${CROWN} C142,64 128,56 100,56 C72,56 58,64 58,80 Z" fill="${color}"/>
        <g fill="${color}">${[[70, 62, 9], [86, 54, 10], [114, 54, 10], [130, 62, 9]]
          .map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}"/>`).join("")}</g>`;
    case 3: // אפרו
      return `<path d="M60,78 C60,58 78,48 100,48 C122,48 140,58 140,78
        C136,66 122,60 100,60 C78,60 64,66 60,78 Z" fill="${color}"/>`;
    case 4: // ארוך
      return `<path d="M58,80 C58,50 78,36 100,36 C122,36 142,50 142,80
        C138,64 124,56 100,56 C76,56 62,64 58,80 Z" fill="${color}"/>
        <path d="M100,36 C118,36 132,44 138,58 C126,46 114,42 100,42 Z"
          fill="${dark}" opacity=".4"/>`;
    case 5: // קוקו
      return `<path d="${CROWN} C142,66 130,58 100,58 C70,58 58,66 58,80 Z" fill="${color}"/>`;
    case 6: // קרחת
      return `<path d="M64,76 C68,58 82,50 100,50 C118,50 132,58 136,76
        C130,66 116,62 100,62 C84,62 70,66 64,76 Z" fill="${color}" opacity=".28"/>
        <ellipse cx="86" cy="58" rx="14" ry="7" fill="#fff" opacity=".10"/>`;
    default: // בלורית
      return `<path d="M58,80 C58,46 80,34 100,34 C126,34 144,48 144,78
        C138,64 128,58 108,58 C92,58 76,62 68,76 C64,68 60,72 58,80 Z" fill="${color}"/>
        <path d="M100,34 C120,34 136,44 142,60 C130,46 116,42 100,42 Z"
          fill="${dark}" opacity=".45"/>`;
  }
}

function facialHair(kind, color) {
  const c = shade(color, -0.1);
  if (kind === 1)      // זיפים
    return `<path d="M66,104 C66,132 82,150 100,150 C118,150 134,132 134,104
      C134,124 120,134 100,134 C80,134 66,124 66,104 Z" fill="${c}" opacity=".26"/>`;
  if (kind === 2)      // זקן
    return `<path d="M64,100 C64,134 82,154 100,154 C118,154 136,134 136,100
      C136,126 120,138 100,138 C80,138 64,126 64,100 Z" fill="${c}"/>
      <path d="M88,120 h24 v8 h-24 z" fill="${shade(c, -0.3)}" opacity=".5"/>`;
  if (kind === 3)      // שפם
    return `<path d="M84,120 C90,116 110,116 116,120 C110,126 90,126 84,120 Z" fill="${c}"/>`;
  return "";
}

/**
 * דיוקן שחקן. size בפיקסלים. club קובע את צבעי החולצה והרקע.
 */
function avatar(player, club, size = 96, opts = {}) {
  const t = faceTraits(player);
  const [skinLight, skinMid, skinDark] = t.skin;
  const [kitPrimary, kitSecondary] = club ? kit(club.cid) : FALLBACK_KIT;
  const id = "av" + (++crestSeq);
  const showBg = opts.background !== false;

  return `<svg viewBox="0 0 200 200" width="${size}" height="${size}" class="avatar"
    role="img" aria-label="דיוקן של ${escAttr(player.name)}">
    <defs>
      <radialGradient id="${id}bg" cx="50%" cy="34%" r="72%">
        <stop offset="0%" stop-color="${shade(kitPrimary, 0.30)}"/>
        <stop offset="60%" stop-color="${kitPrimary}"/>
        <stop offset="100%" stop-color="${shade(kitPrimary, -0.45)}"/>
      </radialGradient>
      <linearGradient id="${id}skin" x1="20%" y1="8%" x2="80%" y2="96%">
        <stop offset="0%" stop-color="${skinLight}"/>
        <stop offset="58%" stop-color="${skinMid}"/>
        <stop offset="100%" stop-color="${skinDark}"/>
      </linearGradient>
      <linearGradient id="${id}kit" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="${shade(kitPrimary, 0.12)}"/>
        <stop offset="100%" stop-color="${shade(kitPrimary, -0.30)}"/>
      </linearGradient>
      <clipPath id="${id}clip"><circle cx="100" cy="100" r="98"/></clipPath>
    </defs>

    <g clip-path="url(#${id}clip)">
      ${showBg ? `<rect width="200" height="200" fill="url(#${id}bg)"/>
      <circle cx="100" cy="88" r="70" fill="#fff" opacity=".07"/>` : ""}

      <!-- כתפיים בחולצת המועדון -->
      <path d="M28,200 C28,166 56,150 78,144 L122,144 C144,150 172,166 172,200 Z"
        fill="url(#${id}kit)"/>
      <path d="M78,144 L100,168 L122,144 L112,140 L100,152 L88,140 Z" fill="${kitSecondary}"/>
      <path d="M28,200 C28,178 40,164 54,156 L54,200 Z" fill="#000" opacity=".14"/>

      <!-- צוואר -->
      <path d="M84,120 h32 v26 c0,10 -32,10 -32,0 Z" fill="${skinMid}"/>
      <path d="M84,124 c8,10 24,10 32,0 v8 c-8,10 -24,10 -32,0 Z" fill="${skinDark}" opacity=".55"/>

      ${hairBack(t.hairStyle, t.hairColor)}

      <!-- ראש -->
      <ellipse cx="100" cy="92" rx="${t.jaw === 0 ? 43 : t.jaw === 1 ? 45 : 41}" ry="49"
        fill="url(#${id}skin)"/>
      <ellipse cx="${t.ear ? 57 : 58}" cy="97" rx="6.5" ry="10" fill="${skinMid}"/>
      <ellipse cx="${t.ear ? 143 : 142}" cy="97" rx="6.5" ry="10" fill="${skinMid}"/>
      <ellipse cx="100" cy="146" rx="26" ry="8" fill="#000" opacity=".18"/>

      <!-- הצללה בצד ימין -->
      <path d="M100,50 C124,52 138,72 138,96 C138,124 120,140 100,140 Z"
        fill="${skinDark}" opacity=".18"/>

      ${hairFront(t.hairStyle, t.hairColor)}

      <!-- גבות -->
      <path d="M74,84 q12,-${5 + t.brow * 2} 24,-1" stroke="${shade(t.hairColor, -0.2)}"
        stroke-width="${4 + t.brow}" fill="none" stroke-linecap="round"/>
      <path d="M102,83 q12,-${4 + t.brow * 2} 24,1" stroke="${shade(t.hairColor, -0.2)}"
        stroke-width="${4 + t.brow}" fill="none" stroke-linecap="round"/>

      <!-- עיניים -->
      <ellipse cx="85" cy="97" rx="9" ry="6.4" fill="#F7F4EF"/>
      <ellipse cx="115" cy="97" rx="9" ry="6.4" fill="#F7F4EF"/>
      <circle cx="86" cy="97" r="4.4" fill="${t.eye}"/>
      <circle cx="116" cy="97" r="4.4" fill="${t.eye}"/>
      <circle cx="86" cy="97" r="2" fill="#140F0C"/>
      <circle cx="116" cy="97" r="2" fill="#140F0C"/>
      <circle cx="84" cy="95" r="1.5" fill="#fff" opacity=".92"/>
      <circle cx="114" cy="95" r="1.5" fill="#fff" opacity=".92"/>
      <path d="M76,93 q9,-5 18,-1" stroke="${skinDark}" stroke-width="1.6" fill="none" opacity=".7"/>
      <path d="M106,92 q9,-4 18,1" stroke="${skinDark}" stroke-width="1.6" fill="none" opacity=".7"/>

      <!-- אף -->
      <path d="M100,100 q-5,12 2,15 q4,2 6,-1" stroke="${skinDark}" stroke-width="2.4"
        fill="none" stroke-linecap="round" opacity=".65"/>

      <!-- פה -->
      ${t.mouth === 0
        ? `<path d="M88,126 q12,8 24,0" stroke="${shade(skinDark, -0.25)}" stroke-width="3"
             fill="none" stroke-linecap="round"/>`
        : t.mouth === 1
        ? `<path d="M88,126 q12,3 24,0" stroke="${shade(skinDark, -0.25)}" stroke-width="3"
             fill="none" stroke-linecap="round"/>`
        : `<path d="M89,124 q11,10 22,1 q-11,4 -22,-1 Z" fill="${shade(skinDark, -0.35)}"/>`}

      ${facialHair(t.facial, t.hairColor)}
    </g>
    <circle cx="100" cy="100" r="97" fill="none" stroke="${shade(kitPrimary, -0.5)}"
      stroke-width="4" opacity=".8"/>
  </svg>`;
}

/** דיוקן קטן לרשימות. */
function avatarChip(player, club, size = 34) {
  return avatar(player, club, size);
}
