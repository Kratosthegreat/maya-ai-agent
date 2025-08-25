import sys
import importlib
import builtins


def test_main_import_without_intelligent_maya(monkeypatch):
    # Ensure 'intelligent_maya' is not importable
    sys.modules.pop('intelligent_maya', None)
    sys.modules.pop('main', None)

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == 'intelligent_maya':
            raise ModuleNotFoundError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fake_import)

    main = importlib.import_module('main')
    assert main.INTELLIGENT_MAYA_AVAILABLE is False
    bot = main.MayaBot()
    assert bot.intelligent_agent is None
