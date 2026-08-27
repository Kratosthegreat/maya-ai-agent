// ---------------------------------------------------------------------------
// מה שקורה לך בגלל שאתה מפורסם, ולא בגלל שאתה טוב — תאום JS של fame.py
//
// חסויות היו כל מה שהיה כאן, וזה חלק קטן מהתמונה. שחקן שהפך לשם עולמי
// מקבל טלפונים מסוג אחר: שותפות עסקית, ליגה שמשלמת על עצם הנוכחות,
// קמפיין, סרט דוקו, קולקציה. לכל אחת מחיר שהוא לא כסף.
// ---------------------------------------------------------------------------

// סוג, כותרת, סף שם עולמי, מכפיל תשלום, מחיר בכושר/חדות
const VENTURES = [
  ["tycoon", "שותפות עסקית", 62, 3.4, 6],
  ["league", "פנייה מליגה זרה", 70, 5.5, 0],
  ["ambassador", "שגריר קמפיין", 58, 2.2, 4],
  ["collection", "קולקציה על שמך", 74, 3.0, 3],
  ["documentary", "סרט דוקו", 66, 1.6, 8],
  ["academy", "אקדמיה על שמך", 78, 2.6, 5],
];

const TYCOONS = [
  "קרן השקעות אטלס", "אחים ורדימון החזקות", "ליאון קפיטל",
  "משפחת דה־קסטרו", "אוליב גרופ", "נורת'סטאר ונצ'רס",
];

const FOREIGN_LEAGUES = [
  ["ליגת המפרץ", 1.9], ["הליגה הצפון־אמריקאית", 1.35],
  ["הליגה היפנית", 1.15], ["הליגה הטורקית", 1.25],
  ["הליגה הסעודית", 2.1], ["הליגה הסינית", 1.6],
];

const CAMPAIGNS = [
  "קמפיין תיירות", "מיזם ספורט לנוער", "קמפיין בטיחות בדרכים",
  "פסטיבל ספורט בינלאומי", "מיזם חינוך דרך כדורגל",
];

/** 0-100. לא "כמה אתה טוב" אלא "כמה אנשים מחוץ לכדורגל מכירים אותך". */
function fameScore(p, clubReputation = 40, honours = 0) {
  let score = p.reputation * 0.70;
  score += p.mediaSkill * 0.22;
  score += Math.min(16, (p.career.goals + p.career.assists) * 0.05);
  score += clubReputation * 0.10;
  score += Math.min(10, honours * 2.5);
  if (hasTrait(p, "media_darling")) score += 8;
  if (hasTrait(p, "hothead")) score -= 3;
  return clamp(score, 0, 100);
}

function openVentures(fame) { return VENTURES.filter(v => fame >= v[2]); }

/** פנייה אחת, אם מישהו בכלל מתעניין השבוע. */
function ventureOffer(game, rng) {
  const me = game.me;
  const club = game.myClub();
  const fame = fameScore(me, club ? club.reputation : 40, game.honours.length);
  const available = openVentures(fame);
  if (!available.length) return null;
  // ככל שאתה גדול יותר, כך הטלפון מצלצל יותר
  if (rng.random() > 0.05 + fame / 900) return null;

  const [kind, title, , mult, cost] = rng.choice(available);
  const base = Math.floor(fame * fame * 24 * mult);
  let payout = Math.floor(base * rng.uniform(0.75, 1.4));

  const offer = { kind, title, payout, cost, weeks: rng.randint(1, 3) };

  if (kind === "tycoon") {
    offer.who = rng.choice(TYCOONS);
    offer.equity = rng.randint(3, 12);
    offer.text = `${offer.who} רוצים אותך כשותף, לא כפרזנטור. `
                + `₪${fmt(payout)} ו-${offer.equity}% מהמיזם.`;
  } else if (kind === "league") {
    const [league, factor] = rng.choice(FOREIGN_LEAGUES);
    offer.who = league;
    offer.payout = Math.floor(payout * factor);
    offer.text = `${league} מוכנים לשלם ₪${fmt(offer.payout)} בשנה — `
               + `על עצם זה שתשחק שם. הרמה נמוכה מהמקום שלך היום.`;
    offer.rep_cost = 4.0;
  } else if (kind === "ambassador") {
    offer.who = rng.choice(CAMPAIGNS);
    offer.text = `הוזמנת להיות הפנים של ${offer.who}. `
               + `₪${fmt(payout)}, וכמה ימי צילום באמצע העונה.`;
  } else if (kind === "collection") {
    offer.who = rng.choice(["נייקי", "אדידס", "פומה", "אמברו"]);
    offer.royalty = rng.randint(2, 7);
    offer.text = `${offer.who} רוצים קולקציה על שמך. `
               + `₪${fmt(payout)} מראש, ואחוזים מהמכירות.`;
  } else if (kind === "documentary") {
    offer.who = rng.choice(["נטפליקס", "אמזון", "ערוץ הספורט"]);
    offer.text = `${offer.who} רוצים לעשות עליך סדרה. `
               + `₪${fmt(payout)}, וצוות שילווה אותך חודשיים.`;
  } else {
    offer.who = "עיריית " + rng.choice(["באר שבע", "חיפה", "נתניה", "אשדוד"]);
    offer.text = `${offer.who} מציעים לפתוח אקדמיה על שמך. `
               + `₪${fmt(payout)}, ומשהו שיישאר אחרייך.`;
  }
  return offer;
}

