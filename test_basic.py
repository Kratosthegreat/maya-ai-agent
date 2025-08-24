"""Basic tests for Maya AI Bot to verify the setup works correctly."""

def test_basic_functionality():
    """Test that basic Python functionality works."""
    assert 1 + 1 == 2

def test_imports():
    """Test that critical imports work."""
    try:
        import telegram
        import flask
        import requests
        import dotenv
        assert True
    except ImportError as e:
        assert False, f"Critical import failed: {e}"

def test_environment():
    """Test that Python environment is set up correctly."""
    import sys
    assert sys.version_info >= (3, 7), "Python version should be 3.7 or higher"