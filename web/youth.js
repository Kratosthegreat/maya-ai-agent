// ---------------------------------------------------------------------------
// איך צדים ילד בן שלוש־עשרה — תאום JS של youth.py
//
// מועדונים גדולים לא מחכים שתגיע לבוגרים. שני דברים מבדילים את השוק
// הזה מזה של הבוגרים: זו לא עסקה של כסף (מעונות, בית ספר, מסלול),
// וההחלטה היא לא רק שלך — יש הורים, ולהם יש דעה משלהם.
//
// והדבר החשוב באמת: מרוץ מעלה את הערך שלך. ילד ששלוש קבוצות רבות
// עליו נהיה שווה יותר מילד שאחת בדקה אותו, עוד לפני שהוכיח משהו.
// ---------------------------------------------------------------------------

// מה חשוב להורים שלך. נקבע פעם אחת בתחילת הקריירה.
const FAMILY_VALUES = [
  ["schooling", "לימודים", "רוצים שתסיים בית ספר כמו כל ילד"],
  ["home", "קרבה לבית", "לא מוכנים שתגור רחוק בגיל הזה"],
  ["money", "ביטחון כלכלי", "המשפחה צריכה את זה, ואין טעם להתבייש"],
  ["football", "כדורגל קודם", "מאמינים בך, ומוכנים לשלם את המחיר"],
];
const FAMILY_NAMES = Object.fromEntries(FAMILY_VALUES.map(v => [v[0], v[1]]));
const FAMILY_WHY = Object.fromEntries(FAMILY_VALUES.map(v => [v[0], v[2]]));

const DISTANCE_NAMES = {
  local: "בעיר שלך", national: "בארץ, נסיעה ארוכה", abroad: "בחו\"ל",
};

const SCOUT_POOL_LIMIT = 12;   // כמה אקדמיות בכלל מסתובבות בטורנירי הנוער
const YOUTH_NOTICED = 20.0;    // מופיע ברשימת "מי מסתכל עליי"
const YOUTH_CHASED = 50.0;     // מוכן להניח הצעה על השולחן
const YOUTH_JOINS = 30.0;      // מצטרף למרוץ ברגע שמישהו אחר פנה
const YOUTH_WINDOW_WEEKS = 6;  // לילד נותנים יותר זמן להחליט

/** פרופיל ההורים. נקבע בלידת הקריירה ולא משתנה. */
function makeFamily(rng) {
  const values = FAMILY_VALUES.map(v => v[0]);
  const first = rng.choice(values);
  const second = rng.choice(values.filter(v => v !== first));
  return { first, second, trust: rng.randint(45, 75) };
}

function family(game) {
  let data = game.flags.family;
  if (!data || typeof data !== "object") {
    data = makeFamily(game.rng);
    game.flags.family = data;
  }
  return data;
}

function familyLine(game) {
  const fam = family(game);
  return `ההורים שלך: ${FAMILY_NAMES[fam.first]} לפני הכול, `
       + `ואחר כך ${FAMILY_NAMES[fam.second]}. ${FAMILY_WHY[fam.first]}.`;
}

function youthInterest(game) {
  let data = game.flags.youth_interest;
  if (!data || typeof data !== "object") {
    data = {};
    game.flags.youth_interest = data;
  }
  return data;
}

/** מי עוקב אחריך עכשיו, מהחזק לחלש. */
function youthWatchers(game, minimum = YOUTH_NOTICED) {
  const table = youthInterest(game);
  const rows = [];
  for (const cid in table)
    if (game.clubs[cid] && Number(table[cid]) >= minimum)
      rows.push([game.clubs[cid], Number(table[cid])]);
  rows.sort((a, b) => b[1] - a[1]);
  return rows;
}

