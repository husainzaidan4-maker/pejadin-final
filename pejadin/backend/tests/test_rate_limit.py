import unittest
import asyncio
from unittest.mock import patch
from starlette.requests import Request
from starlette.responses import Response

import main
from pejadin_docs.rate_limit import RateLimiter, request_rate_limit


class RateLimiterTests(unittest.TestCase):
    def test_rejects_requests_after_limit_until_window_expires(self):
        now = [100.0]
        limiter = RateLimiter(clock=lambda: now[0])

        self.assertTrue(limiter.allow("client", 2, 60))
        self.assertTrue(limiter.allow("client", 2, 60))
        self.assertFalse(limiter.allow("client", 2, 60))

        now[0] = 161.0
        self.assertTrue(limiter.allow("client", 2, 60))

    def test_tracks_clients_independently(self):
        limiter = RateLimiter(clock=lambda: 100.0)

        self.assertTrue(limiter.allow("client-a", 1, 60))
        self.assertTrue(limiter.allow("client-b", 1, 60))
        self.assertFalse(limiter.allow("client-a", 1, 60))

    def test_fails_closed_when_active_client_capacity_is_full(self):
        limiter = RateLimiter(max_clients=1, clock=lambda: 100.0)

        self.assertTrue(limiter.allow("client-a", 2, 60))
        self.assertFalse(limiter.allow("client-b", 2, 60))

    def test_login_aliases_share_same_rate_limit_bucket(self):
        self.assertEqual(request_rate_limit("POST", "/api/login"), ("login", 5))
        self.assertEqual(
            request_rate_limit("POST", "/api/v1/auth/login"),
            ("login", 5),
        )

    def test_complete_pdf_is_limited_but_other_pdf_types_are_not(self):
        self.assertEqual(
            request_rate_limit("GET", "/api/v1/st/42/pdf/lengkap"),
            ("full-pdf", 3),
        )
        self.assertIsNone(
            request_rate_limit("GET", "/api/v1/st/42/pdf/spd")
        )
        self.assertIsNone(
            request_rate_limit("POST", "/api/v1/st/42/pdf/lengkap")
        )

    def test_sensitive_request_returns_standard_429_response(self):
        limiter = RateLimiter(clock=lambda: 100.0)

        async def call_next(request):
            return Response("ok")

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/login",
                "headers": [],
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("192.0.2.10", 12345),
                "scheme": "http",
                "http_version": "1.1",
            }
        )

        async def make_requests():
            with patch.object(main, "rate_limiter", limiter):
                responses = [
                    await main.limit_sensitive_requests(request, call_next)
                    for _ in range(6)
                ]
            return responses

        responses = asyncio.run(make_requests())

        self.assertEqual([response.status_code for response in responses], [200] * 5 + [429])
        self.assertEqual(
            responses[-1].body,
            b'{"error": {"code": "RATE_LIMITED", "message": "Terlalu banyak permintaan. Coba lagi setelah beberapa saat."}}',
        )


if __name__ == "__main__":
    unittest.main()
