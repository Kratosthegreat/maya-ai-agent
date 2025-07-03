# Maya Secretary Bot

מזכירה אישית חכמה, בעברית, עם זיכרון משתמש, AI מתקדם, אבטחה, ותמיכה בפרודקשן.

## יכולות:
- אינטגרציה עם Telegram (python-telegram-bot 20+)
- זיכרון שיחה אישי לכל משתמש (DB)
- בינה מלאכותית (Google Gemini)
- זיהוי מגדר/שפה חכם
- ניהול משימות, מזג אוויר, סטטיסטיקות, עזרה, שכחת זיכרון, ועוד
- הצפנה ואבטחת מידע אישי
- CI/CD אוטומטי (GitHub Actions)
- Docker Ready + Render/Heroku Pipeline

## התקנה מהירה

```bash
git clone https://github.com/yourusername/maya-bot.git
cd maya-bot
cp .env.example .env
# מלאו ערכים רלוונטיים ב-.env
docker build -t maya-bot .
docker run --env-file .env -p 10000:10000 maya-bot
```

## פקודות בוט
• /start – התחלה  
• /help – עזרה  
• /memory – מה הבוט זוכר עליך  
• /weather [עיר] – מזג אוויר  
• /stats – סטטיסטיקות  
• /forget – שכח הכל  
• ועוד בשפה טבעית!

## בדיקות
```bash
pytest tests/
```

## פריסה ל-Render/Heroku
ראה render.yaml ודוקומנטציה באתר Render.
