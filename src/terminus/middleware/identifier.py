from terminus.execution_pipeline import MiddlewareFnRes
from terminus.types import Request

import uuid

def identifier(req: Request) -> MiddlewareFnRes:
    """
    Tag a request with a unique identifier accessible via the [unique_id] key in the request
    context
    """
    # d in ID is lowercased as WSGI converts headers to upper snake case, and the human readable
    # format Terminus converts them to is title kebab-case.
    if "X-Request-Id" in req.headers.raw:
        id = req.headers.raw["X-Request-Id"]
    else:
        # Header is normalised to a string as we want a common format, and in same cases a header
        # may be passed with a non UUID string
        id = str(uuid.uuid4())
    
    req.context["unique_id"] = id
    
    return None