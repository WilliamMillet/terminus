"""
Test for the request object passed to each function.

Params are not tested here because they are sufficiently covered in test_routing.py
"""
import json
import pytest
from pytest_mock import MockerFixture

from terminus.api import API
from terminus.tests.utils import build_environ
from terminus.tests.types import BodyDTO
from terminus.types import Request, HTTPMethod, ContentType

def test_req_headers(mocker: MockerFixture) -> None:
    """
    Test the headers of the requirement object are as expected.
    """
    api = API()
    
    @api.post("/")
    def a(req: Request):
        headers = req.headers
        c_type = headers.content_type.value if headers.content_type is not None else ""
        return {
            "host": headers.host,
            "accept": headers.accept,
            "accept_language": headers.accept_language,
            "accept_encoding": headers.accept_encoding,
            "connection": headers.connection,
            "remote_address": headers.remote_address,
            "content_type": c_type 
        }
    
    body_content = b"This is the body"
    # We create separate environs so there is no risk the test wrongly passes by manipulating the
    # original environmental variables
    exp_environ = build_environ("/", HTTPMethod.POST, BodyDTO(body_content))
     
    start_response = mocker.Mock()
    res = api(build_environ("/", HTTPMethod.POST) , start_response)
    
    body_dict = json.loads(next(iter(res)))
    # assert body_dict == 1
    assert body_dict["host"] == exp_environ["HTTP_HOST"]
    assert body_dict["accept"] == exp_environ["HTTP_ACCEPT"].split(",")
    assert body_dict["accept_language"] == exp_environ["HTTP_ACCEPT_LANGUAGE"].split(",")
    assert body_dict["accept_encoding"] == exp_environ["HTTP_ACCEPT_ENCODING"].split(", ")
    assert body_dict["connection"] == exp_environ["HTTP_CONNECTION"]
    assert body_dict["remote_address"] == exp_environ["REMOTE_ADDR"]
    assert body_dict["content_type"] == exp_environ["CONTENT_TYPE"]

content_types = [
    (ContentType.TEXT_PLAIN, b"Hello World"),
    (ContentType.APPLICATION_JSON, json.dumps({"Hello": "World"}).encode("utf8")),
    (ContentType.APPLICATION_OCTET_STREAM, b"Hello world")
]
    
@pytest.mark.parametrize("content_type, content", content_types)
def test_content_type_set(mocker: MockerFixture, content_type: ContentType,
                          content: bytes) -> None:
    """
    Test that the content type is correctly set for each type of body. This inadvertently tests if
    the body parsing works at all
    """
    api = API()
    @api.post("/")
    def a(req: Request):
        headers = req.headers
        if headers.content_type is not None:
            return headers.content_type.value
        else:
            return ""
            
    
    start_response = mocker.Mock()
    environ = build_environ("/", HTTPMethod.POST, BodyDTO(content, content_type))
    res = api(environ, start_response)

    body = next(iter(res)).decode("utf-8")
    assert body == content_type.value

def test_method_set(mocker: MockerFixture):
    api = API()
    
    @api.delete("/")
    def fn(req: Request):
        return req.method.value
    
    start_response = mocker.Mock()
    environ = build_environ("/", HTTPMethod.DELETE)
    res = api(environ, start_response)

    body = next(iter(res)).decode("utf-8")
    assert body == HTTPMethod.DELETE.value

def test_query_params_set(mocker: MockerFixture):
    api = API()
    
    @api.get("/")
    def fn(req: Request):
        return req.query
    
    start_response = mocker.Mock()
    res = api(build_environ("/?foo=bar&x=y&baz=1&baz=2") , start_response)
    
    body_dict = json.loads(next(iter(res)))
    
    assert body_dict == {
        "foo": "bar",
        "x": "y",
        "baz": ["1", "2"]
    }

def test_server_protocol_set(mocker: MockerFixture):
    api = API()
    
    @api.get("/")
    def fn(req: Request):
        return req.protocol
    
    start_response = mocker.Mock()
    environ = build_environ("/")
    res = api(environ, start_response)

    body = next(iter(res)).decode("utf-8")
    exp_environ = build_environ("/")
    assert body == exp_environ["SERVER_PROTOCOL"] 