/** אילו אקדמיות בכלל מחפשות ילדים כמוך. */
function scoutPool(game) {
  const me = game.me;
  const out = [];
  for (const cid in game.clubs) {
    const club = game.clubs[cid];
    if (club.cid === me.clubId) continue;
    const reach = club.reputation * 0.55 + club.trainingFacilities * 0.30;
    if (me.potential + 6 >= reach) out.push(club);
  }
  // ילד אחד לא נמצא על הרדאר של ארבעים מועדונים. אם כל הביקורים
  // מתפזרים על כולם, אף אחד לא בונה תיק ואף אחד לא פונה.
  out.sort((a, b) => (b.reputation * 0.6 + b.trainingFacilities * 0.4)
                   - (a.reputation * 0.6 + a.trainingFacilities * 0.4));
  return out.slice(0, SCOUT_POOL_LIMIT);
}

/** שבוע של צופי נוער. אין ציוני משחק בגיל הזה — יש עין. */
function youthScoutsThisWeek(game, rng) {
  const me = game.me;
  const lines = [];
  const table = youthInterest(game);

  // דעיכה — צופה שלא חזר לראות אותך מתחיל לשכוח
  for (const cid of Object.keys(table)) {
    table[cid] = Math.round((Number(table[cid]) * 0.985 - 0.15) * 100) / 100;
    if (table[cid] <= 1.0) delete table[cid];
  }

  if (me.age < 12) return lines;
  const pool = scoutPool(game);
  if (!pool.length) return lines;

  let visits = rng.random() < 0.42 + me.potential / 220 ? 1 : 0;
  if (me.potential >= 70 && rng.random() < 0.24) visits += 1;
  for (let v = 0; v < visits; v++) {
    const weights = pool.map(club => {
      let weight = Math.pow(club.reputation / 30, 1.25);
      weight *= 1 + club.trainingFacilities / 90;
      // מי שכבר פתח עליך תיק חוזר לראות אותך שוב
      weight *= 1 + Number(table[club.cid] || 0) / 9;
      return [club, weight];
    });
    const total = weights.reduce((a, w) => a + w[1], 0) || 1;
    let roll = rng.random() * total;
    let club = weights[weights.length - 1][0];
    for (const [candidate, weight] of weights) {
      roll -= weight;
      if (roll <= 0) { club = candidate; break; }
    }

    // מה שהוא רואה: פוטנציאל מול מה שהאקדמיה שלו רגילה אליו
    let move = (me.potential - club.reputation * 0.78) * 0.42;
    move += ((me.detail.determination ?? 10) - 10) * 0.55;
    move += ((me.detail.natural_fitness ?? 10) - 10) * 0.25;
    move += rng.uniform(-2.0, 2.0);
    if (me.age <= 14) move = move * 1.2 + 1.0;   // על ילד קטן מהמרים בקלות
    const before = Number(table[club.cid] || 0);
    const after = Math.round(clamp(before + move, 0, 100) * 100) / 100;
    table[club.cid] = after;

    if (before < YOUTH_NOTICED && after >= YOUTH_NOTICED) {
      lines.push(`👀 צופה של ${club.name} עמד בצד המגרש כל האימון.`);
    } else if (before < YOUTH_CHASED && after >= YOUTH_CHASED) {
      lines.push(`🔥 ${club.name} שלחו את ראש מחלקת הנוער. זה כבר לא סתם מבט.`);
      // וזה בדיוק הרגע שבו כל השאר שומעים
      lines.push(...rivalsHear(game, club, table, rng));
    }
  }
  game.flags.youth_interest = table;
  return lines;
}

/**
 * כשאקדמיה אחת נכנסת ברצינות, המתחרות מתעוררות. בלי זה כל ילד נחטף
 * על ידי המועדון הראשון שראה אותו, ואין מרוץ.
 */
function rivalsHear(game, club, table, rng) {
  const out = [];
  const rivals = scoutPool(game).filter(c =>
    c.cid !== club.cid && Number(table[c.cid] || 0) < YOUTH_CHASED);
  rng.shuffle(rivals);
  for (const rival of rivals.slice(0, 2)) {
    if (rng.random() > 0.55) continue;
    const before = Number(table[rival.cid] || 0);
    table[rival.cid] = Math.round(
      clamp(before + rng.uniform(14, 26), 0, 100) * 100) / 100;
    if (before < YOUTH_NOTICED && table[rival.cid] >= YOUTH_NOTICED)
      out.push(`👀 גם ${rival.name} שלחו מישהו. השמועה עברה.`);
  }
  return out;
}

