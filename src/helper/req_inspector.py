import threading
import time
from typing import Optional, Dict

import requests
from requests import Response

from src.error.errors import RequestError


class RequestInspector:
    def __init__(self, req_hour_rate=720000, headers: Optional[Dict[str, str]] = None) -> None:
        headers = dict((k.strip().lower(), v) for k, v in (headers or dict()).items())
        if 'user-agent' not in headers:
            headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        self.hour_limit = req_hour_rate
        self.last_parsed_time = time.time()
        self.lock = threading.Lock()
        self.minute_rate = int(req_hour_rate / 60)
        self.delta = 0
        self.headers = headers

    def request_get(self, url: str, req_args: Dict[str, str]) -> Response:
        with self.lock:
            self.delta += 1
            now = time.time()
            time_delta = 60 - (now - self.last_parsed_time)
            if time_delta < 60:
                if self.delta >= self.minute_rate:
                    time.sleep(time_delta)
                    self.last_parsed_time = now + time_delta
                    self.delta = 0
            else:
                self.last_parsed_time = now
                self.delta = 0
            res = requests.get(url, params=req_args, headers=self.headers)
            if res.status_code >= 400:
                raise RequestError(f"error while getting resource with status code - {res.status_code}")
            return res