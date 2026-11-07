import logging
import os
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi

from orchestrator import generate_carousel_content
from renderer import render_carousel_slide

logger = logging.getLogger(__name__)

app = FastAPI(title="Carousel Maker API")

# Set FRONTEND_URL in Render to your deployed Vercel URL.
# Local development remains supported by the default localhost origin.
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

# Generated images are served from this directory.
os.makedirs("output_slides", exist_ok=True)
app.mount(
    "/output_slides",
    StaticFiles(directory="output_slides"),
    name="output_slides",
)


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
def get_transcript(payload: dict):
    video_url = payload.get("video_url", "")
    if not isinstance(video_url, str) or not video_url.strip():
        raise HTTPException(status_code=400, detail="A YouTube video URL is required.")

    video_id = extract_youtube_video_id(video_url.strip())
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id)
        transcript_text = " ".join(
            item["text"] for item in transcript.to_raw_data()
            if item.get("text")
        ).strip()
        if not transcript_text:
            raise HTTPException(status_code=404, detail="No transcript is available for this video.")
        return {"text": transcript_text}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("YouTube transcript fetch failed for video ID %s", video_id)
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve this video's captions. Check the Render logs for the underlying YouTubeTranscriptApi error.",
        ) from exc


@app.post("/generate-carousel")
def create_carousel(req: CarouselRequest):
    try:
        if not req.transcript_text or len(req.transcript_text.strip()) < 20:
            raise HTTPException(
                status_code=400,
                detail="Transcript text is missing or too short.",
            )

        if not os.getenv("OPENROUTER_API_KEY"):
            raise HTTPException(
                status_code=500,
                detail="OPENROUTER_API_KEY is not configured on the backend.",
            )

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
