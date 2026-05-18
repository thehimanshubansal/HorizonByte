import faiss
import numpy as np
import requests
import os

class VectorStore:
    def __init__(self, model_name: str = 'bge-small-en-v1.5'):
        # Using a local, highly efficient embedding model to avoid Gemini API costs
        self.model_name = model_name
        # The bge-small model outputs exactly 384 dimensions (unlike Gemini's 768)
        self.dimension = 384  
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_map = {} # Maps faiss index id -> chunk text
        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self.token = os.environ.get("CLOUDFLARE_API_TOKEN")
        
    def _get_embedding(self, text: str):
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/BAAI/bge-small-en-v1.5"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(url, headers=headers, json={"text": [text]})
        return response.json()['result']['data'][0]

        
    def add_chunks(self, chunks: list[str]):
        embeddings = [self._get_embedding(c) for c in chunks]
        embeddings = np.array(embeddings).astype('float32')
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        for i, chunk in enumerate(chunks):
            self.chunk_map[start_idx + i] = chunk
            
    def similarity_search(self, query: str, k: int = 3):
        query_emb = np.array([self._get_embedding(query)]).astype('float32')
        distances, indices = self.index.search(query_emb, k)
        return [self.chunk_map[idx] for idx in indices[0] if idx in self.chunk_map]

    def reset_store(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_map = {}

# Global instance for the server
vector_store = VectorStore()