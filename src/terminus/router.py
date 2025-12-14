from dataclasses import dataclass
from bisect import bisect_left, insort_left
from typing import Callable, Any

from terminus.types import HTTPMethod, PathVariables, Request

type RouteFnRes = tuple[Any] | tuple[Any, int]
type RouteFn = Callable[[Request], RouteFnRes]
type RouteMap = dict[HTTPMethod, dict[str, RouteFn]]

@dataclass(frozen=True)
class RouteDetails:
    fn: RouteFn
    path_var_indices: dict[int, str]
    raw_path: str

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
        """Attempts to register a route to the router"""
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
        
        path_var_indices: dict[int, str] = {}
        for i, p in enumerate(parts):
            if Router.is_param(p):
                path_var_indices[i] = p[1:-1]
        
        curr.details = RouteDetails(fn, path_var_indices, raw_path)
    
    def match_route(self, method: HTTPMethod, raw_path: str) -> RouteDetails | None:
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
        
        return curr.details
    
    @staticmethod
    def match_path_variables(route_details: RouteDetails, req_path: str) -> PathVariables:
        """
        Match path variable values entered in the request URL to there names stored in
        route details
        """
        req_parts = route_details.raw_path.split("/")
        
        path_obj: PathVariables = {}
        for idx, var_name in route_details.path_var_indices.items():
            path_obj[var_name] = req_parts[idx]
        
        return path_obj
        
    @staticmethod 
    def is_param(path_part: str) -> bool:
        """Determine if a part of a route is a path variable position"""
        return path_part[0] == "[" and path_part[-1] == "]"
        
        
class RouteNode:
    """
    A node in a route tree (one part of the route when split by forward slashes).
    If this has content, it is a regular text component of a route.
    If this does not have content, it is the NULL root or a path variable wildcard
    """
    def __init__(self, content: str | None = None) -> None:
        self.content = content
        self.children: list[RouteNode] = []
        # The existence of route details indicates if the node is terminal
        self.details: RouteDetails | None = None
    
    def __lt__(self, other: "RouteNode") -> bool:
        if self.content is None or other.content is None:
            raise Exception("Cannot perform route node comparison when one node is null")
        
        return self.content < other.content