from __future__ import annotations
import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm

class PDFService:
    @staticmethod
    def create_budget(user_id: str, item: str, price: str, quantity: str) -> Path:
        """Generates a budget PDF and returns the absolute path."""
        # /.../Lucy-C/data/budgets
        root = Path(__file__).resolve().parents[2]
        output_dir = root / "data" / "budgets"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"budget_{user_id}_{os.urandom(4).hex()}.pdf"
        output_path = output_dir / filename
        
        c = canvas.Canvas(str(output_path), pagesize=A4)
        width, height = A4
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(2 * cm, height - 3 * cm, "Presupuesto - Lucy Assistant")
        
        c.setFont("Helvetica", 12)
        c.drawString(2 * cm, height - 4 * cm, f"Usuario: {user_id}")
        c.line(2 * cm, height - 4.5 * cm, width - 2 * cm, height - 4.5 * cm)
        
        # Content
        try:
            p = float(price)
            q = int(quantity)
            total = p * q
        except:
            total = 0
            
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, height - 6 * cm, "Detalle del Pedido")
        
        c.setFont("Helvetica", 12)
        c.drawString(3 * cm, height - 7 * cm, f"Item: {item}")
        c.drawString(3 * cm, height - 8 * cm, f"Precio Unitario: ${price}")
        c.drawString(3 * cm, height - 9 * cm, f"Cantidad: {quantity}")
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(width - 7 * cm, height - 11 * cm, f"Total: ${total:.2f}")
        
        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(width / 2, 2 * cm, "Gracias por confiar en Lucy - Soberanía Digital Local")
        
        c.showPage()
        c.save()
        
        return output_path
