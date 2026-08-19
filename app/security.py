import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeRedirectTargetError(ValueError):
    pass


def assert_safe_redirect_target(url: str) -> None:
    """Blocks obviously internal/private targets so the shortener can't be used
    as an open redirector into internal infrastructure."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if hostname is None:
        raise UnsafeRedirectTargetError("URL has no hostname")

    if hostname.lower() == "localhost":
        raise UnsafeRedirectTargetError("Redirect target cannot be localhost")

    try:
        resolved_ips = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except socket.gaierror:
        # Can't resolve at creation time — let it through; the redirect
        # endpoint will fail naturally when someone actually visits it.
        return

    for ip_str in resolved_ips:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise UnsafeRedirectTargetError("Redirect target resolves to a private/internal address")
