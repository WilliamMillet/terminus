from typing import Callable
from terminus.router import RouteFn
from terminus.types import Request, RouteFnRes, Request

type MiddlewareFnRes = RouteFnRes | None
type MiddlewareFn = Callable[[Request], MiddlewareFnRes]
# Afterware cannot return a response
type AfterWareFn = Callable[[Request], None]

class ExecutionPipeline:
    def __init__(self) -> None:
        self._before_fn: list[MiddlewareFn] = []
        self._after_fn: list[AfterWareFn] = []
    
    def add_before_main_fn(self, fn: MiddlewareFn) -> None:
        """
        Add a function to the middleware pipeline right before the main route function
        """
        self._before_fn.append(fn)
        
    def add_after_main_fn(self, fn: AfterWareFn) -> None:
        """
        Add a function to the middleware pipeline right before the main route function
        """
        self._after_fn.append(fn)
        
    def execute(self, fn: RouteFn, req: Request) -> RouteFnRes:
        """
        Execute the request-response pipeline with middleware and the core route function.
        """
        composed = ExecutionPipeline.compose_middleware(fn, self._before_fn, self._after_fn)
        return composed(req)
        
    @staticmethod
    def compose_middleware(fn: RouteFn, pre_fn: list[MiddlewareFn] | None,
                           post_fn: list[AfterWareFn] | None) -> RouteFn:
        """
        Take middleware and a primary function and fuse it into a single executable function
        """
        def composed(req: Request):
            if pre_fn is not None:
                for middleware in pre_fn:
                    middleware_res = middleware(req)
                    if middleware_res is not None:
                        return middleware_res
            fn_res = fn(req)
            if post_fn is not None:
                for middleware in post_fn:
                    middleware(req)
            
            return fn_res
        return composed
        
            
            