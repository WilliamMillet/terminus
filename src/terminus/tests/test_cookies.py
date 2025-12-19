
import json
from pytest_mock import MockerFixture

from terminus.api import API
from terminus.types import HTTPMethod, Request
from terminus.tests.utils import build_environ

def test_request_cookie(mocker: MockerFixture) -> None:
    api = API()
    @api.get("/hello/world")
    def hello(req: Request):
        return req.headers.cookies
    
    cookie_key = "my_cookie"
    cookie_val = "secret"
    
    environ = build_environ("/hello/world", custom_fields={
        "HTTP_COOKIE": f"{cookie_key}={cookie_val}"}
    ) 
    start_response = mocker.Mock()
    
    res = api(environ, start_response)
    
    status_arg, headers_arg = start_response.call_args[0]
    assert status_arg == "200 OK"
    assert ("Content-Type", "application/json") in headers_arg
    parsed = next(iter(res)).decode("utf-8")
    assert {cookie_key: cookie_val} == json.loads(parsed)
    
def test_response_cookie(mocker: MockerFixture) -> None:
    api = API()

    cookie_key = "my_cookie"
    cookie_val = "secret"

    @api.get("/")
    def hello(req: Request):
        return "My body", 200, {cookie_key: cookie_val}
    
    start_response = mocker.Mock()
    res = api(build_environ("/"), start_response)
    
    _, headers_arg = start_response.call_args[0]
    exp_header = ("Set-Cookie", f"{cookie_key}={cookie_val} Path=/; HttpOnly")
    assert exp_header in headers_arg 
    