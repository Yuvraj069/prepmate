# PrepMate

PrepMate is an AI interview coach for technical and non-technical roles. It has a no-JavaScript Flask frontend, cloud-ready authentication, Foundry-compatible GenAI coaching, and Azure AI Speech integration.

## Run locally

1. Create a virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env` and add your cloud credentials (optional for the local demo).
3. Run `python app.py`, then open `http://127.0.0.1:5000`.

Without credentials, you can still register an in-memory demo user and explore every interface. Add credentials to make the integrations live.

## Cloud deployment

- **Authentication/session:** Create a Supabase project, enable Email auth, then set `SUPABASE_URL` and `SUPABASE_KEY` in your deployment environment. Supabase stores user accounts; PrepMate keeps the signed-in session in a secure Flask cookie.
- **AI / agent:** Deploy a chat model in Microsoft Foundry/Azure OpenAI and set `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_DEPLOYMENT`. If you use a Microsoft Foundry project endpoint ending in `services.ai.azure.com/openai/v1`, PrepMate uses your Azure sign-in locally; run `az login` once and leave `AZURE_OPENAI_API_KEY` empty. Standard Azure OpenAI endpoints still use `AZURE_OPENAI_API_KEY`.
- **RAG:** Create an Azure AI Search index containing approved interview guides with `content` (and optionally `title`) fields. Set `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_KEY`, and `AZURE_SEARCH_INDEX`; retrieved references are supplied to the coaching agent before it responds.
- **Voice:** Create an Azure AI Speech resource and set the `AZURE_SPEECH_*` values. Users can play a coach response or upload a recording for transcription without browser JavaScript.

For a free starter deployment, deploy this Flask app to Render and set the same values in its Environment settings. For Azure, use Azure App Service with Python 3.11+ and set the app command to `gunicorn app:app` (add `gunicorn` to requirements for that route).
