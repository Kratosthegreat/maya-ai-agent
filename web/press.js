// ---------------------------------------------------------------------------
// עיתונות, טלוויזיה ושמועות — תאום JS של press.py
//
// במשחק ניהול אמיתי אתה לא לומד על עצמך מטבלה — אתה לומד מהעיתון.
// והעיקר: לא כל שמועה נכונה. לכל מקור יש אמינות, ואתה רואה אותה —
// אבל לא רואה את התשובה.
// ---------------------------------------------------------------------------

const PRESS_SOURCES = [
  ["insider", "תחקירן ההעברות", 0.88, "📰"],
  ["tv", "פרשן הערוץ", 0.74, "📺"],
  ["beat", "כתב המועדון", 0.70, "🖊"],
  ["sources", "מקורות יודעי דבר", 0.52, "🕵"],
  ["radio", "תוכנית הרדיו", 0.44, "📻"],
  ["tabloid", "העיתון הצהוב", 0.26, "🗞"],
  ["fan", "חשבון אוהדים ברשת", 0.20, "📱"],
];
const SOURCE_NAMES = Object.fromEntries(PRESS_SOURCES.map(s => [s[0], s[1]]));
const SOURCE_TRUST = Object.fromEntries(PRESS_SOURCES.map(s => [s[0], s[2]]));
const SOURCE_ICON = Object.fromEntries(PRESS_SOURCES.map(s => [s[0], s[3]]));

const TRUST_WORDS = [
  [0.80, "מקור אמין מאוד"],
  [0.62, "בדרך כלל צודק"],
  [0.40, "לפעמים צודק"],
  [0.00, "כדאי לקחת בעירבון"],
];

const REACTIONS = [
  ["deny", "להכחיש"], ["confirm", "לאשר"], ["silent", "לא להגיב"],
];

const FEED_LIMIT = 30;

function trustWord(trust) {
  for (const [floor, word] of TRUST_WORDS) if (trust >= floor) return word;
  return TRUST_WORDS[TRUST_WORDS.length - 1][1];
}

function pressFeed(game) {
  const data = game.flags.press;
  return Array.isArray(data) ? data : [];
}

function pressPush(game, item) {
  const items = pressFeed(game);
  if (item.year === undefined) item.year = game.year;
  if (item.week === undefined) item.week = game.week;
  if (item.answered === undefined) item.answered = false;
  items.push(item);
  game.flags.press = items.slice(-FEED_LIMIT);
}

/** הפריט האחרון שמחכה לתגובה שלך, אם יש. */
function openQuestion(game) {
  const items = pressFeed(game);
  for (let i = items.length - 1; i >= 0; i--)
    if (items[i].asks && !items[i].answered) return items[i];
  return null;
}

function pressStory(key, source, text, isTrue, asks = false, weight = 1.0) {
  return { key, source, text, true: isTrue, trust: SOURCE_TRUST[source], asks, weight };
}

/**
 * מייצר את מה שנכתב עליך השבוע. השמועות לא נשלפות מהאוויר: כל אחת
 * נשענת על משהו שקורה במצב המשחק, ואז עוברת דרך מקור עם אמינות.
 */
function weeklyPress(game, rng) {
  const me = game.me;
  const out = [];
  if (!["player", "veteran", "youth"].includes(game.stage)) return out;

  // קודם ההגרלה ורק אחר כך בניית הסיפורים: ברוב השבועות לא כותבים
  // עליך כלום, ואין טעם לבנות עשרה סיפורים כדי לזרוק את כולם.
  let chance = 0.16 + me.reputation / 260;
  if (me.reputation > 70) chance += 0.12;
  if (rng.random() > chance) return out;

  const pool = pressCandidates(game);
  if (!pool.length) return out;

  const item = weightedPick(pool, pool.map(i => i.weight), rng);
  pressPush(game, item);
  out.push(`${SOURCE_ICON[item.source]} ${SOURCE_NAMES[item.source]}: "${item.text}"`);
  if (item.asks) out.push("   (אפשר להגיב — בתפריט: 'תקשורת')");
  return out;
}

function weightedPick(items, weights, rng) {
  const total = weights.reduce((a, b) => a + b, 0);
  let roll = rng.random() * total, acc = 0;
  for (let i = 0; i < items.length; i++) {
    acc += weights[i];
    if (roll <= acc) return items[i];
  }
  return items[items.length - 1];
}

