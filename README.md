# Carousel Maker

Turn video transcripts into polished, AI-generated social media carousels.

Carousel Maker takes transcript text, analyzes its key ideas, plans a slide-by-slide narrative, and generates branded carousel visuals.

## Project structure

- `api.py` — FastAPI endpoint for carousel generation
- `orchestrator.py` — AI-powered carousel content planning
- `renderer.py` — Slide rendering
- `pipeline/` — Transcript analysis, slide planning, and image generation
- `frontend/` — Next.js web interface
- `tests/` — Project tests

## Tech stack

- Python, FastAPI, Pydantic
- Next.js, React, TypeScript
- CrewAI and model APIs for content generation
- Image-generation pipeline for slide visuals

## Getting started

### Backend

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure the environment variables required by the integrations you use. Keep API keys in a local `.env` file; never commit secrets.
4. Start the API:

   ```bash
   uvicorn api:app --reload
   ```

### Frontend

1. Change into the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies and start the development server:

   ```bash
   npm install
   npm run dev
   ```

Check the frontend package scripts and backend configuration for any additional setup required by your environment.

## Security

Do not commit `.env` files, API keys, credentials, or generated private data. Use environment variables and the provided ignore rules.

## License

No license has been specified for this repository yet. Add a license before granting reuse rights.


## Transcript provider setup (Supadata + optional Supabase cache)

The backend uses Supadata for YouTube captions. It requests `mode=native` first, so it only retrieves existing captions. If none exist, the backend issues a short-lived, single-use consent token. The browser submits that token only after the user approves; the backend validates and consumes it before calling `mode=generate`. This is an anonymous abuse-resistance measure, not proof of a person's identity or a substitute for rate limiting.

Configure these variables in Render (never in frontend code):

- `SUPADATA_API_KEY` — required; Supadata API key.
- `SUPABASE_URL` — required for persistent transcript caching, consent tokens, and generation coordination.
- `SUPABASE_SERVICE_ROLE_KEY` — required for the same features. Keep this secret and backend-only.

Create a Supabase project, open its SQL Editor, and run the complete contents of `supabase/transcripts.sql`. This creates the transcript cache, one-time consent-token store, and per-video generation lease table. AI transcription is deliberately unavailable unless these backend protections can be stored. Do not run this SQL on a production database until you have reviewed the migration and backed up any existing data.

The cache stores one transcript per video ID and language. Native and AI-generated transcripts are both cached. The frontend accepts the language Supadata actually returns; the existing language is passed to the content model without an intermediate translation call.


AI transcription consent tokens expire after 10 minutes and can be used once for the video for which they were issued. A database lease prevents concurrent requests from starting duplicate AI transcription jobs; requests that encounter an active job wait briefly for the shared cache. Supadata polling uses a bounded deadline and retries transient polling failures. Do not blindly retry a transcript-generation submission after a network timeout because the provider may already have accepted it.

Run backend unit tests with `python -m unittest discover -s tests`.
