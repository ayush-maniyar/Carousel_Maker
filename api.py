import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from orchestrator import generate_carousel_content
from renderer import render_carousel_slide

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