/** לוקח את העסקה. הכסף נכנס, והמחיר נגבה מהמגרש. */
function acceptVenture(game, offer) {
  const me = game.me;
  const out = [`✍️ סגרת: ${offer.title} — ${offer.who || ""}.`];
  game.money += offer.payout;
  out.push(`   ₪${fmt(offer.payout)} נכנסו לחשבון.`);

  if (offer.cost) {
    me.fitness = clamp(me.fitness - offer.cost, 0, 100);
    me.sharpness = clamp(me.sharpness - offer.cost * 1.4, 0, 100);
    out.push("   ימי הצילום עלו לך בכושר ובחדות.");
  }

  gainReputation(me, 1.6);
  me.mediaSkill = clamp(me.mediaSkill + 2.2, 0, 100);

  if (offer.kind === "tycoon") {
    if (!Array.isArray(game.flags.ventures)) game.flags.ventures = [];
    game.flags.ventures.push({ who: offer.who || "", equity: offer.equity,
                               value: offer.payout, year: game.year });
    out.push(`   ${offer.equity}% מהמיזם רשומים על שמך — `
           + `זה ימשיך לעבוד גם אחרי שתפרוש.`);
  } else if (offer.kind === "league") {
    gainReputation(me, -(offer.rep_cost || 0));
    game.setFlag("open_to_europe", true);
    out.push("   בכדורגל האירופי הרימו גבה. הכסף שווה את זה?");
  } else if (offer.kind === "collection") {
    if (!Array.isArray(game.flags.royalties)) game.flags.royalties = [];
    game.flags.royalties.push({ who: offer.who || "", rate: offer.royalty });
    out.push(`   ${offer.royalty}% מכל פריט שנמכר.`);
  } else if (offer.kind === "academy") {
    game.setFlag("academy", offer.who || "");
    out.push("   ילדים ילבשו את השם שלך על הגב.");
  }
  return out;
}

function declineVenture(game, offer) {
  const me = game.me;
  if (offer.kind === "league" && me.age >= 32)
    return "אמרת לא. בגיל הזה לא בטוח שיצלצלו שוב "
         + "— אבל אתה עוד רוצה לשחק כדורגל.";
  me.morale = clamp(me.morale + 1.5, 5, 99);
  return "אמרת לא. הראש נשאר על המגרש.";
}

function ventureBook(game) {
  return Array.isArray(game.flags.ventures) ? game.flags.ventures : [];
}

function royaltyBook(game) {
  return Array.isArray(game.flags.royalties) ? game.flags.royalties : [];
}

/** מה שממשיך להיכנס כל עונה מהמיזמים שסגרת. */
function passiveIncome(game) {
  let total = 0;
  for (const row of ventureBook(game))
    total += Math.floor(row.value * row.equity / 100 * 0.22);
  const club = game.myClub();
  const fame = fameScore(game.me, club ? club.reputation : 40, game.honours.length);
  for (const row of royaltyBook(game))
    total += Math.floor(fame * fame * row.rate * 1.4);
  return total;
}

/** מה השם שלך שווה עכשיו, בשורות. */
function fameLines(game) {
  const me = game.me;
  const club = game.myClub();
  const fame = fameScore(me, club ? club.reputation : 40, game.honours.length);
  const out = [`שם עולמי: ${Math.round(fame)} מתוך 100`];
  const tiers = openVentures(fame);
  if (tiers.length) out.push("פתוח לך: " + tiers.map(t => t[1]).join(", "));
  else {
    const nxt = VENTURES.reduce((a, b) => b[2] < a[2] ? b : a);
    out.push(`הפנייה הראשונה מסוג הזה תגיע סביב ${nxt[2]} — ${nxt[1]}.`);
  }
  const income = passiveIncome(game);
  if (income) out.push(`הכנסה פסיבית מהמיזמים: ₪${fmt(income)} לעונה`);
  return out;
}
