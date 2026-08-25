// ---------------------------------------------------------------------------
// מסלול הפיתוח — תאום JS של development.py
//
// במקום "תתאמן על משהו", המסלול אומר בדיוק מה צריך להיות לך ומתי,
// ומה תקבל אם תגיע לשם. מי שמשלים את כל המסלול עובר פריצה אמיתית.
// ---------------------------------------------------------------------------

const ARCHETYPE_BY_KEY = {};
for (const row of D.ARCHETYPES) ARCHETYPE_BY_KEY[row[0]] = row;

function planOptionsFor(position) {
  const fits = D.ARCHETYPES.filter(row => row[2].includes(position));
  return fits.length ? fits : D.ARCHETYPES.slice();
}

function planKey(game) { return game.flags.plan || null; }
function planRow(game) {
  const key = planKey(game);
  return key ? (ARCHETYPE_BY_KEY[key] || null) : null;
}

function setPlan(game, key) {
  const row = ARCHETYPE_BY_KEY[key];
  if (!row) return "אין מסלול כזה.";
  const previous = planKey(game);
  game.flags.plan = key;
  if (previous && previous !== key) {
    game.flags.plan_done = [];
    return `עברת למסלול "${row[1]}". מה שהספקת במסלול הקודם לא נספר לך כאן — מתחילים מהתחלה.`;
  }
  if (!Array.isArray(game.flags.plan_done)) game.flags.plan_done = [];
  return `המסלול שלך: ${row[1]}. ${row[6]}`;
}

function planDone(game) {
  if (!Array.isArray(game.flags.plan_done)) game.flags.plan_done = [];
  return game.flags.plan_done;
}

/** כל אבני הדרך במסלול, עם המצב הנוכחי מול הדרישה. */
function milestoneRows(game) {
  const row = planRow(game);
  if (!row) return [];
  const me = game.me;
  const done = planDone(game);
  return row[4].map(([age, needs], index) => {
    const parts = [];
    let met = true;
    for (const attr of Object.keys(needs).sort()) {
      const have = me.attributes[attr] ?? 50;
      if (have < needs[attr]) met = false;
      parts.push({ attr, name: D.ATTRIBUTE_NAMES_HE[attr], have, need: needs[attr] });
    }
    return { index, age, needs: parts, met, claimed: done.includes(index),
             late: me.age > age && !met };
  });
}

/** המשפט שאומר לך מה לעשות עכשיו. זו ההכוונה שהייתה חסרה. */
function nextTarget(game) {
  const rows = milestoneRows(game);
  const row = planRow(game);
  if (!row || !rows.length) return null;
  const me = game.me;
  for (const entry of rows) {
    if (entry.claimed) continue;
    const gaps = entry.needs.filter(p => p.have < p.need);
    if (!gaps.length)
      return `🎯 עמדת בדרישות של גיל ${entry.age} — זה ייחתם בסוף העונה.`;
    let worst = gaps[0];
    for (const p of gaps) if (p.have - p.need < worst.have - worst.need) worst = p;
    const when = me.age <= entry.age ? `עד גיל ${entry.age}`
                                     : `(היעד של גיל ${entry.age} כבר מאחוריך)`;
    return `🎯 ${row[1]}: ${worst.name} ${worst.have} → ${worst.need} ${when}. `
           + `חסרות ${worst.need - worst.have} נקודות.`;
  }
  return `🎯 השלמת את כל מסלול "${row[1]}".`;
}

/** על מה כדאי להתאמן השבוע כדי להתקדם במסלול. */
function recommendedFocus(game) {
  for (const entry of milestoneRows(game)) {
    if (entry.claimed) continue;
    const gaps = entry.needs.filter(p => p.have < p.need);
    if (gaps.length) {
      let worst = gaps[0];
      for (const p of gaps) if (p.have - p.need < worst.have - worst.need) worst = p;
      return worst.attr;
    }
  }
  const row = planRow(game);
  return row ? row[3][0][0] : null;
}

/** נקרא בסוף עונה: חותם על מה שהושג ומחלק את הפרסים. */
function claimMilestones(game) {
  const row = planRow(game);
  if (!row) return [];
  const me = game.me;
  const done = planDone(game);
  const lines = [];
  const reward = D.MILESTONE_REWARD;

  for (const entry of milestoneRows(game)) {
    if (entry.claimed || !entry.met) continue;
    const onTime = me.age <= entry.age;
    done.push(entry.index);
    const scale = onTime ? 1.0 : 0.45;
    me.potential = clamp(me.potential + reward.potential * scale, 0, me.ceiling);
    gainReputation(me, reward.rep * scale);
    me.morale = clamp(me.morale + reward.morale * scale, 5, 99);
    const club = game.myClub();
    if (club) club.managerTrust = clamp(club.managerTrust + reward.trust * scale, 0, 100);
    lines.push(`✅ אבן דרך במסלול "${row[1]}" (גיל ${entry.age}) — `
               + (onTime ? "בזמן" : "באיחור") + ".");
  }

  if (done.length >= row[4].length && !game.flag("breakthrough"))
    lines.push(...planBreakthrough(game, row));
  return lines;
}

/** הרגע שבו מפסיקים לקרוא לך כישרון. */
function planBreakthrough(game, row) {
  const me = game.me;
  game.setFlag("breakthrough", true);
  me.potential = clamp(me.potential + 6, 0, me.ceiling);
  gainReputation(me, 7);
  me.morale = clamp(me.morale + 14, 5, 99);
  const lines = [`💎 פריצה. השלמת את מסלול "${row[1]}" במלואו.`, `   ${row[6]}`];
  const trait = row[5];
  if (trait && !me.traits.includes(trait)) {
    me.traits.push(trait);
    lines.push(`   נוספה לך תכונת אופי: ${D.TRAITS[trait].name}.`);
  }
  lines.push("   מהיום מסתכלים עליך אחרת — בתוך המועדון וגם מחוצה לו.");
  const club = game.myClub();
  if (club) {
    club.managerTrust = clamp(club.managerTrust + 12, 0, 100);
    club.fanSupport = clamp(club.fanSupport + 6, 0, 100);
  }
  return lines;
}

function planSummary(game) {
  const row = planRow(game);
  if (!row) {
    return { chosen: false, options: planOptionsFor(game.me.position).map(r => ({
      key: r[0], name: r[1], desc: r[6],
      attrs: r[3].map(([a]) => D.ATTRIBUTE_NAMES_HE[a]) })) };
  }
  const rows = milestoneRows(game);
  return {
    chosen: true, key: row[0], name: row[1], desc: row[6],
    trait: D.TRAITS[row[5]].name, milestones: rows,
    done: rows.filter(r => r.claimed).length, total: rows.length,
    next: nextTarget(game), focus: recommendedFocus(game),
    breakthrough: !!game.flag("breakthrough"),
  };
}
