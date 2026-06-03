#!/usr/bin/env python3
"""
_karnak_api.py
--------------
Karnak REST API client using Spring form-login session authentication.

The running Karnak image does not enable HTTP Basic on the REST API; every
/api/* request goes through the form-login filter.  This client POSTs
credentials to /login once, captures the resulting JSESSIONID cookie, and
reuses the session for all subsequent calls.
"""

import requests


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class KarnakError(Exception):
    """Base exception for all Karnak client errors."""


class AuthenticationError(KarnakError):
    """Raised when login fails or the session is rejected."""


class ApiError(KarnakError):
    """Raised when an API call returns an unexpected HTTP status."""

    def __init__(self, status_code: int, text: str, context: str = "") -> None:
        self.status_code = status_code
        self.text = text
        detail = f"{context} — HTTP {status_code}: {text}" if context else f"HTTP {status_code}: {text}"
        super().__init__(detail)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class KarnakClient:
    """
    Thin wrapper around the Karnak REST API.

    Authentication flow
    -------------------
    1. ``login()`` POSTs form credentials to ``/login``.
    2. Spring Security redirects (302) to ``/`` on success or to
       ``/login?error`` on failure.
    3. The session cookie (JSESSIONID) is retained by *requests.Session*
       and sent with every subsequent request automatically.

    ``_ensure_logged_in()`` calls ``login()`` lazily before the first API
    request so callers do not need to call ``login()`` explicitly.

    Parameters
    ----------
    base_url:  Karnak root URL (default ``http://localhost:8081``).
    username:  Admin username (default ``admin``).
    password:  Admin password (default ``karnak``).
    _session:  Inject a custom ``requests.Session`` (used by tests).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8081",
        username: str = "admin",
        password: str = "karnak",
        _session: requests.Session | None = None,
    ) -> None:
        self.base = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._session: requests.Session = _session if _session is not None else requests.Session()
        self._logged_in = False

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self) -> None:
        """POST form credentials to /login and establish a session cookie.

        Raises
        ------
        AuthenticationError
            If the server redirects to ``/login?error`` (bad credentials) or
            returns an unexpected status code.
        """
        r = self._session.post(
            f"{self.base}/login",
            data={"username": self._username, "password": self._password},
            allow_redirects=False,
        )
        if r.status_code not in (302, 303):
            raise AuthenticationError(
                f"Unexpected login response: HTTP {r.status_code}"
            )
        location = r.headers.get("Location", "")
        if "error" in location or location.rstrip("/").endswith("/login"):
            raise AuthenticationError(
                f"Login failed — invalid credentials for {self._username!r}"
            )
        self._logged_in = True

    def _ensure_logged_in(self) -> None:
        if not self._logged_in:
            self.login()

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        self._ensure_logged_in()
        return self._session.request(method, f"{self.base}{path}", **kwargs)

    @staticmethod
    def _check(r: requests.Response, expected: int, context: str) -> dict:
        """Assert *r* has *expected* status; return parsed JSON or ``{}``."""
        if r.status_code != expected:
            raise ApiError(r.status_code, r.text, context)
        try:
            return r.json()
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Connectivity check
    # ------------------------------------------------------------------

    def check_connectivity(self, timeout: int = 5) -> None:
        """Verify Karnak is reachable and credentials are accepted.

        Raises
        ------
        KarnakError
            On network failure or unexpected status from ``/api/forward-nodes``.
        AuthenticationError
            If login fails (propagated from ``login()``).
        """
        try:
            r = self._request("GET", "/api/forward-nodes", timeout=timeout)
        except requests.ConnectionError as exc:
            raise KarnakError(f"Cannot reach {self.base}") from exc
        if r.status_code not in (200, 204):
            raise KarnakError(f"Connectivity check failed: HTTP {r.status_code}")

    # ------------------------------------------------------------------
    # Profiles  (/api/profiles)
    # ------------------------------------------------------------------

    def upload_profile(self, file_path: str) -> dict:
        """Upload a YAML de-identification profile.  Returns ``{"id": N, "name": "..."}``."""
        with open(file_path, "rb") as fh:
            r = self._request("POST", "/api/profiles", files={"file": fh})
        return self._check(r, 201, f"Upload profile {file_path!r}")

    def list_profiles(self) -> list:
        """Return all profiles (empty list when Karnak returns 204)."""
        r = self._request("GET", "/api/profiles")
        if r.status_code == 204:
            return []
        return self._check(r, 200, "List profiles")

    def get_profile(self, profile_id: int) -> dict:
        """Return full profile details."""
        r = self._request("GET", f"/api/profiles/{profile_id}")
        return self._check(r, 200, f"Get profile {profile_id}")

    def delete_profile(self, profile_id: int) -> None:
        """Delete a profile by ID."""
        r = self._request("DELETE", f"/api/profiles/{profile_id}")
        self._check(r, 204, f"Delete profile {profile_id}")

    # ------------------------------------------------------------------
    # Projects  (/api/projects)
    # ------------------------------------------------------------------

    def create_project(self, name: str, profile_id: int | None = None) -> dict:
        """Create a project, optionally linked to a profile."""
        payload: dict = {"name": name}
        if profile_id is not None:
            payload["profileId"] = profile_id
        r = self._request("POST", "/api/projects", json=payload)
        return self._check(r, 201, f"Create project {name!r}")

    def list_projects(self) -> list:
        r = self._request("GET", "/api/projects")
        if r.status_code == 204:
            return []
        return self._check(r, 200, "List projects")

    def get_project(self, project_id: int) -> dict:
        r = self._request("GET", f"/api/projects/{project_id}")
        return self._check(r, 200, f"Get project {project_id}")

    def delete_project(self, project_id: int) -> None:
        r = self._request("DELETE", f"/api/projects/{project_id}")
        self._check(r, 204, f"Delete project {project_id}")

    # ------------------------------------------------------------------
    # Project secrets  (/api/projects/{id}/secrets)
    # ------------------------------------------------------------------

    def generate_secret(self, project_id: int, hex_key: str | None = None) -> dict:
        """Add or auto-generate an HMAC secret for *project_id*.

        Pass *hex_key* (32 hex chars) to import a known key; omit it to let
        Karnak generate one.  The full key is only returned in this response.
        """
        payload: dict = {}
        if hex_key is not None:
            payload["hexKey"] = hex_key
        r = self._request("POST", f"/api/projects/{project_id}/secrets", json=payload)
        return self._check(r, 201, f"Generate secret for project {project_id}")

    # ------------------------------------------------------------------
    # Forward nodes  (/api/forward-nodes)
    # ------------------------------------------------------------------

    def create_forward_node(self, aet: str, description: str = "") -> dict:
        r = self._request(
            "POST",
            "/api/forward-nodes",
            json={"fwdAeTitle": aet, "fwdDescription": description},
        )
        return self._check(r, 201, f"Create forward node {aet!r}")

    def list_forward_nodes(self) -> list:
        r = self._request("GET", "/api/forward-nodes")
        if r.status_code == 204:
            return []
        return self._check(r, 200, "List forward nodes")

    def get_forward_node(self, node_id: int) -> dict:
        r = self._request("GET", f"/api/forward-nodes/{node_id}")
        return self._check(r, 200, f"Get forward node {node_id}")

    def delete_forward_node(self, node_id: int) -> None:
        r = self._request("DELETE", f"/api/forward-nodes/{node_id}")
        self._check(r, 204, f"Delete forward node {node_id}")

    # ------------------------------------------------------------------
    # Destinations  (/api/forward-nodes/{id}/destinations)
    # ------------------------------------------------------------------

    def create_destination(self, node_id: int, payload: dict) -> dict:
        """Add a DICOM or STOW-RS destination to *node_id*.

        *payload* must include at least ``destinationType`` (``"dicom"`` or
        ``"stow"``) and the required fields for each type (see API.md §4).
        """
        r = self._request(
            "POST",
            f"/api/forward-nodes/{node_id}/destinations",
            json=payload,
        )
        return self._check(r, 201, f"Create destination for node {node_id}")

    def list_destinations(self, node_id: int) -> list:
        r = self._request("GET", f"/api/forward-nodes/{node_id}/destinations")
        if r.status_code == 204:
            return []
        return self._check(r, 200, f"List destinations for node {node_id}")

    def delete_destination(self, node_id: int, dest_id: int) -> None:
        r = self._request(
            "DELETE",
            f"/api/forward-nodes/{node_id}/destinations/{dest_id}",
        )
        self._check(r, 204, f"Delete destination {dest_id} from node {node_id}")

    # ------------------------------------------------------------------
    # Source nodes  (/api/forward-nodes/{id}/source-nodes)
    # ------------------------------------------------------------------

    def add_source_node(self, node_id: int, payload: dict) -> dict:
        """Add a source-node filter to *node_id*.

        Minimum *payload*: ``{"aeTitle": "MODALITY1"}``.
        """
        r = self._request(
            "POST",
            f"/api/forward-nodes/{node_id}/source-nodes",
            json=payload,
        )
        return self._check(r, 201, f"Add source node to node {node_id}")

    def list_source_nodes(self, node_id: int) -> list:
        r = self._request("GET", f"/api/forward-nodes/{node_id}/source-nodes")
        if r.status_code == 204:
            return []
        return self._check(r, 200, f"List source nodes for node {node_id}")

    def delete_source_node(self, node_id: int, source_node_id: int) -> None:
        r = self._request(
            "DELETE",
            f"/api/forward-nodes/{node_id}/source-nodes/{source_node_id}",
        )
        self._check(r, 204, f"Delete source node {source_node_id} from node {node_id}")
