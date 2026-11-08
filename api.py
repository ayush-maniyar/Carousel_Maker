import logging
import os
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from orchestrator import generate_carousel_content
from renderer import render_carousel_slide
from transcript_service import get_video_transcript

logger = logging.getLogger(__name__)

app = FastAPI(title="Carousel Maker API")

frontend_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_URL", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("output_slides", exist_ok=True)
app.mount("/output_slides", StaticFiles(directory="output_slides"), name="output_slides")


class TranscriptRequest(BaseModel):
    video_url: str
    allow_ai_fallback: bool = False


class CarouselRequest(BaseModel):
    transcript_text: str
    persona: str = "General Audience"
    slide_count: int = 5
    colour_scheme: str = "Yellow and Green"
    vibe: str = "modern"


@app.get("/health")
def health_check():
    return {"status": "ok"}


def extract_youtube_video_id(video_url: str) -> str:
    parsed = urlparse(video_url)
    host = (parsed.hostname or "").lower()

    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
    elif host.endswith("youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        else:
            parts = [part for part in parsed.path.split("/") if part]
            video_id = parts[1] if len(parts) > 1 and parts[0] in {"shorts", "embed", "live"} else ""
    else:
        video_id = ""

    if not video_id or len(video_id) != 11:
        raise HTTPException(status_code=400, detail="Please provide a valid YouTube video URL.")
    return video_id


@app.post("/transcript")
def get_transcript(payload: TranscriptRequest):
    if not payload.video_url.strip():
        raise HTTPException(status_code=400, detail="A YouTube video URL is required.")

    video_id = extract_youtube_video_id(payload.video_url.strip())
    try:
        result = get_video_transcript(
            video_id=video_id,
            video_url=payload.video_url.strip(),
            allow_ai_fallback=payload.allow_ai_fallback,
        )
        return result
    except RuntimeError as exc:
        logger.exception("Supadata transcript request failed for video ID %s", video_id)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc


@app.post("/generate-carousel")
def create_carousel(req: CarouselRequest):
    try:
        if not req.transcript_text or len(req.transcript_text.strip()) < 20:
            raise HTTPException(status_code=400, detail="Transcript text is missing or too short.")

        if not os.getenv("OPENROUTER_API_KEY"):
            raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is not configured on the backend.")

        carousel_data = generate_carousel_content(
            transcript_text=req.transcript_text,
            persona=req.persona,
            slide_count=req.slide_count,
            vibe=req.vibe,
        )

        rendered_files = []
        slides = carousel_data.get("slides", [])

        for i, slide_data in enumerate(slides, start=1):
            slide_data["total_slides"] = len(slides)
            filename = f"slide_{i}.png"
            file_path = render_carousel_slide(
                slide_data=slide_data,
                output_filename=filename,
                colour_scheme=req.colour_scheme,
                vibe=req.vibe,
            )
            rendered_files.append(file_path.replace("\\", "/"))

        return {
            "status": "success",
            "title": carousel_data.get("title", "Untitled Carousel"),
            "slides_generated": len(rendered_files),
            "files": rendered_files,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Carousel generation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
