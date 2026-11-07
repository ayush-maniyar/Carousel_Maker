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