/** חבילה לילד ולמשפחה שלו. אין כאן שכר — יש כאן חיים. */
function buildYouthOffer(game, club, rng, eagerness = null) {
  const me = game.me;
  const myClub = game.myClub();
  if (eagerness === null) eagerness = rng.uniform(0.4, 1.0);

  const country = D.CLUB_COUNTRY[club.cid] || "ישראל";
  const home = myClub ? (D.CLUB_COUNTRY[myClub.cid] || "ישראל") : "ישראל";
  let distance;
  if (country !== home) distance = "abroad";
  else if (club.reputation > 55) distance = "national";
  else distance = rng.choice(["local", "national"]);

  const grade = club.trainingFacilities / 100;
  return {
    cid: club.cid,
    distance,
    boarding: distance !== "local" && rng.random() < 0.55 + eagerness * 0.4,
    schooling: Math.floor(clamp(35 + grade * 55 + eagerness * 18, 20, 99)),
    family_help: Math.floor(club.reputation * 900 * (0.5 + eagerness) * grade),
    minutes: eagerness > 0.55,
    pathway: eagerness > 0.72 && club.reputation > 45,
    coach: eagerness > 0.62,
    fee: Math.floor(club.reputation * 1400 * (0.4 + eagerness)),
    eagerness: Math.round(eagerness * 1000) / 1000,
    weeks: YOUTH_WINDOW_WEEKS,
    state: "open",
  };
}

function youthOfferLines(game, offer) {
  const out = [`מיקום: ${DISTANCE_NAMES[offer.distance]}`];
  out.push(offer.boarding ? "מעונות ופנימייה" : "גר בבית, נוסע לאימונים");
  out.push(`בית ספר במסגרת האקדמיה: ${offer.schooling}/100`);
  if (offer.family_help) out.push(`סיוע למשפחה: ₪${fmt(offer.family_help)} לשנה`);
  if (offer.minutes) out.push("הבטחת דקות בקבוצת הנוער");
  if (offer.pathway) out.push("מסלול מוגדר לסגל הבוגרים");
  if (offer.coach) out.push("מאמן אישי צמוד");
  return out;
}

/** כמה זה טוב לכדורגל שלך. 0-100. */
function footballScore(game, offer) {
  const club = game.clubs[offer.cid];
  if (!club) return 0;
  let score = club.reputation * 0.55 + club.trainingFacilities * 0.30;
  if (offer.minutes) score += 8;
  if (offer.pathway) score += 10;
  if (offer.coach) score += 6;
  return clamp(score, 0, 100);
}

/** כמה זה טוב בעיני ההורים. 0-100. לא אותו דבר בכלל. */
function familyScore(game, offer) {
  const fam = family(game);
  const club = game.clubs[offer.cid];
  if (!club) return 0;
  const parts = {
    schooling: offer.schooling,
    home: { local: 92, national: 55, abroad: 18 }[offer.distance],
    money: clamp(offer.family_help / 900, 0, 100),
    football: footballScore(game, offer),
  };
  // הערך הראשון חייב באמת להכריע. אחרת בית ספר טוב וכסף גדול
  // מצליחים "לפצות" על ילד בן שלוש־עשרה שעובר לגור בחו"ל.
  let score = 0;
  for (const key in parts) {
    const weight = key === fam.first ? 4.5 : key === fam.second ? 1.8 : 0.8;
    score += parts[key] * weight;
  }
  score /= (4.5 + 1.8 + 0.8 + 0.8);
  if (offer.boarding && fam.first === "home") score -= 18;
  return clamp(score, 0, 100);
}

