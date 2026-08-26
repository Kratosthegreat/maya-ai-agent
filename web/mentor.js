// ---------------------------------------------------------------------------
// מישהו שמלווה אותך, ולא חוזר על עצמו — תאום JS של mentor.py
//
// הוא לא מגריל שורה מרשימה. הוא קורא את המצב, נותן ציון דחיפות לכל
// דבר שראה, ומדבר על הדחוף ביותר שעוד לא דיבר עליו. מצב שנמשך לא
// מקבל את אותו משפט שוב — הוא מקבל משפט חריף יותר.
// ---------------------------------------------------------------------------

const MENTORS = [
  ["veteran", "יעקב אזולאי", "ותיק שסיים בגיל 38 ויודע בדיוק איפה כואב",
   ["תשמע,", "אני אגיד לך את זה פעם אחת.", "אני הייתי שם."]],
  ["coach", "רונית שגב", "מאמנת כושר שראתה מאתיים נערים נשרפים",
   ["בוא נדבר תכל'ס.", "אני מסתכלת על המספרים שלך.", "שב רגע."]],
  ["scout", "מוני ברזילי", "צופה ותיק שקורא שחקנים לפני שהם קוראים את עצמם",
   ["רשמתי לעצמי משהו.", "אני עוקב אחריך.", "משהו קטן."]],
  ["agent", "דנה פרץ", "סוכנת שמדברת ישר וחוסכת לך שנים",
   ["אני לא אעטוף את זה.", "בינינו.", "תקשיב טוב."]],
];

const MENTOR_COOLDOWN = 26;

function mentorHash(text) {
  let value = 2166136261;
  for (const ch of text) {
    value ^= ch.codePointAt(0);
    value = Math.imul(value, 16777619) >>> 0;
  }
  return value;
}

/** המנטור שלך — נקבע מהשם שלך, ולכן קבוע לכל הקריירה. */
function mentorOf(game) {
  return MENTORS[mentorHash(game.me.name + "mentor") % MENTORS.length];
}

function mentorLog(game) {
  if (!game.flags.mentor_log || typeof game.flags.mentor_log !== "object"
      || Array.isArray(game.flags.mentor_log)) game.flags.mentor_log = {};
  return game.flags.mentor_log;
}

/** כמה פעמים כבר אמר לך כל דבר. זה מה שמונע ממנו לחזור על עצמו. */
function mentorCounts(game) {
  if (!game.flags.mentor_count || typeof game.flags.mentor_count !== "object"
      || Array.isArray(game.flags.mentor_count)) game.flags.mentor_count = {};
  return game.flags.mentor_count;
}

function saidRecently(game, key, cooldown = MENTOR_COOLDOWN) {
  const stamp = mentorLog(game)[key];
  if (stamp === undefined) return false;
  const year = Math.trunc(stamp / 100), week = stamp % 100;
  return (game.year - year) * 43 + (game.week - week) < cooldown;
}

function markSaid(game, key) {
  mentorLog(game)[key] = game.year * 100 + game.week;
  const counts = mentorCounts(game);
  counts[key] = (counts[key] || 0) + 1;
}

function saidTimes(game, key) { return mentorCounts(game)[key] || 0; }

