"""Tool definitions for Ollama native function calling."""

OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca información en internet de forma privada usando DuckDuckGo. Usá esto cuando necesités información actual o que no está en tu base de conocimiento.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La consulta de búsqueda"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "os_run",
            "description": "Ejecuta comandos en el sistema operativo o abre aplicaciones. Ejemplos: 'gnome-calculator', 'firefox', 'ls -la'",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "El comando o aplicación a ejecutar"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memorize_file",
            "description": "Lee y guarda un archivo en la memoria permanente (RAG) para consultas futuras.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Ruta absoluta del archivo a memorizar"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "Busca en la memoria semántica (RAG) información relevante sobre documentos previamente memorizados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La consulta de búsqueda en memoria"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot",
            "description": "Captura y describe lo que hay en la pantalla actualmente.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Hace clic en coordenadas específicas de la pantalla.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Coordenada X"},
                    "y": {"type": "integer", "description": "Coordenada Y"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type",
            "description": "Escribe texto en el elemento activo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "El texto a escribir"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lee el contenido de un archivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta del archivo"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Escribe contenido a un archivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta del archivo"},
                    "content": {"type": "string", "description": "Contenido a escribir"}
                },
                "required": ["path", "content"]
            }
        }
    }
]
