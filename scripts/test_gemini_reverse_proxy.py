#!/usr/bin/env python3
"""
Probe whether a Gemini-compatible base URL behaves like a reverse proxy to the
official Gemini API.

This script does not "prove" reverse proxying. It compares network reachability,
TLS handshake success, and Gemini endpoint behavior against the official API.
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


OFFICIAL_BASE_URL = "https://generativelanguage.googleapis.com"


def resolve_host(hostname: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {"hostname": hostname, "ok": False}
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        addresses = sorted({info[4][0] for info in infos})
        result.update({"ok": True, "addresses": addresses})
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def probe_tls(hostname: str, port: int, timeout: float) -> Dict[str, Any]:
    result: Dict[str, Any] = {"hostname": hostname, "port": port, "ok": False}
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
                cert = tls_sock.getpeercert()
                result.update(
                    {
                        "ok": True,
                        "tls_version": tls_sock.version(),
                        "cipher": tls_sock.cipher(),
                        "subject": cert.get("subject"),
                        "issuer": cert.get("issuer"),
                    }
                )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def http_get(url: str, timeout: float) -> Dict[str, Any]:
    result: Dict[str, Any] = {"url": url, "ok": False}
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "gemini-proxy-tester/1.0",
            "Accept": "application/json, text/plain, */*",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body_bytes = response.read()
            body_text = body_bytes.decode("utf-8", errors="replace")
            result.update(
                {
                    "ok": True,
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body_preview": body_text[:500],
                }
            )
            try:
                result["json"] = json.loads(body_text)
            except json.JSONDecodeError:
                pass
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        result.update(
            {
                "status": exc.code,
                "headers": dict(exc.headers),
                "body_preview": body_text[:500],
            }
        )
        try:
            result["json"] = json.loads(body_text)
        except json.JSONDecodeError:
            pass
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def build_models_url(base_url: str, api_key: str) -> str:
    return urllib.parse.urljoin(base_url.rstrip("/") + "/", f"v1beta/models?key={api_key}")


def summarize(proxy_result: Dict[str, Any], official_result: Dict[str, Any]) -> List[str]:
    summary: List[str] = []

    if proxy_result.get("error"):
        summary.append(
            f"proxy endpoint failed before a usable Gemini API response: {proxy_result['error']}"
        )
    elif proxy_result.get("status") in (400, 401, 403):
        summary.append(
            f"proxy endpoint returned HTTP {proxy_result['status']} on the Gemini models path"
        )
    else:
        summary.append(
            f"proxy endpoint returned HTTP {proxy_result.get('status', 'unknown')}"
        )

    if official_result.get("status") in (400, 401, 403):
        summary.append(
            f"official endpoint returned expected auth-related status HTTP {official_result['status']}"
        )
    elif official_result.get("error"):
        summary.append(f"official endpoint test failed: {official_result['error']}")
    else:
        summary.append(
            f"official endpoint returned HTTP {official_result.get('status', 'unknown')}"
        )

    proxy_json = proxy_result.get("json")
    official_json = official_result.get("json")
    if isinstance(proxy_json, dict) and isinstance(official_json, dict):
        proxy_keys = sorted(proxy_json.keys())
        official_keys = sorted(official_json.keys())
        summary.append(
            f"response JSON top-level keys: proxy={proxy_keys}, official={official_keys}"
        )

    return summary


def print_section(title: str, payload: Dict[str, Any]) -> None:
    print(f"== {title} ==")
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test whether a base URL behaves like a Gemini API reverse proxy."
    )
    parser.add_argument(
        "--base-url",
        default="https://gemini.my996.top",
        help="Candidate reverse proxy base URL.",
    )
    parser.add_argument(
        "--official-base-url",
        default=OFFICIAL_BASE_URL,
        help="Official Gemini API base URL used for comparison.",
    )
    parser.add_argument(
        "--api-key",
        default="invalid-test-key",
        help="API key used for endpoint probing. Invalid is fine for compatibility checks.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Timeout in seconds for DNS/TLS/HTTP probes.",
    )
    args = parser.parse_args()

    proxy_host = urllib.parse.urlparse(args.base_url).hostname
    official_host = urllib.parse.urlparse(args.official_base_url).hostname
    if not proxy_host or not official_host:
        print("Invalid base URL.", file=sys.stderr)
        return 2

    proxy_dns = resolve_host(proxy_host)
    official_dns = resolve_host(official_host)
    proxy_tls = probe_tls(proxy_host, 443, args.timeout)
    official_tls = probe_tls(official_host, 443, args.timeout)
    proxy_http = http_get(build_models_url(args.base_url, args.api_key), args.timeout)
    official_http = http_get(
        build_models_url(args.official_base_url, args.api_key), args.timeout
    )

    print_section("Proxy DNS", proxy_dns)
    print_section("Official DNS", official_dns)
    print_section("Proxy TLS", proxy_tls)
    print_section("Official TLS", official_tls)
    print_section("Proxy HTTP", proxy_http)
    print_section("Official HTTP", official_http)

    print("== Summary ==")
    for line in summarize(proxy_http, official_http):
        print(f"- {line}")

    if proxy_http.get("error"):
        print(
            "- diagnosis: the candidate URL is currently not acting like a usable Gemini HTTPS reverse proxy from this environment"
        )
        return 1

    if proxy_http.get("status") in (400, 401, 403) and official_http.get("status") in (
        400,
        401,
        403,
    ):
        print(
            "- diagnosis: the candidate URL is reachable and behaves similarly to the official Gemini auth/error path"
        )
        return 0

    print(
        "- diagnosis: the candidate URL is reachable, but its behavior does not clearly match the official Gemini API"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
