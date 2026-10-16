import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlsplit

import aiohttp


class SafeFetchError(ValueError):
    """A remote URL could not be safely retrieved."""


@dataclass
class FetchResult:
    status_code: int
    url: str
    body: bytes
    reason: str
    content_type: str
    redirects: list[tuple[str, int]]


def validate_http_url(url: str) -> str:
    """Validate URL syntax and reject non-web or non-public IP destinations."""
    if not isinstance(url, str) or not url or len(url) > 2048:
        raise SafeFetchError("The target URL is invalid.")

    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except ValueError:
        raise SafeFetchError("The target URL is invalid.") from None

    host = (parsed.hostname or "").rstrip(".").lower()
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or any(char.isspace() for char in url)
        or (parsed.scheme.lower() == "http" and port not in (None, 80))
        or (parsed.scheme.lower() == "https" and port not in (None, 443))
        or host in {"localhost", "metadata", "instance-data"}
        or host.endswith((".localhost", ".local", ".internal", ".test"))
    ):
        raise SafeFetchError("Only public HTTP and HTTPS URLs are allowed.")

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return url.strip()

    if not address.is_global:
        raise SafeFetchError("Only public HTTP and HTTPS URLs are allowed.")

    return url.strip()


def _validate_resolved_address(value: str) -> None:
    address_text = value.split("%", 1)[0]
    try:
        address = ipaddress.ip_address(address_text)
    except ValueError:
        raise OSError("The target host resolved to an invalid address.") from None

    if not address.is_global:
        raise OSError("The target host resolved to a non-public address.")


class PublicAddressResolver(aiohttp.abc.AbstractResolver):
    """Resolve a host once and pass only public addresses to aiohttp."""

    async def resolve(
        self,
        host: str,
        port: int = 0,
        family: int = socket.AF_INET,
    ) -> list[dict]:
        loop = asyncio.get_running_loop()
        try:
            results = await loop.getaddrinfo(
                host,
                port,
                family=family,
                type=socket.SOCK_STREAM,
            )
        except OSError:
            raise OSError("The target host could not be resolved.") from None

        resolved = []
        seen = set()
        for address_family, socktype, proto, _, sockaddr in results:
            address = sockaddr[0]
            _validate_resolved_address(address)
            key = (address_family, address)
            if key in seen:
                continue

            seen.add(key)
            resolved.append({
                "hostname": host,
                "host": address,
                "port": port,
                "family": address_family,
                "proto": proto,
                "flags": 0,
            })

        if not resolved:
            raise OSError("The target host could not be resolved.")

        return resolved

    async def close(self) -> None:
        return None


async def fetch_public_url(
    url: str,
    *,
    timeout: float,
    headers: Optional[dict[str, str]] = None,
    max_bytes: int = 2 * 1024 * 1024,
    max_redirects: int = 5,
) -> FetchResult:
    """Fetch a public URL while revalidating every redirect and DNS result."""
    current_url = validate_http_url(url)
    request_headers = {
        "User-Agent": "BrandShield-AI/1.0",
        "Accept": "*/*",
    }
    if headers:
        request_headers.update(headers)

    timeout_config = aiohttp.ClientTimeout(total=timeout)
    connector = aiohttp.TCPConnector(
        resolver=PublicAddressResolver(),
        use_dns_cache=False,
        family=socket.AF_UNSPEC,
        ssl=True,
    )
    redirects: list[tuple[str, int]] = []

    try:
        async with aiohttp.ClientSession(
            timeout=timeout_config,
            connector=connector,
            trust_env=False,
            auto_decompress=True,
        ) as session:
            for redirect_count in range(max_redirects + 1):
                current_url = validate_http_url(current_url)
                async with session.get(
                    current_url,
                    headers=request_headers,
                    allow_redirects=False,
                ) as response:
                    if response.status in {301, 302, 303, 307, 308}:
                        location = response.headers.get("Location")
                        if not location:
                            body = b""
                        else:
                            if redirect_count >= max_redirects:
                                raise SafeFetchError(
                                    "The target returned too many redirects."
                                )
                            redirects.append((str(response.url), response.status))
                            current_url = urljoin(str(response.url), location)
                            continue
                    else:
                        body = b""

                    content_length = response.headers.get("Content-Length")
                    if content_length:
                        try:
                            if int(content_length) > max_bytes:
                                raise SafeFetchError(
                                    "The target response is too large."
                                )
                        except ValueError:
                            pass

                    chunks = []
                    total_size = 0
                    async for chunk in response.content.iter_chunked(64 * 1024):
                        total_size += len(chunk)
                        if total_size > max_bytes:
                            raise SafeFetchError(
                                "The target response is too large."
                            )
                        chunks.append(chunk)
                    body = b"".join(chunks)

                    return FetchResult(
                        status_code=response.status,
                        url=str(response.url),
                        body=body,
                        reason=response.reason or "",
                        content_type=response.headers.get("Content-Type", ""),
                        redirects=redirects,
                    )

    except SafeFetchError:
        raise
    except asyncio.TimeoutError:
        raise SafeFetchError("The target did not respond in time.") from None
    except (aiohttp.ClientError, OSError, ValueError):
        raise SafeFetchError("Unable to retrieve the public target URL.") from None

    raise SafeFetchError("Unable to retrieve the public target URL.")
