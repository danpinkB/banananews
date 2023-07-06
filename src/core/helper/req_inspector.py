import threading
import time
from typing import Optional, Dict


class RequestInspector:
    def __init__(self, req_hour_rate=720000, headers: Optional[Dict[str, str]] = None) -> None:
        headers = dict((k.strip().lower(), v) for k, v in (headers or dict()).items())
        if 'user-agent' not in headers:
            headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        self._hour_limit = req_hour_rate
        self._last_parsed_time = time.time()
        self._lock = threading.Lock()
        self._minute_rate = int(req_hour_rate / 60)
        self._delta = 0
        self._headers = headers

    def get_headers(self) -> Dict[str, str]:
        return self._headers

    def lock_request(self) -> None:
        with self._lock:
            self._delta += 1
            now = time.time()
            time_delta = 60 - (now - self._last_parsed_time)
            if time_delta < 60:
                if self._delta >= self._minute_rate:
                    time.sleep(time_delta)
                    self._last_parsed_time = now + time_delta
                    self._delta = 0
            else:
                self._last_parsed_time = now
                self._delta = 0

    # def request_get(self, url: str, req_args: Dict[str, str], driver: BaseDriver) -> str:
    #     self._lock_request()
    #     return driver.get_resource(url, req_args)
    #
    # def request_get_page(self, url: Template, req_args: Dict[str, str], driver: BaseDriver, page: Any) -> str:
    #     self._lock_request()
    #     return driver.get_page(url, req_args, page)
