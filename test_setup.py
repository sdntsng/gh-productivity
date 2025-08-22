#!/usr/bin/env python3
"""
Quick test script to verify the GitHub Productivity Analytics setup.
Run this after setting up config.py to ensure everything works.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        import pandas
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
        
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
        return False
        
    try:
        import plotly
        print("✅ plotly imported successfully")
    except ImportError as e:
        print(f"❌ plotly import failed: {e}")
        return False
        
    return True

def test_config():
    """Test that config.py is properly set up."""
    print("\n⚙️  Testing configuration...")
    
    if not Path("config.py").exists():
        print("❌ config.py not found. Run: cp config.example.py config.py")
        return False
        
    try:
        import config
        print("✅ config.py imported successfully")
        
        # Check required settings
        required_attrs = ['GITHUB_TOKEN', 'ORG_NAME', 'CORE_TEAM']
        for attr in required_attrs:
            if hasattr(config, attr):
                value = getattr(config, attr)
                if value:
                    print(f"✅ {attr} is set")
                else:
                    print(f"⚠️  {attr} is empty - please set it in config.py")
            else:
                print(f"❌ {attr} not found in config.py")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ config.py error: {e}")
        return False

def test_github_connection():
    """Test GitHub API connectivity."""
    print("\n🌐 Testing GitHub connection...")
    
    try:
        import config
        import requests
        
        if not config.GITHUB_TOKEN:
            print("⚠️  No GitHub token set - skipping connection test")
            return True
            
        headers = {
            'Authorization': f'token {config.GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Test basic API access
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ GitHub API connection successful")
            print(f"   Authenticated as: {user_data.get('login', 'Unknown')}")
            return True
        else:
            print(f"❌ GitHub API error: {response.status_code}")
            print(f"   Response: {response.text[:100]}...")
            return False
            
    except Exception as e:
        print(f"❌ GitHub connection test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 GitHub Productivity Analytics - System Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_config),
        ("GitHub Connection Test", test_github_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to run the analysis.")
        print("\nNext steps:")
        print("   1. python extract.py")
        print("   2. python web_dashboard.py")
        print("   3. Open productivity_dashboard.html in your browser")
    else:
        print("\n🔧 Please fix the failing tests before proceeding.")
        print("   Check the error messages above for guidance.")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
