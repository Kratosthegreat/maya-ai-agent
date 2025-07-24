#!/usr/bin/env python3
"""
Maya AI Bot - Dependency Fixer
==============================
Automatically fixes common dependency issues and creates working requirements.txt
"""

import subprocess
import sys
import os

def run_command(command):
    """Run shell command and return result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    print(f"   Current Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required for Maya AI Bot")
        print("💡 Please upgrade Python: https://python.org/downloads")
        return False
    
    print("✅ Python version compatible")
    return True

def create_minimal_requirements():
    """Create a minimal, working requirements.txt"""
    print("\n📦 Creating minimal requirements.txt...")
    
    minimal_deps = """# Maya AI Bot - Minimal Dependencies (Auto-Generated)
# ==================================================

python-telegram-bot==20.7
google-generativeai
flask
requests
python-dotenv
pymongo
"""
    
    with open("requirements.txt", "w") as f:
        f.write(minimal_deps)
    
    print("✅ Created minimal requirements.txt")

def install_dependencies():
    """Install dependencies with error handling"""
    print("\n🔧 Installing dependencies...")
    
    # Upgrade pip first
    print("   Upgrading pip...")
    success, _, error = run_command(f"{sys.executable} -m pip install --upgrade pip")
    
    if not success:
        print(f"⚠️ Pip upgrade failed: {error}")
    
    # Install dependencies one by one for better error handling
    core_deps = [
        "python-telegram-bot==20.7",
        "google-generativeai",
        "flask",
        "requests", 
        "python-dotenv"
    ]
    
    optional_deps = [
        "pymongo"
    ]
    
    failed_deps = []
    
    print("   Installing core dependencies...")
    for dep in core_deps:
        print(f"     Installing {dep}...")
        success, stdout, stderr = run_command(f"{sys.executable} -m pip install {dep}")
        
        if not success:
            print(f"❌ Failed to install {dep}")
            print(f"   Error: {stderr}")
            failed_deps.append(dep)
        else:
            print(f"✅ Installed {dep}")
    
    print("   Installing optional dependencies...")
    for dep in optional_deps:
        print(f"     Installing {dep}...")
        success, stdout, stderr = run_command(f"{sys.executable} -m pip install {dep}")
        
        if not success:
            print(f"⚠️ Optional dependency {dep} failed (bot will work without it)")
        else:
            print(f"✅ Installed {dep}")
    
    if failed_deps:
        print(f"\n❌ Failed to install: {', '.join(failed_deps)}")
        print("💡 Try running: pip install --upgrade pip setuptools wheel")
        return False
    else:
        print("\n🎉 All core dependencies installed successfully!")
        return True

def test_imports():
    """Test if all critical imports work"""
    print("\n🧪 Testing imports...")
    
    critical_imports = [
        ("telegram", "Telegram Bot API"),
        ("telegram.ext", "Telegram Extensions"), 
        ("google.generativeai", "Google Gemini AI"),
        ("flask", "Flask Web Server"),
        ("requests", "HTTP Requests"),
        ("dotenv", "Environment Variables")
    ]
    
    optional_imports = [
        ("pymongo", "MongoDB Database")
    ]
    
    failed_imports = []
    
    for module, description in critical_imports:
        try:
            __import__(module)
            print(f"✅ {description}")
        except ImportError as e:
            print(f"❌ {description}: {e}")
            failed_imports.append(module)
    
    for module, description in optional_imports:
        try:
            __import__(module)
            print(f"✅ {description} (optional)")
        except ImportError:
            print(f"⚠️ {description} (optional) - not available")
    
    if failed_imports:
        print(f"\n❌ Critical imports failed: {', '.join(failed_imports)}")
        return False
    else:
        print("\n✅ All critical imports successful!")
        return True

def create_render_ready_files():
    """Create Render.com ready configuration"""
    print("\n🚀 Creating Render.com ready files...")
    
    # Create simple requirements.txt for Render
    render_requirements = """python-telegram-bot==20.7
google-generativeai
flask
requests
python-dotenv
pymongo
"""
    
    with open("requirements.txt", "w") as f:
        f.write(render_requirements)
    
    # Create runtime.txt for Python version
    with open("runtime.txt", "w") as f:
        f.write("python-3.10.6")
    
    print("✅ Created Render.com ready files:")
    print("   - requirements.txt (simplified)")
    print("   - runtime.txt (Python version)")

def main():
    """Main function"""
    print("🔧 Maya AI Bot - Dependency Fixer")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create minimal requirements
    create_minimal_requirements()
    
    # Install dependencies
    if not install_dependencies():
        print("\n💡 If installation failed, try these steps:")
        print("   1. python -m pip install --upgrade pip setuptools wheel")
        print("   2. Use requirements-minimal.txt instead")
        print("   3. Install dependencies one by one manually")
        return False
    
    # Test imports
    if not test_imports():
        return False
    
    # Create Render ready files
    create_render_ready_files()
    
    print("\n🎉 All done! Maya is ready for deployment!")
    print("\n📝 Next steps:")
    print("   1. Test locally: python test_maya_locally.py")
    print("   2. Push to GitHub: git add . && git commit -m 'Fixed deps' && git push")
    print("   3. Deploy to Render.com")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Some issues encountered. Check the messages above.")
        sys.exit(1)
    else:
        print("\n✅ Everything looks good!")
        sys.exit(0)
