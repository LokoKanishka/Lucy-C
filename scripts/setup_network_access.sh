#!/bin/bash
# Script para configurar el acceso de red a Lucy-C
# Abre el puerto 5050 en el firewall de Ubuntu

echo "🔓 Configurando Firewall para Lucy-C..."
echo ""

# Verificar si UFW está activo
if sudo ufw status | grep -q "Status: active"; then
    echo "✅ UFW está activo"
    
    # Abrir puerto 5050
    echo "📡 Abriendo puerto 5050/tcp..."
    sudo ufw allow 5050/tcp
    
    # Recargar firewall
    echo "🔄 Recargando firewall..."
    sudo ufw reload
    
    # Mostrar estado
    echo ""
    echo "📊 Estado actual del firewall:"
    sudo ufw status verbose | grep -E "(Status|5050)"
    
else
    echo "⚠️  UFW no está activo o no está instalado"
    echo "El puerto 5050 debería estar accesible sin configuración adicional"
fi

echo ""
echo "✅ Configuración completa!"
echo ""
echo "📱 Para conectarte desde tu celular, usa:"
echo "   http://192.168.0.3:5050"
echo ""
