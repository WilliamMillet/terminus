import json

from wsgiref.types import StartResponse
from typing import Any
from enum import Enum
from dataclasses import dataclass

type RouteFnRes = tuple[Any] | tuple[Any, int]

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

class ContentType(Enum):
    TEXT_PLAIN = "text/plain"
    APPLICATION_JSON = "application/json"

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
        if len(fn_res) == 1:
            status = Response.build_status(200)
        elif len(fn_res) == 2:
            status = Response.build_status(fn_res[1])
        else:
            # Exception is raised here is this is a developer issue
            raise Exception("Invalid route return value. Routes must return" +
                            " either (body, status) or (body)")
            
        body = fn_res[0]
        
        if isinstance(body, dict | tuple | list):
            try:
                body_str = json.dumps(body)
            except TypeError as e:
                body_str = json.dumps({"error": f"Failed to parse body as JSON: {e}"})
            content_type = ContentType.APPLICATION_JSON
        else:
            body_str = str(body)
            content_type = ContentType.TEXT_PLAIN
        
        encoded_body = body_str.encode("utf-8")

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
        