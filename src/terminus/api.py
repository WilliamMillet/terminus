from wsgiref.types import WSGIEnvironment, StartResponse
from typing import Iterable

from terminus.types import HTTPMethod, Request, HTTPError
from terminus.router import Router, RouteFn
from terminus.response import Response
from terminus.request_factory import RequestFactory

class API:
    def __init__(self) -> None:
        self.router = Router()
    
    def __call__(self, environ: WSGIEnvironment,
                 start_response: StartResponse) -> Iterable[bytes]:
        """Entrypoint to the gunicorn web server"""
        
        method_str = environ["REQUEST_METHOD"]
        if method_str not in HTTPMethod.__members__:
            return Response.send_err(start_response, f"HTTP method '{method_str}' not recognised")
        method = HTTPMethod(method_str)
        
        
        path = environ.get("PATH_INFO", "/")
        route_details = self.router.match_route(method, path)
        if route_details is None:
            return Response.send_err(start_response, f"Route '{method_str} {path}' not found")
        
        try:
            req = RequestFactory.build_req(environ, route_details)
        except HTTPError as e:
            return Response.send_err(start_response, str(e), e.status)
        
        fn_res = route_details.fn(req)
        http_res = Response(fn_res, start_response)
        
        return http_res.send()
    
    def _build_route_decorator(self, method: HTTPMethod, path: str):
        """Build a decorator function for some specific HTTP method"""
        def decorator(fn: RouteFn) -> RouteFn:
            self.router.register_route(method, path, fn)
            return fn
        return decorator
        
    def get(self, path: str):
        return self._build_route_decorator(HTTPMethod.GET, path)

    def post(self, path: str):
        return self._build_route_decorator(HTTPMethod.POST, path)
    
    def put(self, path: str):
        return self._build_route_decorator(HTTPMethod.PUT, path)
    
    def delete(self, path: str):
        return self._build_route_decorator(HTTPMethod.DELETE, path)

    def patch(self, path: str):
        return self._build_route_decorator(HTTPMethod.PATCH, path)

    def trace(self, path: str):
        return self._build_route_decorator(HTTPMethod.TRACE, path)

    def options(self, path: str):
        return self._build_route_decorator(HTTPMethod.OPTIONS, path)

    def connect(self, path: str):
        return self._build_route_decorator(HTTPMethod.CONNECT, path)

api = API()

# Temporary testing
@api.post("/")
def hello(req: Request):
    return "hello", 200

@api.get("/hello/world")
def hello_world(req: Request):
    return "hello_world", 200

@api.get("/hello/foo/world")
def hello_foo_world(req: Request):
    return "hello_foo_world", 200

@api.get("/hello/[param]/world")
def hello_param_world(req: Request):
    return "hello_world [param mode]", 200

@api.get("/hello/there")
def hello_there(req: Request):
    return "hello there", 200
