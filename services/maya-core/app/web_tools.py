import requests

def web_search(query: str) -> str:
    try:
        url = f"https://duckduckgo.com/?q={query}&format=json"
        r = requests.get(url, timeout=5)
        return r.text[:1500]
    except Exception as e:
        return f"שגיאה בחיפוש: {e}"
