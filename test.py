import os
import google.generativeai as genai

env_path = r'd:\CODING\PROJECTS\HorizonByte - A RAG Chat AI\backend\.env'
api_key = None
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('GEMINI_API_KEY='):
                api_key = line.strip().split('=', 1)[1].strip('"\'')
                break

if not api_key:
    api_key = os.environ.get('GEMINI_API_KEY')

if api_key:
    genai.configure(api_key=api_key)
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print('Available models for generateContent:')
        for m in models:
            print(m)
    except Exception as e:
        print('Error calling API:', e)
else:
    print('No API key found.')
