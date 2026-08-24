// ---------------------------------------------------------------------------
// סצנות מאוירות לדפי המעבר. הכל SVG מחולל, בשני מצבי התצוגה.
// לכל אירוע עלילה יש סצנה משלו: חדר הלבשה, חדר טיפולים, אולם עיתונאים...
// ---------------------------------------------------------------------------

// כל סצנה היא תמונה מרונדרת שמוטבעת בקובץ (web/art/render.py מייצר אותה),
// ומעליה שכבת הצללה עדינה שמחברת אותה לצבעי הממשק.

function sceneImage(key, label) {
  const src = ART[key] || ART.stadium;
  return `<figure class="scene" role="img" aria-label="${escAttr(label)}">
    <img src="${src}" alt="" decoding="async">
    <span class="scene-tint"></span>
  </figure>`;
}

const SCENE_LABELS = {
  stadium: "אצטדיון בלילה",
  training: "מגרש אימונים",
  dressing: "חדר הלבשה",
  tunnel: "מנהרת השחקנים",
  physio: "חדר טיפולים",
  press: "מסיבת עיתונאים",
  boardroom: "חדר ישיבות",
  trophy: "ארון התארים",
  airport: "שדה תעופה",
  studio: "אולפן טלוויזיה",
  home: "בבית",
  youthpitch: "מגרש שכונתי",
};

const SCENES = {};
for (const key of Object.keys(SCENE_LABELS)) {
  SCENES[key] = () => sceneImage(key, SCENE_LABELS[key]);
}

function sceneDefs() { return ""; }

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
      <div class="pcard-art">${avatar(player, club, 104)}</div>
      <div class="pcard-kit">${shirt(club, player.number || 0, 52)}</div>
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
