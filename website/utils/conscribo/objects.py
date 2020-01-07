import json


class _JsonSerializable(object):
    @property
    def data(self) -> object:
        raise NotImplementedError

    def json(self) -> str:
        return json.dumps(self.data)

    def __str__(self) -> str:
        return self.json()


class Command(_JsonSerializable):
    def __init__(self, command, **params) -> None:
        self._command = command
        self._params = params

    @property
    def data(self) -> dict:
        return {
            "command": self._command,
            **self._params,
        }


class Request(_JsonSerializable):
    def __init__(self, commands) -> None:
        self._commands = commands

    @property
    def data(self) -> dict:
        if len(self._commands) == 1:
            return {"request": self._commands[0].data}
        return {
            "requests": {
                "request": [
                    {**v.data, "requestSequence": str(k)}
                    for k, v in enumerate(self._commands)
                ]
            }
        }

    @staticmethod
    def single(command, **params) -> _JsonSerializable:
        if isinstance(command, Command):
            return Request([command])
        return Request([Command(command, **params)])

    @staticmethod
    def multi(commands) -> _JsonSerializable:
        return Request(commands)


class ResultException(Exception):
    def __init__(self, notifications):
        msg = "Error occurred on server:\n" + "\n".join(notifications)
        super(ResultException, self).__init__(msg)


class Result(object):
    def __init__(self, data) -> None:
        self._data = data
        self._success = self._data.pop("success", False)
        self._request_sequence = self._data.pop("requestSequence", 0)
        self._notifications = self._data.pop("notifications", {"notification": []}).get(
            "notification"
        )

    @staticmethod
    def single(data):
        return Result(data.get("result", {}))

    @staticmethod
    def multi(data):
        return [
            Result(result)
            for result in data.get("results", {"result": []}).get("result", None)
        ]

    @property
    def success(self):
        return self._success

    @property
    def notifications(self):
        return self._notifications

    @property
    def request_sequence(self):
        return self._request_sequence

    @property
    def data(self):
        return self._data

    def raise_for_status(self):
        if not self.success:
            raise ResultException(self.notifications)
