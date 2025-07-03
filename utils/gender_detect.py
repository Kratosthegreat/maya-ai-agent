import re

def detect_gender(text: str) -> str:
    if re.search(r'\b(אני|שמי|קוראים לי|אני גרה|עובדת|כותבת)\b', text):
        return 'female'
    if re.search(r'\b(אני גר|עובד|כותב)\b', text):
        return 'male'
    return 'neutral'
