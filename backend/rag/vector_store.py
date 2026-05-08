import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        # Using sentence-transformers for fast local embeddings (runs on CPU)
        self.embedding_model = SentenceTransformer(model_name)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_map = {} # Maps faiss index id -> chunk text
        
    def add_chunks(self, chunks: list[str]):
        if not chunks:
            return
            
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks)
        
        # FAISS expects float32
        embeddings = np.array(embeddings).astype('float32')
        
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        
        for i, chunk in enumerate(chunks):
            self.chunk_map[start_idx + i] = chunk
            
    def similarity_search(self, query: str, k: int = 3) -> list[str]:
        if self.index.ntotal == 0:
            return []
            
        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx in self.chunk_map:
                results.append(self.chunk_map[idx])
                
        return results

# Global instance for the server
vector_store = VectorStore()
