import asyncio
import io
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from bson import ObjectId
from fastapi import HTTPException, UploadFile

from app.config import settings
from app.routes.brands import (
    get_readable_brand,
    get_writable_brand,
    upload_brand_logo,
)
from app.routes.threats import get_authorized_threat
from app.services.auth_service import (
    decode_access_token,
    is_legacy_default_account,
    require_current_user,
    verify_google_id_token,
)
from app.routes.access_control import (
    is_brand_child_visible,
    readable_brand_filter,
    readable_brand_children_filter,
)
from app.utils.safe_http import (
    SafeFetchError,
    _validate_resolved_address,
    fetch_public_url,
    validate_http_url,
)


class MemoryBrands:
    def __init__(self, documents):
        self.documents = documents

    async def find_one(self, query):
        return next(
            (document for document in self.documents if matches(document, query)),
            None,
        )

    def find(self, query, projection=None):
        return MemoryCursor([
            document
            for document in self.documents
            if matches(document, query)
        ])


class MemoryCursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, length):
        return self.documents[:length]


class MemoryThreats:
    def __init__(self, documents):
        self.documents = documents
        self.last_query = None

    async def find_one(self, query):
        self.last_query = query
        return next(
            (document for document in self.documents if matches(document, query)),
            None,
        )


class MemoryDatabase:
    def __init__(self, documents, threats=None):
        self.brands = MemoryBrands(documents)
        self.threats = MemoryThreats(threats or [])


def matches(document, query):
    for key, expected in query.items():
        if key == "$or":
            if not any(matches(document, branch) for branch in expected):
                return False
            continue
        if key == "$and":
            if not all(matches(document, branch) for branch in expected):
                return False
            continue

        if isinstance(expected, dict):
            if "$exists" in expected and (key in document) != expected["$exists"]:
                return False
            if "$eq" in expected and document.get(key) != expected["$eq"]:
                return False
            if "$in" in expected and document.get(key) not in expected["$in"]:
                return False
            continue

        if document.get(key) != expected:
            return False

    return True


