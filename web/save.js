// ---------------------------------------------------------------------------
// דחיסת שמורות.
//
// שמורה מלאה היא כ-1.5MB של JSON — יותר ממה שדפדפנים בטלפון מוכנים
// לשמור, ובלי דחיסה השמירה נכשלת בשקט והקריירה הולכת לאיבוד.
// כאן דוחסים ב-LZW על בייטים ומקודדים ל-base64: כשליש מהגודל,
// סינכרוני לגמרי, ובלי לאבד ולו סיבית אחת.
//
// הדחיסה חייבת להיות מדויקת: מצב ההגרלה ומוני ההתפתחות מזינים את
// הסימולציה, ולכן עיגול מספרים — מפתה ככל שיהיה — היה משנה בשקט את
// העתיד של הקריירה בכל טעינה.
// ---------------------------------------------------------------------------

const SAVE_FORMAT = 2;
const SAVE_PREFIX = "fm2:";

/** LZW על בייטים: כל ליטרל 0-255, המילון מתחיל ב-256 ונעצר ב-65536. */
function lzwEncode(bytes) {
  const dict = new Map();
  let next = 256, prev = -1;
  const codes = [];
  for (let i = 0; i < bytes.length; i++) {
    const byte = bytes[i];
    if (prev === -1) { prev = byte; continue; }
    const key = prev * 256 + byte;
    const known = dict.get(key);
    if (known !== undefined) { prev = known; continue; }
    codes.push(prev);
    if (next < 65536) dict.set(key, next++);
    prev = byte;
  }
  if (prev !== -1) codes.push(prev);
  return codes;
}

function lzwDecode(codes) {
  if (!codes.length) return new Uint8Array(0);
  // כל ערך במילון הוא (קוד קודם, בייט אחרון) — משחזרים אחורה
  const prevOf = new Int32Array(65536);
  const lastOf = new Uint8Array(65536);
  let next = 256;

  const out = [];
  const expand = code => {
    const stack = [];
    while (code >= 256) { stack.push(lastOf[code]); code = prevOf[code]; }
    stack.push(code);
    for (let i = stack.length - 1; i >= 0; i--) out.push(stack[i]);
    return code;              // הבייט הראשון של הרצף
  };

  let prev = codes[0];
  expand(prev);
  for (let i = 1; i < codes.length; i++) {
    const code = codes[i];
    let first;
    if (code < next) {
      first = code < 256 ? code : firstByteOf(code, prevOf, lastOf);
      expand(code);
    } else {
      // המקרה הקלאסי: הקוד נוצר בדיוק עכשיו
      first = prev < 256 ? prev : firstByteOf(prev, prevOf, lastOf);
      expand(prev);
      out.push(first);
    }
    if (next < 65536) { prevOf[next] = prev; lastOf[next] = first; next++; }
    prev = code;
  }
  return Uint8Array.from(out);
}

function firstByteOf(code, prevOf, lastOf) {
  while (code >= 256) code = prevOf[code];
  return code;
}

/** קודים → base64. עובד גם על מערכים ענקיים (בלי stack overflow). */
function codesToBase64(codes) {
  const bytes = new Uint8Array(codes.length * 2);
  for (let i = 0; i < codes.length; i++) {
    bytes[i * 2] = codes[i] >> 8;
    bytes[i * 2 + 1] = codes[i] & 255;
  }
  let binary = "";
  const CHUNK = 8192;
  for (let i = 0; i < bytes.length; i += CHUNK)
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
  return btoa(binary);
}

function base64ToCodes(text) {
  const binary = atob(text);
  const codes = new Array(binary.length >> 1);
  for (let i = 0; i < codes.length; i++)
    codes[i] = (binary.charCodeAt(i * 2) << 8) | binary.charCodeAt(i * 2 + 1);
  return codes;
}

/** מצב משחק → מחרוזת דחוסה. */
function packSave(state) {
  const json = JSON.stringify(state);
  const bytes = new TextEncoder().encode(json);
  return SAVE_PREFIX + codesToBase64(lzwEncode(bytes));
}

/**
 * מצב משחק → בייטים דחוסים, בלי base64.
 *
 * base64 מנפח ב-33%, ו-localStorage מאחסן ב-UTF-16 ולכן מכפיל שוב:
 * שמורה של מגה־בייט הופכת שם לשלושה. IndexedDB מקבל בייטים כמו שהם,
 * ולכן זו הדרך היחידה שבה שמירה אוטומטית של קריירה מלאה נכנסת בנוחות.
 */
