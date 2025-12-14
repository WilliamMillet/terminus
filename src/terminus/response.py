import json

from wsgiref.types import StartResponse
from typing import Any
from enum import Enum
from dataclasses import dataclass

type RouteFnRes = Any | tuple[Any, int]

STATUS_CODE_MAP = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}

VALID_BODY_TYPE_NAMES = [
    "dict"
    "list"
    "bytes"
    "int"
    "str"
    "bool"
]

class ContentType(Enum):
    TEXT_PLAIN = "text/plain"
    APPLICATION_JSON = "application/json"
    APPLICATION_OCTET_STREAM = "application/octet-stream"

@dataclass(frozen=True)
class ResponseFields:
    status: str
    body: bytes
    content_type: ContentType
    
class Response:
    def __init__(self, fn_res: RouteFnRes, start_response: StartResponse) -> None:
        res_fields = Response.parse_function_res(fn_res)
        headers = [("Content-type", res_fields.content_type.value)]
        self.response_routine = lambda: start_response(res_fields.status, headers)
        
        self.body = [res_fields.body]
            
    @staticmethod
    def parse_function_res(fn_res: RouteFnRes) -> ResponseFields:
        """
        Takes the return value from a route's function and extracts the HTTP
        status, parses and encodes the body then returns relevant response
        fields
        """
        if isinstance(fn_res, tuple) and len(fn_res) == 2:
            status = Response.build_status(fn_res[1])
            body = fn_res[0]
        elif not isinstance(fn_res, tuple):
            status = Response.build_status(200)
            body = fn_res
        else:
            # Exception is raised here is this is a developer issue
            raise Exception("Invalid route return value. If route is a tuple, it must be of the" +
                            "The form (body, status)")
            
        if isinstance(body, dict | list):
            try:
                body_str = json.dumps(body)
            except TypeError as e:
                body_str = json.dumps({"error": f"Failed to parse body as JSON: {e}"})
            content_type = ContentType.APPLICATION_JSON
            encoded_body = body_str.encode("utf-8")
        elif isinstance(body, bytes):
            content_type = ContentType.APPLICATION_OCTET_STREAM
            encoded_body = body
        elif isinstance(body, int | float | str | bool):
            body_str = str(body)
            content_type = ContentType.TEXT_PLAIN
            encoded_body = body_str.encode("utf-8")
        else:
            wrong_type = type(body).__name__
            raise Exception(f"Unsupported response body type '{wrong_type}'. Accepted types" +
                            "are:" + "\n - ".join(VALID_BODY_TYPE_NAMES) + "\n")
        
        return ResponseFields(
            status=status,
            body=encoded_body,
            content_type=content_type
        )
    
    def send(self) -> list[bytes]:
        """
        Triggers the start response routine and returns the body in a format
        that can be returned exactly by the WSGI callable entrypoint
        """
        self.response_routine()
        return self.body
    
    @staticmethod
    def send_err(start_response: StartResponse, err_msg: str) -> list[bytes]:
        """Triggers the start response routine and returns the body for an error"""
        err_status = Response.build_status(500)
        err_header = [("Content-type", ContentType.APPLICATION_JSON.value)]
        start_response(err_status, err_header)
        return [json.dumps({"error": err_msg}).encode("utf-8")]
    
    @staticmethod
    def build_status(status_code: int) -> str:
        """
        Build an HTTP status message of the format '[{CODE} {MESSAGE}]'
        """
        if status_code in STATUS_CODE_MAP:
            return str(status_code) + " " + STATUS_CODE_MAP[status_code]
        else:
            return "500 " + STATUS_CODE_MAP[500]
        