from wsgiref.types import WSGIEnvironment, StartResponse
from typing import Iterable, Any
import json

from dataclasses import dataclass
from typing import Callable
from enum import Enum

type ReturnTuple = tuple[Any] | tuple[Any, int]
type RouteMap = dict[HTTPMethod, dict[str, Callable[..., ReturnTuple]]]

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    
@dataclass(frozen=True)
class ReturnDetails:
    status: str
    body: bytes
    

STATUS_CODE_MAP = {
    # 2xx Success
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}

def build_http_status(status_code: int) -> str:
    if status_code in STATUS_CODE_MAP:
        return str(status_code) + " " + STATUS_CODE_MAP[status_code]
    else:
        return "500 Internal Server Error"

class API:
    def __init__(self) -> None:
        self.routes: RouteMap = {
            method: {} for method in HTTPMethod
        }
    
    def __call__(self, environ: WSGIEnvironment,
                 start_response: StartResponse) -> Iterable[bytes]:
        headers = [("Content-type", 'text/plain')]
        
        # start_response("200 OK", headers)
        # return [b"TESTING"]
        
        path = environ.get("PATH_INFO", "/")
        method_str = environ["REQUEST_METHOD"]
        if method_str not in HTTPMethod.__members__:
            start_response(build_http_status(400), headers)
            return [json.dumps({
                "error": f"Unknown HTTP request method '{method_str}'"
                }).encode("utf-8")
            ]
            
        method = HTTPMethod[method_str]

        if path not in self.routes[method]:
            start_response(build_http_status(400), headers)
            return [json.dumps({
                "error": f"Route '{method_str} {path}' could not be found"
                }).encode("utf-8")
            ]
        
        return_tuple = self.routes[method][path]()
        return_dtl = self.parse_return_tuple(return_tuple)
        start_response(return_dtl.status, headers)

        return [return_dtl.body]
    
    # TODO - possibly make static or move
    def parse_return_tuple(self, return_tuple: ReturnTuple) -> ReturnDetails:
        """
        Take a return tuple and extract details such as the numeric and text
        HTTP status, as well as the byte text encoding
        """
        if len(return_tuple) == 1:
            status = build_http_status(200)
        elif len(return_tuple) == 2:
            status = build_http_status(return_tuple[1])
        else:
            raise Exception("Invalid route return value. Routes must return" +
                            " either (body, status) or (body)")
        
        # TODO - parse different types of bodies such as
        # Dictionary -> JSON
        # XML 
        
        body = str(return_tuple[0]).encode("utf-8")

        return ReturnDetails(status=status, body=body)
        
    def get(self, path: str):
        def decorator(fn: Callable[..., ReturnTuple]):
            self.routes[HTTPMethod.GET][path] = fn
            return fn
        return decorator      

@dataclass(frozen=True)
class RoutePathVariable:
    name: str

# @dataclass(frozen=True)
# class Route:
#     parts: list[str | RoutePathVariable]
    
# Example developer code

api = API()

@api.get("/hello/world")
def hello_world():
    return "hello_world", 200
