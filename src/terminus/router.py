from dataclasses import dataclass
from bisect import bisect_left, insort_left
from typing import Callable

from terminus.response import RouteFnRes
from terminus.types import HTTPMethod, PathVariables, Request

type RouteFn = Callable[[Request], RouteFnRes]
type RouteMap = dict[HTTPMethod, dict[str, RouteFn]]

# We set wildcard to be the empty string so it's lexicographically minimal, and therefore we can
# easily check for it at the start of the sorted child list
WILDCARD = ""

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
        for i, p in enumerate(parts):
            if Router.is_param(p):
                if len(curr.children) == 0 or curr.children[0] != WILDCARD:
                    new_node = RouteNode(WILDCARD)
                    curr.children.insert(0, new_node)
                    curr = curr.children[0]
                else:
                    curr = curr.children[0]
            else:
                new_node = RouteNode(p)
                pos_idx = bisect_left(curr.children, new_node)
                
                inbound = pos_idx < len(curr.children)
                if not inbound or curr.children[pos_idx].content != p:
                    insort_left(curr.children, new_node)
                elif i + 1 == len(parts):
                    raise Exception(f"Cannot register route '{raw_path}' that already exists")
                
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
            exact_match = inbound and curr.children[pos_idx].content == p
            # If there is no exact match but a wildcard/path variable exists we follow that
            if not exact_match:
                if len(curr.children) >= 1 and curr.children[0].content == WILDCARD:
                    curr = curr.children[0]
                else:
                    return None
            else:
                curr = curr.children[pos_idx]
        
        return curr.details
    
    @staticmethod
    def match_path_variables(route_details: RouteDetails, req_path: str) -> PathVariables:
        """
        Match path variable values entered in the request URL to there names stored in
        route details
        """
        req_parts = req_path.split("/")
        
        path_obj: PathVariables = {}
        for idx, var_name in route_details.path_var_indices.items():
            path_obj[var_name] = req_parts[idx]
        
        return path_obj
        
    @staticmethod 
    def is_param(path_part: str) -> bool:
        """Determine if a part of a route is a path variable position"""
        return len(path_part) >= 2 and path_part[0] == "[" and path_part[-1] == "]"
        
        
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