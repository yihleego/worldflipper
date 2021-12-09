from base64 import b64encode

from PIL import Image


def base64(image: Image.Image, scale: float = 1):
    if scale != 1 and scale > 0:
        w, h = image.size
        s = image.resize((int(w * scale), int(h * scale)))._repr_png_()
    else:
        s = image._repr_png_()
    return b64encode(s).decode()
