# 🤖 Maya - Advanced AI Telegram Bot

**Maya** היא בוט טלגרם חכם ומתקדם המבוסס על בינה מלאכותית של Google Gemini, עם תמיכה מלאה בעברית ויכולות אוטונומיות מתקדמות.

## ✨ תכונות עיקריות

### 🧠 בינה מלאכותית מתקדמת
- **Google Gemini Pro**: מודל AI חדיש עם יכולות שיחה טבעיות
- **IntelligentMayaAgent**: מנוע AI חכם עם הבנה מהקשרית מתקדמת
- **זיכרון הקשרי**: זוכרת שיחות קודמות ומתאמת תשובות
- **אינטליגנציה רגשית**: מזהה ומגיבה למצבים רגשיים
- **למידה אישית**: מתאמת את האופי לכל משתמש
- **תמיכה בעברית**: מבינה ומגיבה בעברית טבעית ושוטפת
- **חיבור ישיר ל-Gemini**: כל הודעה מעובדת דרך Gemini API
- **Fallback Intelligence**: מערכת גיבוי מתקדמת למקרי תקלה

### 💬 ניהול שיחות חכם
- **ממשק אינטואיטיבי**: תפריטים ידידותיים עם כפתורים
- **מצבי שיחה**: מעבר חלק בין סוגי אינטראקציה שונים
- **היסטוריית שיחות**: שמירה ומעקב אחר כל השיחות
- **תגובות מהירות**: זמן תגובה מתחת ל-2 שניות

### 📊 ניהול נתונים מתקדם
- **MongoDB Integration**: מסד נתונים מקצועי עם גיבויים
- **סטטיסטיקות מתקדמות**: מעקב אחר שימוש והתנהגות משתמשים
- **Fallback Storage**: פעולה גם ללא מסד נתונים חיצוני
- **אבטחת מידע**: הצפנה ואבטחה מתקדמת

### 🚀 תשתית ענן מתקדמת
- **Render.com Ready**: קל לפריסה ולתחזוקה
- **Keep-Alive System**: זמינות 24/7 עם UptimeRobot
- **Docker Support**: קונטיינרים מוכנים לייצור
- **Auto-scaling**: התאמה אוטומטית לעומס

## 🛠️ התקנה והגדרה

### שלב 1: הכנות ראשוניות

1. **יצירת בוט ב-Telegram**:
   - שלח `/newbot` ל-@BotFather
   - בחר שם ושם משתמש לבוט
   - שמור את הטוקן שתקבל

