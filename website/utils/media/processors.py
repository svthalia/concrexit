from da_vinci import Image as DaVinciImage
from PIL.ImageOps import exif_transpose


def process_upload(image: DaVinciImage, **kwargs):
    """Process an incoming image.

    - Rotate and flip the image based on EXIF data.
    - Resize the image to the maximum allowed size if it is larger.
    - Convert the image to RGB colors.

    """
    # Get the PIL image out of the DaVinci image wrapper,
    # so we can manipulate it more completely.
    pil_image = image.get_pil_image()

    # Rotate and flip the image based on EXIF
    # data, so the image is stored upright.
    pil_image = exif_transpose(pil_image)

    # Resize the image to at most the maximum allowed size.
    max_width, max_height = kwargs["width"], kwargs["height"]
    pil_image.thumbnail((max_width, max_height))

    if kwargs["format"] == "jpg":
        # Store in RGB colors.
        pil_image = pil_image.convert("RGB")
        image.set(format="JPEG")
    elif kwargs["format"] == "png":
        image.set(format="PNG")
        if pil_image.mode != "RGBA" and pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
    else:
        raise ValueError(f"Unsupported format: {kwargs['format']}")

    # Put the PIL image back into the wrapper.
    image.set_pil_image(pil_image)
    return image
