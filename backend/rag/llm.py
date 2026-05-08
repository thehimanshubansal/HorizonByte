import google.generativeai as genai
import os

# Ensure the user sets GEMINI_API_KEY
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def generate_response(query: str, retrieved_context: list[str], chat_history: str, model_name: str = "gemini-2.5-flash", persona: str = "cyber-brutalist") -> str:
    if not api_key:
        return "ERROR: GEMINI_API_KEY environment variable is not set. Please set it to proceed."
        
    context_str = "\n\n---\n\n".join(retrieved_context)
    
    # Map persona string to description
    persona_mapping = {
        "cyber-brutalist": "cold, efficient, and authoritative",
        "verbose": "detailed, extremely comprehensive, and highly analytical",
        "casual": "friendly, conversational, and highly helpful"
    }
    personality_desc = persona_mapping.get(persona, persona_mapping["cyber-brutalist"])
    
    prompt = f"""You are HorizonByte, an advanced neural AI assistant in a cyber-terminal environment.
Your personality is {personality_desc}.
Answer the user's question based on the provided context. If the context does not contain the answer, state that there is insufficient data.

DOCUMENT CONTEXT:
{context_str}

RECENT CHAT HISTORY (Last 5 minutes):
{chat_history}

USER QUERY:
{query}

AI RESPONSE:"""

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
            
        return response.text.strip()
    except Exception as e:
        return f"[SYSTEM ERROR] Could not connect to neural uplink: {str(e)}"

import json

def generate_suggestions(context_summary: str, chat_history: str, model_name: str = "gemini-2.5-flash") -> list[str]:
    if not api_key:
        return ["System status kya hai?", "Pichla task dikhao", "Data analyze karo", "Mujhe summary chahiye"]
        
    prompt = f"""You are HorizonByte, an advanced neural AI assistant in a cyber-terminal environment.
Generate exactly 4 short, action-oriented, or highly relevant follow-up questions/prompts that the user might want to click next, based on the uploaded document summary and recent chat history.
Each suggestion should be under 40 characters and read like a terminal command or short query.
Wrap the 4 strings in a JSON array. Do not include markdown formatting like ```json.

DOCUMENT SUMMARY:
{context_summary}

RECENT CHAT HISTORY:
{chat_history}

JSON ARRAY OF 4 SUGGESTIONS:"""

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        # Fallback to static if it fails
        return ["System status kya hai?", "Pichla task dikhao", "Data analyze karo", "Mujhe summary chahiye"]

def rephrase_text(text: str, tone: str, model_name: str = "gemini-2.5-flash") -> str:
    if not api_key:
        return "ERROR: GEMINI_API_KEY environment variable is not set."
        
    prompt = f"""You are HorizonByte, an advanced neural AI assistant. 
The user provided a text written in Hinglish (a mix of Hindi and English) or English.
Please translate/rephrase it entirely into English using a '{tone}' tone. 
Return ONLY the final translated/rephrased English string, nothing else.

ORIGINAL TEXT:
{text}

REPHRASED TEXT ({tone} TONE):"""

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[SYSTEM ERROR] Rephrase failed: {str(e)}"

