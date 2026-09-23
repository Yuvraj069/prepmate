# PrepMate 🎯

> **AI-powered interview coaching for technical and non-technical roles**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-prepmate--b2fc.onrender.com-blue?style=flat-square)](https://prepmate-b2fc.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-black?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![Azure](https://img.shields.io/badge/Azure%20AI-Foundry-0078D4?style=flat-square&logo=microsoftazure&logoColor=white)](https://ai.azure.com)

---

## 👥 Team

| Name | Role |
|---|---|
| **Rhythm Gupta** | Team Member |
| **Ananya Punj** | Team Member |
| **Akshit Rawat** | Team Member |
| **Akashdeep Matharu** | Team Member |
| **Yuvraj Sharma** | Team Member |

---

## 📌 Problem Statement

Job seekers — especially students and early-career professionals — struggle to prepare effectively for interviews. Generic guides and YouTube videos offer one-size-fits-all advice, while professional interview coaching costs hundreds of dollars per session and is inaccessible to most.

**The gap:** No affordable, personalised, always-available coach exists that can ask real interview questions, evaluate structured answers, and give actionable feedback across both technical and non-technical tracks.

---

## 💡 Solution Overview

PrepMate is a web-based AI interview coach that gives every user a personal, always-on coaching session. It supports **six interview tracks** across tech and non-tech roles and operates in two modes:

- **Practice Mode** — the AI asks a real interview question, evaluates your answer for structure, clarity, and evidence, then asks a targeted follow-up.
- **Ask Mode (Open Coaching)** — a free-form chatbot where users can ask anything about interview strategy, answer structure, or role-specific advice.

Both modes include **voice output** (browser TTS reads coach responses aloud) and **voice input** (mic button streams your spoken answer into the text box in real time).

---

## 🏗️ Solution Architecture & Data Flow

PrepMate is built as a **Flask web application** hosted on Render. When a user opens the app in their browser, all page interactions happen over HTTPS. Here is how the main pieces connect:

The **browser** is responsible for rendering the UI and handling all voice features locally — it uses the built-in Web Speech API to read coach responses aloud and transcribe mic input into text, with no extra server calls needed.

The **Flask app** sits at the centre. It handles login and session management through **Supabase** (a cloud database and auth service that stores user accounts). When a user submits an answer or asks a question, Flask passes the request to the **InterviewCoach** module, which first checks **Azure AI Search** for any relevant interview knowledge to use as context (this is the RAG step), then sends the full conversation to **Azure AI Foundry** (running a GPT-4o model) to generate a personalised coaching response. That response is returned to the browser and displayed on screen.

In short, the data flows like this:

1. **User signs in** → Flask verifies credentials with Supabase and stores the session in a secure cookie.
2. **User submits an answer or question** → Flask calls the InterviewCoach, which fetches relevant context from Azure AI Search, then asks Azure AI Foundry (GPT-4o) for a coaching response.
3. **Coach reply is displayed** → the browser renders the text; the user can click **Listen** to have it read aloud via the browser's built-in speech engine.
4. **Voice input** → the user can click the mic button; the browser transcribes speech directly into the text box in real time, again with no server involvement.



---

## 🛠️ Technology Stack

### Backend

| Layer | Technology |
|---|---|
| Web framework | **Flask 3.1** (Python 3.11+) |
| WSGI server | **Gunicorn** |
| Auth & database | **Supabase** (PostgreSQL + Auth) |
| Session | Secure Flask cookie |
| Env config | `python-dotenv` |

### AI Services & Models

| Service | Purpose |
|---|---|
| **Azure AI Foundry / Azure OpenAI** | Core LLM — GPT-4o (or any deployed chat model) via the OpenAI Python SDK using the `/v1` chat completions endpoint |
| **Azure AI Search** | Optional RAG — retrieves relevant interview coaching material to ground the model's responses |
| **Browser `SpeechSynthesis` API** | Text-to-speech — coach responses read aloud in the user's browser, zero API keys needed |
| **Browser `SpeechRecognition` API** | Speech-to-text — live mic transcription streamed into the answer textarea |

### Frontend

| Layer | Technology |
|---|---|
| Templating | **Jinja2** (Flask) |
| Styling | Vanilla CSS (custom design system) |
| Voice | Web Speech API (browser-native, no SDK) |

### Infrastructure

| Service | Role |
|---|---|
| **Render** | Flask app hosting (free tier, auto-deploy from GitHub) |
| **Supabase** | Managed PostgreSQL + Auth (free tier) |
| **GitHub** | Source control & CI trigger for Render auto-deploy |

---

## ⚙️ Setup Instructions

### Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project with **Email** auth enabled
- An [Azure AI Foundry](https://ai.azure.com) project with a deployed chat model (e.g. GPT-4o)

### 1. Clone & install

```bash
git clone https://github.com/Yuvraj069/prepmate.git
cd prepmate
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
# Flask
FLASK_SECRET_KEY=your-long-random-secret

# Supabase — enables cloud auth
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Azure AI Foundry — enables AI coaching
AZURE_OPENAI_ENDPOINT=https://your-resource.services.ai.azure.com/openai/v1
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Azure AI Search — optional RAG grounding
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=interview-knowledge

# Azure AI Speech — optional server-side TTS/STT fallback
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=eastus
```

> **Note:** Without any credentials you can still run the app locally — a demo in-memory user is used and the AI coach returns a helpful fallback message.

### 3. Run locally

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

### 4. Deploy to Render

1. Push the repo to GitHub.
2. Create a new **Web Service** on [Render](https://render.com), connect your repo, and set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
3. Add all `.env` values as **Environment Variables** in the Render dashboard.
4. Every push to `main` triggers an automatic redeploy.

---

## 🧪 Testing & Results

### Functional Testing

| Feature | Status | Notes |
|---|---|---|
| User registration & login | ✅ Pass | Supabase email auth |
| In-memory demo login | ✅ Pass | Works without Supabase keys |
| Practice mode — question display | ✅ Pass | All 6 tracks |
| Practice mode — answer evaluation | ✅ Pass | GPT-4o feedback with RAG grounding |
| Ask mode — chatbot | ✅ Pass | Multi-turn conversation history (last 8 turns) |
| Voice output (Listen button) | ✅ Pass | Browser `speechSynthesis`; Chrome, Safari, Edge |
| Voice input (mic button) | ✅ Pass | Browser `SpeechRecognition`; Chrome/Edge best |
| Render deployment | ✅ Pass | Auto-deploy from GitHub `main` |

### AI Response Quality

The model is prompted to:
- Give **concise, structured** feedback (what worked, one improvement, a follow-up question)
- **Never fabricate** facts the candidate did not state
- Ground answers in retrieved knowledge base references when available

Manual testing across all 6 tracks showed contextually accurate, track-specific feedback. Fallback hardcoded responses are returned if the API call fails, ensuring the UI is never broken.

---

## ⚠️ Known Limitations

| Limitation | Detail |
|---|---|
| **In-memory sessions** | Practice history and chat are stored in Flask's session cookie; they are lost on server restart or if the cookie exceeds ~4 KB |
| **Single fixed question per track** | Each track currently has one opening question; there is no question bank or randomisation |
| **No persistent history** | Past sessions are not saved to the database; each browser session starts fresh |
| **SpeechRecognition browser support** | Live mic input requires Chrome or Edge; Firefox has limited support; Safari is partial |
| **RAG index required** | Without an Azure AI Search index the coach responds without grounding context; quality is still good but not customised to specific materials |
| **Free-tier cold starts** | Render's free tier spins down after inactivity; the first request after a sleep period can take 30–60 seconds |

---

## 🚀 Future Improvements

- [ ] **Question bank & randomisation** — multiple questions per track shuffled each session to prevent repetition
- [ ] **Persistent session history** — store conversation history in Supabase so users can review past sessions
- [ ] **Answer scoring** — quantitative rubric (structure, specificity, relevance) displayed alongside qualitative feedback
- [ ] **Custom RAG content** — allow users or admins to upload their own company guides, job descriptions, or CV for personalised coaching
- [ ] **Timed mock interviews** — countdown timer and pacing feedback
- [ ] **Progress dashboard** — track improvement across sessions with charts
- [ ] **Multi-language support** — extend voice and coaching to non-English interviews
- [ ] **Mobile app** — React Native wrapper for native mic access and push reminders
