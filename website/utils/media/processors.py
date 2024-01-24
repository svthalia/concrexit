from da_vinci import Image as DaVinciImage
from PIL import Image, ImageOps


def process_upload(image: DaVinciImage, **kwargs):
    """Process an incoming image.

    - Rotate and flip the image based on EXIF data.
    - Resize the image to the maximum allowed size if it is larger.
    - Convert the image to RGB colors, or keep RGBA for PNGs.

    Warning: for django-thumbnails to save the image with the right filename, the
    format must also be set on the '<size>.FORMAT' key in settings.THUMBNAILS_SIZES.
    """
    # Get the PIL image out of the DaVinci image wrapper,
    # so we can manipulate it more completely.
    pil_image = image.get_pil_image()

    # Rotate and flip the image based on EXIF
    # data, so the image is stored upright.
    pil_image = ImageOps.exif_transpose(pil_image)

    # Resize the image to at most the maximum allowed size.
    pil_image.thumbnail(kwargs["size"])

    if kwargs["format"] == "jpg":
        # Store in RGB colors.
        pil_image = pil_image.convert("RGB")
        image.format = "JPEG"
    elif kwargs["format"] == "png":
        image.format = "PNG"
        if pil_image.mode not in ("RGBA", "RGB"):
            pil_image = pil_image.convert("RGB")
    else:
        raise ValueError(f"Unsupported format: {kwargs['format']}")

    # Put the PIL image back into the wrapper.
    image.set_pil_image(pil_image)
    return image


def thumbnail(image: DaVinciImage, **kwargs):
    """Thumbnail an image to at most the given size.

    If `mode="contain"` (the default), the image is resized to fit within the given size.
    The original aspect ratio is preserved, so the image may be smaller than specified.

    If `mode="cover"`, the image is cropped to the aspect ratio of the given size.
    The thumbnails are saved to WebP format with lossy compression.

    If `mode="pad"`, the image is resized to fit within the given size.
    Padding is added to the edges to make the image the exact size specified.

    Warning: for django-thumbnails to save the image with the right filename,
    the '<size>.FORMAT' key in settings.THUMBNAILS_SIZES must be set to 'webp'.

    """
    pil_image = image.get_pil_image()

    size = kwargs["size"]
    mode = kwargs.get("mode", "contain")

    match mode:
        case "contain":
            pil_image = ImageOps.contain(pil_image, size, Image.Resampling.LANCZOS)
        case "cover":
            pil_image = ImageOps.fit(pil_image, size, Image.Resampling.LANCZOS)
        case "pad":
            pil_image = pil_image.convert("RGBA")
            pil_image = ImageOps.pad(pil_image, size, Image.Resampling.LANCZOS)

    image.set_pil_image(pil_image)
    image.format = "WEBP"
    image.quality = 90

    return image
