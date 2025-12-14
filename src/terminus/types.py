"""
General types not specific to any of the other modules
"""
from enum import Enum
from dataclasses import dataclass
from wsgiref.types import WSGIEnvironment

from urllib.parse import parse_qs

type PathVariables = dict[str, str]
type QueryVariables = dict[str, str | list[str]]

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    TRACE = "TRACE"
    OPTIONS = "OPTIONS"
    CONNECT = "CONNECT"
    
@dataclass(frozen=True)
class Headers:
    host: str
    accept: list[str]
    accept_language: list[str]
    accept_encoding: list[str]
    connection: str
    remote_address: str
    
    @staticmethod
    def of(environ: WSGIEnvironment) -> "Headers":
        return Headers(
            host=environ["HTTP_HOST"],
            accept=environ["HTTP_ACCEPT"].split(","),
            accept_language = environ["HTTP_ACCEPT_LANGUAGE"].split(","),
            accept_encoding = environ["HTTP_ACCEPT_ENCODING"].split(", "),
            connection = environ["HTTP_CONNECTION"],
            remote_address = environ["REMOTE_ADDR"],
        )
        
@dataclass(frozen=True)
class Request:
    method: HTTPMethod
    path: PathVariables
    query: QueryVariables
    protocol: str
    headers: Headers
    
    @staticmethod
    def build_query(query_str: str) -> QueryVariables:
        """Build the query parameter string from environmental variables"""
        
        parsed = parse_qs(query_str)
        
        query_vars: QueryVariables = {}
        for key, val in parsed.items():
            # This should always be true. the parse_qs return type is just arbitrarily typed
            # with the Any type
            assert all(isinstance(itm, str) for itm in val)
            if len(val) == 1:
                query_vars[key] = val[0]
            else:
                query_vars[key] = val
        
        return query_vars
                 
                 
        
    