/** כל מה שהמנטור מזהה עכשיו, עם ציון דחיפות. */
function mentorObservations(game) {
  const me = game.me;
  const club = game.myClub();
  const out = [];

  const see = (key, urgency, title, body, action = null, cooldown = MENTOR_COOLDOWN) => {
    const times = saidTimes(game, key);
    const titles = Array.isArray(title) ? title : [title];
    const bodies = Array.isArray(body) ? body : [body];
    out.push({
      key, urgency: urgency + times * 6,
      title: titles[Math.min(times, titles.length - 1)],
      body: bodies[Math.min(times, bodies.length - 1)],
      action, times, cooldown: cooldown + times * 10,
      exhausted: times >= Math.max(titles.length, bodies.length) + 1,
    });
  };

  const needs = rankedNeeds(game, 3);
  if (needs.length) {
    const top = needs[0];
    const name = D.DETAIL_NAMES_HE[top.attr];
    const why = top.reasons.length ? top.reasons[0] : "זו החולשה הבולטת שלך";
    see(`need_${top.attr}`, 62 + top.score * 0.25, `תתאמן על ${name}`,
        `${why}. ${forecastLine(game, top.attr)}`, top.attr, 18);
  }

  if (me.role) {
    const mine = roleSuitability(me, me.role);
    const [bestKey, bestScore] = bestRole(me);
    if (bestKey !== me.role && bestScore - mine >= 8) {
      const row = roleRow(bestKey), current = roleRow(me.role);
      see("role_mismatch", 74,
        [`אתה לא ${current[1]}`, `עדיין משחקים אותך כ${current[1]}`],
        [`התכונות שלך אומרות ${row[1]} (${Math.round(bestScore)}) ולא `
         + `${current[1]} (${Math.round(mine)}). ${row[6]} לך תדבר איתו — `
         + "או תתאמן על מה שהתפקיד הנוכחי דורש, ותפסיק להילחם בזה.",
         `אמרתי לך שאתה ${row[1]}. אתה עדיין ${current[1]}. שתי אפשרויות `
         + "נשארו: או שאתה מקבל את התפקיד ובונה את התכונות שהוא דורש, או "
         + `שאתה מוצא מאמן שרואה בך ${row[1]}. מה שאתה עושה עכשיו — לא עובד.`]);
    }
  }

  if (club) {
    const [fit, note] = styleSuitsPlayer(club, me);
    if (fit < 35) {
      const styleName = tacticalStyle(club)[1];
      see("style_mismatch", 58,
        [`אתה לא בנוי ל${styleName}`, `${styleName} עדיין חונק אותך`],
        [`${note}. אצל מאמן אחר אותן תשעים דקות היו נראות אחרת. אם זה `
         + "נמשך עונה שלמה — תתחיל לחשוב על מעבר.",
         `${note}. עברה עונה ולא השתנה כלום. יש שחקנים שנשברים בניסיון `
         + "להתאים את עצמם למערכת, ויש כאלה שמוצאים מערכת שמתאימה להם. "
         + "השנייה מהירה יותר."]);
    }
  }

  if (game.noStartStreak >= 5) {
    see("no_minutes", 80,
      ["אתה לא משחק", "עדיין לא משחק", "זה כבר לא מקרי"],
      [`${game.noStartStreak} משחקים ברצף בלי הרכב. בגיל שלך ספסל זה לא `
       + "מנוחה — זה קיפאון. או שאתה משנה משהו באימונים, או שאתה מחפש "
       + "מקום שבו תשחק.",
       `${game.noStartStreak} משחקים. דיברנו על זה, ושום דבר לא זז. המאמן `
       + "החליט מה הוא חושב עליך, וזה לא ישתנה מאימון טוב אחד. או שאתה "
       + "מוכיח לו במשהו קונקרטי, או שאתה מרים טלפון לסוכן.",
       `${game.noStartStreak} משחקים. אני לא אחזור על זה יותר. עונה שלמה `
       + "על הספסל בגיל הזה עולה לך שנתיים של קריירה. תחליט."],
      null, 14);
  }

  if (me.fitness < 45) {
    see("fitness", 88,
      ["הגוף שלך על הקצה", "שוב הגעת לאדום", "אתה מתעלם ממני"],
      [`רעננות ${Math.round(me.fitness)}. ככה נכנסים למשחק ויוצאים פצועים, `
       + "וגם הציון נענש. שבוע מנוחה עכשיו שווה יותר משלושה אימונים.",
       `רעננות ${Math.round(me.fitness)}, ושוב. זה כבר לא מקרה — זה איך `
       + "שאתה מנהל את השבוע. תוריד עצימות, או תיקח שבוע.",
       `רעננות ${Math.round(me.fitness)}. אני אומר לך את זה בפעם השלישית. `
       + "הפציעה הבאה שלך כבר נקבעה, השאלה היא רק מתי."],
      "rest", 10);
  } else if (me.sharpness < 45 && isAvailable(me)) {
    see("sharpness", 52, "אין לך דקות ברגליים",
      `חדות ${Math.round(me.sharpness)}. אתה יכול להיות בכושר מצוין ועדיין `
      + "להיכנס למשחק חלוד. חדות נבנית רק ממשחקים.", null, 16);
  }

  if (me.resilience < 38) {
    see("fragile", 66, "אתה נשבר יותר מדי",
      `עמידות ${Math.round(me.resilience)}. עבודת כוח וסיבולת בונה גוף `
      + "שמחזיק. זה משעמם, וזה מה שיקבע כמה עונות תשחק.", "strength");
  }

  const plan = planSummary(game);
  if (plan.chosen) {
    for (const entry of plan.milestones) {
      if (entry.claimed) continue;
      const gaps = entry.needs.filter(p => p.have < p.need);
      const missing = gaps.reduce((a, p) => a + (p.need - p.have), 0);
      if (gaps.length && missing <= 3) {
        const names = gaps.map(p => `${p.name} ${p.have}/${p.need}`).join(", ");
        see(`milestone_${entry.index}`, 76,
          `אתה על סף אבן הדרך של גיל ${entry.age}`,
          `חסרות ${missing} נקודות: ${names}. תסגור את זה עכשיו — אבן דרך `
          + "בזמן שווה כפול מאבן דרך באיחור.", gaps[0].attr, 12);
      }
      break;
    }
  } else if (["youth", "academy", "player", "veteran"].includes(game.stage)) {
    see("no_plan", 70,
      ["אין לך מסלול", "עדיין בלי מסלול"],
      ["אתה מתאמן בלי יעד. תבחר תפקיד שאתה רוצה להיות, ותקבל יעדים לפי "
       + "גיל במקום לנחש כל שבוע.",
       "עוד לא בחרת. כל שבוע בלי מסלול הוא שבוע שבו אתה מפזר עבודה על "
       + "שלושים ושש תכונות במקום על ארבע שחשובות."]);
  }

  const history = Array.isArray(game.flags.focus_log) ? game.flags.focus_log : [];
  if (history.length >= 12) {
    const recent = history.slice(-12);
    if (new Set(recent).size <= 2 && recent[recent.length - 1] in D.DETAIL_NAMES_HE) {
      const name = D.DETAIL_NAMES_HE[recent[recent.length - 1]];
      see("training_rut", 64, "נתקעת על אותו אימון",
        `שלושה חודשים של ${name}. ככל שתכונה מתרחקת מהשאר, כל נקודה נעשית `
        + "יקרה יותר — ובמקביל חורים נפערים במקום אחר. תחליף מיקוד לכמה שבועות.",
        null, 20);
    }
  }

  if (me.contract.yearsLeft <= 1 && club && ["player", "veteran"].includes(game.stage)) {
    see("contract", 68, "החוזה שלך נגמר",
      "שנה אחת נשארה. מכאן והלאה כל מועדון יכול לדבר איתך בחינם, וגם "
      + "המועדון שלך יודע את זה. או שאתה מחדש עכשיו מעמדת כוח, או שאתה "
      + "מחכה ומהמר.", null, 30);
  }

  const chasers = watchers(game, SCOUT_COURTED);
  if (chasers.length) {
    const country = clubCountry(chasers[0][0].cid);
    see("suitor", 60, `${chasers[0][0].name} רציניים לגביך`,
      `הם עוקבים אחריך כבר תקופה${country !== "ישראל" ? " מ" + country : ""}. `
      + "זה לא אומר לעזוב — זה אומר שיש לך קלף. תמשיך לשחק ככה, והם יגיעו "
      + "עם הצעה בחלון.", null, 22);
  }

  if (me.age >= 31 && me.badges === 0) {
    see("after", 50, "תתחיל לחשוב על מה שאחרי",
      "בגיל שלך כל עונה היא בונוס. תעודות אימון היום שוות שנים של קריירה "
      + "שנייה. זה לא במקום לשחק — זה במקביל.", "badges", 40);
  }

  if (me.morale < 35) {
    see("morale", 72,
      ["הראש שלך לא שם", "אתה עדיין למטה"],
      [`מורל ${Math.round(me.morale)}. זה לא רק הרגשה — זה מוריד לך את קצב `
       + "ההתפתחות באימונים בעשרות אחוזים. משחק אחד טוב הופך את זה.",
       `מורל ${Math.round(me.morale)} כבר תקופה. אתה מפסיד התפתחות בכל שבוע `
       + "שאתה נשאר שם. תתחיל ממשהו קטן שאתה יודע לעשות טוב."],
      null, 16);
  }

  return out;
}

