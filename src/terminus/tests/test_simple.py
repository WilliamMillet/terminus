
import json
from pytest_mock import MockerFixture

from terminus.api import API
from terminus.types import HTTPMethod, Request
from terminus.tests.utils import build_environ

def test_simple_get(mocker: MockerFixture) -> None:
    api = API()
    @api.get("/hello/world")
    def hello(req: Request):
        return "Hello World", 200
    
    environ = build_environ("/hello/world", HTTPMethod.GET) 
    start_response = mocker.Mock()
    
    res = api(environ, start_response)
    
    status_arg, headers_arg = start_response.call_args[0]
    assert status_arg == "200 OK"
    assert ("Content-Type", "text/plain") in headers_arg
    assert ("Content-Length", str(len("Hello World"))) in headers_arg
    
    res_list = list(res)
    assert len(res_list) == 1
    assert res_list[0].decode("utf-8") == "Hello World"
    
def test_unknown_http_method_sends_err(mocker: MockerFixture) -> None:
    api = API()
    @api.get("/hello/world")
    def hello(req: Request):
        return "Hello World", 200
    
    environ = build_environ("/hello/world", "FAKE_METHOD") 
    start_response = mocker.Mock()
    
    res = api(environ, start_response)
    
    args = start_response.call_args[0]
    assert len(args) == 2
    status_arg, headers_arg = args
    assert "500" in status_arg
    assert headers_arg == [("Content-Type", "application/json")] 
    
    assert "error" in json.loads(next(iter(res)))
    
    