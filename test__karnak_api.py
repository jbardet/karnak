"""
test__karnak_api.py
-------------------
Unit tests for _karnak_api.KarnakClient.

All HTTP calls are intercepted via the injected *_session* parameter so no
real Karnak instance is required.
"""

import json
import pytest
from unittest.mock import MagicMock, call, patch

from _karnak_api import (
    ApiError,
    AuthenticationError,
    KarnakClient,
    KarnakError,
)

BASE = "http://localhost:8081"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resp(status_code=200, body=None, text=None, headers=None):
    """Build a mock requests.Response."""
    r = MagicMock()
    r.status_code = status_code
    r.headers = headers or {}
    if body is not None:
        r.text = json.dumps(body)
        r.json.return_value = body
    else:
        r.text = text or ""
        r.json.side_effect = ValueError("no JSON")
    return r


def _logged_in_client(session=None):
    """Return a KarnakClient whose _logged_in flag is already set (login skipped)."""
    if session is None:
        session = MagicMock()
    client = KarnakClient(BASE, "admin", "karnak", _session=session)
    client._logged_in = True
    return client, session


def _fresh_client(session=None):
    """Return a KarnakClient that has NOT logged in yet."""
    if session is None:
        session = MagicMock()
    client = KarnakClient(BASE, "admin", "karnak", _session=session)
    return client, session


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------

class TestLogin:
    def test_success_302_to_root(self):
        client, sess = _fresh_client()
        sess.post.return_value = _resp(302, headers={"Location": "/"})

        client.login()

        assert client._logged_in
        sess.post.assert_called_once_with(
            f"{BASE}/login",
            data={"username": "admin", "password": "karnak"},
            allow_redirects=False,
        )

    def test_success_303_to_root(self):
        client, sess = _fresh_client()
        sess.post.return_value = _resp(303, headers={"Location": "/"})
        client.login()
        assert client._logged_in

    def test_failure_redirect_to_login_error(self):
        client, sess = _fresh_client()
        sess.post.return_value = _resp(302, headers={"Location": "/login?error"})

        with pytest.raises(AuthenticationError, match="Login failed"):
            client.login()
        assert not client._logged_in

    def test_failure_redirect_back_to_login(self):
        client, sess = _fresh_client()
        # Some Spring configs redirect to /login (no ?error)
        sess.post.return_value = _resp(302, headers={"Location": "/login"})

        with pytest.raises(AuthenticationError):
            client.login()

    def test_failure_unexpected_status_200(self):
        client, sess = _fresh_client()
        sess.post.return_value = _resp(200)

        with pytest.raises(AuthenticationError, match="Unexpected login response"):
            client.login()

    def test_failure_unexpected_status_401(self):
        client, sess = _fresh_client()
        sess.post.return_value = _resp(401)

        with pytest.raises(AuthenticationError, match="Unexpected login response"):
            client.login()

    def test_custom_credentials_sent(self):
        sess = MagicMock()
        client = KarnakClient(BASE, "operator", "s3cr3t", _session=sess)
        sess.post.return_value = _resp(302, headers={"Location": "/"})

        client.login()

        sess.post.assert_called_once_with(
            f"{BASE}/login",
            data={"username": "operator", "password": "s3cr3t"},
            allow_redirects=False,
        )


# ---------------------------------------------------------------------------
# Auto-login (_ensure_logged_in)
# ---------------------------------------------------------------------------

class TestAutoLogin:
    def test_login_triggered_before_first_request(self):
        client, sess = _fresh_client()
        # Sequence: POST /login → GET /api/forward-nodes
        sess.post.return_value = _resp(302, headers={"Location": "/"})
        sess.request.return_value = _resp(200, body=[])

        client.list_forward_nodes()

        sess.post.assert_called_once()  # login
        sess.request.assert_called_once()  # the API call

    def test_login_not_repeated_on_second_call(self):
        client, sess = _fresh_client()
        sess.post.return_value = _resp(302, headers={"Location": "/"})
        sess.request.return_value = _resp(200, body=[])

        client.list_forward_nodes()
        client.list_forward_nodes()

        assert sess.post.call_count == 1  # login called only once
        assert sess.request.call_count == 2

    def test_login_failure_propagates_from_api_call(self):
        client, sess = _fresh_client()
        sess.post.return_value = _resp(302, headers={"Location": "/login?error"})

        with pytest.raises(AuthenticationError):
            client.list_forward_nodes()