/** כל הסיפורים שאפשר לכתוב עליך עכשיו, לפי מצב המשחק. */
function pressCandidates(game) {
  const me = game.me;
  const club = game.myClub();
  const rng = game.rng;
  const out = [];
  const clubName = club ? club.name : "המועדון";

  // -- התעניינות אמיתית של מועדון -----------------------------------
  const seen = watchers(game);
  if (seen.length) {
    const [other, score] = seen[0];
    const strong = score >= SCOUT_CHASED;
    const source = strong ? "insider" : rng.choice(["sources", "beat", "tv"]);
    out.push(pressStory("interest", source,
      `${other.name} שולחים צופים לכל משחק של ${me.name}. `
      + `בהנהלה מדברים על פנייה רשמית.`, true, true, strong ? 2.4 : 1.4));
  }

  // -- התעניינות שהיא בעיקר רעש --------------------------------------
  const pool = candidateClubs(game).filter(c => !seen.some(w => w[0].cid === c.cid));
  if (pool.length && me.reputation > 45) {
    const other = rng.choice(pool);
    out.push(pressStory("rumour", rng.choice(["tabloid", "fan", "radio"]),
      `${other.name} הניחו עין על ${me.name}. מדובר בסכום דמיוני.`,
      false, true, 1.6));
  }

  // -- כושר ------------------------------------------------------------
  if (me.season.apps >= 4) {
    const rating = avgRating(me.season);
    if (rating >= 7.3) {
      out.push(pressStory("hot", "tv",
        `אין היום שחקן בכושר של ${me.name}. ממוצע ${rating.toFixed(2)} `
        + `זה לא מקרי — זה מישהו שעולה מדרגה.`, true, false, 1.8));
    } else if (rating <= 6.3) {
      out.push(pressStory("cold", rng.choice(["radio", "tabloid", "beat"]),
        `מה קרה ל${me.name}? ממוצע ${rating.toFixed(2)} מתחילת העונה. `
        + `ב${clubName} מתחילים לשאול שאלות.`, true, true, 1.6));
    }
  }

  // -- חוזה -------------------------------------------------------------
  if (me.contract.yearsLeft <= 1 && game.stage !== "youth") {
    out.push(pressStory("contract", "insider",
      `החוזה של ${me.name} ב${clubName} נגמר בסוף העונה, `
      + `והמגעים לחידוש תקועים.`, true, true, 2.0));
  }

  // -- פציעה ------------------------------------------------------------
  if (me.injuryWeeks > 0) {
    out.push(pressStory("injury", "tabloid",
      `הפציעה של ${me.name} חמורה בהרבה ממה שב${clubName} מוכנים להגיד. `
      + `מדברים על חצי עונה.`, false, true, 1.8));
  } else if (me.fitness < 62) {
    out.push(pressStory("fitness", "sources",
      `${me.name} מגיע לאימונים על חצי מיכל. בצוות הרפואי לא רגועים.`,
      me.fitness < 55, true, 1.2));
  }

  // -- יחסים במועדון -----------------------------------------------------
  if (club && club.managerTrust < 42) {
    out.push(pressStory("manager", rng.choice(["sources", "beat"]),
      `ב${clubName} מספרים על שיחה לא נעימה בין המאמן ל${me.name}. `
      + `הוא לא בטוח בהרכב.`, true, true, 1.9));
  } else if (club && club.managerTrust > 78) {
    out.push(pressStory("trusted", "beat",
      `המאמן של ${clubName} על ${me.name}: "הוא הראשון על הדף שלי."`,
      true, false, 1.0));
  }

  // -- שמועה מומצאת לגמרי ------------------------------------------------
  if (me.reputation > 55) {
    out.push(pressStory("gossip", rng.choice(["tabloid", "fan"]), rng.choice([
      `${me.name} נראה מחפש בתים בחו"ל. אצלנו יודעים למה.`,
      `ב${clubName} כועסים על ${me.name} אחרי שאיחר לאימון. המקורבים מכחישים.`,
      `${me.name} החליף סוכן בשקט. זה תמיד אומר משהו.`,
    ]), false, true, 1.3));
  }

  // -- נבחרת -------------------------------------------------------------
  if (me.reputation > 62 && !game.caps) {
    out.push(pressStory("national", rng.choice(["tv", "sources"]),
      `השם של ${me.name} עלה בישיבת הסגל של הנבחרת. `
      + `יש מי שאומר שזה רק עניין של זמן.`,
      me.reputation > 70, true, 1.7));
  }
  return out;
}

