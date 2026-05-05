import cv2
import json
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def load_font(font_size):
    possible_fonts = [
        "NotoSansSymbols2-Regular.ttf",
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "arial.ttf",
    ]

    for font_path in possible_fonts:
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            continue

    return ImageFont.load_default()

def get_font(text, font_size):
    symbol_chars = set("♡♥❤★☆✿✧")

    if any(ch in symbol_chars for ch in text):
        try:
            return ImageFont.truetype("NotoSansSymbols2-Regular.ttf", font_size)
        except:
            pass

    return ImageFont.truetype("C:/Windows/Fonts/comicz.ttf", font_size)


def normalize_text(text):
    replacements = {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.replace("\n", " ").replace("\r", " ")

    text = " ".join(text.split())

    text = text.upper()

    return text


def overlay_translated_text(
    image_path,
    json_path,
    output_path=None,
    thickness=1,
):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if output_path is None:
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = f"{base_name}_translate.png"

    
    def wrap_text(draw, text, max_width, font, narrow_threshold):
        text = normalize_text(text)

        if max_width < narrow_threshold:
            lines = []
            current = ""

            for ch in text:
                if ch == " ":
                    if current:
                        lines.append(current)
                        current = ""
                    continue

                test_line = current + ch
                bbox = draw.textbbox((0, 0), test_line, font=font)
                w = bbox[2] - bbox[0]

                if w <= max_width:
                    current = test_line
                else:
                    if current:
                        lines.append(current)
                    current = ch

            if current:
                lines.append(current)

            return lines

        words = text.split(" ")
        lines = []
        current = ""

        for word in words:
            test_line = (current + " " + word).strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]

            if w <= max_width:
                current = test_line
            else:
                if current:
                    lines.append(current)
                    current = word
                else:
                    # break long word
                    chunk = ""
                    for ch in word:
                        test_chunk = chunk + ch
                        bbox = draw.textbbox((0, 0), test_chunk, font=font)
                        cw = bbox[2] - bbox[0]

                        if cw <= max_width:
                            chunk = test_chunk
                        else:
                            if chunk:
                                lines.append(chunk)
                            chunk = ch
                    current = chunk

        if current:
            lines.append(current)

        return lines

    # Convert OpenCV image to PIL
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)

    img_h, img_w = img.shape[:2]

    width_ratio = 0.085  # tweak this (0.06–0.1)
    narrow_threshold = int(img_w * width_ratio)

    for block in data["parsing_res_list"]:
        x1, y1, x2, y2 = map(int, block["block_bbox"])
        text = normalize_text(block.get("translated_content", ""))

        if not text.strip():
            continue

        box_width = max(1, x2 - x1)
        box_height = max(1, y2 - y1)

        font_size = 128
        min_font_size = 6
        
        font = get_font(text, font_size)

        lines = []
        while font_size >= min_font_size:
            font = get_font(text, font_size)
            lines = wrap_text(draw, text, box_width, font, narrow_threshold)

            bbox = draw.textbbox((0, 0), "Ag", font=font)
            line_height = int((bbox[3] - bbox[1]) * 1.4)

            if len(lines) * line_height <= box_height:
                break

            font_size -= 1

        bbox = draw.textbbox((0, 0), "Ag", font=font)
        line_height = int((bbox[3] - bbox[1]) * 1.4)

        pad_x = narrow_threshold // 5
        pad_y = 3
        x1_pad = max(0, x1 - pad_x)
        y1_pad = max(0, y1 - pad_y)
        x2_pad = min(img_w, x2 + pad_x)
        y2_pad = min(img_h, y2 + pad_y)

        draw.rectangle([x1_pad, y1_pad, x2_pad, y2_pad], fill=(255, 255, 255))

        padding = 5
        print (f"Block: {text[:30]}... | Font size: {font_size} | Lines: {len(lines)} | width: {box_width} | height: {box_height}")
        
        for i, line in enumerate(lines):
            y = y1 + padding + i * line_height
            if y > y2:
                break
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]

            x = x1 + (box_width - text_width) // 2
            
            draw.text((x, y), line, font=font, fill=(0, 0, 0))

    # Convert back to OpenCV and save
    final_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, final_img)
    print(f"Saved: {output_path}")


def run_all_draw(file_dir, image_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for file in os.listdir(file_dir):
        if file.endswith("_translated.json"):
            base_name = file.replace("_res.json_translated.json", "").replace(
                "_translated.json", ""
            )
            image_path = os.path.join(image_dir, f"{base_name}.png")
            json_path = os.path.join(file_dir, file)
            output_path = os.path.join(output_dir, f"{base_name}_final.png")

            if os.path.exists(image_path):
                print(image_path, json_path, output_path)
                overlay_translated_text(image_path, json_path, output_path)
            else:
                print(f"Missing image for: {file}")

# run_all_draw("output/", "images/", "final/")
