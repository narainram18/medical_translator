import json
from urllib import request, parse

class LibreTranslateAPI:
    def __init__(self, url="http://localhost:5000/", api_key=None):
        self.url = url.rstrip("/") + "/"
        self.api_key = api_key

    def translate(self, q, source="en", target="es"):
        url = self.url + "translate"
        params = {"q": q, "source": source, "target": target}
        if self.api_key:
            params["api_key"] = self.api_key
        data = parse.urlencode(params).encode()
        req = request.Request(url, data=data)
        response = request.urlopen(req)
        return json.loads(response.read().decode())["translatedText"]

    def detect(self, q):
        url = self.url + "detect"
        params = {"q": q}
        if self.api_key:
            params["api_key"] = self.api_key
        data = parse.urlencode(params).encode()
        req = request.Request(url, data=data)
        response = request.urlopen(req)
        return json.loads(response.read().decode())

    def languages(self):
        url = self.url + "languages"
        params = {"api_key": self.api_key} if self.api_key else {}
        data = parse.urlencode(params).encode()
        req = request.Request(url, data=data, method="GET")
        response = request.urlopen(req)
        return json.loads(response.read().decode())
