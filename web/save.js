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