/** מה ההורים אומרים, ולמה. */
function familyVerdict(game, offer) {
  const fam = family(game);
  const mine = footballScore(game, offer);
  const theirs = familyScore(game, offer);
  const club = game.clubs[offer.cid];
  const name = club ? club.name : "המועדון";

  let mood, text;
  if (theirs >= 68) {
    mood = "happy"; text = `"${name} זה מקום טוב. אנחנו איתך."`;
  } else if (theirs >= 48) {
    mood = "unsure"; text = `"אנחנו לא בטוחים לגבי ${name}, אבל נקשיב לך."`;
  } else {
    mood = "against";
    text = {
      schooling: `"ומה עם בית הספר? זה לא נגמר בכדורגל."`,
      home: `"אתה בן ${game.me.age}. לא נותנים לך לגור לבד."`,
      money: `"אנחנו לא יכולים לממן את זה. פשוט לא."`,
      football: `"זה לא המקום שיוציא ממך את המקסימום."`,
    }[fam.first];
  }

  return {
    mood, text,
    family: Math.round(theirs * 10) / 10,
    football: Math.round(mine * 10) / 10,
    conflict: mood === "against" && mine >= theirs + 12,
  };
}

function openYouthOffers(game) {
  return Array.isArray(game.flags.youth_offers) ? game.flags.youth_offers : [];
}

function setYouthOffers(game, offers) { game.flags.youth_offers = offers; }

function liveYouthOffers(game) {
  return openYouthOffers(game).filter(o => o.state === "open")
    .sort((a, b) => footballScore(game, b) - footballScore(game, a));
}

function youthOfferFor(game, cid) {
  return openYouthOffers(game).find(o => o.cid === cid) || null;
}

function clearYouthOffers(game) { delete game.flags.youth_offers; }

/** אם מספיק אקדמיות רוצות אותך — הן מניחות הצעות. */
function maybeOpenYouthMarket(game, rng) {
  const me = game.me;
  if (game.stage !== "youth" || openYouthOffers(game).length) return [];
  const chasing = youthWatchers(game, YOUTH_CHASED);
  if (!chasing.length) return [];
  if (rng.random() > 0.30) return [];

  // ברגע שאחת פונה רשמית, כל מי שיש לו תיק פתוח מניח משהו על השולחן
  // גם הוא — זה מה שיוצר מרוץ ולא פנייה בודדת.
  const joining = youthWatchers(game, YOUTH_JOINS);
  const offers = joining.slice(0, 4).map(([club, score]) =>
    buildYouthOffer(game, club, rng, clamp(0.35 + (score - YOUTH_JOINS) / 48, 0.35, 1.0)));
  setYouthOffers(game, offers);

  const live = liveYouthOffers(game);
  const lines = [`📞 טלפון הביתה. ${live.length} `
               + `${live.length > 1 ? "אקדמיות" : "אקדמיה"} רוצות אותך:`];
  for (const offer of live) {
    const club = game.clubs[offer.cid];
    lines.push(`   • ${club.name} — ${DISTANCE_NAMES[offer.distance]}`);
  }
  lines.push("   ההחלטה היא שלך ושל ההורים. (בתפריט: 'אקדמיות')");
  lines.push(...chaseBonus(game));
  return lines;
}

function tickYouthOffers(game) {
  const lines = [];
  const offers = openYouthOffers(game);
  if (!offers.length) return lines;
  for (const offer of offers.filter(o => o.state === "open")) {
    offer.weeks -= 1;
    const club = game.clubs[offer.cid];
    const name = club ? club.name : "אקדמיה";
    if (offer.weeks <= 0) {
      offer.state = "gone";
      lines.push(`⌛ ${name} סגרו את הרשימה שלהם לעונה הזאת.`);
    } else if (offer.weeks === 1) {
      lines.push(`⏳ ${name} מבקשים תשובה השבוע.`);
    }
  }
  setYouthOffers(game, offers);
  return lines;
}

/**
 * מרוץ על ילד מעלה את הערך שלו — עוד לפני שהוכיח משהו. ברגע שנודע
 * ששלוש אקדמיות רוצות את אותו נער, הוא מפסיק להיות "עוד ילד" ומתחיל
 * להיות נכס. הציפייה עצמה מייצרת שווי, וגם לחץ.
 */
function chaseBonus(game) {
  const me = game.me;
  const count = liveYouthOffers(game).length;
  if (count < 2) return [];
  gainReputation(me, 1.6 * count);
  const before = me.potential;
  me.potential = Math.round(clamp(me.potential + count, 0, me.ceiling));
  if (count >= 3 && me.ceiling < 95) me.ceiling = Math.min(95, me.ceiling + 1);
  me.morale = clamp(me.morale + 4, 5, 99);
  const out = [`💎 ${count} אקדמיות רבות עליך. בגיל ${me.age} זה כבר סיפור.`];
  if (me.potential > before) out.push(`   ההערכה עליך עלתה ל-${me.potential}.`);
  return out;
}

