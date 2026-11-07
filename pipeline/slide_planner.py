import json
import os

OUTPUT_DIR = "outputs"

def plan_slides(analysis: dict, metadata: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    slides = []

    slides.append({
        "slide_number": 1,
        "type": "hook",
        "title": analysis["theme"],
        "bullets": [],
        "visual_hint": "bold typography, high contrast"
    })

    for i, point in enumerate(analysis["key_points"][:5], start=2):
        slides.append({
            "slide_number": i,
            "type": "content",
            "title": point,
            "bullets": [],
            "visual_hint": "minimal icons, clean layout"
        })

    slides.append({
        "slide_number": len(slides) + 1,
        "type": "cta",
        "title": "Follow for more insights",
        "bullets": [],
        "visual_hint": "branding colors"
    })

    with open(os.path.join(OUTPUT_DIR, "slides.json"), "w") as f:
        json.dump(slides, f, indent=2)

    return slides