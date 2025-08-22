#!/usr/bin/env python3
"""
Setup script for GitHub Productivity Analytics
Helps users configure the tool for first-time use.
"""

import os
import sys
from pathlib import Path

def main():
    print("🚀 GitHub Productivity Analytics Setup")
    print("=" * 50)
    
    # Check if config.py exists
    config_file = Path("config.py")
    example_config = Path("config.example.py")
    
    if not config_file.exists():
        if not example_config.exists():
            print("❌ Error: config.example.py not found!")
            print("Please ensure you're running this from the project directory.")
            return 1
            
        print("📝 Creating config.py from example...")
        config_file.write_text(example_config.read_text())
        print("✅ config.py created successfully!")
        print()
        print("📋 Next steps:")
        print("1. Edit config.py and set your GITHUB_TOKEN and ORG_NAME")
        print("2. Customize CORE_TEAM with your team member names")
        print("3. Run: python extract.py")
        print("4. Run: python web_dashboard.py")
        print()
        print("🔗 Need a GitHub token? Visit:")
        print("   https://github.com/settings/tokens/new")
        print("   Required scopes: repo, read:org, read:user")
        
    else:
        print("✅ config.py already exists")
        
        # Test import
        try:
            import config
            print("✅ Configuration loads successfully")
            
            # Check required settings
            issues = []
            if not hasattr(config, 'GITHUB_TOKEN') or not config.GITHUB_TOKEN:
                issues.append("GITHUB_TOKEN is not set")
            if not hasattr(config, 'ORG_NAME') or not config.ORG_NAME:
                issues.append("ORG_NAME is not set")
            if not hasattr(config, 'CORE_TEAM') or not config.CORE_TEAM:
                issues.append("CORE_TEAM is empty")
                
            if issues:
                print("⚠️  Configuration issues found:")
                for issue in issues:
                    print(f"   - {issue}")
                print("\nPlease edit config.py to fix these issues.")
            else:
                print("✅ Configuration looks good!")
                print(f"   Organization: {config.ORG_NAME}")
                print(f"   Core team members: {len(config.CORE_TEAM)}")
                print("\n🎉 Ready to run analysis!")
                print("   Next: python extract.py")
                
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            print("Please check config.py for syntax errors.")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
