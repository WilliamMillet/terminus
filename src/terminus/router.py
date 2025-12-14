from dataclasses import dataclass
from bisect import bisect_left, insort_left
from typing import Callable, Any
from enum import Enum

type RouteFnRes = tuple[Any] | tuple[Any, int]
type RouteFn = Callable[..., RouteFnRes]
type RouteMap = dict[HTTPMethod, dict[str, RouteFn]]

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class Router:
    """
    An object for storing routes with path variables, then matching incoming
    requests with the functions associated with routes
    """
    def __init__(self) -> None:
        # Separate tries exist for each HTTP method and each part length (e.g. routes with two parts
        # like /data/users will be in the Route at key two)
        self.routes: dict[HTTPMethod, dict[int, RouteNode]] = {
            method: {} for method in HTTPMethod
        }

    def register_route(self, method: HTTPMethod, raw_path: str, fn: RouteFn) -> None:
        """
        Attempts to register a route to the router
        """
        parts = raw_path.split("/")
        
        method_routes = self.routes[method]
        if len(parts) not in method_routes:
            method_routes[len(parts)] = RouteNode(None)
            
        curr = method_routes[len(parts)]
        for p in parts:
            new_node = RouteNode(p)
            pos_idx = bisect_left(curr.children, new_node)
            
            inbound = pos_idx < len(curr.children)
            if not inbound or curr.children[pos_idx].content != p:
                insort_left(curr.children, new_node)
            
            curr = curr.children[pos_idx]
        
        curr.fn = fn
    
    def match_route(self, method: HTTPMethod, raw_path: str) -> RouteFn | None:
        """
        Takes a request path and method and returns the associated function. If
        a route is not found, None will be returned
        """
        parts = raw_path.split("/")
        
        method_routes = self.routes[method]
        if len(parts) not in method_routes:
            return None
    
        curr = method_routes[len(parts)]
        for p in parts:
            new_node = RouteNode(p)
            pos_idx = bisect_left(curr.children, new_node)

            inbound = pos_idx < len(curr.children)
            if not inbound or curr.children[pos_idx].content != p:
                return None
            
            curr = curr.children[pos_idx]
        
        return curr.fn
        
class RouteNode:
    """
    A node in a route tree
    """
    def __init__(self, content: str | None = None, fn: RouteFn | None = None) -> None:
        self.content = content
        self.children: list[RouteNode] = []
        # The existence of a function indicates this is a terminal node
        self.fn = fn 
    
    def __lt__(self, other: "RouteNode") -> bool:
        if self.content is None or other.content is None:
            raise Exception("Cannot perform route node comparison when one node is null")
        
        return self.content < other.content