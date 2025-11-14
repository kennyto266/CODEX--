from PIL import Image, ImageDraw
import io

# Create a simple 16x16 favicon with HK flag colors
width, height = 16, 16
image = Image.new('RGB', (width, height), color='#CE1126')  # Red background
draw = ImageDraw.Draw(image)

# Draw a simple white star (representing financial/trading)
# This is a simple approach - creating a basic shape
for x in range(6, 10):
    for y in range(6, 10):
        draw.point((x, y), fill='white')

# Save as ICO
image.save('favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
print("Favicon created successfully!")
print(f"File size: {len(io.BytesIO().getvalue())} bytes")

