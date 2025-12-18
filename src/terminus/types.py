"""
General types not specific to any of the other modules
"""
from enum import Enum
from typing import Any
from wsgiref.types import WSGIEnvironment
from dataclasses import dataclass, field

type PathVariables = dict[str, str]
type QueryVariables = dict[str, str | list[str]]
type RequestBody = dict | list | str | bytes

type RouteFnRes = Any | tuple[Any, int]

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    TRACE = "TRACE"
    OPTIONS = "OPTIONS"
    CONNECT = "CONNECT"
    
class ContentType(Enum):
    TEXT_PLAIN = "text/plain"
    APPLICATION_JSON = "application/json"
    APPLICATION_OCTET_STREAM = "application/octet-stream"

@dataclass(frozen=True)
class Headers:
    host: str
    accept: list[str]
    accept_language: list[str]
    accept_encoding: list[str]
    connection: str
    remote_address: str
    content_type: ContentType | None
    raw: dict[str, str]
    
    @staticmethod
    def of(environ: WSGIEnvironment) -> "Headers":
        raw: dict[str, str] = {}
        for key, val in environ.items():
            if key.startswith("HTTP"):
                parsed_key = key[5:].replace("_", "-").title()
                raw[parsed_key] = val
            elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                parsed_key = key.replace("_", "-").title()
                raw[parsed_key] = val
                
        c_type = environ.get("CONTENT_TYPE", None)
        return Headers(
            host=environ["HTTP_HOST"],
            accept=environ["HTTP_ACCEPT"].split(","),
            accept_language = environ["HTTP_ACCEPT_LANGUAGE"].split(","),
            accept_encoding = environ["HTTP_ACCEPT_ENCODING"].split(", "),
            connection = environ["HTTP_CONNECTION"],
            remote_address = environ["REMOTE_ADDR"],
            content_type = None if c_type is None else ContentType(c_type),
            raw=raw
        )
    
    
@dataclass(frozen=True)
class Request:
    method: HTTPMethod
    body: RequestBody | None
    params: PathVariables
    query: QueryVariables
    protocol: str
    path: str
    headers: Headers
    context: dict[Any, Any] = field(default_factory=dict)
    
class HTTPError(Exception):
    """
    An error related to an HTTP request, response or parsing of data associated with these entities
    """
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.status = 400

class RouteError(Exception):
    """
    An error related to the definition of a route or it's middleware on the part of a developer
    """
    pass