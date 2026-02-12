import subprocess
import platform
import urllib.parse
import logging
from lucy_c.tool_router import ToolResult

log = logging.getLogger("LucyC.WebTools")

def tool_web_search(args, ctx):
    """Search DuckDuckGo and return a text summary to the LLM."""
    if not args:
        return ToolResult(False, "Falta la consulta para buscar.", "🌐 RED")
    
    query = args[0]
    log.info("Performing private web search for: %s", query)
    
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            # Use 'text' (search results)
            # The new version might have slightly different return types.
            results = ddgs.text(query, max_results=5)
            if not results:
                return ToolResult(True, "No encontré resultados para esa búsqueda.", "🌐 RED")
            
            summary = []
            for r in results:
                summary.append(f" - {r['title']}: {r['body']} (URL: {r['href']})")
            
            output = "\n".join(summary)
            return ToolResult(True, f"Resultados de búsqueda para '{query}':\n{output}", "🌐 RED")
    except Exception as e:
        log.error("DuckDuckGo search failed: %s", e)
        return ToolResult(False, f"Error en la búsqueda web: {e}", "🌐 RED")

def tool_open_url(args, ctx):
    """Open a URL specifically using Firefox for privacy."""
    if not args:
        return ToolResult(False, "Falta la URL para abrir.", "🌐 RED")
    
    url = args[0].strip()
    if not url.startswith(("http://", "https://")):
        # If it looks like a domain without proto, add it
        if "." in url and not " " in url:
             url = "https://" + url
        else:
            # Maybe it's a search?
            return tool_web_search(args, ctx)
        
    log.info("Opening Firefox towards: %s", url)
    try:
        # We use subprocess directly to enforce firefox instead of system default
        subprocess.Popen(["firefox", url])
        return ToolResult(True, f"Abriendo {url} en Firefox.", "🌐 RED")
    except Exception as e:
        log.error("Failed to launch Firefox: %s", e)
        return ToolResult(False, f"Error al abrir Firefox: {e}", "🌐 RED")

def tool_read_url(args, ctx):
    """Read and extract clean text content from a web page."""
    if not args:
        return ToolResult(False, "Falta la URL para leer.", "🌐 RED")
    
    url = args[0].strip()
    
    # Validate URL format
    if not url.startswith(("http://", "https://")):
        if "." in url and " " not in url:
            url = "https://" + url
        else:
            return ToolResult(False, f"URL inválida: {url}", "🌐 RED")
    
    log.info("Reading content from: %s", url)
    
    try:
        import trafilatura
        
        # Fetch with timeout
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ToolResult(False, f"No pude descargar el contenido de {url}", "🌐 RED")
        
        # Extract main content
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
        
        if not text:
            return ToolResult(False, f"No pude extraer texto de {url}. Puede ser que la página esté protegida.", "🌐 RED")
        
        # Limit output to avoid overwhelming the LLM (first 4000 chars)
        if len(text) > 4000:
            text = text[:4000] + "\n\n[... contenido truncado por longitud ...]"
        
        return ToolResult(True, f"Contenido de {url}:\n\n{text}", "🌐 RED")
        
    except Exception as e:
        log.error("Failed to read URL: %s", e)
        return ToolResult(False, f"Error al leer {url}: {e}", "🌐 RED")
