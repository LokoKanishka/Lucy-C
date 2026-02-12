from __future__ import annotations
import logging
from lucy_c.tool_router import ToolResult

log = logging.getLogger("LucyC.BusinessTools")

def tool_check_shipping(args, ctx):
    """check_shipping(destino) -> Simulates shipping cost and time calculation."""
    if not args:
        return ToolResult(False, "Falta el destino para calcular el envío.", "📦 ENVÍO")
    
    destino = args[0]
    # Mock logic
    costo = 2500 + (len(destino) * 100)
    dias = 2 + (len(destino) % 3)
    
    return ToolResult(True, f"Costo de envío a {destino}: ${costo}. Tiempo estimado: {dias} días hábiles.", "📦 ENVÍO")

def tool_process_payment(args, ctx):
    """process_payment(monto, metodo) -> Simulates payment processing."""
    if len(args) < 2:
        return ToolResult(False, "Faltan monto y método (ej: 5000, tarjeta).", "💳 PAGO")
    
    monto, metodo = args[0], args[1]
    return ToolResult(True, f"Pago de ${monto} con {metodo} procesado con éxito. (Simulación)", "💳 PAGO")

def tool_generate_budget_pdf(args, ctx):
    """generate_budget_pdf(item, precio, cantidad) -> Generates a PDF budget."""
    if len(args) < 3:
        return ToolResult(False, "Faltan datos: item, precio, cantidad.", "📄 PDF")
    
    try:
        from lucy_c.services.pdf_service import PDFService
        item, precio, cantidad = args[0], args[1], args[2]
        
        session_user = ctx.get("session_user", "anonymous")
        pdf_path = PDFService.create_budget(session_user, item, precio, cantidad)
        
        # We return a link-like structured string that the UI can interpret if we add support
        # Or just the filename for now.
        return ToolResult(True, f"Presupuesto generado para {item}. Podés descargarlo desde la interfaz. Link: /data/budgets/{pdf_path.name}", "📄 PDF")
    except Exception as e:
        log.error("PDF generation failed: %s", e)
        return ToolResult(False, f"Error al generar el PDF: {e}", "⚠️ ERROR")