/** מנסה לשכנע את ההורים. פעם אחת לכל הצעה. */
function persuadeFamily(game, cid, rng) {
  const offer = youthOfferFor(game, cid);
  if (!offer || offer.state !== "open") return "ההצעה כבר לא על השולחן.";
  if (offer.persuaded) return "כבר דיברת איתם על זה. יותר מזה רק יזיק.";
  const me = game.me;
  const fam = family(game);
  offer.persuaded = true;

  let chance = 0.20 + fam.trust / 260;
  chance += ((me.detail.determination ?? 10) - 10) * 0.030;
  if ((game.flag("school", 0) || 0) >= 6) chance += 0.12;  // למדת — יש קרדיט
  if (familyScore(game, offer) < 35) chance -= 0.18;
  chance = clamp(chance, 0.05, 0.88);

  if (rng.random() < chance) {
    offer.blessing = true;
    fam.trust = Math.round(clamp(fam.trust + 6, 0, 100));
    game.flags.family = fam;
    return "ישבתם במטבח שעתיים. בסוף אבא אמר \"אם אתה בטוח — אנחנו מאחוריך.\"";
  }
  fam.trust = Math.round(clamp(fam.trust - 4, 0, 100));
  game.flags.family = fam;
  me.morale = clamp(me.morale - 5, 5, 99);
  return "הם לא השתכנעו. \"אנחנו לא אומרים לא לכדורגל, אנחנו אומרים לא עכשיו.\"";
}

/** חותם באקדמיה. אם ההורים נגד — זה עולה במשהו. */
function acceptYouthOffer(game, cid) {
  const offer = youthOfferFor(game, cid);
  if (!offer || offer.state !== "open") return ["ההצעה כבר לא על השולחן."];
  const club = game.clubs[offer.cid];
  const me = game.me;
  const verdict = familyVerdict(game, offer);
  const against = verdict.mood === "against" && !offer.blessing;

  const out = [`✍️ עברת לאקדמיה של ${club.name}.`];
  game.transferMe(club.cid, 0, 3);
  if (offer.family_help) {
    game.money += offer.family_help;
    out.push(`   המשפחה קיבלה ₪${fmt(offer.family_help)} סיוע.`);
  }
  game.flags.academy_deal = {
    cid: club.cid, minutes: offer.minutes, pathway: offer.pathway,
    coach: offer.coach, schooling: offer.schooling, boarding: offer.boarding,
  };
  if (offer.pathway) out.push("   יש לך מסלול כתוב לסגל הבוגרים.");
  if (offer.coach) out.push("   הצמידו לך מאמן אישי.");
  if (offer.boarding) out.push("   ארזת תיק. בן כמה היית כשעזבת את הבית?");

  if (against) {
    me.morale = clamp(me.morale - 12, 5, 99);
    const fam = family(game);
    fam.trust = Math.round(clamp(fam.trust - 14, 0, 100));
    game.flags.family = fam;
    out.push("   ההורים לא הסכימו, והלכת בכל זאת. בבית לא מדברים על זה.");
  } else {
    me.morale = clamp(me.morale + 9, 5, 99);
  }

  clearYouthOffers(game);
  game.flags.youth_interest = {};
  return out;
}

function declineYouthOffer(game, cid) {
  const offer = youthOfferFor(game, cid);
  if (!offer) return "אין הצעה כזאת.";
  offer.state = "gone";
  setYouthOffers(game, openYouthOffers(game));
  const club = game.clubs[cid];
  if (liveYouthOffers(game).length)
    return `אמרת לא ל${club ? club.name : "אקדמיה"}. נשארו אחרות.`;
  clearYouthOffers(game);
  game.me.morale = clamp(game.me.morale + 2, 5, 99);
  return "נשארת איפה שאתה. יש עוד זמן.";
}
