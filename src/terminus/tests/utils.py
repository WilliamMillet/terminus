
from io import BytesIO
from wsgiref.types import WSGIEnvironment
from wsgiref.util import setup_testing_defaults

from terminus.tests.types import BodyDTO
from terminus.types import HTTPMethod

URI_MAX_PARTS = 2

EXTRA_ENVIRON_DEFAULTS = {
    'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,' +
    'image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9',
    'HTTP_ACCEPT_ENCODING':  'gzip, deflate, br, zstd',
    'HTTP_CONNECTION': 'keep-alive',
    'REMOTE_ADDR': '127.0.0.1'
}

def build_environ(uri: str, method: HTTPMethod | str = HTTPMethod.GET,
                  body: BodyDTO | None = None,
                  custom_fields: dict[str, str] | None = None) -> dict:
    """
    Create a dictionary of WSGI endpoint environmental variables using a set of defaults as well
    as a provided raw URI (path + query parameters concatenated) and an HTTP method 
    """
    environ: WSGIEnvironment = EXTRA_ENVIRON_DEFAULTS
    
    setup_testing_defaults(environ)
    
    parts = uri.split("?")
    assert len(parts) <= URI_MAX_PARTS
    if len(parts) == 2:
        path, query = parts
    else:
        path, query = parts[0], ""
    
    environ["PATH_INFO"] = path
    environ["QUERY_STRING"] = query
    environ["RAW_URI"] = uri
    if body is not None:
        environ["wsgi.input"] = BytesIO(body.content)
        environ["CONTENT_TYPE"] = body.content_type.value
        environ["CONTENT_LENGTH"] = body.content_length
    
    if custom_fields is not None:
        environ.update(custom_fields)
    
    environ["REQUEST_METHOD"] = method if isinstance(method, str) else method.value

    return environ