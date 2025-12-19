from ipaddress import IPv4Address, ip_address
from typing import Literal

from terminus.execution_pipeline import MiddlewareFn, MiddlewareFnRes
from terminus.types import HTTPError, Request


def create_restrictor(whitelist: list[str] | None = None,
                blacklist: list[str] | None = None,
                protocol: Literal["ipv4"] | Literal["ipv6"] | None = None) -> MiddlewareFn:
    """Create a middleware function based a blacklist, whitelist and or protocol restriction"""
    if whitelist is not None and blacklist is not None:
        raise HTTPError("Cannot have an IP blacklist and whitelist simultaneously")
    
    def restrictor(req: Request) -> MiddlewareFnRes:
        ip = req.headers.remote_address
        
        if protocol is not None:
            is_ipv4 = isinstance(ip_address(ip), IPv4Address)
            if (is_ipv4 and (protocol != "ipv4")) or (not is_ipv4 and (protocol == "ipv4")):
                return {
                    "error": f"Unsupported IP protocol. Only {protocol.upper()} is permitted"
                }, 403
        
        if whitelist is not None and ip not in whitelist:
            return {"error": f"IP '{ip}' is not whitelisted"}, 403
        
        if blacklist is not None and ip in blacklist:
            return {"error": f"IP '{ip}' is blacklisted"}, 403
        
        return None
        

    return restrictor
