"""Fail-closed URL validation and DNS-pinned HTTPS. No redirect following."""

import concurrent.futures
import http.client
import ipaddress
import os
import re
import socket
import ssl
import threading
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from app.discovery.errors import DiscoveryError
from app.discovery.sources import SourcePolicy

MAX_PAGE_BYTES = 256_000
_dns_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="discovery-dns")
_dns_slots = threading.BoundedSemaphore(2)


def validate_url(value: str, policy: SourcePolicy, *, listing: bool = True) -> str:
    if not isinstance(value, str) or len(value) > 2048 or re.search(r"[\x00-\x20\x7f\\]", value):
        raise DiscoveryError("invalid_url", "Invalid external URL")
    try:
        parts = urlsplit(value)
        host = parts.hostname
        if (
            parts.scheme != "https"
            or not host
            or parts.port not in (None, 443)
            or parts.username
            or parts.password
        ):
            raise ValueError
        if host not in policy.allowed_domains or not re.fullmatch(r"[a-z0-9.-]+", host):
            raise ValueError
        # Literal IPs are never approved source domains, even if an injected policy names them.
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError
        if host == "localhost" or host.endswith(".localhost"):
            raise ValueError
        if listing and not re.fullmatch(r"/careers/[0-9]+/?", parts.path):
            raise ValueError
        if not listing and parts.path != "/robots.txt":
            raise ValueError
        query = []
        for key, val in parse_qsl(parts.query, keep_blank_values=True, max_num_fields=30):
            if key.lower().startswith("utm_") or key.lower() in {"gclid", "fbclid"}:
                continue
            if key not in {"jobId", "job_id", "gh_jid"} or not re.fullmatch(
                r"[a-zA-Z0-9_-]{1,128}", val
            ):
                raise ValueError
            query.append((key, val))
        return urlunsplit(
            ("https", host, parts.path.rstrip("/") or "/", urlencode(sorted(query)), "")
        )
    except (ValueError, UnicodeError):
        raise DiscoveryError("invalid_url", "URL is outside approved HTTPS source policy") from None


def resolve_public(host: str, deadline: float) -> list[str]:
    if not _dns_slots.acquire(blocking=False):
        raise DiscoveryError("dns_busy", "DNS resolver capacity is exhausted")
    future = _dns_pool.submit(socket.getaddrinfo, host, 443, type=socket.SOCK_STREAM)
    future.add_done_callback(lambda _: _dns_slots.release())
    try:
        answers = future.result(timeout=max(0.01, min(3, deadline - time.monotonic())))
    except (TimeoutError, OSError):
        raise DiscoveryError("dns_failure", "Source DNS resolution failed") from None
    addresses = list(dict.fromkeys(str(answer[4][0]) for answer in answers))
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise DiscoveryError("unsafe_dns", "Source resolved to a non-public address")
    return addresses


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, address: str, timeout: float):
        super().__init__(host, timeout=timeout, context=ssl.create_default_context())
        self.address = address
        self.tls_context = ssl.create_default_context()

    def connect(self) -> None:
        # Connect only to the validated numeric address; TLS still validates the original hostname.
        connection = socket.create_connection((self.address, 443), self.timeout)
        try:
            self.sock = self.tls_context.wrap_socket(connection, server_hostname=self.host)
        except BaseException:
            connection.close()
            raise


class DetailFetcher:
    def __init__(self, *, resolver=resolve_public, connection_factory=PinnedHTTPSConnection):
        self.resolver = resolver
        self.connection_factory = connection_factory

    def _get(self, url: str, policy: SourcePolicy, deadline: float, *, listing: bool) -> str:
        url = validate_url(url, policy, listing=listing)
        # Do not bypass an environment's required proxy. A vetted, pinning proxy transport is future work.
        if any(
            os.environ.get(name)
            for name in ("HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy")
        ):
            raise DiscoveryError(
                "proxy_transport_unavailable",
                "DNS-pinned source fetching requires an approved direct-egress deployment",
            )
        parts = urlsplit(url)
        addresses = self.resolver(parts.hostname, deadline)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise DiscoveryError("execution_timeout", "Discovery execution budget exhausted")
        connection = self.connection_factory(parts.hostname, addresses[0], min(5, remaining))

        def abort():
            if connection.sock:
                try:
                    connection.sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            connection.close()

        budget = threading.Timer(remaining, abort)
        budget.daemon = True
        budget.start()
        try:
            connection.request(
                "GET",
                parts.path + (f"?{parts.query}" if parts.query else ""),
                headers={
                    "User-Agent": "SkillSphereDiscovery/1.0",
                    "Accept-Encoding": "identity",
                    "Accept": "text/html,text/plain",
                },
            )
            response = connection.getresponse()
            if response.status != 200:  # Includes redirects: no hop is followed.
                raise DiscoveryError(
                    "source_access_restricted", "Source returned a redirect or unsuccessful status"
                )
            if response.getheader("Content-Encoding", "identity") != "identity":
                raise DiscoveryError(
                    "unsupported_encoding", "Compressed source content is not accepted"
                )
            expected = "text/html" if listing else "text/plain"
            if expected not in response.getheader("Content-Type", "").lower():
                raise DiscoveryError("unsupported_content", "Unexpected source content type")
            content = bytearray()
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise DiscoveryError(
                        "execution_timeout", "Discovery execution budget exhausted"
                    )
                if connection.sock:
                    connection.sock.settimeout(min(5, remaining))
                block = response.read1(min(16_384, MAX_PAGE_BYTES + 1 - len(content)))
                if not block:
                    break
                content.extend(block)
                if len(content) > MAX_PAGE_BYTES:
                    raise DiscoveryError(
                        "content_too_large", "Source content exceeds extraction limits"
                    )
            return content.decode("utf-8", errors="strict")
        except (OSError, UnicodeError, http.client.HTTPException):
            raise DiscoveryError("source_fetch_failed", "Source detail retrieval failed") from None
        finally:
            budget.cancel()
            connection.close()

    def fetch(self, url: str, policy: SourcePolicy, deadline: float) -> str:
        canonical = validate_url(url, policy)
        robots_url = f"https://{urlsplit(canonical).hostname}/robots.txt"
        robots = RobotFileParser()
        robots.parse(self._get(robots_url, policy, deadline, listing=False).splitlines())
        # Conservative throttle: do not exceed crawl delay/rate guidance in this initial workflow.
        delay = robots.crawl_delay("SkillSphereDiscovery")
        rate = robots.request_rate("SkillSphereDiscovery")
        if (
            not robots.can_fetch("SkillSphereDiscovery", canonical)
            or (delay and float(delay) > 0)
            or rate
        ):
            raise DiscoveryError(
                "robots_restricted", "Robots policy disallows this initial discovery workflow"
            )
        return self._get(canonical, policy, deadline, listing=True)
