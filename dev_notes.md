# Resources
https://peps.python.org/pep-0333/#the-application-framework-side
https://rahmonov.me/posts/what-the-hell-is-wsgi-anyway-and-what-do-you-eat-it-with/
https://packaging.python.org/en/latest/tutorials/packaging-projects/

# TODO
Ordered

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
```
## Things to test
### Return related
- Return the following json types
    "dict"
    "list"
- Return the following primitive-like types
    "bytes"
    "int"
    "str"
    "bool"

Test unsupported body type leads to an error being thrown

Test unknown status code defaults to 500


### Routing
Test when route does not exist, an error json is shown