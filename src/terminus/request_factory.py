import json
from wsgiref.types import WSGIEnvironment

from urllib.parse import parse_qs
from io import BytesIO

from terminus.router import RouteDetails, Router
from terminus.types import ContentType, RequestBody, QueryVariables
from terminus.types import Request, Headers

class RequestFactory:
    @staticmethod
    def build_req(environ: WSGIEnvironment, route_details: RouteDetails) -> "Request":
        """
        Generate a structured request object from environmental variables and details about the route
        """
        return Request(
            method=environ["REQUEST_METHOD"],
            params=Router.match_path_variables(route_details, environ["PATH_INFO"]),
            body=RequestFactory.parse_body(
                environ["wsgi.input"],
                environ["CONTENT_TYPE"],
                environ["CONTENT_LENGTH"]
            ),
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
        print(type(body))
        c_type = ContentType(content_type)
        if c_type == ContentType.APPLICATION_JSON:
            return json.load(body)
        elif c_type == ContentType.APPLICATION_OCTET_STREAM:
            return body.read(content_len)
        else:
            return body.read(content_len).decode("utf-8")