function packSaveBytes(state) {
  const json = JSON.stringify(state);
  const codes = lzwEncode(new TextEncoder().encode(json));
  const out = new Uint8Array(codes.length * 2);
  for (let i = 0; i < codes.length; i++) {
    out[i * 2] = codes[i] >> 8;
    out[i * 2 + 1] = codes[i] & 255;
  }
  return out;
}

function unpackSaveBytes(bytes) {
  if (!bytes || !bytes.length) return null;
  const view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  const codes = new Array(view.length >> 1);
  for (let i = 0; i < codes.length; i++)
    codes[i] = (view[i * 2] << 8) | view[i * 2 + 1];
  return JSON.parse(new TextDecoder().decode(lzwDecode(codes)));
}

/** מחרוזת → מצב משחק. מקבל גם שמורות ישנות שנשמרו כ-JSON גולמי. */
function unpackSave(text) {
  if (!text) return null;
  if (text.startsWith(SAVE_PREFIX)) {
    const bytes = lzwDecode(base64ToCodes(text.slice(SAVE_PREFIX.length)));
    return JSON.parse(new TextDecoder().decode(bytes));
  }
  return JSON.parse(text);       // פורמט 1 — שמורה שנוצרה לפני הדחיסה
}


// ---------------------------------------------------------------------------
// אחסון השמורה — אוטומטי, בלי קבצים
//
// עד עכשיו השמורה ישבה ב-localStorage כ-base64. שתי בעיות: base64
// מנפח ב-33%, ו-localStorage סופר UTF-16 ולכן מכפיל שוב — קריירה של
// מגה־בייט וחצי תפסה שם שלושה מגה מתוך מכסה של חמישה. ברגע שהמכסה
// נגמרת השמירה נכשלת, ואז נשארים רק קבצים.
//
// IndexedDB פותר את שניהם: בייטים כמו שהם, ומכסה של מאות מגה־בייטים.
// localStorage נשאר כרשת ביטחון לדפדפנים שחוסמים IndexedDB.
// ---------------------------------------------------------------------------

const SAVE_DB = "fm_saves";
const SAVE_STORE = "careers";
const SLOT_AUTO = "auto";
const CHECKPOINT_LIMIT = 5;

