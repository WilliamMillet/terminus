from pathlib import Path

from pytest import CaptureFixture, raises
from pytest_mock import MockerFixture

from terminus.api import API
from terminus.middleware import create_logger, identifier
from terminus.tests.types import BodyDTO
from terminus.tests.utils import build_environ
from terminus.types import HTTPMethod, Request, RouteError

BASE_LOG_KEYS = "Timestamp", "Log ID", "Method", "Path", "Path parameters", "Query parameters"

UUID4_LEN = 36
UUID_HYPHENS = 4

def test_simple_stdout_log(mocker: MockerFixture, capsys: CaptureFixture) -> None:
    api = API()

    @api.get("/", pre=[create_logger()])
    def fn(req: Request):
        return "Body", 200
    
    start_response = mocker.Mock()
    environ = build_environ("/?a=1&b=2&b=3", HTTPMethod.GET)
    api(environ, start_response)

    out = capsys.readouterr().out
    
    print(out)
    
    for k in BASE_LOG_KEYS:
        assert k in out
    
    # Sanity check core fields
    rows = out.split("\n")
    for row in rows:
        if row.startswith("Query parameters:"):
            *_, arr_left, arr_mid, arr_right = row.split()
            arr = " ".join([arr_left, arr_mid, arr_right])
            assert arr == "[a=1, b=['2', '3']]"
        elif row.startswith("Path:"):
            _, path = row.split()
            assert path == "/"
        elif row.startswith("Method:"):
             _, method = row.split()
             assert method == "GET"
        elif row.startswith("Log ID:"):
            *_, id = row.split()
            assert len(id) == UUID4_LEN
            assert id.count("-") == UUID_HYPHENS
            
def test_log_to_file(mocker: MockerFixture, tmp_path: Path) -> None:
    """
    Test we can log to a custom file correctly
    """
    api = API()

    out_file = tmp_path / "out.txt"
    @api.get("/", pre=[create_logger(write_to=out_file)])
    def fn(req: Request):
        return "Body", 200
    
    start_response = mocker.Mock()
    environ = build_environ("/?a=1&b=2&b=3", HTTPMethod.GET)
    api(environ, start_response)

    contents = out_file.read_bytes().decode("utf-8")
    # We can just use this field as an indicator that something was written to the file. We have
    # already checked the contents of the logging middleware
    assert "Log ID" in contents
    
def test_log_with_body(mocker: MockerFixture, capsys: CaptureFixture) -> None:
    api = API()

    @api.post("/", pre=[create_logger(include_body=True)])
    def fn(req: Request):
        return "Body", 200
    
    exp_body = b"Hello_World"
    start_response = mocker.Mock()
    environ = build_environ("/", HTTPMethod.POST, BodyDTO(exp_body))
    api(environ, start_response)
    
    out = capsys.readouterr().out
    
    rows = out.split("\n")
    for r in rows:
        if r.startswith("Body:"):
            _, body = r.split()
            assert body == exp_body.decode("utf-8")
            
def test_logging_with_headers(mocker: MockerFixture, capsys: CaptureFixture) -> None:
    api = API()
    
    @api.get("/", pre=[create_logger(include_headers=True)])
    def fn(req: Request):
        return "Body", 200
    
    start_response = mocker.Mock()
    environ = build_environ("/")
    api(environ, start_response)
    
    out = capsys.readouterr().out
    
    rows = out.split("\n")
    for r in rows:
        if r.startswith("Headers:"):
            assert "host" in r
            assert "accept" in r
            assert "connection" in r 
            
def test_logging_with_context(mocker: MockerFixture, capsys: CaptureFixture) -> None:
    """Make sure the context defined in the request can be logged correctly"""
    api = API()
    
    @api.pre_request
    def middleware(req: Request):
        req.context["Foo"] = "Bar"
    
    @api.get("/", pre=[create_logger(include_context=True)])
    def fn(req: Request):
        return "Body", 200
    
    start_response = mocker.Mock()
    environ = build_environ("/")
    api(environ, start_response)
    
    out = capsys.readouterr().out
    
    rows = out.split("\n")
    for r in rows:
        if r.startswith("Context:"):
            _, ctx = r.split()
            assert ctx == "[Foo=Bar]" 
            
def test_logging_request_id(mocker: MockerFixture, capsys: CaptureFixture) -> None:
    """Test that the option to log the request ID from the identifier middleware works"""
    api = API()    
    
    logger = create_logger(include_req_id=True)
    @api.get("/", pre=[identifier, logger])
    def fn(req: Request):
        return "Body", 200
    
    test_id = "very_good_id"
    
    start_response = mocker.Mock()
    environ = build_environ("/", custom_fields={"HTTP_X_REQUEST_ID": test_id})
    api(environ, start_response)
    
    out = capsys.readouterr().out
    
    rows = out.split("\n")
    for r in rows:
        if r.startswith("Request ID:"):
            *_, id = r.split()
            assert id == test_id

def test_logging_missing_request_id(mocker: MockerFixture) -> None:
    """
    Test that when the logger middleware has the include_req_id field enabled but the identifier
    middleware is used before (and therefore the context variable is not set) that an error will
    be raised
    """
    api = API()    
    
    @api.get("/", pre=[create_logger(include_req_id=True)])
    def fn(req: Request):
        return "Body", 200
    
    with raises(RouteError):
        start_response = mocker.Mock()
        environ = build_environ("/")
        api(environ, start_response)