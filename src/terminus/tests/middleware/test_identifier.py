from pytest_mock import MockerFixture
from pytest import CaptureFixture, raises

from terminus.api import API
from terminus.tests.utils import build_environ
from terminus.types import Request, HTTPMethod, HTTPError
from terminus.middleware import create_logger, identifier
from terminus.tests.types import BodyDTO

def test_identifier_with_x_request_id(mocker: MockerFixture) -> None:
    """
    Test that the identifier middleware uses a pre-provided identifier from the X-Request-ID
    header if it is provided
    """
    api = API()    
    
    @api.get("/", pre=[identifier])
    def fn(req: Request):
        return req.context["unique_id"], 200
    
    test_id = "very_good_id"
    
    start_response = mocker.Mock()
    environ = build_environ("/", custom_fields={"HTTP_X_REQUEST_ID": test_id})
    res = api(environ, start_response)
    
    body = next(iter(res)).decode("utf-8")
    assert body == test_id

def test_identifier_with_no_x_request_id(mocker: MockerFixture) -> None:
    """
    Test that the identifier middleware generates a random ID even when no X-Request-ID header
    exists
    """
    api = API()

    @api.get("/", pre=[identifier])
    def fn(req: Request):
        return req.context["unique_id"], 200
    
    start_response = mocker.Mock()
    environ = build_environ("/")
    res = api(environ, start_response)
    
    body = next(iter(res)).decode("utf-8")
    assert len(body) >= 1