# Resources
https://peps.python.org/pep-0333/#the-application-framework-side
https://rahmonov.me/posts/what-the-hell-is-wsgi-anyway-and-what-do-you-eat-it-with/
https://packaging.python.org/en/latest/tutorials/packaging-projects/

# TODO
## Shorter term goals
- Middleware

## Longer term goals
- Add validator and parser system like the one described below
- IP white list or black list
- Add rate limiting based on IP
- Cooking parsing

```py
schema = RouteSchema(
    body={
        "a": s.list(elements=(x | y), length=2)
        "b": s.string(pattern=my_regex) | None
    }
    path={
        "id": s.int(min=0, max=6)
    }
)
```
Maybe allow predicate applied on bodies (e.g. validate=lambda x: x in people)
## Things to test

### Routing
Test when route does not exist, an error json is shown

Test post routes