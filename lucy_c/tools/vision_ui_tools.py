"""
Vision UI Tools for Lucy
OCR-based screen analysis and intelligent UI interaction.
"""

import os
import logging
import base64
from io import BytesIO
from typing import List, Dict, Tuple, Optional
# Lazy import pyautogui to avoid X11 connection on module load
# import pyautogui  # MOVED TO FUNCTION LEVEL
from PIL import Image
from lucy_c.tool_router import ToolResult

log = logging.getLogger("LucyC.VisionUI")


def _capture_screenshot(display: Optional[str] = None) -> Image.Image:
    """
    Capture screenshot from specified display.
    
    Args:
        display: Display to capture from (e.g., ":99"), None for current
        
    Returns:
        PIL Image
    """
    # Lazy import to avoid X11 connection on module load
    import pyautogui
    
    # If display specified, temporarily set DISPLAY env var
    old_display = os.environ.get('DISPLAY')
    if display:
        os.environ['DISPLAY'] = display
    
    try:
        screenshot = pyautogui.screenshot()
        return screenshot
    finally:
        # Restore original DISPLAY
        if old_display:
            os.environ['DISPLAY'] = old_display
        elif display and 'DISPLAY' in os.environ:
            del os.environ['DISPLAY']


def _run_ocr(image: Image.Image) -> List[Dict]:
    """
    Run OCR on image and return structured data.
    
    Returns:
        List of dicts with: text, x, y, width, height, conf
    """
    try:
        import pytesseract
        
        # Get detailed OCR data
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        results = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])
            
            # Filter out empty text and low confidence
            if not text or conf < 30:
                continue
            
            results.append({
                'text': text,
                'x': data['left'][i],
                'y': data['top'][i],
                'width': data['width'][i],
                'height': data['height'][i],
                'conf': conf
            })
        
        return results
        
    except ImportError:
        log.error("pytesseract not installed. Install with: pip install pytesseract")
        return []
    except Exception as e:
        log.error("OCR failed: %s", e)
        return []


def _find_text_fuzzy(ocr_results: List[Dict], target: str, threshold: float = 0.8) -> Optional[Dict]:
    """
    Find text in OCR results using fuzzy matching.
    
    Args:
        ocr_results: List of OCR result dicts
        target: Target text to find
        threshold: Similarity threshold (0-1)
        
    Returns:
        Best matching result or None
    """
    try:
        from Levenshtein import ratio
    except ImportError:
        # Fallback to exact match
        log.warning("python-Levenshtein not available, using exact match")
        for result in ocr_results:
            if target.lower() in result['text'].lower():
                return result
        return None
    
    target_lower = target.lower()
    best_match = None
    best_score = 0.0
    
    for result in ocr_results:
        text_lower = result['text'].lower()
        
        # Check if target is substring
        if target_lower in text_lower or text_lower in target_lower:
            score = 1.0
        else:
            score = ratio(target_lower, text_lower)
        
        if score > best_score:
            best_score = score
            best_match = result
    
    if best_score >= threshold:
        return best_match
    
    return None


def tool_scan_ui(args, ctx):
    """Scan screen with OCR and return all text elements with coordinates."""
    display = args[0] if args else None
    
    log.info("Scanning UI with OCR (display: %s)", display or "current")
    
    try:
        # Capture screenshot
        screenshot = _capture_screenshot(display)
        
        # Run OCR
        results = _run_ocr(screenshot)
        
        if not results:
            return ToolResult(False, "No pude detectar texto en la pantalla. Verificá que tesseract-ocr esté instalado.", "👁️ VISIÓN")
        
        # Format output
        output_lines = [f"Detecté {len(results)} elementos de texto:"]
        for i, item in enumerate(results[:30]):  # Limit to 30 for readability
            output_lines.append(f" - '{item['text']}' en ({item['x']}, {item['y']})")
        
        if len(results) > 30:
            output_lines.append(f"... y {len(results) - 30} más")
        
        return ToolResult(True, "\n".join(output_lines), "👁️ VISIÓN")
        
    except Exception as e:
        log.error("scan_ui failed: %s", e)
        return ToolResult(False, f"Error escaneando UI: {e}", "👁️ VISIÓN")


def tool_click_text(args, ctx):
    """Find text on screen and click it."""
    if not args:
        return ToolResult(False, "Falta el texto a buscar. Uso: click_text('botón')", "👁️ VISIÓN")
    
    target_text = args[0].strip()
    double_click = len(args) > 1 and args[1].lower() in ('true', '1', 'yes', 'doble')
    display = args[2] if len(args) > 2 else None
    
    log.info("Looking for text '%s' to click (double: %s, display: %s)", 
             target_text, double_click, display or "current")
    
    try:
        # Capture and OCR
        screenshot = _capture_screenshot(display)
        results = _run_ocr(screenshot)
        
        if not results:
            return ToolResult(False, "No detecté ningún texto en la pantalla.", "👁️ VISIÓN")
        
        # Find target text
        match = _find_text_fuzzy(results, target_text)
        
        if not match:
            # Provide helpful candidates
            candidates = [r['text'] for r in results[:10]]
            return ToolResult(
                False,
                f"No encontré '{target_text}'. Textos disponibles: {', '.join(candidates)}",
                "👁️ VISIÓN"
            )
        
        # Calculate center of text box
        center_x = match['x'] + match['width'] // 2
        center_y = match['y'] + match['height'] // 2
        
        # Set DISPLAY if needed
        if display:
            old_display = os.environ.get('DISPLAY')
            os.environ['DISPLAY'] = display
        
        try:
            # Lazy import
            import pyautogui
            
            # Perform click
            clicks = 2 if double_click else 1
            pyautogui.click(center_x, center_y, clicks=clicks, duration=0.2)
            
            action = "doble clic" if double_click else "clic"
            return ToolResult(
                True,
                f"Hice {action} en '{match['text']}' (coordenadas: {center_x}, {center_y})",
                "👁️ VISIÓN"
            )
        finally:
            # Restore DISPLAY
            if display and old_display:
                os.environ['DISPLAY'] = old_display
            elif display and 'DISPLAY' in os.environ:
                del os.environ['DISPLAY']
        
    except Exception as e:
        log.error("click_text failed: %s", e)
        return ToolResult(False, f"Error al hacer clic: {e}", "👁️ VISIÓN")


def tool_peek_desktop(args, ctx):
    """Capture current desktop and return as base64 image for display."""
    display = args[0] if args else None
    
    log.info("Capturing desktop peek (display: %s)", display or "current")
    
    try:
        # Capture screenshot
        screenshot = _capture_screenshot(display)
        
        # Resize to reasonable size (800x600) for chat display
        screenshot.thumbnail((800, 600), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return ToolResult(
            True,
            f"Captura del escritorio (display: {display or 'current'}):\n\ndata:image/png;base64,{img_b64}",
            "👁️ VISIÓN"
        )
        
    except Exception as e:
        log.error("peek_desktop failed: %s", e)
        return ToolResult(False, f"Error capturando escritorio: {e}", "👁️ VISIÓN")
