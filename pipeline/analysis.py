from openai import OpenAI
import os
import json
import re

# Initialize OpenRouter client
# OpenRouter provides access to multiple LLM models through a unified API
# https://openrouter.ai/
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
)

def analyse_transcript(transcript_path: str) -> dict:
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    prompt = """
You are an expert content analyst.

Task:
1. Identify the core theme of the video.
2. Extract the most important ideas.
3. Ignore filler and repetition.

Return STRICT JSON with:
- theme
- key_points (array of strings)
- notable_quotes (array of strings)
"""

    response = client.chat.completions.create(
        model=os.getenv("OPENROUTER_TEXT_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": transcript + "\n\n" + prompt}
        ]
    )

    content = response.choices[0].message.content
    
    # Extract JSON from markdown code blocks if present
    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        content = json_match.group(1)
    elif content.startswith('```') and content.endswith('```'):
        # Handle code blocks without language specification
        content = content.strip('```').strip()
    
    return json.loads(content)