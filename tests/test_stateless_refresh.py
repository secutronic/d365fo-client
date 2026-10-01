"""Refresh must survive a server restart without a reconnect.

Client registrations and refresh tokens live only in process memory, so a new
provider instance stands in for a restarted server. No network is used: the
upstream (Entra) refresh call is patched.
"""

import base64
from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.auth.provider import RefreshToken, TokenError
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp import FastMCP
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyHttpUrl, AnyUrl
from starlette.testclient import TestClient

from d365fo_client.mcp.auth_server.auth.providers.azure import AzureProvider

BASE_URL = "http://localhost:8000"
SCOPES = ["User.Read", "email", "openid", "profile", "offline_access"]
CLIENT_ID = "claude-ai-dcr-client"
CLIENT_SECRET = "dcr-secret-issued-before-restart"
ENTRA_REFRESH_TOKEN = "entra-refresh-token-from-before-restart"
REFRESH = "authlib.integrations.httpx_client.AsyncOAuth2Client.refresh_token"


def make_provider() -> AzureProvider:
    """A fresh provider == a freshly started server (nothing persisted)."""
    return AzureProvider(
        client_id="upstream-client-id",
        client_secret="upstream-client-secret",
        tenant_id="test-tenant-id",
        base_url=BASE_URL,
        required_scopes=SCOPES,
        redirect_path="/auth/callback",
    )


@pytest.fixture
def restarted_provider() -> AzureProvider:
    return make_provider()


class TestProviderAfterRestart:
    async def test_get_client_unknown_id_returns_public_client(
        self, restarted_provider
    ):
        client = await restarted_provider.get_client(CLIENT_ID)

        assert client is not None
        assert client.client_id == CLIENT_ID
        assert client.client_secret is None
        assert client.token_endpoint_auth_method == "none"
        assert client.grant_types == ["authorization_code", "refresh_token"]
        assert client.response_types == ["code"]
        assert client.scope == " ".join(SCOPES)
        # Not stored
        assert CLIENT_ID not in restarted_provider._clients

    async def test_get_client_known_id_returns_registered_client(
        self, restarted_provider
    ):
        await restarted_provider.register_client(
            OAuthClientInformationFull(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uris=[AnyUrl("https://claude.ai/api/mcp/auth_callback")],
                token_endpoint_auth_method="client_secret_post",
            )
        )

        client = await restarted_provider.get_client(CLIENT_ID)

        assert client is restarted_provider._clients[CLIENT_ID]
        assert client.client_secret == CLIENT_SECRET

    async def test_load_refresh_token_unknown_returns_presented_token(
        self, restarted_provider
    ):
        client = await restarted_provider.get_client(CLIENT_ID)

        token = await restarted_provider.load_refresh_token(client, ENTRA_REFRESH_TOKEN)

        assert isinstance(token, RefreshToken)
        assert token.token == ENTRA_REFRESH_TOKEN
        assert token.client_id == CLIENT_ID
        assert token.scopes == SCOPES
        assert token.expires_at is None

    async def test_load_refresh_token_falls_back_to_required_scopes(
        self, restarted_provider
    ):
        client = OAuthClientInformationFull(
            client_id=CLIENT_ID,
            redirect_uris=[AnyUrl("http://localhost")],
            scope=None,
        )

        token = await restarted_provider.load_refresh_token(client, ENTRA_REFRESH_TOKEN)

        assert token is not None
        assert token.scopes == SCOPES

    async def test_load_refresh_token_known_returns_stored(self, restarted_provider):
        stored = RefreshToken(
            token="known-token",
            client_id="original-client",
            scopes=["openid"],
            expires_at=None,
        )
        restarted_provider._refresh_tokens["known-token"] = stored
        client = await restarted_provider.get_client(CLIENT_ID)

        token = await restarted_provider.load_refresh_token(client, "known-token")

        assert token is stored

    async def test_exchange_refused_upstream_is_invalid_grant(self, restarted_provider):
        client = await restarted_provider.get_client(CLIENT_ID)
        token = await restarted_provider.load_refresh_token(client, ENTRA_REFRESH_TOKEN)

        refused = AsyncMock(side_effect=Exception("AADSTS70008"))
        with patch(REFRESH, new=refused), pytest.raises(TokenError) as exc_info:
            await restarted_provider.exchange_refresh_token(client, token, token.scopes)

        assert exc_info.value.error == "invalid_grant"


def make_token_app(provider: AzureProvider):
    """The SDK's own /token route, wired as fastmcp_main wires it."""
    mcp = FastMCP(
        name="test",
        auth_server_provider=provider,
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(BASE_URL),
            client_registration_options=ClientRegistrationOptions(
                enabled=True, valid_scopes=SCOPES, default_scopes=SCOPES
            ),
            required_scopes=SCOPES,
            resource_server_url=AnyHttpUrl(BASE_URL),
        ),
    )
    return mcp.streamable_http_app()


UPSTREAM_RESPONSE = {
    "access_token": "new-entra-access-token",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": " ".join(SCOPES),
    "refresh_token": "rotated-entra-refresh-token",
}


class TestTokenEndpointAfterRestart:
    """POST /token through the SDK's handler and client authenticator."""

    @pytest.mark.parametrize("auth_style", ["post", "basic", "no_secret"])
    def test_refresh_succeeds_when_upstream_accepts(self, auth_style):
        provider = make_provider()
        app = make_token_app(provider)
        form = {
            "grant_type": "refresh_token",
            "refresh_token": ENTRA_REFRESH_TOKEN,
            "client_id": CLIENT_ID,
        }
        headers = {}
        if auth_style == "post":
            form["client_secret"] = CLIENT_SECRET
        elif auth_style == "basic":
            raw = f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
            headers["Authorization"] = "Basic " + base64.b64encode(raw).decode()

        upstream = AsyncMock(return_value=dict(UPSTREAM_RESPONSE))
        with patch(REFRESH, new=upstream), TestClient(app) as http:
            response = http.post("/token", data=form, headers=headers)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["access_token"] == "new-entra-access-token"
        assert body["refresh_token"] == "rotated-entra-refresh-token"
        upstream.assert_awaited_once()
        assert upstream.await_args.kwargs["refresh_token"] == ENTRA_REFRESH_TOKEN

    def test_refresh_refused_upstream_is_invalid_grant(self):
        provider = make_provider()
        app = make_token_app(provider)
        form = {
            "grant_type": "refresh_token",
            "refresh_token": "revoked-entra-refresh-token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

        upstream = AsyncMock(side_effect=Exception("invalid_grant: AADSTS70008"))
        with patch(REFRESH, new=upstream), TestClient(app) as http:
            response = http.post("/token", data=form)

        assert response.status_code == 400, response.text
        assert response.json()["error"] == "invalid_grant"

    def test_known_client_still_requires_its_secret(self):
        provider = make_provider()
        provider._clients[CLIENT_ID] = OAuthClientInformationFull(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uris=[AnyUrl("http://localhost")],
            grant_types=["authorization_code", "refresh_token"],
            token_endpoint_auth_method="client_secret_post",
        )
        app = make_token_app(provider)
        form = {
            "grant_type": "refresh_token",
            "refresh_token": ENTRA_REFRESH_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": "wrong-secret",
        }

        upstream = AsyncMock(return_value=dict(UPSTREAM_RESPONSE))
        with patch(REFRESH, new=upstream), TestClient(app) as http:
            response = http.post("/token", data=form)

        assert response.status_code == 401, response.text
        upstream.assert_not_awaited()
