import pytest
import json
from pytest_mock import MockerFixture

from terminus.types import HTTPMethod, Request, HTTPError
from terminus.api import API
from terminus.tests.utils import build_environ

def test_singular_return(mocker: MockerFixture) -> None:
    """Test that when a non tuple is passed, the response defaults to 200"""
    api = API()
    @api.get("/hello/world")
    def hello(req: Request):
        return "Hello World"
    
    start_response = mocker.Mock()
    res = api(build_environ("/hello/world"), start_response)
    
    status_args, headers_arg = start_response.call_args[0]
    assert status_args == "200 OK" 
    assert ("Content-Type", "text/plain") in headers_arg
    
    assert next(iter(res)).decode("utf-8") == "Hello World"

def test_unknown_status_has_no_message(mocker: MockerFixture) -> None:
    """Unknown status codes should not have a message"""
    api = API()
    @api.get("/unknown/status")
    def hello(req: Request):
        return "Hi", 1823

    start_response = mocker.Mock()
    api(build_environ("/unknown/status") , start_response)
    
    status_args, headers_arg = start_response.call_args[0]
    assert status_args == "1823" 
    assert ("Content-Type", "text/plain") in headers_arg

def test_non_int_status_raises(mocker: MockerFixture) -> None:
    """Non integer status codes are not allowed and should raise an error for a developer"""
    api = API()
    @api.get("/")
    def hello(req: Request):
        return "Hi", "Totally really status code"

    with pytest.raises(HTTPError):
        start_response = mocker.Mock()
        api(build_environ("/") , start_response)
        
def test_non_dictionary_cookie_res_raises(mocker: MockerFixture) -> None:
    """API endpoint functions can only return cookie dictionaries of strings"""
    api = API()
    @api.get("/")
    def hello(req: Request):
        return "Hi", 200, "My cookie dictionary that should break"

    with pytest.raises(HTTPError):
        start_response = mocker.Mock()
        api(build_environ("/") , start_response)

def test_non_str_cookie_res_raises(mocker: MockerFixture) -> None:
    """
    When an API endpoint returns a dictionary of cookies where a key or value is not a string,
    this should break even though a dictionary is being used
    """
    api = API()
    @api.get("/")
    def hello(req: Request):
        return "Hi", 200, {"Key", 190123}

    with pytest.raises(HTTPError):
        start_response = mocker.Mock()
        api(build_environ("/") , start_response)
        

@pytest.mark.parametrize("primitive, string", [("Hello", "Hello"), (1, "1"), (True, "True")])
def test_primitive_like_bodies(mocker: MockerFixture, primitive, string) -> None:
    api = API()
    @api.get("/return/primitive")
    def return_primitive(req: Request):
        return primitive, 200
    
    start_response = mocker.Mock()
    res = api(build_environ("/return/primitive") , start_response)
    
    headers_arg = start_response.call_args[0][1]
    assert ("Content-Type", "text/plain") in headers_arg
    
    assert next(iter(res)).decode("utf-8") == string

def test_byte_body(mocker: MockerFixture) -> None:
    api = API()
    @api.get("/return/bytes")
    def return_bytes(req: Request):
        return b"Hello World", 200
    
    start_response = mocker.Mock()
    res = api(build_environ("/return/bytes") , start_response)
    
    headers_arg = start_response.call_args[0][1]
    assert  ("Content-Type", "application/octet-stream") in headers_arg
    
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
    @api.get("/return/json")
    def return_json(req: Request):
        return json_body, 200
    
    environ = build_environ("/return/json", HTTPMethod.GET) 
    start_response = mocker.Mock()
    
    res = api(environ, start_response)
    
    headers_arg = start_response.call_args[0][1]
    assert ("Content-Type", "application/json") in headers_arg
    
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
    
    start_response = mocker.Mock()

    with pytest.raises(Exception):
        api(build_environ("/bad") , start_response)
               
def test_unknown_body_disallowed(mocker: MockerFixture) -> None:
    """
    Bodies of an unknown type should lead to an exception
    """
    api = API()
    @api.get("/bad")
    def hello(req: Request):
        # Set is not a valid type
        return set([1, 2, 3]), 200
    
    start_response = mocker.Mock()
    
    with pytest.raises(Exception):
        api(build_environ("/bad") , start_response)
        
def test_unparsable_dict_sends_err(mocker: MockerFixture) -> None:
    """Certain dictionaries are not parsable as JSON and we should return an error JSON instead"""
    api = API()
    @api.get("/return/json")
    def return_json(req: Request):
        return {(1, 2, 3): "I am a tuple key"}, 200
    
    start_response = mocker.Mock()
    with pytest.raises(Exception):
        res = api(build_environ("/return/json") , start_response)