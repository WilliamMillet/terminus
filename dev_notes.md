# Resources
https://peps.python.org/pep-0333/#the-application-framework-side
https://rahmonov.me/posts/what-the-hell-is-wsgi-anyway-and-what-do-you-eat-it-with/
https://packaging.python.org/en/latest/tutorials/packaging-projects/

# TODO
Ordered
- Handle dictionary return types being converted to JSON
- Handle path parameters
- Handle query parameters

Long term
- Handle default schema content type infering
- Handle turning turning off default schema content type infering

TO DO 

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