class TestBrandOwnershipControls(unittest.IsolatedAsyncioTestCase):
    async def test_user_cannot_read_another_users_private_brand(self):
        brand_id = ObjectId()
        db = MemoryDatabase([{
            "_id": brand_id,
            "owner_id": "user-a",
            "is_demo": False,
            "is_shared": False,
        }])

        with self.assertRaises(HTTPException) as raised:
            await get_readable_brand(db, str(brand_id), "user-b")

        self.assertEqual(raised.exception.status_code, 404)

    async def test_threat_lookup_is_owner_scoped_in_the_mongo_query(self):
        brand_id = ObjectId()
        threat_id = ObjectId()
        db = MemoryDatabase(
            [{
                "_id": brand_id,
                "owner_id": "user-a",
                "is_demo": False,
                "is_shared": False,
            }],
            [{
                "_id": threat_id,
                "brand_id": str(brand_id),
                "owner_id": "user-a",
            }],
        )

        threat = await get_authorized_threat(
            db,
            str(threat_id),
            "user-a",
        )
        self.assertEqual(threat["_id"], threat_id)
        self.assertIn("$and", db.threats.last_query)
        self.assertFalse(matches(
            db.threats.documents[0],
            {
                "$and": [
                    {"_id": threat_id},
                    readable_brand_children_filter([], "user-b"),
                ]
            },
        ))

        with self.assertRaises(HTTPException) as raised:
            await get_authorized_threat(db, str(threat_id), "user-b")
        self.assertEqual(raised.exception.status_code, 404)

    async def test_ownerless_legacy_brand_is_not_public(self):
        brand_id = ObjectId()
        db = MemoryDatabase([{
            "_id": brand_id,
            "is_demo": True,
            "is_shared": True,
        }])

        with self.assertRaises(HTTPException) as raised:
            await get_readable_brand(db, str(brand_id), "user-a")

        self.assertEqual(raised.exception.status_code, 404)

    async def test_explicit_shared_demo_is_readable_but_not_writable(self):
        brand_id = ObjectId()
        db = MemoryDatabase([{
            "_id": brand_id,
            "owner_id": None,
            "is_demo": True,
            "is_shared": True,
        }])

        brand = await get_readable_brand(db, str(brand_id), "user-a")
        self.assertEqual(brand["_id"], brand_id)

        with self.assertRaises(HTTPException) as raised:
            await get_writable_brand(db, str(brand_id), "user-a")

        self.assertEqual(raised.exception.status_code, 403)

    async def test_user_cannot_update_or_delete_another_users_brand(self):
        brand_id = ObjectId()
        db = MemoryDatabase([{
            "_id": brand_id,
            "owner_id": "user-a",
            "is_demo": False,
            "is_shared": False,
        }])

        for operation in ("update", "delete"):
            with self.subTest(operation=operation):
                with self.assertRaises(HTTPException) as raised:
                    await get_writable_brand(db, str(brand_id), "user-b")
                self.assertEqual(raised.exception.status_code, 404)

    def test_private_brand_children_are_owner_scoped(self):
        brand_id = ObjectId()
        brand = {
            "_id": brand_id,
            "owner_id": "user-a",
            "is_demo": False,
            "is_shared": False,
        }
        record_filter = readable_brand_children_filter([brand], "user-a")

        self.assertTrue(matches({
            "brand_id": str(brand_id),
            "owner_id": "user-a",
        }, record_filter))
        self.assertTrue(matches({
            "brand_id": str(brand_id),
        }, record_filter))
        self.assertFalse(matches({
            "brand_id": str(brand_id),
            "owner_id": "user-b",
        }, record_filter))

    def test_shared_demo_children_must_be_explicitly_shared(self):
        brand_id = ObjectId()
        brand = {
            "_id": brand_id,
            "owner_id": None,
            "is_demo": True,
            "is_shared": True,
        }
        record_filter = readable_brand_children_filter([brand], "user-a")

        self.assertTrue(matches({
            "brand_id": str(brand_id),
            "owner_id": None,
            "is_demo": True,
            "is_shared": True,
        }, record_filter))
        self.assertFalse(matches({
            "brand_id": str(brand_id),
            "owner_id": None,
        }, record_filter))
        self.assertFalse(matches({
            "brand_id": str(brand_id),
            "is_demo": True,
            "is_shared": True,
        }, record_filter))

    def test_record_visibility_rejects_cross_owner_and_legacy_demo_data(self):
        private_brand = {"_id": ObjectId(), "owner_id": "user-a"}
        self.assertFalse(is_brand_child_visible(
            private_brand,
            "user-a",
            {"owner_id": "user-b"},
        ))

        shared_brand = {
            "_id": ObjectId(),
            "owner_id": None,
            "is_demo": True,
            "is_shared": True,
        }
        self.assertFalse(is_brand_child_visible(
            shared_brand,
            "user-a",
            {"owner_id": None},
        ))

    def test_private_child_queries_exclude_other_users_across_resources(self):
        brand_id = ObjectId()
        brand = {
            "_id": brand_id,
            "owner_id": "user-a",
            "is_demo": False,
            "is_shared": False,
        }
        query = readable_brand_children_filter([brand], "user-a")

        for collection in (
            "threats",
            "alerts",
            "campaigns",
            "investigations",
            "evidence",
            "official_assets",
            "instagram_analyses",
            "verification_history",
            "reports",
        ):
            with self.subTest(collection=collection):
                self.assertTrue(matches({
                    "brand_id": str(brand_id),
                    "owner_id": "user-a",
                }, query))
                self.assertFalse(matches({
                    "brand_id": str(brand_id),
                    "owner_id": "user-b",
                }, query))

    def test_same_brand_name_is_visible_only_to_its_owner_or_as_shared_demo(self):
        query = readable_brand_filter("user-a")
        records = [
            {"owner_id": "user-a", "name": "Example"},
            {"owner_id": "user-b", "name": "Example"},
            {
                "owner_id": None,
                "is_demo": True,
                "is_shared": True,
                "name": "Example",
            },
        ]

        visible = [record for record in records if matches(record, query)]
        self.assertEqual(
            [record.get("owner_id") for record in visible],
            ["user-a", None],
        )


