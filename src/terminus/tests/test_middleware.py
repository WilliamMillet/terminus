from pytest_mock import MockerFixture
from pytest import CaptureFixture

from terminus.api import API
from terminus.tests.utils import build_environ
from terminus.types import Request, HTTPMethod

def test_simple_pre_middleware(mocker: MockerFixture) -> None:
    api = API()
    
    @api.pre_request
    def pre(req: Request):
        req.context["Test"] = "mycontext"
    
    @api.get("/")
    def fn(req: Request):
        return req.context["Test"]
    
    start_response = mocker.Mock()
    environ = build_environ("/", HTTPMethod.GET)
    res = api(environ, start_response)

    body = next(iter(res)).decode("utf-8")
    assert body == "mycontext"
    
def test_pre_middleware_early_res(mocker: MockerFixture) -> None:
    """Make sure that middleware can lead to a proper early return when prompted"""
    api = API()
    
    @api.pre_request
    def pre(req: Request):
        return "Override", 400
    
    @api.get("/")
    def fn(req: Request):
        return "Normal"
    
    start_response = mocker.Mock()
    environ = build_environ("/", HTTPMethod.GET)
    res = api(environ, start_response)
    
    status_args, headers_arg = start_response.call_args[0]
    assert "400" in status_args 
    assert ("Content-type", "text/plain") in headers_arg
    
    assert next(iter(res)).decode("utf-8") == "Override"
    
def test_simple_post_middleware(mocker: MockerFixture, capsys: CaptureFixture) -> None:
    api = API()
    
    @api.after_request
    def post(req: Request):
        print("MY_UNIQUE_STRING")
    
    @api.get("/")
    def fn(req: Request):
        return "Hello World", 200
    
    start_response = mocker.Mock()
    environ = build_environ("/", HTTPMethod.GET)
    api(environ, start_response)

    std_buffers = capsys.readouterr()
    assert "MY_UNIQUE_STRING" in str(std_buffers)

    
def test_middleware_pipeline(mocker: MockerFixture, capsys: CaptureFixture) -> None:
    api = API()
    
    @api.pre_request
    def pre1(req: Request):
        req.context["foo"] = "a"
    
    @api.pre_request
    def pre2(req: Request):
        req.context["foo"] += "b"
        
    @api.get("/")
    def fn(req: Request):
        return req.context["foo"], 200

    @api.after_request
    def post(req: Request):
        print("MY_UNIQUE_STRING")
    
    start_response = mocker.Mock()
    environ = build_environ("/", HTTPMethod.GET)
    res = api(environ, start_response)
    
    status_args, headers_arg = start_response.call_args[0]
    assert "200" in status_args 
    assert ("Content-type", "text/plain") in headers_arg
    assert next(iter(res)).decode("utf-8") == "ab"

    std_buffers = capsys.readouterr()
    assert "MY_UNIQUE_STRING" in str(std_buffers)