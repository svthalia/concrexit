import requests

from utils.conscribo.objects import Request, Result


class ConscriboApi:
    def __init__(self, account, username, password):
        self._session = requests.session()
        self._endpoint = f"https://secure.conscribo.nl/{account}/request.json"
        self._headers = {"X-Conscribo-API-Version": "0.20161212"}
        self.authenticate(username, password)

    def single_request(self, command, **params):
        response = self._session.post(
            self._endpoint,
            Request.single(command, **params).json(),
            headers=self._headers,
        )
        response.raise_for_status()
        result = Result.single(response.json())
        return result

    def multi_request(self, commands):
        if len(commands) == 1:
            return [self.single_request(commands[0])]
        response = self._session.post(
            self._endpoint, Request.multi(commands).json(), headers=self._headers
        )
        response.raise_for_status()
        return Result.multi(response.json())

    def authenticate(self, username, password):
        result = self.single_request(
            command="authenticateWithUserAndPass",
            userName=username,
            passPhrase=password,
        )

        self._headers.update(
            {"X-Conscribo-SessionId": result.data.get("sessionId", None)}
        )
