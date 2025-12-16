import json
from wsgiref.types import WSGIEnvironment

from urllib.parse import parse_qs
from io import BytesIO

from terminus.router import RouteDetails, Router
from terminus.types import ContentType, RequestBody, QueryVariables, Request, Headers, HTTPMethod, HTTPError

class RequestFactory:
    BODY_KEYS = ("wsgi.input", "CONTENT_TYPE", "CONTENT_LENGTH")
    @staticmethod
    def build_req(environ: WSGIEnvironment, route_details: RouteDetails) -> "Request":
        """
        Generate a structured request object from environmental variables and details about the route
        """
        included_body_keys = [k for k in RequestFactory.BODY_KEYS if k in environ]
        if len(included_body_keys) == len(RequestFactory.BODY_KEYS):
            body = RequestFactory.parse_body(
                environ["wsgi.input"],
                environ["CONTENT_TYPE"],
                environ["CONTENT_LENGTH"]
            )
        elif "wsgi.input" in environ and len(included_body_keys) == len(RequestFactory.BODY_KEYS):
            raise HTTPError("Request with body must contain 'Content-Type' and" +
                               "'Content-Length' headers")
        else:
            body = None
            
        return Request(
            method=HTTPMethod(environ["REQUEST_METHOD"]),
            params=Router.match_path_variables(route_details, environ["PATH_INFO"]),
            body=body,
            query=RequestFactory.build_query(environ["QUERY_STRING"]),
            protocol=environ["SERVER_PROTOCOL"],
            headers=Headers.of(environ)
        )
    
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
    

    @staticmethod
    def parse_body(body: BytesIO, content_type: str, content_len: int) -> RequestBody:
        c_type = ContentType(content_type)
        match c_type:
            case ContentType.APPLICATION_JSON:
                return json.load(body)
            case ContentType.APPLICATION_OCTET_STREAM:
                return body.read(content_len)
            case _:
                return body.read(content_len).decode("utf-8")