import logging
from pathlib import Path
from lucy_c.tool_router import ToolResult

log = logging.getLogger("LucyC.KnowledgeTools")

def create_knowledge_tools(memory_engine):
    """Factory function to create knowledge/memory tools."""
    
    def tool_memorize_file(args, ctx):
        """Ingest a file into Lucy's permanent semantic memory.
        
        This allows Lucy to "read" and remember documents, code, or any text file
        for future reference, even across sessions.
        
        Args:
            args[0]: file_path (str) - Path to the file to memorize
        """
        if not args:
            return ToolResult(False, "Falta la ruta del archivo a memorizar.", "📚 MEMORIA")
        
        file_path = args[0]
        log.info("Attempting to memorize file: %s", file_path)
        
        try:
            # Expand relative paths
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                return ToolResult(False, f"El archivo '{file_path}' no existe.", "📚 MEMORIA")
            
            if not path.is_file():
                return ToolResult(False, f"'{file_path}' no es un archivo.", "📚 MEMORIA")
            
            # Check file size (limit to 10MB to avoid memory issues)
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 10:
                return ToolResult(False, f"El archivo es muy grande ({size_mb:.1f}MB). Límite: 10MB.", "📚 MEMORIA")
            
            # Ingest the file
            num_chunks = memory_engine.ingest_file(str(path))
            
            return ToolResult(
                True, 
                f"Memoricé '{path.name}' exitosamente ({num_chunks} fragmentos guardados). Ahora puedo consultarlo cuando lo necesite.",
                "📚 MEMORIA"
            )
            
        except UnicodeDecodeError:
            return ToolResult(False, f"No pude leer '{file_path}' (encoding inválido).", "📚 MEMORIA")
        except Exception as e:
            log.error("Failed to memorize file %s: %s", file_path, e, exc_info=True)
            return ToolResult(False, f"Error al memorizar archivo: {e}", "📚 MEMORIA")
    
    def tool_recall(args, ctx):
        """Search Lucy's semantic memory for relevant information.
        
        This is Lucy's way of "remembering" information from previously ingested
        documents, even if they weren't mentioned in the current conversation.
        
        Args:
            args[0]: query (str) - What Lucy wants to remember/search for
        """
        if not args:
            return ToolResult(False, "Falta la consulta para buscar en mi memoria.", "📚 MEMORIA")
        
        query = args[0]
        log.info("Querying memory: %s", query)
        
        try:
            # Get memory stats first
            stats = memory_engine.stats()
            if stats["total_documents"] == 0:
                return ToolResult(
                    False,
                    "Mi memoria está vacía. Primero necesito que me pidas memorizar archivos usando [[memorize_file(path)]].",
                    "📚 MEMORIA"
                )
            
            # Search memory
            results = memory_engine.query(query, n_results=3)
            
            if not results:
                return ToolResult(
                    False,
                    f"No encontré nada relevante en mi memoria para: '{query}'",
                    "📚 MEMORIA"
                )
            
            # Format results
            output_lines = [f"Encontré {len(results)} fragmentos relevantes en mi memoria:\n"]
            
            for i, result in enumerate(results, 1):
                meta = result['metadata']
                text = result['text']
                source = meta.get('file_name', meta.get('source', 'unknown'))
                
                output_lines.append(f"**Fragmento {i}** (de `{source}`):")
                output_lines.append(text[:400] + "..." if len(text) > 400 else text)
                output_lines.append("")  # Blank line
            
            return ToolResult(True, "\n".join(output_lines), "📚 MEMORIA")
            
        except Exception as e:
            log.error("Failed to query memory: %s", e, exc_info=True)
            return ToolResult(False, f"Error al buscar en memoria: {e}", "📚 MEMORIA")
    
    def tool_memory_stats(args, ctx):
        """Get statistics about Lucy's memory."""
        try:
            stats = memory_engine.stats()
            return ToolResult(
                True,
                f"Memoria: {stats['total_documents']} fragmentos almacenados en {stats['persist_directory']}",
                "📚 MEMORIA"
            )
        except Exception as e:
            return ToolResult(False, f"Error al obtener stats: {e}", "📚 MEMORIA")
    
    return {
        "memorize_file": tool_memorize_file,
        "recall": tool_recall,
        "memory_stats": tool_memory_stats
    }
