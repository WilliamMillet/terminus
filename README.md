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
To return a response in your API endpoint, there are several options. If you wish to specify the status code, you must return a tuple `(body, status)`. The status field here must be an integer. The body can be of a range of types. The primitive-like types supported are `str`, `int`, `bool` which are stringified and encoded in UTF-8, as `bytes` which is left as is. For these types the *Content-Type* HTTP header will be set to `text/plain`, unless binary is used in which `application/octet-stream` is set Lists. and dictionaries are also supported. When either of these is returned, they are parsed to a JSON string which is encoded into a UTF-8 format. The content type will then be automatically set to `application/json`.

If you return a non-tuple, the whole return type will be treated as the body and the status code will be automatically set to 200.
```py
# ...Tuple return
return "Failed to found user", 404

# ...Single return
return "Hello World
```