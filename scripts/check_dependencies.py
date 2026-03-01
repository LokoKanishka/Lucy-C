#!/usr/bin/env python3
"""Check system dependencies for Lucy's advanced features."""

import subprocess
import sys
import os

def check_wmctrl():
    """Check if wmctrl is installed"""
    try:
        result = subprocess.run(
            ["wmctrl", "-h"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_x11():
    """Check if running X11 (not Wayland)"""
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "x11"

def main():
    print("Checking system dependencies for Lucy-C Advanced Agency...\n")
    
    all_ok = True
    
    # Check Python packages
    print("Python packages:")
    try:
        import trafilatura
        print("  ✅ trafilatura")
    except ImportError:
        print("  ❌ trafilatura - Install with: pip install trafilatura")
        all_ok = False
    
    try:
        import bs4
        print("  ✅ beautifulsoup4")
    except ImportError:
        print("  ❌ beautifulsoup4 - Install with: pip install beautifulsoup4")
        all_ok = False
    
    try:
        import lxml
        print("  ✅ lxml")
    except ImportError:
        print("  ❌ lxml - Install with: pip install lxml")
        all_ok = False
    
    try:
        import requests
        print("  ✅ requests")
    except ImportError:
        print("  ❌ requests - Install with: pip install requests")
        all_ok = False
    
    # Check system tools
    print("\nSystem tools:")
    if check_wmctrl():
        print("  ✅ wmctrl")
    else:
        print("  ⚠️  wmctrl - Install with: sudo apt install wmctrl")
        print("     (Window management features will be disabled without this)")
    
    # Check window system
    print("\nWindow system:")
    if check_x11():
        print("  ✅ X11 (window management will work)")
    else:
        session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
        print(f"  ⚠️  {session_type} detected (window management may not work)")
        print("     Consider switching to X11 session for full functionality")
    
    print()
    if all_ok:
        print("✅ All Python dependencies are installed!")
    else:
        print("⚠️  Some Python dependencies are missing. Run: pip install -r requirements.txt")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