function saveDbOpen() {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") { reject(new Error("no idb")); return; }
    const request = indexedDB.open(SAVE_DB, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(SAVE_STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function saveDbRun(mode, action) {
  return saveDbOpen().then(db => new Promise((resolve, reject) => {
    const tx = db.transaction(SAVE_STORE, mode);
    const request = action(tx.objectStore(SAVE_STORE));
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  }));
}

/** שומר תא. הערך כולל מטא־דאטה כדי שמסך השמירה יידע מה יש בו. */
function putSlot(slot, bytes, meta) {
  return saveDbRun("readwrite", store =>
    store.put({ bytes, meta, at: Date.now() }, slot));
}

function getSlot(slot) {
  return saveDbRun("readonly", store => store.get(slot)).catch(() => null);
}

function deleteSlot(slot) {
  return saveDbRun("readwrite", store => store.delete(slot)).catch(() => null);
}

function listSlots() {
  return saveDbOpen().then(db => new Promise((resolve, reject) => {
    const tx = db.transaction(SAVE_STORE, "readonly");
    const store = tx.objectStore(SAVE_STORE);
    const keys = store.getAllKeys();
    const values = store.getAll();
    tx.oncomplete = () => resolve(keys.result.map((key, index) => ({
      slot: key, at: values.result[index] ? values.result[index].at : 0,
      meta: values.result[index] ? values.result[index].meta : null,
      size: values.result[index] && values.result[index].bytes
        ? values.result[index].bytes.length : 0,
    })));
    tx.onerror = () => reject(tx.error);
  })).catch(() => []);
}

/**
 * תור כתיבה: השמירה נקראת אחרי כל פעולה, ו-IndexedDB אסינכרוני.
 * במקום להריץ עשרים כתיבות במקביל שומרים תמיד את האחרונה בלבד.
 */
let savePending = null;
let saveWriting = false;
let saveOnDone = null;

function queueSave(bytes, meta, onDone) {
  savePending = { bytes, meta };
  saveOnDone = onDone || saveOnDone;
  if (saveWriting) return;
  saveWriting = true;
  const flush = () => {
    const job = savePending;
    savePending = null;
    if (!job) { saveWriting = false; return; }
    putSlot(SLOT_AUTO, job.bytes, job.meta)
      .then(() => { if (saveOnDone) saveOnDone(true, ""); })
      .catch(err => {
        if (saveOnDone) saveOnDone(false, describeSaveError(err));
      })
      .then(flush, flush);
  };
  flush();
}

function describeSaveError(err) {
  const name = err && err.name;
  if (name === "QuotaExceededError" || name === "NS_ERROR_DOM_QUOTA_REACHED")
    return "נגמר המקום הפנוי בדפדפן. אפשר למחוק נקודות שחזור ישנות.";
  return "הדפדפן חוסם אחסון בעמוד הזה — נסה לצאת ממצב גלישה פרטית.";
}

/** נקודת שחזור אוטומטית לתחילת עונה, עם גלגול של הישנות. */
function saveCheckpoint(bytes, meta) {
  const slot = `cp_${meta.year}_${String(meta.week).padStart(2, "0")}`;
  return putSlot(slot, bytes, meta)
    .then(() => listSlots())
    .then(rows => {
      const points = rows.filter(row => row.slot.startsWith("cp_"))
        .sort((a, b) => b.at - a.at);
      return Promise.all(points.slice(CHECKPOINT_LIMIT)
        .map(row => deleteSlot(row.slot)));
    })
    .catch(() => null);
}

/** כמה מקום השמורות תופסות, ומה הדפדפן מרשה. */
function storageEstimate() {
  if (typeof navigator === "undefined" || !navigator.storage
      || !navigator.storage.estimate) return Promise.resolve(null);
  return navigator.storage.estimate()
    .then(info => ({ used: info.usage || 0, quota: info.quota || 0 }))
    .catch(() => null);
}


// ---------------------------------------------------------------------------
// קובץ שמירה קבוע
//
// גיבוי שיוצר קובץ חדש בכל לחיצה הוא לא גיבוי — זו ערימה. דפדפנים
// מודרניים מאפשרים לבחור קובץ פעם אחת ולכתוב אליו שוב ושוב, בלי
// דיאלוג ובלי כפילויות. המזהה של הקובץ נשמר ב-IndexedDB כדי שהחיבור
// ישרוד גם סגירה של הדף.
// ---------------------------------------------------------------------------

const FILE_DB = "fm_save_files";
const FILE_STORE = "handles";
const FILE_KEY = "career";
const SAVE_FILENAME = "fm-career.txt";

/** האם הדפדפן יודע לכתוב חזרה לקובץ שהמשתמש בחר. */
function fileSaveSupported() {
  return typeof window !== "undefined" && typeof window.showSaveFilePicker === "function";
}

function idbOpen() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(FILE_DB, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(FILE_STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function idbRun(mode, action) {
  return idbOpen().then(db => new Promise((resolve, reject) => {
    const tx = db.transaction(FILE_STORE, mode);
    const request = action(tx.objectStore(FILE_STORE));
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  })).catch(() => null);
}

const rememberSaveHandle = handle => idbRun("readwrite", store => store.put(handle, FILE_KEY));
const storedSaveHandle = () => idbRun("readonly", store => store.get(FILE_KEY));
const forgetSaveHandle = () => idbRun("readwrite", store => store.delete(FILE_KEY));

/**
 * מצב ההרשאה לקובץ: "granted" מוכן לכתיבה, "prompt" צריך לחיצה,
 * "denied" נחסם. request=true מבקש הרשאה — חייב לרוץ מתוך לחיצה.
 */
async function saveFilePermission(handle, request = false) {
  if (!handle || !handle.queryPermission) return "denied";
  const options = { mode: "readwrite" };
  try {
    let state = await handle.queryPermission(options);
    if (state !== "granted" && request) state = await handle.requestPermission(options);
    return state;
  } catch (err) { return "denied"; }
}

/** בוחר קובץ שמירה. מחזיר את המזהה, או null אם המשתמש ביטל. */
async function pickSaveFile() {
  try {
    const handle = await window.showSaveFilePicker({
      suggestedName: SAVE_FILENAME,
      types: [{ description: "שמורת קריירה", accept: { "text/plain": [".txt"] } }],
    });
    await rememberSaveHandle(handle);
    return handle;
  } catch (err) { return null; }     // המשתמש ביטל
}

/** כותב לקובץ הקיים — דורס אותו, לא יוצר חדש. */
async function writeSaveFile(handle, text) {
  const writable = await handle.createWritable();
  await writable.write(text);
  await writable.close();
}
