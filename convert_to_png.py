import os
import argparse
from PIL import Image

parser = argparse.ArgumentParser(description="Convert images to PNG format.")
parser.add_argument("input_folder", help="Folder containing input images")
parser.add_argument("output_folder", help="Folder to save converted PNG images")
args = parser.parse_args()

input_folder = args.input_folder
output_folder = args.output_folder

supported_formats = (".jpg", ".jpeg", ".bmp", ".tiff", ".webp", ".gif")

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.lower().endswith(supported_formats):
        input_path = os.path.join(input_folder, filename)
        png_filename = os.path.splitext(filename)[0] + ".png"
        output_path = os.path.join(output_folder, png_filename)

        with Image.open(input_path) as img:
            if img.mode in ("P", "RGBA", "LA"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            img.save(output_path, "PNG")
        
        print(f"Converted: {filename} -> {png_filename}")

print("All supported images have been converted to PNG.")
