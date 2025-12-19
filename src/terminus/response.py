import json

from wsgiref.types import StartResponse
from dataclasses import dataclass, field
from typing import Any

from terminus.types import ContentType, RouteFnRes, Cookies, WSGIFormatHeaders, HTTPError
from terminus.constants import STATUS_CODE_MAP

VALID_BODY_TYPE_NAMES = [
    "dict"
    "list"
    "bytes"
    "int"
    "str"
    "bool"
]

@dataclass(frozen=True)
class ResponseFields:
    status: str
    body: bytes
    content_type: ContentType
    extra_headers: WSGIFormatHeaders
    
@dataclass(frozen=True)
class NormalisedRouteFnRes:
    body: Any
    status: str = "200 OK"
    cookies: WSGIFormatHeaders = field(default_factory=list)
    
@dataclass(frozen=True)
class BodyTypePair:
    content: bytes
    content_type: ContentType

class Response:
    def __init__(self, fn_res: RouteFnRes, start_response: StartResponse) -> None:
        res_fields = Response.parse_function_res(fn_res)
        self._body = [res_fields.body]
        headers: WSGIFormatHeaders = [
            ("Content-Type", res_fields.content_type.value),
            ("Content-Length", str(len(res_fields.body)))
        ] + res_fields.extra_headers
        
        self._response_routine = lambda: start_response(res_fields.status, headers)
            
    @staticmethod
    def parse_function_res(fn_res: RouteFnRes) -> ResponseFields:
        """
        Takes the return value from a route's function and extracts the HTTP
        status, parses and encodes the body then returns relevant response
        fields
        """
        normalised = Response._normalise_route_fn_res(fn_res)
        parsed_body = Response._parse_body(normalised.body)
        
        return ResponseFields(
            status=normalised.status,
            body=parsed_body.content,
            content_type=parsed_body.content_type,
            extra_headers=normalised.cookies
        )
        
    @staticmethod
    def _parse_body(body: Any) -> BodyTypePair:
        """Parse the response body and determine the content type according to this"""
        if isinstance(body, dict | list):
            try:
                body_str = json.dumps(body)
            except TypeError as e:
                raise HTTPError(f"Body container type is valid (f{type(body)}), but it failed" +
                                "to be parsed. This is likely due to an invalid inner key such" +
                                f"as a tuple, frozenset, etc. Parsing Error:\n {e}")
            return BodyTypePair(body_str.encode("utf8"), ContentType.APPLICATION_JSON)
        elif isinstance(body, bytes):
            return BodyTypePair(body, ContentType.APPLICATION_OCTET_STREAM)
        elif isinstance(body, int | float | str | bool):
            body_str = str(body)
            return BodyTypePair(body_str.encode("utf-8"), ContentType.TEXT_PLAIN)
        else:
            wrong_type = type(body).__name__
            raise HTTPError(f"Unsupported response body type '{wrong_type}'. Accepted types" +
                            " are: \n" + "\n - ".join(VALID_BODY_TYPE_NAMES) + "\n")
        
    @staticmethod
    def _normalise_route_fn_res(fn_res: RouteFnRes) -> NormalisedRouteFnRes:
        """
        Convert the raw return value of a route endpoint function to a normalised
        dataclass. This does not process the body.
        """
        cookies: WSGIFormatHeaders = []
        status = "200 OK"
        if isinstance(fn_res, tuple):
            if not (0 < len(fn_res) <= 3):
                # HTTPError is raised here is this is a developer issue
                raise HTTPError("Invalid route return value. If route is a tuple, it must be of the" +
                                "The form (body, status) or (body, status, cookies)")
            
            body = fn_res[0]
            if len(fn_res) >= 2:
                if not isinstance(fn_res[1], int):
                    raise HTTPError(f"Status '{fn_res[1]}' is not valid. Only integers may be "
                                    + "returned as statuses")
                status = Response.build_status(fn_res[1])
            if len(fn_res) >= 3:
                if not isinstance(fn_res[2], dict):
                    raise HTTPError("Cookies returned from function must be a dictionary. " +
                                    str(fn_res[2]) + " is not a valid cookie dictionary")
                for key, val in fn_res[2].items():
                    if not isinstance(key, str) or not isinstance(val, str):
                        raise HTTPError("The cookie dictionary returned by a function may only "
                                        + "have string keys")
                
                cookie_list = Response._parse_cookies_as_header(fn_res[2])
                cookies.extend(cookie_list)
        else:
            body = fn_res
        return NormalisedRouteFnRes(body, status, cookies)

    @staticmethod
    def _parse_cookies_as_header(cookies: Cookies) -> WSGIFormatHeaders:
        return [
            ("Set-Cookie", f"{key}={val} Path=/; HttpOnly")
            for key, val in cookies.items()
        ]
    
    def send(self) -> list[bytes]:
        """
        Triggers the start response routine and returns the body in a format
        that can be returned exactly by the WSGI callable entrypoint
        """
        self._response_routine()
        return self._body
    
    @staticmethod
    def send_err(start_response: StartResponse, err_msg: str, err_code: int = 500) -> list[bytes]:
        """Triggers the start response routine and returns the body for an error"""
        err_status = Response.build_status(err_code)
        err_header = [("Content-Type", ContentType.APPLICATION_JSON.value)]
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
            return str(status_code)
        