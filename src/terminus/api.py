from wsgiref.types import WSGIEnvironment, StartResponse
from typing import Iterable, Callable, TypedDict, Unpack, Any

from terminus.types import HTTPMethod, Request, HTTPError
from terminus.router import Router, RouteFn
from terminus.response import Response
from terminus.request_factory import RequestFactory
from terminus.execution_pipeline import ExecutionPipeline, MiddlewareFn, AfterWareFn

type RouteDecorator = Callable[[RouteFn], RouteFn]

# Options declared as a type dict for easy unpacking in each method route
class RouteOptions(TypedDict, total=False):
    pre: list[MiddlewareFn]
    after: list[AfterWareFn]

class API:
    def __init__(self) -> None:
        self.router = Router()
        self.pipeline = ExecutionPipeline()
    
    def __call__(self, environ: WSGIEnvironment,
                 start_response: StartResponse) -> Iterable[bytes]:
        """Entrypoint to the gunicorn web server"""
        
        method_str = environ["REQUEST_METHOD"]
        if method_str not in HTTPMethod:
            return Response.send_err(start_response, f"HTTP method '{method_str}' not recognised")
        method = HTTPMethod(method_str)
        
        path = environ.get("PATH_INFO", "/")
        route_details = self.router.match_route(method, path)
        if route_details is None:
            return Response.send_err(start_response, f"Route '{method_str} {path}' not found", 404)
        
        try:
            req = RequestFactory.build_req(environ, route_details)
            pipeline_res = self.pipeline.execute(route_details.fn, req)
        except HTTPError as e:
            return Response.send_err(start_response, str(e), e.status)
        else:
            http_res = Response(pipeline_res, start_response)
            return http_res.send()
    
    def _build_route_decorator(self, method: HTTPMethod, path: str, **opts: Unpack[RouteOptions]) -> RouteDecorator:
        """Build a decorator function for some specific HTTP method"""
        def decorator(fn: RouteFn) -> RouteFn:
            fn_with_middleware = ExecutionPipeline.compose_middleware(
                fn, opts.get("pre"), opts.get("after")
            )                
            self.router.register_route(method, path, fn_with_middleware)
            return fn
        return decorator
    
    def pre_request(self, fn: MiddlewareFn):
        """Global middleware to execute before the core route function anytime a route is called"""
        self.pipeline.add_before_main_fn(fn)
        return fn
    
    def after_request(self, fn: AfterWareFn):
        """Global middleware to execute after the route function anytime a route is called"""
        self.pipeline.add_after_main_fn(fn)
        return fn
    
    # Separate methods are used here over a generalised __getattr__ method as it allows for
    # better type hinting with static type checkers
    
    def get(self, path, **opts: Unpack[RouteOptions]):
        return self._build_route_decorator(HTTPMethod.GET, path, **opts)

    def post(self, path, **opts: Unpack[RouteOptions]):
        return self._build_route_decorator(HTTPMethod.POST, path, **opts)

    def put(self, path, **opts: Unpack[RouteOptions]):
        return self._build_route_decorator(HTTPMethod.PUT, path, **opts)

    def delete(self, path, **opts: Unpack[RouteOptions]):
        return self._build_route_decorator(HTTPMethod.DELETE, path, **opts)

    def patch(self, path, **opts: Unpack[RouteOptions]):
        return self._build_route_decorator(HTTPMethod.PATCH, path, **opts)

    def trace(self, path, **opts: Unpack[RouteOptions]):
        return self._build_route_decorator(HTTPMethod.TRACE, path, **opts)

    def options(self, path, **opts: Unpack[RouteOptions]):
        return self._build_route_decorator(HTTPMethod.OPTIONS, path, **opts)

    def connect(self, path, **opts: Unpack[RouteOptions]):
        return self._build_route_decorator(HTTPMethod.CONNECT, path, **opts)
            
api = API()