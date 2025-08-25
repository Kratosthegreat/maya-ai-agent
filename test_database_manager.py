import sys
import types


def test_fallback_resets_task_collections():
    # main.py requires 'intelligent_maya' which isn't available in tests.
    # Provide a lightweight stub so we can import DatabaseManager without
    # pulling in the full dependency graph.
    dummy = types.ModuleType("intelligent_maya")
    dummy.IntelligentMayaAgent = object
    dummy.init_intelligent_maya = lambda *args, **kwargs: None
    dummy.intelligent_maya = None
    dummy.smart_response = None
    sys.modules.setdefault("intelligent_maya", dummy)

    from main import DatabaseManager

    db = DatabaseManager()
    # Simulate that the database was previously connected and holds
    # task-related state
    db.tasks = {"dummy": {"id": "1"}}
    db.tasks_collection = object()

    # Trigger fallback to in-memory storage
    db._setup_fallback_storage()

    assert db.tasks == {}
    assert db.tasks_collection is None
