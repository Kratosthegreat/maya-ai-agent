import pytest
from main import (
    validate_user_input, extract_keywords,
    DatabaseManager, TaskManager, MayaAI, MayaBot
)

def test_validate_user_input_good():
    assert validate_user_input("שלום עולם") is True

def test_validate_user_input_long():
    assert validate_user_input("א" * 5000) is False

def test_validate_user_input_dangerous():
    assert validate_user_input("<script>alert(1)</script>") is False

def test_extract_keywords():
    text = "שלום אני רוצה לקבוע פגישה דחופה"
    kw = extract_keywords(text)
    assert "פגישה" in kw

def test_database_manager_memory():
    db = DatabaseManager()
    assert db.users is not None
    assert db.log_conversation(1, "msg", "resp")

def test_register_user():
    db = DatabaseManager()
    user = {"user_id": 123, "username": "maya"}
    assert db.register_user(user)

def test_log_conversation():
    db = DatabaseManager()
    assert db.log_conversation(123, "הודעה", "תגובה")

def test_get_user_context():
    db = DatabaseManager()
    db.log_conversation(1, "msg", "resp")
    ctx = db.get_user_context(1)
    assert isinstance(ctx, list)

def test_save_task_and_get():
    db = DatabaseManager()
    task = {"id": "t1", "user_id": 1, "title": "בדיקה"}
    assert db.save_task(task)
    assert db.get_user_tasks(1) != []

def test_task_manager_intent():
    db = DatabaseManager()
    tm = TaskManager(db)
    result = tm.analyze_user_intent("תזכור לי דוח דחוף")
    assert result is not None

def test_task_manager_extract_details():
    db = DatabaseManager()
    tm = TaskManager(db)
    details = tm.extract_task_details("תקבע פגישה מחר")
    assert isinstance(details, dict)
    assert "title" in details

def test_task_manager_save_and_complete():
    db = DatabaseManager()
    tm = TaskManager(db)
    details = tm.extract_task_details("תזכור לי לעשות משהו")
    details['user_id'] = 1
    task_id = tm._save_task(details)
    assert task_id is not None
    assert tm.complete_task(task_id, 1)

def test_maya_ai_response_fallback():
    ai = MayaAI()
    text = ai._fallback_response("שלום")
    assert "מאיה" in text

def test_maya_bot_init():
    bot = MayaBot()
    assert bot.db is not None
    assert bot.ai is not None
