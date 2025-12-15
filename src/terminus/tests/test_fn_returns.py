import pytest
import json
from pytest_mock import MockerFixture

from terminus.types import HTTPMethod, Request
from terminus.api import API
from terminus.tests.utils import build_environ

def test_singular_return(mocker: MockerFixture) -> None:
    """Test that when a non tuple is passed, the response defaults to 200"""
    api = API()
    @api.get("/hello/world")
    def hello(req: Request):
        return "Hello World"
    
    environ = build_environ("/hello/world", HTTPMethod.GET) 
    start_response = mocker.Mock()
    
    res = api(environ, start_response)
    
    start_response.assert_called_once_with(
        "200 OK",
        [("Content-type", "text/plain")]
    )
    
    assert next(iter(res)).decode("utf-8") == "Hello World"

def test_unknown_status_has_no_message(mocker: MockerFixture) -> None:
    api = API()
    @api.get("/unknown/status")
    def hello(req: Request):
        return "Hi", 1823

    environ = build_environ("/unknown/status", HTTPMethod.GET) 
    start_response = mocker.Mock()
    
    res = api(environ, start_response)
    
    start_response.assert_called_once_with(
        "1823",
        [("Content-type", "text/plain")]
    )


@pytest.mark.parametrize("primitive, string", [("Hello", "Hello"), (1, "1"), (True, "True")])
def test_primitive_like_bodies(mocker: MockerFixture, primitive, string) -> None:
    api = API()
    @api.get("/return/primitive")
    def return_primitive(req: Request):
        return primitive, 200
    
    environ = build_environ("/return/primitive", HTTPMethod.GET) 
    start_response = mocker.Mock()
    
    res = api(environ, start_response)
    
    start_response.assert_called_once_with(
        "200 OK",
        [("Content-type", "text/plain")]
    )
    
    assert next(iter(res)).decode("utf-8") == string

def test_byte_body(mocker: MockerFixture) -> None:
    api = API()
    @api.get("/return/bytes")
    def return_bytes(req: Request):
        return b"Hello World", 200
    
    environ = build_environ("/return/bytes", HTTPMethod.GET) 
    start_response = mocker.Mock()
    
    res = api(environ, start_response)
    
    start_response.assert_called_once_with(
        "200 OK",
        [("Content-type", "application/octet-stream")]
    )
    
    assert next(iter(res)) == b"Hello World"

JSON_BODIES = [
    ({
        "Foo": 1,
        "Bar": (1, 2, 3, True),
        "nested": {
            1: "I love wsgi"
        }
    },
    {
        "Foo": 1,
        "Bar": [1, 2, 3, True],
        "nested": {
            "1": "I love wsgi"
        }
    }),
    (
        [1, 2],
        [1, 2]
    )
]    

@pytest.mark.parametrize("json_body, exp", JSON_BODIES)
def test_json_body(mocker: MockerFixture, json_body, exp) -> None:
    api = API()
    @api.get("/return/bytes")
    def return_bytes(req: Request):
        return json_body, 200
    
    environ = build_environ("/return/bytes", HTTPMethod.GET) 
    start_response = mocker.Mock()
    
    res = api(environ, start_response)
    
    start_response.assert_called_once_with(
        "200 OK",
        [("Content-type", "application/json")]
    )
    
    decoded = next(iter(res)).decode()
    assert json.loads(decoded) == exp
    
def test_long_tuple_is_disallowed(mocker: MockerFixture) -> None:
    """
    Tuples with a length over 3 should not be returned as tuples should be reserved for responding
    with information other then the body, such as the status code
    """
    api = API()
    @api.get("/bad")
    def hello(req: Request):
        return ("My", "Name", "Is", "John")
    
    environ = build_environ("/bad", HTTPMethod.GET) 
    start_response = mocker.Mock()
    
    with pytest.raises(Exception):
        api(environ, start_response)
        
def test_unknown_body_disallowed(mocker: MockerFixture) -> None:
    """
    Unknown status codes should lead to an 
    """
    api = API()
    @api.get("/bad")
    def hello(req: Request):
        # Set is not a valid type
        return set([1, 2, 3]), 200
    
    environ = build_environ("/bad", HTTPMethod.GET) 
    start_response = mocker.Mock()
    
    with pytest.raises(Exception):
        api(environ, start_response)
        