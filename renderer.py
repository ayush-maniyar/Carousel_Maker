from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

def parse_color(color_input: str, default_rgb: tuple) -> tuple:
    """Parses text color descriptions into RGB tuples."""
    if isinstance(color_input, tuple):
        return color_input
    text = str(color_input).lower()
    if 'yellow' in text: return (234, 179, 8)
    elif 'green' in text: return (34, 197, 94)
    elif 'red' in text or 'crimson' in text: return (239, 68, 68)
    elif 'blue' in text: return (59, 130, 246)
    elif 'black' in text: return (15, 15, 15)
    return default_rgb

def wrap_text(text: str, max_width: int, font: ImageFont.FreeTypeFont) -> list:
    """Dynamically wraps text into multiple lines based on available canvas width."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = font.getbbox(test_line)
        if (bbox[2] - bbox[0]) <= max_width:
            current_line = test_line
        else:
            if current_line: lines.append(current_line)
            current_line = word
    if current_line: lines.append(current_line)
    return lines

def load_font(size: int, vibe: str = "modern") -> ImageFont.ImageFont:
    """Load a portable font on Linux/Windows, with a guaranteed Pillow fallback."""
    preferred = "cinzel.ttf" if "medieval" in vibe.lower() else "arial.ttf"
    candidates = [
        os.path.join(os.path.dirname(__file__), "assets", "fonts", preferred),
        os.path.join(os.path.dirname(__file__), "assets", "fonts", "DejaVuSans.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        preferred,
    ]
    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue

    # Pillow's bundled bitmap font is always available; size is supported by
    # current Pillow releases, while the TypeError fallback keeps older ones working.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def render_carousel_slide(slide_data: dict, output_filename: str, colour_scheme: str = "Yellow and Green", vibe: str = "modern"):
    width, height = 1080, 1350
    
    # 1. Colors & Theme Setup
    bg_color = (10, 12, 16) if 'black' not in colour_scheme.lower() else (5, 5, 5)
    accent_color = parse_color(colour_scheme, (234, 179, 8))
    secondary_accent = (34, 197, 94) if 'green' in colour_scheme.lower() else (148, 163, 184)
    text_color = (241, 245, 249)

    base_image = Image.new("RGBA", (width, height), bg_color + (255,))
    bg_draw = ImageDraw.Draw(base_image)

    # 2. Glowing Background Orbs
    bg_draw.ellipse([-200, -200, 500, 500], fill=accent_color + (25,))
    bg_draw.ellipse([600, 900, 1300, 1600], fill=secondary_accent + (15,))

    # 3. Dynamic Thematic Symbols
    icon_type = slide_data.get('icon_type', '').lower()
    symbol_color = accent_color + (40,)
    
    if 'video' in icon_type or 'camera' in icon_type or 'film' in icon_type:
        bg_draw.ellipse([600, 150, 900, 450], outline=symbol_color, width=15)
        bg_draw.ellipse([675, 225, 825, 375], outline=symbol_color, width=5)
    elif 'target' in icon_type or 'war' in icon_type:
        bg_draw.ellipse([650, 150, 950, 450], outline=symbol_color, width=8)
        bg_draw.line([800, 100, 800, 500], fill=symbol_color, width=8)
        bg_draw.line([600, 300, 1000, 300], fill=symbol_color, width=8)
    elif 'code' in icon_type or 'tech' in icon_type:
        try:
            bracket_font = load_font(350, vibe)
            bg_draw.text((650, 50), "{ }", fill=symbol_color, font=bracket_font)
        except:
            pass
    elif 'chart' in icon_type or 'growth' in icon_type or 'history' in icon_type:
        bg_draw.rectangle([650, 350, 700, 450], fill=symbol_color)
        bg_draw.rectangle([750, 250, 800, 450], fill=symbol_color)
        bg_draw.rectangle([850, 150, 900, 450], fill=symbol_color)

    base_image = base_image.filter(ImageFilter.GaussianBlur(radius=40))

    # 4. The Glassmorphism UI Card
    ui_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ui_draw = ImageDraw.Draw(ui_layer)
    
    card_x1, card_y1, card_x2, card_y2 = 60, 100, 1020, 1270
    ui_draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=40, fill=(20, 25, 35, 210), outline=(255, 255, 255, 30), width=2)

    title_font = load_font(60, vibe)
    body_font = load_font(36, vibe)
    ui_font = load_font(24, vibe)

    max_text_width = width - 240 

    # 5. UI Elements: Slide Tracker & Progress Bar
    total_slides = slide_data.get('total_slides', 5)
    slide_num = slide_data.get('slide_number', 1)
    
    ui_draw.rounded_rectangle([120, 150, 200, 190], radius=15, fill=accent_color + (255,))
    ui_draw.text((135, 155), f"{slide_num}/{total_slides}", fill=(10, 10, 10, 255), font=ui_font)

    progress_width = ((card_x2 - card_x1 - 120) / max(1, total_slides)) * slide_num
    ui_draw.rounded_rectangle([card_x1 + 60, card_y2 - 60, card_x2 - 60, card_y2 - 55], radius=2, fill=(255, 255, 255, 30))
    ui_draw.rounded_rectangle([card_x1 + 60, card_y2 - 60, card_x1 + 60 + progress_width, card_y2 - 55], radius=2, fill=accent_color + (255,))

    # 6. DYNAMIC CENTERING MATH
    header_text = slide_data.get('header', '').replace("**", "").replace("__", "")
    wrapped_header = wrap_text(header_text, max_text_width, title_font)
    
    bullet_points = slide_data.get('bullet_points', [])
    wrapped_bullets = [wrap_text(b.replace("**", "").replace("__", ""), max_text_width - 50, body_font) for b in bullet_points]
    
    header_height = len(wrapped_header) * 70
    bullets_height = sum((len(wb) * 50) + 45 for wb in wrapped_bullets) 
    total_content_height = header_height + 60 + bullets_height 
    
    available_card_space = (card_y2 - 60) - (card_y1 + 100) 
    starting_y = card_y1 + 100 + max(0, (available_card_space - total_content_height) // 2)
    
    y_cursor = starting_y

    # 7. Render Header
    for line in wrapped_header:
        ui_draw.text((120, y_cursor), line, fill=text_color + (255,), font=title_font)
        y_cursor += 70

    y_cursor += 60 

    # 8. Render Sleek Bullet Points
    for wrapped_bullet in wrapped_bullets:
        pill_height = len(wrapped_bullet) * 50
        ui_draw.rounded_rectangle([120, y_cursor + 5, 126, y_cursor + pill_height - 10], radius=3, fill=accent_color + (255,))
        
        for line in wrapped_bullet:
            ui_draw.text((155, y_cursor), line, fill=(200, 210, 220, 255), font=body_font)
            y_cursor += 50  
            
        y_cursor += 45 

    final_image = Image.alpha_composite(base_image, ui_layer)

    os.makedirs("output_slides", exist_ok=True)
    file_path = os.path.join("output_slides", output_filename)
    final_image.convert("RGB").save(file_path, quality=95)
    
    return file_path