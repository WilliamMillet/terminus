from typing import Callable
from terminus.router import RouteFn
from terminus.types import Request, RouteFnRes, Request, HTTPError

type MiddlewareFnRes = RouteFnRes | None
type MiddlewareFn = Callable[[Request], MiddlewareFnRes]

class ExecutionPipeline:
    def __init__(self) -> None:
        self._before_fn: list[MiddlewareFn] = []
        self._after_fn: list[MiddlewareFn] = []
    
    def add_before_main_fn(self, fn: MiddlewareFn) -> None:
        """
        Add a function to the middleware pipeline right before the main route function
        """
        self._before_fn.append(fn)
        
    def add_after_main_fn(self, fn: MiddlewareFn) -> None:
        """
        Add a function to the middleware pipeline right before the main route function
        """
        self._after_fn.append(fn)
        
    def execute(self, fn: RouteFn, req: Request) -> RouteFnRes:
        """
        Execute the request-response pipeline with middleware and the core route function.
        """
        for middleware in self._before_fn:
            middleware_res = middleware(req)
            # Early end of HTTP if a function in the pipeline already returned 
            if middleware_res:
                return middleware_res
        
        main_fn_res = fn(req)
        if len(self._after_fn) == 0:
            return main_fn_res
        
        for middleware in self._after_fn:
            middleware_res = middleware(req)
            if middleware_res:
                return middleware_res

        raise HTTPError("Middleware after main function does not return a response")
        
        
            
            