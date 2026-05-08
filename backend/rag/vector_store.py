import faiss
import numpy as np
import google.generativeai as genai
import os

class VectorStore:
    def __init__(self, model_name: str = 'models/text-embedding-004'):
        # Using Gemini API for embeddings instead of local PyTorch to save RAM
        self.model_name = model_name
        self.dimension = 768  # Dimension for text-embedding-004
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_map = {} # Maps faiss index id -> chunk text
        
    def add_chunks(self, chunks: list[str]):
        if not chunks:
            return
            
        # Generate embeddings using Gemini API
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not set. Cannot generate embeddings.")
            return
            
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=chunks,
                task_type="retrieval_document"
            )
            embeddings = result['embedding']
            
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
            return []
            
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=query,
                task_type="retrieval_query"
            )
            query_embedding = result['embedding']
            query_embedding = np.array([query_embedding]).astype('float32')
            
            distances, indices = self.index.search(query_embedding, k)
            
            results = []
            for idx in indices[0]:
                if idx != -1 and idx in self.chunk_map:
                    results.append(self.chunk_map[idx])
                    
            return results
        except Exception as e:
            print(f"Error during similarity search: {e}")
            return []

# Global instance for the server
vector_store = VectorStore()
