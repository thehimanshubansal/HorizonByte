import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

class VectorStore:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        # Using a local, highly efficient embedding model to avoid Gemini API costs
        self.model_name = model_name
        # The MiniLM model outputs exactly 384 dimensions (unlike Gemini's 768)
        self.dimension = 384  
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_map = {} # Maps faiss index id -> chunk text
        
        # Load the model directly into memory
        print(f"[SYSTEM] Loading neural embedding model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        
    def add_chunks(self, chunks: list[str]):
        if not chunks:
            return
            
        try:
            # Generate local embeddings (No API Key needed)
            embeddings = self.model.encode(chunks)
            
            # FAISS expects float32
            embeddings = np.array(embeddings).astype('float32')
            
            start_idx = self.index.ntotal
            self.index.add(embeddings)
            
            for i, chunk in enumerate(chunks):
                self.chunk_map[start_idx + i] = chunk
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            
    def similarity_search(self, query: str, k: int = 3) -> list[str]:
        if self.index.ntotal == 0:
            return[]
            
        try:
            # Encode single query locally
            query_embedding = self.model.encode([query])
            query_embedding = np.array(query_embedding).astype('float32')
            
            distances, indices = self.index.search(query_embedding, k)
            
            results = []
            for idx in indices[0]:
                if idx != -1 and idx in self.chunk_map:
                    results.append(self.chunk_map[idx])
                    
            return results
        except Exception as e:
            print(f"Error during similarity search: {e}")
            return[]
    def reset_store(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_map = {}

# Global instance for the server
vector_store = VectorStore()