import json
from io import BytesIO

import face_recognition
import numpy as np
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from PIL import Image
from requests_oauthlib import OAuth2Session


class PhotoEncodingProcessor:
    def build_session(self):
        client = BackendApplicationClient(client_id=self.client_id)
        oauth = OAuth2Session(client=client)
        token = oauth.fetch_token(
            token_url=self.token_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        return OAuth2Session(self.client_id, token=token)

    def __init__(self, base_url, client_id, client_secret):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = f"{base_url}/user/oauth/token/"
        self.session = self.build_session()

    def process_encodings(self):
        url = f"{self.base_url}/api/v2/photos/facerecognition/unprocessed/"

        try:
            response = self.session.get(url)
        except TokenExpiredError:
            self.session.refresh_token(self.token_url)
            response = self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Error: received HTTP {response.status_code}")

        while response.json()["results"]:
            self.process_response(response.json()["results"])
            response = self.session.get(url)

    def process_response(self, results):
        for result in results:
            image_file = self.session.get(result["file"]["full"]).content
            encodings = self.get_encoding(image_file)
            encoding_data = [list(encoding) for encoding in encodings]
            data = {"encodings": json.dumps(encoding_data)}
            self.push_encoding(result["pk"], result["type"], data)

    def push_encoding(self, pk, obj_type, data):
        url = (
            f"{self.base_url}/api/v2/photos/facerecognition/encodings/{obj_type}/{pk}/"
        )
        try:
            response = self.session.post(url, data=data)
        except TokenExpiredError:
            self.session.refresh_token(self.token_url)
            response = self.session.post(url, data=data)

        if response.status_code not in {200, 201}:
            print("Error")
            return
        print(data)

    def get_encoding(self, image_file):
        img = Image.open(BytesIO(image_file))
        img = img.convert("RGB")
        img.thumbnail((500, 500))
        encodings = face_recognition.face_encodings(np.array(img))
        return encodings


if __name__ == "__main__":
    base_url = "http://127.0.0.1:8000"
    client_id = "ql2BaF7Wo9KGvJKUjdOciiAkbTX7SC9e4pmXfTN6"
    client_secret = "DMu1fX3GjIcGg5vlbBt2i4FJsa7ZAHFmIOcvXjTXNR73poD7Jg2DxsujJK4aQBFen8G7xLQXqBJ522Uqb9G6mAUPfYNFQvpB1lHZeo1QNedmofTODR8USD4hdsUYUKl6"
    processor = PhotoEncodingProcessor(base_url, client_id, client_secret)
    processor.process_encodings()
