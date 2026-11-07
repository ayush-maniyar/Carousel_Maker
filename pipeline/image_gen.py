import os
from PIL import Image, ImageDraw, ImageFont
import textwrap

def draw_icon(draw, icon_type, x, y, color):
    """Draws clean minimalist vector icons programmatically."""
    if icon_type == "camera":
        # Camera body & lens
        draw.rounded_rectangle([x, y+8, x+38, y+32], radius=6, outline=color, width=3)
        draw.ellipse([x+12, y+12, x+26, y+26], outline=color, width=3)
        draw.rectangle([x+13, y+3, x+19, y+8], fill=color)
    elif icon_type == "code":
        # Code brackets </->
        font = ImageFont.load_default()
        draw.text((x+2, y+6), "</>", fill=color, font=font)
    elif icon_type == "target":
        draw.ellipse([x+2, y+2, x+34, y+34], outline=color, width=3)
        draw.ellipse([x+11, y+11, x+25, y+25], outline=color, width=3)
        draw.point((x+18, y+18), fill=color)
    else: # Default chart/metrics
        draw.rectangle([x+3, y+20, x+10, y+34], fill=color)
        draw.rectangle([x+14, y+12, x+21, y+34], fill=color)
        draw.rectangle([x+25, y+4, x+32, y+34], fill=color)

def generate_images(slides, size_config, style_config):
    os.makedirs("generated_images", exist_ok=True)
    
    bg_color = (12, 18, 28)
    card_fill = (22, 32, 48, 230)
    text_primary = (255, 255, 255)
    
    accent_color = (65, 140, 245)
    if "red" in style_config.lower():
        accent_color = (235, 60, 60)

    for slide in slides:
        slide_num = slide.get("slide_number", 1)
        header_text = slide.get("header", "Key Insights")
        bullets = slide.get("bullet_points", [])
        icon_type = slide.get("icon_type", "target")
        
        img = Image.new("RGBA", (1024, 1024), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Blueprint grid lines
        for x in range(0, 1024, 96): draw.line([(x, 0), (x, 1024)], fill=(24, 34, 50), width=1)
        for y in range(0, 1024, 96): draw.line([(0, y), (1024, y)], fill=(24, 34, 50), width=1)

        try:
            font_title = ImageFont.truetype("arial.ttf", size=36)
            font_body = ImageFont.truetype("arial.ttf", size=26)
            font_slide_num = ImageFont.truetype("arial.ttf", size=22)
        except:
            font_title = font_body = font_slide_num = ImageFont.load_default()

        # Structured Card Container (Safe bounds: 70 to 930)
        draw.rounded_rectangle([70, 140, 954, 900], radius=20, fill=card_fill, outline=accent_color, width=2)
        
        # Header Banner
        draw.rounded_rectangle([110, 180, 600, 256], radius=12, fill=accent_color)
        draw.text((130, 195), header_text.upper(), fill=text_primary, font=font_title)
        
        # Draw Topic Icon top-right inside card
        draw_icon(draw, icon_type, 870, 190, accent_color)
        
        # Slide Counter
        draw.text((880, 100), f"{slide_num}/5", fill=(150, 170, 200), font=font_slide_num)

        # Render Bullets with Safe Overflow Padding
        y_cursor = 300
        for bullet in bullets:
            wrapped = textwrap.wrap(f"• {bullet}", width=48)
            for line in wrapped:
                draw.text((110, y_cursor), line, fill=text_primary, font=font_body)
                y_cursor += 36
            y_cursor += 16

        img.convert("RGB").save(f"generated_images/slide_{slide_num}.png", "PNG")
        print(f"✨ Built overflow-protected slide {slide_num} with {icon_type} icon")