import requests
import json
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Pure Cloudflare Configurations
cf_account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
cf_api_token = os.environ.get("CLOUDFLARE_API_TOKEN")

def call_cloudflare_ai(prompt: str, model: str = "@cf/meta/llama-3.3-70b-instruct-fp8-fast") -> str:
    """Core function to call Cloudflare Workers AI."""
    if not cf_account_id or not cf_api_token:
        return "[SYSTEM ERROR] Cloudflare credentials missing (CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN)."
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/run/{model}"
    headers = {"Authorization": f"Bearer {cf_api_token}"}
    payload = {
        "messages": [
            {"role": "system", "content": "You are HorizonByte, an advanced neural AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            return result["result"]["response"].strip()
        return f"[SYSTEM ERROR] Cloudflare API error: {result.get('errors')}"
    except Exception as e:
        return f"[SYSTEM ERROR] Could not connect to Cloudflare: {str(e)}"

def generate_response(query: str, retrieved_context: list[str], chat_history: str, model_name: str = "@cf/meta/llama-3.3-70b-instruct-fp8-fast", persona: str = "cyber-brutalist") -> str:
    context_str = "\n\n---\n\n".join(retrieved_context) if retrieved_context else ""
    
    # Map persona string to description
    persona_mapping = {
        "cyber-brutalist": "cold, efficient, and authoritative",
        "verbose": "detailed, extremely comprehensive, and highly analytical",
        "casual": "friendly, conversational, and highly helpful"
    }
    personality_desc = persona_mapping.get(persona, persona_mapping["cyber-brutalist"])
    
    prompt = f"""You are HorizonByte, an advanced neural AI assistant in a cyber-terminal environment.
Your personality is {personality_desc}.
Answer the user's question based on the provided context. If the context is provided but doesn't contain the answer, or if the context is missing and the query specifically asks about a document, state that there is insufficient data. Otherwise, answer to the best of your ability.

DOCUMENT CONTEXT:
{context_str}

RECENT CHAT HISTORY:
{chat_history}

USER QUERY:
{query}

AI RESPONSE:"""

    return call_cloudflare_ai(prompt, model=model_name)

def generate_suggestions(context_summary: str, chat_history: str, model_name: str = "@cf/meta/llama-3.3-70b-instruct-fp8-fast") -> list[str]:
    fallback_suggestions = ["System status kya hai?", "Pichla task dikhao", "Data analyze karo", "Mujhe summary chahiye"]
        
    prompt = f"""You are HorizonByte, an advanced neural AI assistant in a cyber-terminal environment.
Generate exactly 4 short, action-oriented, or highly relevant follow-up questions/prompts that the user might want to click next, based on the document summary and chat history.
Each suggestion should be under 40 characters and read like a terminal command or short query.
Wrap the 4 strings in a JSON array. Return ONLY valid JSON, nothing else. No markdown, no preambles.

DOCUMENT SUMMARY:
{context_summary}

RECENT CHAT HISTORY:
{chat_history}

JSON ARRAY OF 4 SUGGESTIONS:"""

    try:
        text = call_cloudflare_ai(prompt, model=model_name)
        
        # 1. Clean whitespace
        text = text.strip()
        
        # 2. Aggressive search: Find the first '[' and last ']'
        # This ignores text before the start and after the end
        match = re.search(r'\[.*\]', text, re.DOTALL)
        
        if match:
            clean_text = match.group(0)
            return json.loads(clean_text)
        else:
            # If no brackets found, print the raw output so you can see why it failed
            print(f"[DEBUG] Raw response was not valid JSON: {text}")
            return fallback_suggestions
            
    except json.JSONDecodeError as e:
        print(f"[DEBUG] JSON syntax error: {e}")
        return fallback_suggestions

def rephrase_text(text: str, tone: str, model_name: str = "@cf/meta/llama-3.3-70b-instruct-fp8-fast") -> str:
    prompt = f"""You are HorizonByte, an advanced neural AI assistant. 
The user provided a text written in Hinglish (a mix of Hindi and English) or English.
Please translate/rephrase it entirely into English using a '{tone}' tone. 
Return ONLY the final translated/rephrased English string, nothing else.

ORIGINAL TEXT:
{text}

REPHRASED TEXT ({tone} TONE):"""

    return call_cloudflare_ai(prompt, model=model_name)

def rerank_chunks(query: str, chunks: list[str]) -> list[str]:
    try:
        # Number the chunks for the LLM
        context_str = "\n\n".join([f"[CHUNK {i}]: {chunk}" for i, chunk in enumerate(chunks)])
        
        prompt = f"""You are a Re-ranker. Given a User Query and a set of Context Chunks, identify which chunks are most relevant.
        
        USER QUERY: {query}
        
        CONTEXT CHUNKS:
        {context_str}
        
        INSTRUCTION: Return ONLY the indices (e.g., 0, 2, 4) of the 3 most relevant chunks, in order of relevance. 
        Format: A comma-separated list of numbers. Do not include any other text.
        """
        
        response = call_cloudflare_ai(prompt) # Calls your Llama 3.3
        # Parse indices from string "0, 2, 4"
        indices = [int(i.strip()) for i in response.split(",")]
        return [chunks[i] for i in indices[:3]]
    except Exception as e:
        print(f"[DEBUG] Re-ranker failed, falling back to top 3: {e}")
        return chunks[:3] # Fallback to default
