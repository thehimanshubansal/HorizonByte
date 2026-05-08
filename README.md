# HorizonByte

**HorizonByte** is a cutting-edge Neural AI Assistant engineered with a custom Retrieval-Augmented Generation (RAG) architecture. Built with a lightweight Python/FastAPI backend and a highly stylized Cyber-Brutalist frontend, it allows users to chat with their documents, extract insights, and refine their writing seamlessly.

## 🚀 Features

- **Document Chat (RAG)**: Upload PDF or TXT files. The system utilizes recursive semantic chunking and FAISS vector indexing to ensure high-context accuracy.
- **Powered by Gemini**: Driven by the bleeding-edge Google Gemini 2.5 (Flash/Pro) models for fast and deep reasoning.
- **Hinglish Rephrase Engine**: A specialized module that translates and restructures natural Hinglish thoughts into formal, professional, or casual English.
- **Cyber-Brutalist Aesthetics**: A terminal-inspired, high-bandwidth UI utilizing Tailwind CSS with multiple theme presets (Cobalt Blue, Hacker Green, Amber Alert, Crimson).
- **Fully Configurable**: Easily change AI personas, neural models, and chunking sizes directly from the UI config menu.

## 🛠️ Tech Stack

- **Backend**: FastAPI, Uvicorn
- **AI / LLM**: `google-generativeai` (Gemini 2.5)
- **Vector Store**: FAISS (`faiss-cpu`)
- **Embeddings**: `sentence-transformers`
- **Document Parsing**: PyMuPDF
- **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS (CDN)

## ⚙️ Local Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/HorizonByte.git
cd HorizonByte
```

### 2. Set up a Python Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
You will need a Google Gemini API key to run the models.
Ensure your environment has the API key set. You can set it in your terminal before running:
```bash
# On Windows
set GEMINI_API_KEY=your_api_key_here
# On macOS/Linux
export GEMINI_API_KEY=your_api_key_here
```
*(Alternatively, you can create a `.env` file if you have configured python-dotenv).*

### 5. Run the Application
Start the FastAPI server using Uvicorn:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Access the App
Open your web browser and navigate to:
`http://localhost:8000`

## 🌐 Deployment (Render)

HorizonByte can be easily deployed as a Web Service on platforms like Render:
1. Connect your repository to Render.
2. Select **Python 3** as the runtime environment.
3. Set Build Command: `pip install -r requirements.txt`
4. Set Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add your `GEMINI_API_KEY` to the Environment Variables tab.
6. Deploy!

*(Note: If using ephemeral file systems like Render's free tier, uploaded documents and FAISS indices will reset upon service restart).*

## 📄 License
This project is for educational and personal use.