class TestAuthenticationValidation(unittest.IsolatedAsyncioTestCase):
    async def test_missing_current_user_is_unauthorized(self):
        with self.assertRaises(HTTPException) as raised:
            await require_current_user(None)

        self.assertEqual(raised.exception.status_code, 401)

    def test_expired_and_subjectless_jwts_are_rejected(self):
        secret = "isolated-test-secret-not-for-use-outside-tests"
        now = datetime.now(timezone.utc)

        expired = jwt.encode(
            {
                "sub": "user-a",
                "iat": now - timedelta(hours=2),
                "exp": now - timedelta(hours=1),
            },
            secret,
            algorithm="HS256",
        )
        subjectless = jwt.encode(
            {
                "iat": now,
                "exp": now + timedelta(hours=1),
            },
            secret,
            algorithm="HS256",
        )

        with patch.object(settings, "JWT_SECRET_KEY", secret):
            self.assertIsNone(decode_access_token(expired))
            self.assertIsNone(decode_access_token(subjectless))

    async def test_google_token_audience_is_checked(self):
        class FakeResponse:
            status = 200

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def json(self, **kwargs):
                return {
                    "aud": "another-client",
                    "iss": "https://accounts.google.com",
                    "sub": "google-user",
                    "email": "user@example.org",
                    "email_verified": True,
                }

        class FakeClientSession:
            def __init__(self, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            def get(self, *args, **kwargs):
                return FakeResponse()

        with patch.object(settings, "GOOGLE_CLIENT_ID", "expected-client"):
            with patch(
                "app.services.auth_service.aiohttp.ClientSession",
                FakeClientSession,
            ):
                with self.assertRaises(HTTPException) as raised:
                    await verify_google_id_token("non-empty-test-token")

        self.assertEqual(raised.exception.status_code, 401)

    async def test_google_token_requires_verified_email_and_valid_issuer(self):
        class FakeResponse:
            status = 200

            def __init__(self, payload):
                self.payload = payload

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def json(self, **kwargs):
                return self.payload

        class FakeClientSession:
            payload = {}

            def __init__(self, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            def get(self, *args, **kwargs):
                return FakeResponse(self.payload)

        with patch.object(settings, "GOOGLE_CLIENT_ID", "expected-client"):
            with patch(
                "app.services.auth_service.aiohttp.ClientSession",
                FakeClientSession,
            ):
                for invalid_claims in (
                    {"iss": "untrusted-issuer", "email_verified": True},
                    {"iss": "https://accounts.google.com", "email_verified": False},
                ):
                    FakeClientSession.payload = {
                        "aud": "expected-client",
                        "sub": "google-user",
                        "email": "user@example.org",
                        **invalid_claims,
                    }
                    with self.subTest(claims=invalid_claims):
                        with self.assertRaises(HTTPException) as raised:
                            await verify_google_id_token("non-empty-test-token")
                        self.assertEqual(raised.exception.status_code, 401)

                FakeClientSession.payload = {
                    "aud": "expected-client",
                    "iss": "https://accounts.google.com",
                    "sub": "google-user",
                    "email": "user@example.org",
                    "email_verified": True,
                }
                verified = await verify_google_id_token("non-empty-test-token")

        self.assertEqual(verified["sub"], "google-user")
        self.assertEqual(verified["email"], "user@example.org")


class TestPublicLogoUpload(unittest.IsolatedAsyncioTestCase):
    async def test_svg_upload_is_rejected(self):
        upload = UploadFile(
            filename="logo.svg",
            file=io.BytesIO(b"<svg></svg>"),
        )

        with self.assertRaises(HTTPException) as raised:
            await upload_brand_logo(upload, {"id": "user-a"})

        self.assertEqual(raised.exception.status_code, 400)


class TestSafeRemoteFetching(unittest.TestCase):
    def test_only_public_http_and_https_urls_are_accepted(self):
        self.assertEqual(
            validate_http_url("https://example.org/logo.png"),
            "https://example.org/logo.png",
        )

        for url in (
            "file:///etc/passwd",
            "http://localhost/",
            "http://127.0.0.1/",
            "http://169.254.169.254/",
            "http://[::1]/",
            "http://user@example.org/",
            "https://example.org:8443/",
        ):
            with self.subTest(url=url):
                with self.assertRaises(SafeFetchError):
                    validate_http_url(url)

    def test_dns_results_must_be_public(self):
        _validate_resolved_address("8.8.8.8")
        for address in ("10.0.0.1", "127.0.0.1", "169.254.10.20", "::1"):
            with self.subTest(address=address):
                with self.assertRaises(OSError):
                    _validate_resolved_address(address)

    def test_redirect_to_private_host_is_rejected(self):
        class RedirectResponse:
            status = 302
            reason = "Found"
            url = "https://example.org/start"
            headers = {"Location": "http://127.0.0.1/private"}

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

        class FakeSession:
            calls = 0

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            def get(self, *args, **kwargs):
                self.calls += 1
                return RedirectResponse()

        fake_session = FakeSession()
        with patch(
            "app.utils.safe_http.aiohttp.ClientSession",
            return_value=fake_session,
        ):
            with self.assertRaises(SafeFetchError):
                asyncio.run(fetch_public_url("https://example.org/start", timeout=1))

        self.assertEqual(fake_session.calls, 1)


class TestLegacyAccountBlocking(unittest.TestCase):
    def test_legacy_default_account_is_blocked_case_insensitively(self):
        self.assertTrue(is_legacy_default_account("ANALYST@BRANDSHIELD.AI"))
        self.assertFalse(is_legacy_default_account("user@example.org"))
        self.assertFalse(is_legacy_default_account(None))


if __name__ == "__main__":
    unittest.main()
