import faiss
import numpy as np
import requests
import os

class VectorStore:
    def __init__(self, model_name: str = 'bge-small-en-v1.5'):
        self.model_name = model_name
        self.dimension = 384  
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_map = {} 
        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self.token = os.environ.get("CLOUDFLARE_API_TOKEN")
        
    def _get_embedding(self, texts: list[str]):
        # Check if credentials exist
        if not self.account_id or not self.token:
            print("[ERROR] Cloudflare credentials not set.")
            return None

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/BAAI/bge-small-en-v1.5"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.post(url, headers=headers, json={"text": texts}, timeout=30)
            result = response.json()
            
            if not result.get("success"):
                print(f"[ERROR] Cloudflare API Error: {result.get('errors')}")
                return None
                
            return result['result']['data']
        except Exception as e:
            print(f"[ERROR] Embedding request failed: {e}")
            return None

    def add_chunks(self, chunks: list[str]):
        # Batching: Send 5 chunks at a time to avoid timeout/payload limits
        batch_size = 5
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            embeddings = self._get_embedding(batch)
            
            if embeddings is None: continue
                
            embeddings = np.array(embeddings).astype('float32')
            # Normalize for better L2 distance accuracy
            faiss.normalize_L2(embeddings)
            
            start_idx = self.index.ntotal
            self.index.add(embeddings)
            for j, chunk in enumerate(batch):
                self.chunk_map[start_idx + j] = chunk
            
    def similarity_search(self, query: str, k: int = 3):
        # Handle search carefully
        emb_data = self._get_embedding([query])
        if emb_data is None: return[]
            
        query_emb = np.array(emb_data).astype('float32')
        faiss.normalize_L2(query_emb) # Always normalize query too!
        
        distances, indices = self.index.search(query_emb, k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx in self.chunk_map:
                results.append(self.chunk_map[idx])
        return results

    def reset_store(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_map = {}

vector_store = VectorStore()