import base64
import json
from io import BytesIO

import face_recognition
import numpy as np
import requests
from PIL import Image


def process_encodings():
    url = f"http://127.0.0.1:8000/api/v2/photos/facerecognition/unprocessed/"

    session = requests.Session()
    # session.headers.update({"Authorization": f"Bearer {key}"}
    response = session.get(url)

    if response.status_code != 200:
        print("Error")
        return

    while response.json()["results"]:
        process_response(response.json()["results"])
        response = session.get(url)


def process_response(results):
    for result in results:
        image_file = requests.get(result["file"]["full"]).content
        encodings = get_encoding(image_file)
        encoding_data = [list(encoding) for encoding in encodings]
        data = {"encodings": json.dumps(encoding_data)}
        push_encoding(result["pk"], result["type"], data)


def push_encoding(pk, obj_type, data):
    url = f"http://127.0.0.1:8000/api/v2/photos/facerecognition/encodings/{obj_type}/{pk}/"
    session = requests.Session()
    # session.headers.update({"Authorization": f"Bearer {key}"}
    response = session.post(url, data=data)
    if response.status_code not in {200, 201}:
        print("Error")
        return
    print(data)


def get_encoding(image_file):
    img = Image.open(BytesIO(image_file))
    img = img.convert("RGB")
    img.thumbnail((500, 500))
    encodings = face_recognition.face_encodings(np.array(img))
    return encodings


if __name__ == "__main__":
    process_encodings()
