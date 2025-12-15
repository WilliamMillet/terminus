
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
    
    start_response.assert_called_once_with(
        "200 OK",
        [("Content-type", "text/plain")]
    )
    
    res_list = list(res)
    assert len(res_list) == 1
    assert res_list[0].decode("utf-8") == "Hello World"