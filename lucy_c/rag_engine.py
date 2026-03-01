"""RAG Memory Engine for Lucy using ChromaDB and sentence-transformers."""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

log = logging.getLogger("LucyC.RAG")

class MemoryEngine:
    """Semantic memory engine using ChromaDB for document storage and retrieval."""
    
    def __init__(self, persist_directory: str = "data/chroma_db"):
        """Initialize the memory engine.
        
        Args:
            persist_directory: Path where ChromaDB will persist data
        """
        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            import chromadb
            from chromadb.config import Settings
            from sentence_transformers import SentenceTransformer
            
            # Initialize ChromaDB client
            self.client = chromadb.Client(Settings(
                persist_directory=str(self.persist_dir),
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="lucy_memory",
                metadata={"description": "Lucy's semantic memory"}
            )
            
            # Initialize embedding model (lightweight and fast)
            log.info("Loading embedding model (all-MiniLM-L6-v2)...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            log.info("Memory engine initialized. Collection has %d documents.", self.collection.count())
            
        except ImportError as e:
            log.error("Failed to import RAG dependencies: %s", e)
            raise RuntimeError("ChromaDB or sentence-transformers not installed. Run: pip install chromadb sentence-transformers")
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk (in characters)
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_len:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size // 2:  # Only break if we're past halfway
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [c for c in chunks if c]  # Filter empty chunks
    
    def ingest_text(self, text: str, metadata: Dict[str, Any]) -> int:
        """Ingest text into memory by chunking and embedding.
        
        Args:
            text: Text content to memorize
            metadata: Metadata about the text (e.g., file_path, source)
            
        Returns:
            Number of chunks added
        """
        chunks = self._chunk_text(text)
        
        if not chunks:
            log.warning("No chunks created from text")
            return 0
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
        
        # Create unique IDs for each chunk
        base_id = hashlib.md5(text.encode()).hexdigest()[:8]
        ids = [f"{base_id}_chunk_{i}" for i in range(len(chunks))]
        
        # Prepare metadata for each chunk
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_meta = metadata.copy()
            chunk_meta.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_text": chunk[:200]  # Store preview
            })
            metadatas.append(chunk_meta)
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=metadatas
        )
        
        log.info("Ingested %d chunks from %s", len(chunks), metadata.get("source", "unknown"))
        return len(chunks)
    
    def ingest_file(self, file_path: str) -> int:
        """Read and ingest a file into memory.
        
        Args:
            file_path: Path to file to ingest
            
        Returns:
            Number of chunks added
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            content = path.read_text(encoding='latin-1')
        
        metadata = {
            "source": "file",
            "file_path": str(path.absolute()),
            "file_name": path.name,
            "file_size": path.stat().st_size
        }
        
        return self.ingest_text(content, metadata)
    
    def query(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search memory for relevant information.
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        if self.collection.count() == 0:
            log.warning("Memory is empty, no results to return")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query_text], show_progress_bar=False)[0]
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(n_results, self.collection.count())
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })
        
        log.info("Query '%s' returned %d results", query_text[:50], len(formatted_results))
        return formatted_results
    
    def clear(self):
        """Clear all memory (for testing)."""
        self.client.delete_collection("lucy_memory")
        self.collection = self.client.get_or_create_collection(
            name="lucy_memory",
            metadata={"description": "Lucy's semantic memory"}
        )
        log.info("Memory cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_documents": self.collection.count(),
            "persist_directory": str(self.persist_dir)
        }
