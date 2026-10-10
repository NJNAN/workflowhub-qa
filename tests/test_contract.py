import uuid
import pytest
from conftest import authenticate, ticket


def test_http_health_and_browser_entry(client, service):
    assert client.get("health").json()["database"] == "ok"
    response = client.get(service[0] + "/")
    assert response.status_code == 200 and "WorkFlowHub" in response.text


@pytest.mark.parametrize("path", ["tickets", "tickets/stats", "assets", "users", "auth/me"])
def test_protected_routes_over_real_http(client, path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize(
    "username,expected", [("requester", 403), ("engineer", 403), ("admin", 201)]
)
def test_asset_role_matrix(client, service, username, expected):
    authenticate(client, service, username)
    assert (
        client.post(
            "assets", json={"code": "QA-" + uuid.uuid4().hex[:12], "name": "QA asset"}
        ).status_code
        == expected
    )


def test_end_to_end_workflow_and_history(client, service):
    authenticate(client, service)
    t = ticket(client)
    path = f"tickets/{t['id']}"
    authenticate(client, service, "admin")
    engineer = next(u for u in client.get("users").json() if u["username"] == "engineer")
    assert (
        client.post(
            path + "/assign", json={"version": 1, "assignee_id": engineer["id"]}
        ).status_code
        == 200
    )
    authenticate(client, service, "engineer")
    assert (
        client.post(path + "/notes", json={"version": 2, "text": "Replaced cable"}).status_code
        == 201
    )
    assert (
        client.post(path + "/transition", json={"version": 3, "target": "RESOLVED"}).status_code
        == 200
    )
    authenticate(client, service)
    assert (
        client.post(path + "/transition", json={"version": 4, "target": "CLOSED"}).status_code
        == 200
    )
    assert client.patch(path, json={"version": 5, "title": "Rejected"}).status_code == 409
    assert (
        client.post(path + "/transition", json={"version": 5, "target": "OPEN"}).json()[
            "assignee_id"
        ]
        is None
    )
    history = client.get(path + "/history").json()
    assert [h["action"] for h in history] == [
        "created",
        "assigned",
        "note_added",
        "state_changed",
        "state_changed",
        "state_changed",
    ]


def test_cross_user_read_write_history_and_stats(client, service):
    authenticate(client, service)
    t = ticket(client)
    authenticate(client, service, "other")
    assert client.get(f"tickets/{t['id']}").status_code == 403
    assert client.get(f"tickets/{t['id']}/history").status_code == 403
    assert (
        client.patch(f"tickets/{t['id']}", json={"version": 1, "title": "Intrusion"}).status_code
        == 403
    )
    assert client.get("tickets").json()["total"] == 0
    assert client.get("tickets/stats").json()["by_status"] == {}


@pytest.mark.parametrize(
    "body",
    [
        {"title": "", "description": "Valid"},
        {"title": "x" * 121, "description": "Valid"},
        {"title": "Title", "description": "Valid", "priority": 4},
        {"title": "Title", "description": "Valid", "status": "CLOSED"},
    ],
)
def test_equivalence_and_boundary_inputs(client, service, body):
    authenticate(client, service)
    assert client.post("tickets", json=body).status_code == 422


def test_duplicate_and_stale_requests(client, service):
    authenticate(client, service)
    body = {"title": "Idempotent", "description": "HTTP retry"}
    headers = {"Idempotency-Key": uuid.uuid4().hex}
    a = client.post("tickets", json=body, headers=headers)
    b = client.post("tickets", json=body, headers=headers)
    assert a.status_code == 201 and b.status_code == 200 and a.json()["id"] == b.json()["id"]
    path = f"tickets/{a.json()['id']}"
    assert client.patch(path, json={"version": 1, "title": "Version two"}).status_code == 200
    assert client.patch(path, json={"version": 1, "title": "Lost update"}).status_code == 409


def test_logout_and_openapi(client, service):
    authenticate(client, service)
    assert client.post("auth/logout").status_code == 204
    assert client.get("auth/me").status_code == 401
    spec = client.get(service[0] + "/openapi.json").json()
    assert "/api/tickets/{ticket_id}/transition" in spec["paths"]