# ---------------------------------------------------------------------------
# check_connectivity()
# ---------------------------------------------------------------------------

class TestCheckConnectivity:
    def test_success_200(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(200, body=[])
        client.check_connectivity()  # no exception

    def test_success_204(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)
        client.check_connectivity()

    def test_connection_error(self):
        import requests as req_lib
        client, sess = _logged_in_client()
        sess.request.side_effect = req_lib.ConnectionError("refused")

        with pytest.raises(KarnakError, match="Cannot reach"):
            client.check_connectivity()

    def test_bad_status(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(500)

        with pytest.raises(KarnakError, match="Connectivity check failed"):
            client.check_connectivity()

    def test_timeout_passed_to_request(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(200, body=[])

        client.check_connectivity(timeout=10)

        _, kwargs = sess.request.call_args
        assert kwargs.get("timeout") == 10


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

class TestProfiles:
    def test_upload_profile_success(self, tmp_path):
        yml = tmp_path / "profile.yml"
        yml.write_text("name: Test\n")
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(201, body={"id": 7, "name": "Test"})

        result = client.upload_profile(str(yml))

        assert result == {"id": 7, "name": "Test"}
        args, kwargs = sess.request.call_args
        assert args[0] == "POST"
        assert args[1] == f"{BASE}/api/profiles"
        assert "files" in kwargs

    def test_upload_profile_bad_yaml(self, tmp_path):
        yml = tmp_path / "bad.yml"
        yml.write_text("!!invalid\n")
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(400, text="Unreadable file")

        with pytest.raises(ApiError) as exc_info:
            client.upload_profile(str(yml))
        assert exc_info.value.status_code == 400

    def test_upload_profile_validation_error(self, tmp_path):
        yml = tmp_path / "invalid.yml"
        yml.write_text("name: Bad\n")
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(
            422, body={"errors": ["Unknown codename: foo"]}
        )

        with pytest.raises(ApiError) as exc_info:
            client.upload_profile(str(yml))
        assert exc_info.value.status_code == 422

    def test_list_profiles_200(self):
        profiles = [{"id": 1, "name": "Default"}, {"id": 2, "name": "Custom"}]
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(200, body=profiles)

        result = client.list_profiles()

        assert result == profiles

    def test_list_profiles_204_empty(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)

        assert client.list_profiles() == []

    def test_get_profile(self):
        profile = {"id": 3, "name": "My Profile", "version": "1.0"}
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(200, body=profile)

        result = client.get_profile(3)

        assert result == profile
        assert sess.request.call_args[0][1] == f"{BASE}/api/profiles/3"

    def test_get_profile_not_found(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(404, text="Not found")

        with pytest.raises(ApiError) as exc_info:
            client.get_profile(999)
        assert exc_info.value.status_code == 404

    def test_delete_profile(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)

        client.delete_profile(3)

        args, _ = sess.request.call_args
        assert args[0] == "DELETE"
        assert args[1] == f"{BASE}/api/profiles/3"


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

class TestProjects:
    def test_create_project_without_profile(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(201, body={"id": 5, "name": "Trial"})

        result = client.create_project("Trial")

        assert result["id"] == 5
        _, kwargs = sess.request.call_args
        assert kwargs["json"] == {"name": "Trial"}

    def test_create_project_with_profile(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(201, body={"id": 6, "name": "Trial"})

        result = client.create_project("Trial", profile_id=3)

        _, kwargs = sess.request.call_args
        assert kwargs["json"] == {"name": "Trial", "profileId": 3}

    def test_create_project_missing_name(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(400, text="Name is required")

        with pytest.raises(ApiError) as exc_info:
            client.create_project("")
        assert exc_info.value.status_code == 400

    def test_create_project_profile_not_found(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(404, text="Profile not found")

        with pytest.raises(ApiError) as exc_info:
            client.create_project("Trial", profile_id=999)
        assert exc_info.value.status_code == 404

    def test_list_projects_200(self):
        projects = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(200, body=projects)

        assert client.list_projects() == projects

    def test_list_projects_204(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)

        assert client.list_projects() == []

    def test_get_project(self):
        project = {"id": 1, "name": "A"}
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(200, body=project)

        assert client.get_project(1) == project

    def test_get_project_not_found(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(404)

        with pytest.raises(ApiError) as exc_info:
            client.get_project(999)
        assert exc_info.value.status_code == 404

    def test_delete_project(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)

        client.delete_project(1)

        args, _ = sess.request.call_args
        assert args[0] == "DELETE"
        assert "projects/1" in args[1]


# ---------------------------------------------------------------------------
# Project secrets
# ---------------------------------------------------------------------------

class TestProjectSecrets:
    SECRET_BODY = {
        "projectId": 1,
        "hexKey": "deadbeefdeadbeefdeadbeefdeadbeef",
        "displayKey": "deadbeef-dead-beef-dead-beefdeadbeef",
        "active": True,
    }

    def test_generate_secret_auto(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(201, body=self.SECRET_BODY)

        result = client.generate_secret(1)

        assert result["hexKey"] == "deadbeefdeadbeefdeadbeefdeadbeef"
        _, kwargs = sess.request.call_args
        assert kwargs["json"] == {}

    def test_generate_secret_with_known_key(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(201, body=self.SECRET_BODY)

        client.generate_secret(1, hex_key="deadbeefdeadbeefdeadbeefdeadbeef")

        _, kwargs = sess.request.call_args
        assert kwargs["json"] == {"hexKey": "deadbeefdeadbeefdeadbeefdeadbeef"}

    def test_generate_secret_invalid_key(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(400, text="Invalid hex key")

        with pytest.raises(ApiError) as exc_info:
            client.generate_secret(1, hex_key="tooshort")
        assert exc_info.value.status_code == 400

    def test_generate_secret_project_not_found(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(404)

        with pytest.raises(ApiError) as exc_info:
            client.generate_secret(999)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Forward nodes
# ---------------------------------------------------------------------------

class TestForwardNodes:
    def test_create_forward_node(self):
        node = {"id": 2, "fwdAeTitle": "GW1", "fwdDescription": "Main"}
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(201, body=node)

        result = client.create_forward_node("GW1", "Main")

        assert result["id"] == 2
        _, kwargs = sess.request.call_args
        assert kwargs["json"] == {"fwdAeTitle": "GW1", "fwdDescription": "Main"}

    def test_create_forward_node_default_description(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(201, body={"id": 3, "fwdAeTitle": "GW2"})

        client.create_forward_node("GW2")

        _, kwargs = sess.request.call_args
        assert kwargs["json"]["fwdDescription"] == ""

    def test_create_forward_node_conflict(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(409, text="AET already exists")

        with pytest.raises(ApiError) as exc_info:
            client.create_forward_node("GW1")
        assert exc_info.value.status_code == 409

    def test_create_forward_node_missing_aet(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(400, text="fwdAeTitle is required")

        with pytest.raises(ApiError) as exc_info:
            client.create_forward_node("")
        assert exc_info.value.status_code == 400

    def test_list_forward_nodes_200(self):
        nodes = [{"id": 1, "fwdAeTitle": "GW1"}, {"id": 2, "fwdAeTitle": "GW2"}]
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(200, body=nodes)

        assert client.list_forward_nodes() == nodes

    def test_list_forward_nodes_204(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)

        assert client.list_forward_nodes() == []

    def test_get_forward_node(self):
        node = {"id": 1, "fwdAeTitle": "GW1"}
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(200, body=node)

        result = client.get_forward_node(1)

        assert result == node
        assert sess.request.call_args[0][1] == f"{BASE}/api/forward-nodes/1"

    def test_get_forward_node_not_found(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(404)

        with pytest.raises(ApiError) as exc_info:
            client.get_forward_node(999)
        assert exc_info.value.status_code == 404

    def test_delete_forward_node(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)

        client.delete_forward_node(1)

        args, _ = sess.request.call_args
        assert args[0] == "DELETE"
        assert args[1] == f"{BASE}/api/forward-nodes/1"

    def test_delete_forward_node_not_found(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(404)

        with pytest.raises(ApiError) as exc_info:
            client.delete_forward_node(999)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Destinations
# ---------------------------------------------------------------------------

class TestDestinations:
    DICOM_PAYLOAD = {
        "destinationType": "dicom",
        "aeTitle": "ARCHIVE",
        "hostname": "192.168.1.20",
        "port": 11112,
        "activate": True,
    }
    STOW_PAYLOAD = {
        "destinationType": "stow",
        "url": "https://dicomweb.example.com/studies",
        "activate": True,
    }

    def test_create_dicom_destination(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(201, body={"id": 10, **self.DICOM_PAYLOAD})

        result = client.create_destination(1, self.DICOM_PAYLOAD)

        assert result["id"] == 10
        args, kwargs = sess.request.call_args
        assert args[0] == "POST"
        assert args[1] == f"{BASE}/api/forward-nodes/1/destinations"
        assert kwargs["json"]["destinationType"] == "dicom"

    def test_create_stow_destination(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(201, body={"id": 11, **self.STOW_PAYLOAD})

        result = client.create_destination(1, self.STOW_PAYLOAD)

        assert result["id"] == 11
        _, kwargs = sess.request.call_args
        assert kwargs["json"]["destinationType"] == "stow"

    def test_create_destination_with_deid(self):
        client, sess = _logged_in_client()
        payload = {
            **self.DICOM_PAYLOAD,
            "desidentification": True,
            "deIdentificationProject": {"id": 5},
        }
        sess.request.return_value = _resp(201, body={"id": 12, **payload})

        result = client.create_destination(1, payload)

        assert result["id"] == 12
        _, kwargs = sess.request.call_args
        assert kwargs["json"]["desidentification"] is True
        assert kwargs["json"]["deIdentificationProject"] == {"id": 5}

    def test_create_destination_node_not_found(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(404)

        with pytest.raises(ApiError) as exc_info:
            client.create_destination(999, self.DICOM_PAYLOAD)
        assert exc_info.value.status_code == 404

    def test_list_destinations_200(self):
        dests = [{"id": 1, "destinationType": "dicom"}]
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(200, body=dests)

        assert client.list_destinations(1) == dests

    def test_list_destinations_204(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)

        assert client.list_destinations(1) == []

    def test_delete_destination(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)

        client.delete_destination(node_id=1, dest_id=10)

        args, _ = sess.request.call_args
        assert args[0] == "DELETE"
        assert args[1] == f"{BASE}/api/forward-nodes/1/destinations/10"


# ---------------------------------------------------------------------------
# Source nodes
# ---------------------------------------------------------------------------

class TestSourceNodes:
    def test_add_source_node(self):
        payload = {"aeTitle": "PACS_SRC", "hostname": "192.168.1.10", "checkHostname": True}
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(201, body={"id": 5, **payload})

        result = client.add_source_node(1, payload)

        assert result["id"] == 5
        args, kwargs = sess.request.call_args
        assert args[0] == "POST"
        assert args[1] == f"{BASE}/api/forward-nodes/1/source-nodes"
        assert kwargs["json"]["aeTitle"] == "PACS_SRC"

    def test_list_source_nodes_200(self):
        nodes = [{"id": 5, "aeTitle": "PACS_SRC"}]
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(200, body=nodes)

        assert client.list_source_nodes(1) == nodes

    def test_list_source_nodes_204(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)

        assert client.list_source_nodes(1) == []

    def test_delete_source_node(self):
        client, sess = _logged_in_client()
        sess.request.return_value = _resp(204)

        client.delete_source_node(node_id=1, source_node_id=5)

        args, _ = sess.request.call_args
        assert args[0] == "DELETE"
        assert args[1] == f"{BASE}/api/forward-nodes/1/source-nodes/5"


# ---------------------------------------------------------------------------
# ApiError / error message formatting
# ---------------------------------------------------------------------------

class TestApiError:
    def test_message_with_context(self):
        err = ApiError(404, "Not found", "Get profile 99")
        assert "404" in str(err)
        assert "Get profile 99" in str(err)
        assert "Not found" in str(err)

    def test_message_without_context(self):
        err = ApiError(500, "Internal error")
        assert "500" in str(err)
        assert "Internal error" in str(err)

    def test_attributes(self):
        err = ApiError(409, "Conflict body", "Create node")
        assert err.status_code == 409
        assert err.text == "Conflict body"


# ---------------------------------------------------------------------------
# URL construction
# ---------------------------------------------------------------------------

class TestUrlConstruction:
    def test_trailing_slash_stripped_from_base(self):
        sess = MagicMock()
        client = KarnakClient("http://localhost:8081/", "admin", "karnak", _session=sess)
        client._logged_in = True
        sess.request.return_value = _resp(200, body=[])

        client.list_forward_nodes()

        assert sess.request.call_args[0][1] == "http://localhost:8081/api/forward-nodes"

    def test_custom_base_url(self):
        sess = MagicMock()
        client = KarnakClient("http://karnak.hospital.local:9090", "admin", "karnak", _session=sess)
        client._logged_in = True
        sess.request.return_value = _resp(204)

        client.list_forward_nodes()

        assert sess.request.call_args[0][1].startswith("http://karnak.hospital.local:9090")