/** הטיפ הבא — הדחוף ביותר שעוד לא נאמר לאחרונה. null כשאין מה לחדש. */
function mentorAdvise(game, rng = null) {
  rng = rng || game.rng;
  const fresh = mentorObservations(game).filter(row =>
    !row.exhausted && !saidRecently(game, row.key, row.cooldown));
  if (!fresh.length) return null;
  fresh.sort((a, b) => b.urgency - a.urgency);
  const top = fresh[0].urgency;
  const pool = fresh.filter(row => row.urgency >= top - 8);
  const chosen = rng.choice(pool);
  markSaid(game, chosen.key);

  const [, name, blurb, openers] = mentorOf(game);
  return {
    mentor: name, blurb,
    opener: openers[mentorHash(chosen.key) % openers.length],
    title: chosen.title, body: chosen.body,
    action: chosen.action, urgency: chosen.urgency,
  };
}

function mentorLines(game, rng = null) {
  const tip = mentorAdvise(game, rng);
  if (!tip) return [];
  const lines = [`${tip.mentor}: "${tip.opener} ${tip.title}."`, tip.body];
  if (tip.action && tip.action in D.DETAIL_NAMES_HE)
    lines.push(`→ מומלץ להתאמן השבוע על ${D.DETAIL_NAMES_HE[tip.action]}.`);
  return lines;
}

/** כל מה שהמנטור רואה עכשיו — למסך שלו. */
function mentorBoard(game) {
  const [, name, blurb] = mentorOf(game);
  const rows = mentorObservations(game).slice().sort((a, b) => b.urgency - a.urgency);
  return {
    name, blurb,
    items: rows.map(row => ({
      title: row.title, body: row.body, action: row.action,
      urgency: Math.round(row.urgency),
      said: saidRecently(game, row.key, row.cooldown),
    })),
    needs: rankedNeeds(game, 5),
  };
}
