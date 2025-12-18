from terminus.execution_pipeline import MiddlewareFnRes, MiddlewareFn
from terminus.types import Request, RouteError
from datetime import datetime

import uuid 
from pathlib import Path

def create_logger(write_to: Path | None = None, include_body: bool = False,
                  include_headers: bool = False, include_req_id: bool = False,
                  include_context: bool = False) -> MiddlewareFn:
    """
    Create a logging middleware function to log requests to stdout and possibly a file path.
    Arguments:
        - <write_to> The file, if any to write to (stdout is always written too)
        - <include_body> Whether or not to include the body of the request. The body will be
          truncated after 4096 characters
        - <include_req_id> Include the request_id set via the identifier middleware. If this has
          not been set a RouteError will be raised
        - <include_context> Whether or not to include the request context property in the request
    """
    
    stringify_dict = lambda d: "[" + ", ".join(f"{str(k)}={str(v)}" for k, v in d.items()) + "]"
    
    def logger(req: Request) -> MiddlewareFnRes:
        log_obj: dict[str, str] = {
            "Timestamp": str(datetime.now()),
            "Log ID": str(uuid.uuid4()),
            "Method": req.method.value,
            "Path": req.path,
            "Path parameters": stringify_dict(req.params),
            "Query parameters": stringify_dict(req.query)
        }
        
        if include_body:
            log_obj["Body"] = str(req.body)[:4096] if req.body is not None else "None"
        if include_headers:
            log_obj["Headers"] = str(req.headers)  
        if include_req_id:
            if "unique_id" not in req.context:
                raise RouteError("Cannot log request ID if no request ID is set. Please use the" +
                                "identifier middleware earlier in the middleware pipeline")
            log_obj["Request ID"] = req.context["unique_id"]
        if include_context:
            log_obj["Context"] = stringify_dict(req.context)
            
        log_str = "\n" + "\n".join(f"{key}: {val}" for key, val in log_obj.items())
        
        print(log_str)
        if write_to is not None:
            with open(write_to, "a") as f:
                f.write(log_str)     
        
        return None   
    
    return logger