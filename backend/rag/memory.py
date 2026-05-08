import time

class ChatMemory:
    def __init__(self, ttl_seconds: int = 300): # 5 minutes default
        self.sessions = {} # session_id -> list of dicts {"role": "user/model", "text": "...", "timestamp": float}
        self.document_summaries = {} # session_id -> str
        self.ttl_seconds = ttl_seconds
        
    def set_document_summary(self, session_id: str, summary: str):
        self.document_summaries[session_id] = summary
        
    def get_document_summary(self, session_id: str) -> str:
        return self.document_summaries.get(session_id, "")
        
    def add_message(self, session_id: str, role: str, text: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            
        self.sessions[session_id].append({
            "role": role,
            "text": text,
            "timestamp": time.time()
        })
        
    def get_context(self, session_id: str) -> str:
        if session_id not in self.sessions:
            return ""
            
        current_time = time.time()
        # Filter messages within TTL
        recent_messages = [
            msg for msg in self.sessions[session_id] 
            if current_time - msg["timestamp"] <= self.ttl_seconds
        ]
        
        # Update session with only recent messages to save memory
        self.sessions[session_id] = recent_messages
        
        context_str = ""
        for msg in recent_messages:
            role_prefix = "User" if msg["role"] == "user" else "Assistant"
            context_str += f"{role_prefix}: {msg['text']}\n"
            
        return context_str

memory = ChatMemory()
