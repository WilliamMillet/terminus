from wsgiref.types import WSGIEnvironment, StartResponse
from typing import Iterable

from terminus.types import HTTPMethod, Request, Headers
from terminus.router import Router, RouteFn
from terminus.response import Response

class API:
    def __init__(self) -> None:
        self.router = Router()
    
    def __call__(self, environ: WSGIEnvironment,
                 res_rtn: StartResponse) -> Iterable[bytes]:
        method_str = environ["REQUEST_METHOD"]
        if method_str not in HTTPMethod.__members__:
            return Response.send_err(res_rtn, f"HTTP method '{method_str}' not recognised")
        
        method = HTTPMethod(method_str)
        
        path = environ.get("PATH_INFO", "/")
        
        route_details = self.router.match_route(method, path)
        if route_details is None:
            return Response.send_err(res_rtn, f"Route '{method_str} {path}' not found")
        
        req = Request(
            method=method,
            path=Router.match_path_variables(route_details, path),
            query=Request.build_query(environ["QUERY_STRING"]),
            protocol=environ["SERVER_PROTOCOL"],
            headers=Headers.of(environ)
        )
        
        fn_res = route_details.fn(req)
        http_res = Response(fn_res, res_rtn)
        
        return http_res.send()
    
        
    def get(self, path: str):
        def decorator(fn: RouteFn) -> RouteFn:
            self.router.register_route(HTTPMethod.GET, path, fn)
            return fn
        return decorator

api = API()

@api.get("/hello/world")
def hello_world(req: Request):
    return "hello_world", 200
