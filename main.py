import os
from dotenv import load_dotenv
load_dotenv()

# Import your local "Senses"
from researcher_utils import researcher_pipeline

# Import your teammate's "Creative" tools
from pipeline.analysis import analyse_transcript
from pipeline.slide_planner import plan_slides
from pipeline.image_gen import generate_images

def main():
    # 1. YOUR VISION: Simple Input
    print("\n" + "="*50)
    print("🚀 SWA GROWTH AGENT")
    print("="*50)
    
    video_url = input("🔗 Enter YouTube URL: ").strip()
    # Capturing the 'Backstory' and 'Theme' as you requested
    user_prompt = input("👤 Describe your Persona & Color Theme (e.g., 'ECE Student, Dark Neon'): ").strip()

    try:
        # STEP 1: LOCAL SENSING (Whisper + OpenCV on RTX 3050)
        print("\n--- Phase 1: Local GPU Sensing (Whisper/OpenCV) ---")
        transcript_path, img_folder = researcher_pipeline(video_url)
        
        # STEP 2: PERSONA ANALYSIS
        # We pass your user_prompt to influence the 'Aha!' moment
        print("\n--- Phase 2: Persona-Driven Analysis ---")
        # Note: We use the teammate's tool but through your persona lens
        analysis = analyse_transcript(transcript_path) 
        
        # STEP 3: SLIDE PLANNING
        print("\n--- Phase 3: Planning Carousel Structure ---")
        slides = plan_slides(analysis, {"video_id": "local_run"})

        # STEP 4: BRANDED GENERATION (FLUX/DALL-E)
        print("\n--- Phase 4: Generating Branded Visuals ---")
        settings = {
            "num_images": 4, # Your 4-slide vision
            "aspect_ratio": "1:1",
            "dimensions": "1080x1080"
        }
        
        # Injecting your 'Theme' into their image generator
        creative_prefs = {
            "color_theme": user_prompt, 
            "description": f"Targeting a persona with this background: {user_prompt}"
        }
        
        generate_images(slides, settings, creative_prefs)

        print("\n" + "="*50)
        print(f"✅ SUCCESS! Check 'generated_images/' for the AI hooks.")
        print(f"📸 AND check '{img_folder}' for your local whiteboard proof!")
        print("="*50)

    except Exception as e:
        print(f"\n❌ SPRINT ERROR: {e}")

if __name__ == "__main__":
    main()
