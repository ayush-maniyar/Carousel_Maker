from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from orchestrator import generate_carousel_content
from renderer import render_carousel_slide
import os

app = FastAPI()

# Enable CORS for Next.js communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static directory to serve generated slide images
os.makedirs("output_slides", exist_ok=True)
app.mount("/output_slides", StaticFiles(directory="output_slides"), name="output_slides")

class CarouselRequest(BaseModel):
    transcript_text: str
    persona: str = "General Audience"
    slide_count: int = 5
    colour_scheme: str = "Yellow and Green"
    vibe: str = "modern"

@app.post("/generate-carousel")
def create_carousel(req: CarouselRequest):
    try:
        if not req.transcript_text or len(req.transcript_text.strip()) < 20:
            raise HTTPException(status_code=400, detail="Transcript text is missing or too short.")

        # 1. Generate slide content via CrewAI
        carousel_data = generate_carousel_content(
            transcript_text=req.transcript_text,
            persona=req.persona,
            slide_count=req.slide_count,
            vibe=req.vibe
        )

        # 2. Render each slide using the visual engine
        rendered_files = []
        slides = carousel_data.get("slides", [])

        for i, slide_data in enumerate(slides, start=1):
            slide_data["total_slides"] = len(slides)
            filename = f"slide_{i}.png"
            file_path = render_carousel_slide(
                slide_data=slide_data,
                output_filename=filename,
                colour_scheme=req.colour_scheme,
                vibe=req.vibe
            )
            # Normalize path for frontend URL consumption
            rendered_files.append(file_path.replace("\\", "/"))

        return {
            "status": "success",
            "title": carousel_data.get("title", "Untitled Carousel"),
            "slides_generated": len(rendered_files),
            "files": rendered_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))