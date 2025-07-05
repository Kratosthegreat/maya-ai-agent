# ... (הקוד שלך עד פה לא משתנה)

# === מילון תרגום ערים נפוצות ===
HEB_ENG_CITIES = {
    "בואנוס איירס": "Buenos Aires",
    "ניו יורק": "New York",
    "לוס אנג'לס": "Los Angeles",
    "ברלין": "Berlin",
    "פריז": "Paris",
    "לונדון": "London",
    "בלגיה": "Belgium",
    "בולגריה": "Bulgaria",
    "בוניה": "Bunia",
    "יוהנסבורג": "Johannesburg",
    "רומא": "Rome",
    "מדריד": "Madrid",
    "אמסטרדם": "Amsterdam",
    "מוסקבה": "Moscow",
    "טוקיו": "Tokyo",
    "בייג'ינג": "Beijing",
    # תוכל להוסיף למילון עוד שמות לפי הצורך
}

def city_to_english(city_hebrew: str) -> str:
    return HEB_ENG_CITIES.get(city_hebrew.strip(), city_hebrew)

# === WEATHER SERVICE ===
class GlobalWeatherService:
    def extract_location(self, text: str) -> str:
        text = text.replace("מזג אוויר", "").replace("טמפרטורה", "")
        text = text.replace("ב", "").replace("של", "").replace("את", "")
        text = text.strip()
        if not text or len(text) < 2:
            return "תל אביב"
        return text

    def get_weather_anywhere(self, location: str) -> str:
        # שלב 1: תרגום שם עיר אם צריך
        location_translated = city_to_english(location)
        try:
            # Geocoding
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_translated}&count=1&language=he&format=json"
            geo_response = requests.get(geocoding_url, timeout=5)
            geo_data = geo_response.json()

            if not geo_data.get('results'):
                # נסה פעם שניה באנגלית אם המשתמש כתב בעברית ולא הצליח
                if location != location_translated:
                    # כבר ניסינו תרגום, נחזיר הודעה למשתמש
                    return f"לא מצאתי את '{location}' (ניסיתי גם '{location_translated}'). נסה לכתוב את שם העיר באנגלית, או נסה עיר גדולה אחרת 🌍"
                else:
                    return f"לא מצאתי את '{location}'. נסה לכתוב את שם העיר באנגלית, או נסה עיר גדולה אחרת 🌍"

            result = geo_data['results'][0]
            lat = result['latitude']
            lon = result['longitude']
            place_name = result['name']
            country = result.get('country', '')

            # Weather
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            weather_response = requests.get(weather_url, timeout=5)
            weather_data = weather_response.json()

            current = weather_data['current_weather']
            temp = current['temperature']
            windspeed = current['windspeed']

            if temp > 30:
                temp_emoji = "🔥"
            elif temp > 20:
                temp_emoji = "☀️"
            elif temp > 10:
                temp_emoji = "🌤️"
            elif temp > 0:
                temp_emoji = "☁️"
            else:
                temp_emoji = "❄️"

            location_display = place_name
            if country and country != place_name:
                location_display += f", {country}"

            return f"{temp_emoji} {location_display}: {temp}°C (רוח {windspeed} קמ\"ש)"

        except Exception as e:
            logger.error(f"Weather error: {e}")
            return f"בעיה בקבלת מזג אוויר עבור {location} 🌍"

# ... (המשך הקוד שלך כרגיל)
