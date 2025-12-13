# backend_framework
A Python WSGI backend interface using the Gunicorn web server.

Run with 1 worker process:
```bash
gunicorn -w 1 -b 127.0.0.1:8000 --reload --log-level debug --capture-output api:api
```
This will restart when the python code changes.

# Routes
Routes may contain path parameters closed by square brackets. This will look like
```py
t"/app/data/people/{id:int}/"
```

```py
people = [
    "John",
    "Dave",
    "Sarah",
    "Will",
    "Max",
    "Sally",
    "Jane",
]

schema = RouteSchema(
    # When a dictionary body is used, terminus automatically infers that JSON
    # is the data type. This is on by default but can be disabled
    body={
        "a": s.list(elements=(x | y), length=2)
        "b": s.string(pattern=my_regex) | None
    }
    path={
        "id": s.int(min=0, max=6)
    }
)

@app.post("/app/data/people/[id]", schema)
def my_route(req: Request) -> String:
    person_id = req["id"]
    return people[person_id], 200
```