import os
from crewai import Agent, Task, Crew, Process, LLM
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Slide(BaseModel):
    slide_number: int = Field(description="Sequential slide number")
    header: str = Field(description="Impactful section title, completely organic in length")
    bullet_points: List[str] = Field(description="Core insights, facts, or plot points without markdown symbols.")
    icon_type: str = Field(description="Visual theme keyword (e.g., 'history', 'tech', 'story', 'target')")
    layout_style: str = Field(description="Visual layout choice: 'editorial_flow', 'headline_focus', or 'deep_dive'")

class Carousel(BaseModel):
    title: str = Field(description="Viral headline for the carousel")
    slides: List[Slide] = Field(description="Structured carousel slides")

def generate_carousel_content(transcript_text: str, persona: str, slide_count: int = 5, vibe: str = "modern") -> dict:
    nemotron_llm = LLM(
        model="openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    researcher = Agent(
        role="Content Strategist & Analyst",
        goal="Analyze the provided transcript, determine the core intent of the video (e.g., narrative story, technical tutorial, opinion piece), and extract the most valuable beats accordingly.",
        backstory="You are a master at understanding context. You know that a story needs its plot explained chronologically, while a tutorial needs its steps outlined. You autonomously adapt your extraction strategy to perfectly match the source material.",
        verbose=True,
        llm=nemotron_llm,
        max_tokens=4000
    )

    copywriter = Agent(
        role="Carousel Content Architect",
        goal=f"Convert the researcher’s insights into structured, clean slide copy for: {persona}. Vibe requested: {vibe}.",
        backstory=(
            "You design professional carousels. "
            "CRITICAL RULES: "
            "1. ABSOLUTELY NO MARKDOWN: Do NOT use symbols like ** or __. "
            "2. DYNAMIC TEXT DENSITY: You must match your text length to the layout_style: "
            "   - 'headline_focus': 1-2 punchy bullets for quick impact. "
            "   - 'editorial_flow': 3 medium bullets telling a connected story. "
            "   - 'deep_dive': 4-5 detailed bullets explaining a complex mechanism. "
            "3. Adapt naturally. Do not leave 'deep_dive' slides empty, but do not clutter 'headline_focus' slides."
        ),
        verbose=True,
        llm=nemotron_llm,
        max_tokens=4000
    )

    task1 = Task(
        description=f"Analyze the following video transcript: \n\n{transcript_text}\n\nIdentify if it is a story, tutorial, or essay, and extract the key chronological points or steps based on that classification.",
        expected_output="Clear, perfectly adapted breakdown of the video's actual events, core points, or plot.",
        agent=researcher
    )

    task2 = Task(
        description=(
            f"Create exactly {slide_count} structured carousel slides. "
            f"The overall aesthetic vibe must be: '{vibe}'. "
            "CRITICAL: Each slide must contain an impactful header, clean bullet points (NO MARKDOWN), an icon_type keyword, and a layout_style. "
            "Return strictly as the Carousel schema."
        ),
        expected_output=f"A valid Carousel object containing exactly {slide_count} slides with perfectly clean text.",
        agent=copywriter,
        output_pydantic=Carousel
    )

    crew = Crew(
        agents=[researcher, copywriter],
        tasks=[task1, task2],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    if hasattr(result, "pydantic") and result.pydantic:
        return result.pydantic.model_dump()
    return result.raw


