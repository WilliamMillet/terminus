"""Tests for the route tree algorithm"""

import pytest
import json
from pytest_mock import MockerFixture

from terminus.types import HTTPMethod, Request
from terminus.api import API
from terminus.tests.utils import build_environ

def test_unknown_route(mocker: MockerFixture) -> None:
    api = API()
    
    # No routes declared
    
    start_response = mocker.Mock()
    res = api(build_environ("/a"), start_response)
    
    status_args, headers_arg = start_response.call_args[0]
    assert "404" in status_args 
    assert ("Content-type", "application/json") in headers_arg
    
    assert "error" in json.loads(next(iter(res)))

def test_wrong_method(mocker: MockerFixture) -> None:
    """
    Make sure that if a route is declared for method A and a request comes in with method B, the
    request will not wrongly match the the route
    """
    api = API()
    
    @api.get("/a")
    def a(req: Request):
        return "a"
    
    start_response = mocker.Mock()
    res = api(build_environ("/a", HTTPMethod.DELETE), start_response)
    
    status_args, headers_arg = start_response.call_args[0]
    assert "404" in status_args 
    assert ("Content-type", "application/json") in headers_arg
    
    assert "error" in json.loads(next(iter(res)))
    

def test_sub_route(mocker: MockerFixture) -> None:
    api = API()
    
    @api.get("/a")
    def a(req: Request):
        return "a"
    @api.get("/b")
    def b(req: Request):
        return "b"
    @api.get("/a/1")
    def a_1(req: Request):
        return "a_1"
    @api.get("/a/2")
    def a_2(req: Request):
        return "a_2"
    @api.get("/a/2/i")
    def a_2_i(req: Request):
        return "a_2_i"
    @api.get("/a/2/i/x")
    def a_2_i_x(req: Request):
        return "a_2_i_x"
    
    start_response = mocker.Mock()
    res = api(build_environ("/a/2/i"), start_response)
    
    assert start_response.call_args[0][0] == "200 OK" 
    
    assert next(iter(res)).decode("utf-8") == "a_2_i"
    
def test_path_variable(mocker: MockerFixture) -> None:
    """Test that path variables are correctly matched and accessed"""
    api = API()
    
    @api.get("/my/path/[var]/test")
    def a(req: Request):
        return req.params["var"]
    
    var = "chair"
    start_response = mocker.Mock()
    res = api(build_environ(f"/my/path/{var}/test"), start_response)
    
    assert start_response.call_args[0][0] == "200 OK" 
    
    assert next(iter(res)).decode("utf-8") == var
    
def test_path_edge_cases(mocker: MockerFixture) -> None:
    """
    Make sure path variables still behave properly even when placed at the start and end of
    a request 
    """
    api = API()
    
    @api.get("/[var]")
    def a(req: Request):
        return req.params["var"]
    
    var = "chair"
    
    start_response = mocker.Mock()
    res = api(build_environ(f"/{var}"), start_response)
    assert start_response.call_args[0][0] == "200 OK" 
    assert next(iter(res)).decode("utf-8") == var
    
    @api.get("/test/[var]")
    def b(req: Request):
        return req.params["var"]
    
    start_response = mocker.Mock()
    res = api(build_environ(f"/test/{var}"), start_response)
    assert start_response.call_args[0][0] == "200 OK" 
    assert next(iter(res)).decode("utf-8") == var
    

def test_query_params_matching(mocker: MockerFixture) -> None:
    """
    Test routing works correctly when query parameters are applied
    """
    api = API()
    
    @api.get("/")
    def a(req: Request):
        return req.query["q"]
    
    query_param = "apple"
    start_response = mocker.Mock()
    res = api(build_environ(f"/?q={query_param}"), start_response)
    assert start_response.call_args[0][0] == "200 OK" 
    assert next(iter(res)).decode("utf-8") == query_param
    