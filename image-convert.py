from PIL import Image

# Load your original PNG
img = Image.open("assets/gp.png")

# Save as ICO containing standard Windows icon resolutions
img.save(
    "logo.ico",
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
)
