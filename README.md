# Terminus
Terminus is a clean and intuitive backend web framework for Python implemented on top of WSGI and Gunicorn. As of now, the project provides a range of features such as 
- A simple API object which endpoints can be attached to via decorators, adding them to an endpoint registry
- Dynamic routing with path and query variables
- Simplified objects such as `Request` and `Headers` and `Response` for rapid development

(and more to come!)
# Running
As of now, the server can be run be executing this command while in the `src` folder:
```bash
gunicorn -w 1 -b 127.0.0.1:8000 --reload --log-level debug --capture-output terminus.api:api
```
This will restart when the python code changes.

I will (hopefully) soon add a simplified command for running the server
# Framework Guide
## Routes
To declare a route in Terminus, you can use one of various decorators implemented for each HTTP method. This must contain the path the route should be triggered by, and support a request object.
```py
@api.get("/hello/world")
def hello_world(req: Request):
    return "Hello World", 200
```
The HTTP routes supported are:
- `GET`
- `POST`
- `PUT`
- `DELETE`
- `PATCH`
- `TRACE`
- `OPTIONS`
- `CONNECT`

In your route function, you can find the details of the request in the `Request` argument passed. This contains data such as any path variables, dictionaries for query and path variables, various headers and more. 

To denote that a route accepts path variables, you can enclose the parameter in square brackets. You can then access these by indexing req.params
```py
@api.get("/app/users/[id]")
def hello_world(req: Request):
    user_id = req.params["id"]

    return users[user_id], 200
```
## Responses
To return a response in your API endpoint, there are several options. If you wish to specify the status code, you must return a tuple `(body, status)`. The status field here must be an integer. The body can be of a range of types. The primitive-like types supported are `str`, `int`, `bool` which are stringified and encoded in UTF-8, as `bytes` which is left as is. For these types the *Content-Type* HTTP header will be set to `text/plain`, unless binary is used in which `application/octet-stream` is set. Lists and dictionaries are also supported. When either of these is returned, they are parsed to a JSON string which is encoded into a UTF-8 format. The content type will then be automatically set to `application/json`.

If you return a non-tuple, the whole return type will be treated as the body and the status code will be automatically set to 200.
```py
# ...Tuple return
return "Failed to found user", 404

# ...Single return
return "Hello World
```
## Requests
Terminus provides an immutable `Request` object for interacting with the HTTP request that triggered a function call. This provides the following properties
- `method`: An `HTTPMethod` enum representing the method used in the request. The value of this enum will be the capitalised method name
- `body`: The body of the call parsed as a `dict`, `list`, `str` or `bytes` in accordance with the `Content-Type` header. When including a body in an HTTP request, you must include the headers `Content-Type` and `Content-Length`. Failing to do this will lead to a 400 status code response. By default in Terminus, bodies will be automatically parsed according to the content type. For example, JSON responses will be parsed to dictionaries. A feature to disable this should be added in the future.
- `params`: A dictionary of path parameters
- `query`: A dictionary of query parameters. The values of this dictionary can be either a single string, or a list of strings if there where multiple of one key in the URL (e.g. `/app?a=1&a=2&a=3`).
- `protocol`: The HTTP protocol string.
- `headers`: A `Header` dataclass containing relevant HTTP headers. These headers are:
    - `host`: The HTTP host string
    - `accept`: The `Accept` HTTP key split into a list of strings by spaces
    - `accept_language`: The `Accept-Language` HTTP key split into a list by spaces
    - `accept_encoding`: The `Accept-Encoding` HTTP key split into a list by spaces
    - `connection`: The `Connection` header value as a string
    - `remote_address`: The string IP of the requester
    - `content_type`: A `ContentType` enum representing the content type being sent (e.g "`application/json`"). The value of this will be the actual content type header string.

## Middleware
Terminus supports the use of middleware before and after a core function request. This can be used for authentication, logging, validation and various other tasks. One way to start a global middleware *pipeline* is to use the `pre_request` decorator:
```py
@api.pre_request
def pre1(req: Request):
    pass
```
Declaring a function with this decorator will add this middleware to the end of the pre-function routines in the middleware pipeline. This means that when any route in an API is called, this middleware will be executed first. In pre-request middleware you can either return a value or not return a value. If you don't return a value, the middleware pipeline will continue as normal and the next function will be executed. If you do return a value, it must be a regular request function return type (e.g. a body and status code tuple, or just a body). This will end the pipeline and return that body and status code if one is provided.

You can also declare `after_request` decorated functions
```py
@api.after_request
def after(req: Request):
    pass
``` 
This will execute after your primary function has returned. Unlike pre-primary function middleware, this cannot return a value, so it is largely limited to logging an interaction with external systems.

In both pre and after requests, you can read and write to a `context` property of the request object
```py
@api.pre_request
def pre1(req: Request):
    # Reading
    print(req.context["Foo"])
    # Writing
    print(req.context["Bar"]) = 10
```
This is the most effective way of transferring information between middleware. It is particularly useful for authentication/authorisation scenarios, as you can store details of the authenticated user after validating them.
```py
@api.pre_request
def auth(req: Request):
    # Auth checks
    req.context["username"] = validated_username
    req.context["email"] = validated_email
    req.context["id"] = validated_id
```

# Technical notes
The 8 near identical methods `get`, `post`, `put`, etc in `api.py` do not constitute the prettiest code, although I am of the belief it is superior to the alternative. Previously I used
the  use the `__getattr__` method. However, there a fundamental problems that arise when using this method with static type checkers like MyPy. When typing this function, we would have to use the Callable type from typing which does not allow for optional arguments.
```py
def __getattr__(self, name: str) -> Callable[[str, list[MiddlewareFn] | None, list[MiddlewareFn] | None], RouteDecorator # Many more arguments...
	pass
```
So, MyPy will continuously get upset with you. The current routes are not perfect, but with unpacked typed dicts they are reasonably compact and work well from a static perspective
```py
def get(self, path, **opts: Unpack[RouteOptions]):
        return self._build_route_decorator(HTTPMethod.GET, path, **opts) 
```