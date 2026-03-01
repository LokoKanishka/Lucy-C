# Proyecto: Gmail CV (Automatización de Postulaciones)

Este flujo de trabajo automatiza el envío de tu currículum a colegios listados en un Excel, filtrando por Comuna y personalizando el mensaje para cada institución.

## Estructura de Archivos

- `data/colegios.xlsx`: Lista de instituciones (basado en CABA).
- `data/Mi_Curriculum.pdf`: Tu currículum que se adjuntará (Reemplazalo con tu archivo real).
- `workflow.json`: El código del flujo para importar en n8n.

## Pasos para el Usuario

1. **Reemplazar el CV**: Copia tu PDF real a la carpeta `data/` con el nombre `Mi_Curriculum.pdf`.
2. **Configurar Gmail (en n8n)**:
   - Ingresa a la interfaz de n8n.
   - Entra al nodo "Enviar Gmail".
   - Conecta tu cuenta de Google (Gmail Credential) y da los permisos.
3. **Activar**: Una vez testeado, activá el workflow para que corra los Lunes a Viernes a las 08:00 AM.

## Ajustes técnicos realizados en este Workspace

- Se ajustaron las rutas de los archivos para que apunten al volumen persistente de n8n:
  - `/home/node/.n8n-files/gmail_cv/data/colegios.xlsx`
  - `/home/node/.n8n-files/gmail_cv/data/Mi_Curriculum.pdf`
- El JSON está configurado y ha sido desplegado exitosamente vía `n8n_cli.py`.
