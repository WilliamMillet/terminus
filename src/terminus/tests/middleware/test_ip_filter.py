import json
from typing import Literal

import pytest
from pytest_mock import MockerFixture

from terminus.api import API
from terminus.middleware.ip_filter import create_restrictor
from terminus.tests.utils import build_environ
from terminus.types import HTTPError, HTTPMethod, Request

IPV4_IP = "192.168.1.1"
IPV6_IP = "2001:db8:130f:0000:0000:09c0:876a:130b"
    
def test_simple_whitelist(mocker: MockerFixture) -> None:
    api = API()
    
    restrictor1 = create_restrictor(whitelist=["127.0.0.1"])
    @api.get("/1", pre=[restrictor1])
    def fn1(req: Request):
        return "Body"
    
    start_response1 = mocker.Mock()
    environ1 = build_environ("/1", HTTPMethod.GET)
    res1 = api(environ1, start_response1)
    
    status_args1, _ = start_response1.call_args[0]
    assert "200" in status_args1 

    body1 = next(iter(res1)).decode("utf-8")
    assert body1 == "Body"
    
    restrictor2 = create_restrictor(whitelist=["127.0.0.2"])
    @api.get("/2", pre=[restrictor2])
    def fn2(req: Request):
        return "Body"

    start_response2 = mocker.Mock()
    environ2 = build_environ("/2", HTTPMethod.GET)
    res2 = api(environ2, start_response2)
    
    body2 = next(iter(res2))
    
    status_args, _ = start_response2.call_args[0]
    assert "403" in status_args
    assert "error" in json.loads(body2)
    
def test_simple_blacklist(mocker: MockerFixture) -> None:
    api = API()
    
    restrictor1 = create_restrictor(blacklist=["127.0.0.2"])
    @api.get("/1", pre=[restrictor1])
    def fn1(req: Request):
        return "Body"
    
    start_response1 = mocker.Mock()
    environ1 = build_environ("/1", HTTPMethod.GET)
    res1 = api(environ1, start_response1)
    
    status_args1, _ = start_response1.call_args[0]
    assert "200" in status_args1 

    body1 = next(iter(res1)).decode("utf-8")
    assert body1 == "Body"
    
    restrictor2 = create_restrictor(blacklist=["127.0.0.1"])
    @api.get("/2", pre=[restrictor2])
    def fn2(req: Request):
        return "Body"

    start_response2 = mocker.Mock()
    environ2 = build_environ("/2", HTTPMethod.GET)
    res2 = api(environ2, start_response2)
    
    body2 = next(iter(res2))
    
    status_args, _ = start_response2.call_args[0]
    assert "403" in status_args
    assert "error" in json.loads(body2)

PROTOCOL_PARAMS = [
    ("ipv4", IPV4_IP, IPV6_IP),
    ("ipv6", IPV6_IP, IPV4_IP)
]

@pytest.mark.parametrize("protocol, example, counter_example", PROTOCOL_PARAMS)
def test_protocol_filter(mocker: MockerFixture, protocol: Literal["ipv4"] | Literal["ipv6"],
                         example: str, counter_example: str) -> None:
    api = API()
    
    restrictor1 = create_restrictor(protocol=protocol)
    @api.get("/1", pre=[restrictor1])
    def fn1(req: Request):
        return "Body"
    
    start_response1 = mocker.Mock()
    environ1 = build_environ("/1", HTTPMethod.GET, custom_fields={"REMOTE_ADDR": example})
    res1 = api(environ1, start_response1)
    
    status_args1, _ = start_response1.call_args[0]
    assert "200" in status_args1 

    body1 = next(iter(res1)).decode("utf-8")
    assert body1 == "Body"

    start_response2 = mocker.Mock()
    environ2 = build_environ("/1", HTTPMethod.GET, custom_fields={"REMOTE_ADDR": counter_example})
    res2 = api(environ2, start_response2)
    
    body2 = next(iter(res2))
    
    status_args, _ = start_response2.call_args[0]
    assert "403" in status_args
    assert "error" in json.loads(body2)
    
def test_whitelist_and_blacklist_together(mocker: MockerFixture) -> None:
    """Whitelist and blacklist should not exist simultaneously"""
    
    with pytest.raises(HTTPError):
        api = API()
        
        restrictor1 = create_restrictor(whitelist=[IPV4_IP], blacklist=[IPV6_IP])
        @api.get("/", pre=[restrictor1])
        def fn1(req: Request):
            return "Body"
        
        start_response1 = mocker.Mock()
        environ1 = build_environ("/1", HTTPMethod.GET)
        res = api(environ1, start_response1)
        
        status_args1, _ = start_response1.call_args[0]
        assert "200" in status_args1
        
        body = next(iter(res))
        assert "error" in json.loads(body)
        