2. **קבלת מפתח Gemini AI**:
   - לך ל-[Google AI Studio](https://makersuite.google.com/app/apikey)
   - צור מפתח API חדש
   - שמור את המפתח

3. **הגדרת MongoDB Atlas** (אופציונלי אך מומלץ):
   - הירשם ל-[MongoDB Atlas](https://cloud.mongodb.com)
   - צור Cluster חינמי
   - קבל את connection string

### שלב 2: הגדרת הפרויקט

```bash
# שכפול המאגר
git clone <repository-url>
cd maya-ai-bot

# יצירת קובץ הגדרות
cp .env.example .env

# עריכת הגדרות
nano .env
```

**מלא את הפרטים הבאים ב-`.env`**:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
MONGO_URI=your_mongodb_uri_here
ADMIN_ID=your_telegram_user_id
```

### שלב 3: פריסה ל-Render.com

1. **העלאה ל-GitHub**:
   ```bash
   git add .
   git commit -m "Initial Maya bot setup"
   git push origin main
   ```

2. **יצירת שירות ב-Render**:
   - הירשם ל-[Render.com](https://render.com)
   - צור Web Service חדש
   - חבר את המאגר שלך
   - Render יזהה את `render.yaml` אוטומטית

3. **הוספת Secrets**:
   - לך ל-Environment בעמוד השירות
   - הוסף את המשתנים הרגישים:
     - `TELEGRAM_BOT_TOKEN`
     - `GEMINI_API_KEY`
     - `MONGO_URI`
     - `ADMIN_ID`

4. **הגדרת Keep-Alive**:
   - הירשם ל-[UptimeRobot](https://uptimerobot.com)
   - צור monitor חדש עם URL של השירות
   - הגדר בדיקה כל 5 דקות

### 🚀 הפעלה מקומית (Quick Start)

לאחר הגדרת משתני הסביבה, ניתן להפעיל את הבוט בקלות:

```bash
# הפעלה עם בדיקות
python3 test_maya_integration.py

# הפעלה רגילה
python3 start_maya.py

# או ישירות
python3 main.py
```

הבוט יבדוק אוטומטית את משתני הסביבה ויפעיל את המנוע החכם עם fallback מובנה.

## 📋 שימוש

### פקודות בסיסיות
- `/start` - התחלת עבודה עם הבוט
- `/help` - מדריך שימוש מפורט
- `/feedback` - שליחת משוב למפתחים

### פקודות מנהל
- `/admin_stats` - סטטיסטיקות מתקדמות
- `/broadcast` - שליחת הודעה לכל המשתמשים

### תכונות מתקדמות
- **שיחה טבעית**: שלח כל הודעה ומאיה תגיב בצורה חכמה
- **זיכרון הקשרי**: מאיה זוכרת את השיחה ומתייחסת להקשר
- **תפריטים אינטראקטיביים**: השתמש בכפתורים למעבר מהיר

## 🏗️ ארכיטקטורה

```
Maya AI Bot
├── 🤖 Core Bot (Telegram Integration)
├── 🧠 AI Engine (Google Gemini)
├── 💾 Database Manager (MongoDB)
├── 🌐 Keep-Alive Server (Flask)
├── 📊 Analytics & Stats
└── 👑 Admin Panel
```

### רכיבי המערכת:
- **MayaBot**: הבוט הראשי עם כל הhandlers
- **MayaAI**: מנוע הAI עם Gemini
- **DatabaseManager**: ניהול נתונים עם MongoDB
- **Flask Server**: שרת keep-alive לRender

## 🔧 פיתוח והתאמה

### הוספת תכונות חדשות
```python
# הוספת פקודה חדשה
async def my_new_command(self, update: Update, context):
    await update.message.reply_text("תכונה חדשה!")

# רישום הפקודה ב-main()
application.add_handler(CommandHandler("new", maya.my_new_command))
```

### התאמת אישיות מאיה
ערוך את `MAYA_PERSONALITY` ב-`main.py`:
```python
MAYA_PERSONALITY = """
אני מאיה, בוט AI חכם עם אישיות מותאמת...
"""
```

### הוספת יכולות AI חדשות
```python
# הוספת מידע ספציפי לפרומפט
prompt = f"""
{MAYA_PERSONALITY}

מידע נוסף: {extra_context}
שאלת המשתמש: {message}
"""
```

## 📊 ניטור וביצועים

### מטריקות מומלצות למעקב:
- **זמן תגובה**: < 2 שניות ממוצע
- **זמינות**: > 99% uptime
- **דירוג משתמשים**: מעקב אחר שביעות רצון
- **שימוש בAI**: מעקב עלויות וביצועים

### לוגים וdiagnostics:
```bash
# צפייה בלוגים ב-Render
render logs -f

# בדיקת בריאות המערכת
curl https://your-bot.onrender.com/stats
```

## 🔒 אבטחה

### עקרונות אבטחה:
- ✅ אף פעם לא שמירת טוקנים בקוד
- ✅ שימוש ב-environment variables
- ✅ הגבלת גישה לפקודות מנהל
- ✅ ולידציה של כל קלט משתמש
- ✅ הצפנת נתונים רגישים

### מומלץ לביצוע:
- רוטציה תקופתית של מפתחות
- ניטור לוגים לפעילות חשודה
- עדכון תלויות באופן קבוע
- גיבויים תקופתיים של המסד נתונים

## 🚨 פתרון תקלות נפוצות

### הבוט לא מגיב
1. בדוק שהטוקן נכון ב-Environment Variables
2. ודא שהשירות ב-Render פועל
3. בדוק שUptimeRobot פעיל

### שגיאות AI
1. ודא שמפתח Gemini תקין
2. בדוק מכסת השימוש ב-Google AI Studio
3. בדוק את הלוגים לשגיאות ספציפיות

### בעיות מסד נתונים
1. ודא ש-MongoDB Atlas זמין
2. בדוק את ה-connection string
3. הבוט ימשיך לפעול גם ללא MongoDB

## 🤝 תרומה ופיתוח

### איך לתרום:
1. Fork את המאגר
2. צור branch חדש לתכונה
3. בצע שינויים ובדיקות
4. שלח Pull Request

### קווים מנחים:
- קוד ברור עם הערות בעברית
- בדיקות לכל תכונה חדשה
- עדכון התיעוד
- שמירה על תאימות לגרסאות קודמות

## 📞 תמיכה וקהילה

- **Issues**: דווח על בעיות ב-GitHub Issues
- **Discussions**: שאלות כלליות ב-GitHub Discussions
- **Discord**: [הצטרף לשרת הקהילה](link-to-discord)
- **Email**: support@maya-bot.com

## 📄 רישיון

פרויקט זה מופץ תחת רישיון MIT. ראה את קובץ `LICENSE` לפרטים מלאים.

## 🙏 תודות

- **Google AI**: על Gemini API המדהים
- **Python Telegram Bot**: על הספרייה המעולה
- **MongoDB**: על מסד הנתונים החינמי
- **Render.com**: על פלטפורמת הענן

---

**Maya AI Bot** - נבנה עם ❤️ עבור הקהילה הישראלית

*גרסה 2.0 | עודכן: 2025*
