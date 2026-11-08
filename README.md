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

The backend uses Supadata for YouTube captions. It requests `mode=native` first, so it only retrieves existing captions. If none exist, the frontend asks the user before the backend calls `mode=generate`.

Configure these variables in Render (never in frontend code):

- `SUPADATA_API_KEY` — required; Supadata API key.
- `SUPABASE_URL` — optional; Supabase project URL for persistent transcript caching.
- `SUPABASE_SERVICE_ROLE_KEY` — optional; Supabase service-role key. Keep this secret and backend-only.

To enable the persistent cache, create a Supabase project, open its SQL Editor, and run the contents of `supabase/transcripts.sql`. If Supabase is not configured, transcript retrieval still works but transcripts will not persist across backend restarts.

The cache stores one transcript per video ID and language. Native and AI-generated transcripts are both cached. The frontend accepts the language Supadata actually returns; the existing language is passed to the content model without an intermediate translation call.
