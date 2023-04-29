from rest_framework.views import APIView

# TODO: Lambda can authenticate to both of these views using BaseFaceEncodingSource.token


class ReferenceFaceEncodingView(APIView):
    """View where the Lambda can submit the face encoding of a reference photo."""

    pass  # TODO


class PhotoFaceEncodingView(APIView):
    """View where the Lambda can submit the face encodings of a photo."""

    pass  # TODO
