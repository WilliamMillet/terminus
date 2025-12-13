from wsgiref.types import WSGIEnvironment, StartResponse
from typing import Iterable

def app(environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
    status = "200 OK"
    headers = [("Content-type", 'text/plain')]
    start_response(status, headers)
    
    return [b"This is the HTTP body\n"]