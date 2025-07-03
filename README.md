# 🤖 Maya Secretary Bot

מאיה - מזכירה אישית חכמה בטלגרם עם בינה מלאכותית מתקדמת, זיכרון משתמש וכלים שימושיים.

## ✨ תכונות

- 🧠 **זיכרון חכם** - זוכרת פרטים חשובים על כל משתמש
- 🤖 **AI מתקדם** - מבוסס על Google Gemini
- 🌤️ **מזג אוויר** - מידע מדויק לכל העיר
- 📊 **סטטיסטיקות** - מעקב אחר שימוש
- 🔒 **אבטחה** - הצפנת נתונים ומגבלות קצב
- 💾 **דטאבייס** - PostgreSQL לייצוב מלא
- 🚀 **מוכן לפרודקשן** - מותאם לRender

## 🛠️ התקנה מהירה

### 1. הכן את הסביבה

```bash
git clone https://github.com/yourusername/maya-secretary-bot.git
cd maya-secretary-bot
pip install -r requirements.txt
```

### 2. הגדר משתני סביבה

```bash
cp .env.example .env
# ערוך את .env עם הנתונים שלך
```

### 3. הרץ מקומית

```bash
python app.py
```

## 🌐 פריסה ב-Render

### שלב 1: הכנת הקוד
1. העלה את הקוד ל-GitHub
2. וודא שכל הקבצים נמצאים במקום

### שלב 2: יצירת שירותים ב-Render

#### Web Service:
- **Repository**: הריפו שלך ב-GitHub
- **Name**: `maya-secretary-bot`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app`

#### Database:
- **Type**: PostgreSQL
- **Name**: `maya-db`
- **Plan**: Free

### שלב 3: משתני סביבה ב-Render

הגדר את המשתנים הבאים ב-Dashboard:

```bash
TELEGRAM_TOKEN=your_bot_token_from_botfather
GEMINI_API_KEY=your_gemini_api_key
WEBHOOK_URL=https://your-app-name.onrender.com/webhook
DATABASE_URL=postgresql://... (Render יספק)
SECRET_KEY=your_secret_key_32_chars
ENCRYPTION_KEY=your_encryption_key_32_chars
ENVIRONMENT=production
DEBUG=false
```

### שלב 4: Deploy!
לחץ על "Deploy" ב-Render והמתן 2-3 דקות.

## 📱 פקודות הבוט

### פקודות בסיסיות:
- `/start` - התחלת העבודה
- `/help` - רשימת פקודות
- `/memory` - מה שמאיה זוכרת עליך
- `/stats` - סטטיסטיקות שימוש
- `/forget` - מחיקת זיכרון

### פקודות מתקדמות:
- `/weather [עיר]` - מזג אוויר
- `מה השעה?` - זמן נוכחי
- `איך מרגיש?` - שיחה כללית

### דוגמאות שימוש:
```
👤 משתמש: מה מזג האוויר בתל אביב?
🤖 מאיה: 🌤️ מזג האוויר בתל אביב:
🌡️ 25°C
💨 רוח: 10 קמ"ש

👤 משתמש: תזכירי לי להתקשר לדני מחר
🤖 מאיה: בוודאי! רשמתי שאתה צריך להתקשר לדני מחר. אזכיר לך כשתחזור לשוחח איתי.
```

## 🏗️ מבנה הפרויקט

```
maya-secretary-bot/
├── app.py                 # הקוד הראשי
├── config.py             # הגדרות המערכת
├── requirements.txt      # תלויות Python
├── set_webhook.py        # הגדרת webhook
├── runtime.txt           # גרסת Python
├── render.yaml           # הגדרת Render
├── .env.example         # תבנית משתני סביבה
├── README.md            # המדריך הזה
└── utils/
    └── lang_detect.py   # כלי עזר
```

## 🔧 פתרון בעיות

### הבוט לא מגיב?
1. **בדוק לוגים** ב-Render Dashboard
2. **וודא webhook** - `python set_webhook.py info`
3. **בדוק טוקנים** - כל המשתנים מוגדרים?

### שגיאות דטאבייס?
1. **חיבור לDB** - `DATABASE_URL` נכון?
2. **טבלאות** - צריך לראות "Database tables created"

### שגיאות AI?
1. **Gemini API** - המפתח תקף?
2. **Quota** - לא חרגת מהמכסה?

## 🔒 אבטחה

### הגדרות אבטחה:
- ✅ הצפנת נתונים רגישים
- ✅ Rate limiting (30 בקשות/דקה)
- ✅ Validation של inputs
- ✅ משתני סביבה בטוחים
- ✅ לוגים בטוחים

### גיבוי נתונים:
```bash
# גיבוי ידני של הדטאבייס
pg_dump $DATABASE_URL > backup.sql
```

## 📊 ניטור

### בדיקות תקינות:
- `GET /` - health check
- `GET /stats` - סטטיסטיקות API
- `POST /set_webhook` - הגדרת webhook

### מטריקות חשובות:
- זמן תגובה < 2 שניות
- זמינות > 99%
- שגיאות < 1%

## 🚀 שדרוגים עתידיים

### בתוכנית:
- [ ] אינטגרצ
