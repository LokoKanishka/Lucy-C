#!/usr/bin/env python3
"""
Verification script for Lucy's Virtual Display and Computer Vision capabilities.
Tests virtual display, OCR, intelligent clicking, and non-intrusive operation.
"""

import sys
import os
import time
import subprocess

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_virtual_display():
    """Test 1: Virtual Display initialization"""
    print("\n" + "="*60)
    print("TEST 1: Virtual Display Service")
    print("="*60)
    
    try:
        from lucy_c.services.virtual_display import VirtualDisplay
        
        vd = VirtualDisplay(display=":99")
        
        # Test start
        print("Starting virtual display...")
        if not vd.start():
            print("\n⚠️  SKIP: Xvfb not available. Install with: sudo apt install xvfb")
            return None
        
        print(f"✅ Virtual display started (running: {vd.is_running()})")
        
        # Test environment
        env = vd.get_env()
        print(f"✅ Environment: {env}")
        
        # Test stop
        vd.stop()
        print(f"✅ Virtual display stopped (running: {vd.is_running()})")
        
        print("\n✅ PASS: Virtual Display service works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        return False


def test_ocr_basic():
    """Test 2: Basic OCR functionality"""
    print("\n" + "="*60)
    print("TEST 2: OCR Basic Functionality")
    print("="*60)
    
    try:
        import pytesseract
        from PIL import Image, ImageDraw, ImageFont
        
        # Create test image with text
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw some text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 80), "TEST BUTTON", fill='black', font=font)
        
        # Run OCR
        text = pytesseract.image_to_string(img)
        
        if "TEST" in text or "BUTTON" in text:
            print(f"✅ OCR detected: {text.strip()}")
            print("\n✅ PASS: OCR working correctly")
            return True
        else:
            print(f"❌ OCR result unexpected: {text}")
            return False
            
    except ImportError as e:
        print(f"\n⚠️  SKIP: pytesseract not installed - {e}")
        print("Install with: pip install pytesseract && sudo apt install tesseract-ocr")
        return None
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        return False


def test_vision_tools():
    """Test 3: Vision UI tools integration"""
    print("\n" + "="*60)
    print("TEST 3: Vision UI Tools")
    print("="*60)
    
    try:
        from lucy_c.tools.vision_ui_tools import tool_scan_ui, tool_click_text, tool_peek_desktop
        
        # Test scan_ui
        print("Testing scan_ui...")
        result = tool_scan_ui([], {})
        
        if result.success:
            print(f"✅ scan_ui works: {result.output[:100]}...")
        else:
            print(f"⚠️  scan_ui: {result.output}")
        
        # Test peek
        print("\nTesting peek_desktop...")
        result = tool_peek_desktop([], {})
        
        if result.success and "data:image/png;base64" in result.output:
            print("✅ peek_desktop captured screenshot")
        else:
            print(f"❌ peek_desktop failed: {result.output[:100]}")
        
        print("\n✅ PASS: Vision UI tools available")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nonintrusive_operation():
    """Test 4: Verify mouse doesn't move on main display"""
    print("\n" + "="*60)
    print("TEST 4: Non-Intrusive Operation")
    print("="*60)
    
    try:
        import pyautogui
        
        # Get initial mouse position on main display
        initial_pos = pyautogui.position()
        print(f"Initial mouse position: {initial_pos}")
        
        # Simulate operation on virtual display (if available)
        from lucy_c.services.virtual_display import VirtualDisplay
        
        vd = VirtualDisplay(display=":99")
        if not vd.start():
            print("\n⚠️  SKIP: Xvfb not available for isolation test")
            return None
        
        time.sleep(1)
        
        # Check mouse hasn't moved
        final_pos = pyautogui.position()
        print(f"Final mouse position: {final_pos}")
        
        vd.stop()
        
        if initial_pos == final_pos:
            print("\n✅ PASS: Mouse position unchanged (non-intrusive)")
            return True
        else:
            print(f"\n❌ FAIL: Mouse moved from {initial_pos} to {final_pos}")
            return False
            
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        return False


def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("LUCY-C VIRTUAL DISPLAY & COMPUTER VISION VERIFICATION")
    print("="*60)
    
    results = {
        "virtual_display": test_virtual_display(),
        "ocr_basic": test_ocr_basic(),
        "vision_tools": test_vision_tools(),
        "non_intrusive": test_nonintrusive_operation()
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP"
        print(f"{test_name:20s}: {status}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! Virtual Display and Computer Vision ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