/**
 * מגיב לשמועה הפתוחה. לכל בחירה יש מחיר, וגם לשתיקה.
 */
function pressReact(game, choice, rng) {
  const item = openQuestion(game);
  if (!item) return "אין כרגע משהו שמחכה לתגובה.";
  const me = game.me;
  const club = game.myClub();
  item.answered = true;
  item.reaction = choice;
  game.flags.press = pressFeed(game);

  let smooth = me.mediaSkill / 100;
  if (hasTrait(me, "media_darling")) smooth += 0.18;
  if (hasTrait(me, "hothead")) smooth -= 0.20;
  smooth = clamp(smooth, 0, 1);

  if (choice === "deny") {
    if (item.true) {
      // הכחשת אמת מחזיקה בדיוק עד שהיא לא
      if (rng.random() < 0.45 - smooth * 0.30) {
        gainReputation(me, -2.5);
        me.morale = clamp(me.morale - 7, 5, 99);
        if (club) club.fanSupport = clamp(club.fanSupport - 5, 0, 100);
        return "הכחשת — ותוך שבוע יצאה ההקלטה. "
             + "\"אמרתי מה שהייתי צריך להגיד\" לא עבד הפעם.";
      }
      if (club) {
        club.managerTrust = clamp(club.managerTrust + 4, 0, 100);
        club.fanSupport = clamp(club.fanSupport + 3, 0, 100);
      }
      return "הכחשת בתוקף. במועדון אהבו את זה; אתה יודע מה האמת.";
    }
    gainReputation(me, 0.8 + smooth);
    if (club) club.fanSupport = clamp(club.fanSupport + 5, 0, 100);
    return "הכחשת, וצדקת. הסיפור נגמר תוך יומיים והיציע זכר את זה.";
  }

  if (choice === "confirm") {
    if (item.true) {
      gainReputation(me, 2.2);
      me.morale = clamp(me.morale + 4, 5, 99);
      if (club) {
        club.managerTrust = clamp(club.managerTrust - 7, 0, 100);
        club.fanSupport = clamp(club.fanSupport - 8, 0, 100);
      }
      game.setFlag("open_to_europe", true);
      return "אישרת. הכותרות ענקיות, הסוכן שלך מאושר, "
           + "וביציע לא סולחים על זה מהר.";
    }
    gainReputation(me, -3.0);
    me.morale = clamp(me.morale - 5, 5, 99);
    return "אישרת משהו שלא היה. כשהתברר שאין שום הצעה, "
         + "יצאת מי שמנסה ליצור לעצמו שוק.";
  }

  // שתיקה
  if (item.true) {
    if (club) club.managerTrust = clamp(club.managerTrust - 2, 0, 100);
    return "לא הגבת. הסיפור המשיך לרוץ, וכולם הבינו לבד.";
  }
  return "לא הגבת. בלי דלק הסיפור דעך מעצמו תוך שבוע.";
}

/** מה אמרו עליך באולפן אחרי המשחק. נשען על המספרים האמיתיים. */
function broadcast(game, result, rng) {
  const me = game.me;
  const stats = game.flags.last_stats;
  const rating = stats && stats.rating ? stats.rating : 0;
  if (!rating) return [];
  const lines = [];
  if (rating >= 8.2) {
    lines.push(rng.choice([
      `📺 "אם מישהו עוד לא ראה את ${me.name} — תראו את המשחק הזה."`,
      `📺 "ציון ${rating.toFixed(1)}. לא צריך להוסיף מילה."`,
    ]));
  } else if (rating >= 7.2) {
    lines.push(rng.choice([
      `📺 "${me.name} היה הכי טוב על המגרש, ובלי לעשות רעש."`,
      `📺 "זה שחקן שהקבוצה כבר בנויה סביבו."`,
    ]));
  } else if (rating <= 5.6) {
    lines.push(rng.choice([
      `📺 "אני אגיד את זה בזהירות — ${me.name} לא היה שם היום."`,
      `📺 "ציון ${rating.toFixed(1)}. יש ימים כאלה, אבל לא שניים ברצף."`,
    ]));
  }
  return lines;
}
