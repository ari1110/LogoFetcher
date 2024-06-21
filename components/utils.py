from PIL import Image
from io import BytesIO
import zipfile

def is_white_svg(svg_content):
    white_colors = ['#ffffff', '#fff', 'rgb(255,255,255)']
    return any(color in svg_content.lower() for color in white_colors)

def is_white_image(image_content, image_format):
    if image_format.lower() in ['png', 'jpg', 'jpeg']:
        try:
            image = Image.open(BytesIO(image_content))
            image = image.convert('RGB')
            colors = image.getcolors(image.size[0] * image.size[1])
            dominant_color = max(colors, key=lambda item: item[0])[1]
            return dominant_color == (255, 255, 255) or sum(dominant_color) > 700
        except Exception as e:
            return False
    return False

def create_zip_file(logo_files):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_name, file_content in logo_files:
            zip_file.writestr(file_name, file_content)
    zip_buffer.seek(0)  # Move the pointer to the beginning of the buffer
    return zip_buffer.getvalue()