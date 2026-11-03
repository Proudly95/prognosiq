from tests.test_assets import create_asset
from tests.test_auth import register_and_login
from tests.test_orgs import create_org, org_with_member


def create_work_order(client, tokens, org_id, asset_id, title="Replace seal"):
    """Create one work order as the given user. Fails loudly if setup breaks."""
    r = client.post(
        f"/orgs/{org_id}/work-orders",
        json={
            "asset_id": asset_id,
            "title": title,
            "description": "Seal leakage beyond threshold",
        },
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 201, f"setup failed: {r.status_code} {r.json()}"
    return r.json()


def test_outsider_cannot_list_work_orders(client):
    tokens, org_id = create_org(client)
    outsider = register_and_login(client, email="wo-outsider@test.com")

    response = client.get(
        f"/orgs/{org_id}/work-orders",
        headers={"Authorization": f"Bearer {outsider['access_token']}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not a member of this organization"


def test_agent_can_create_work_order(client):
    admin_tokens, agent_tokens, org_id = org_with_member(client, member_role="agent")
    asset = create_asset(client, admin_tokens, org_id)

    created = create_work_order(client, agent_tokens, org_id, asset["id"])
    assert created["organization_id"] == org_id
    assert created["asset_id"] == asset["id"]
    assert created["status"] == "open"  # model default — no status on create
    assert created["priority"] == "normal"
    assert created["source"] == "manual"
    assert created["created_by_id"] is not None


def test_create_against_other_orgs_asset_returns_404(client):
    admin_a, org_a = create_org(client, email="wo-admin-a@test.com")
    foreign_asset = create_asset(client, admin_a, org_a)

    admin_b, org_b = create_org(client, email="wo-admin-b@test.com")
    response = client.post(
        f"/orgs/{org_b}/work-orders",
        json={
            "asset_id": foreign_asset["id"],
            "title": "Sneaky",
            "description": "Must not attach to another org's asset",
        },
        headers={"Authorization": f"Bearer {admin_b['access_token']}"},
    )
    assert response.status_code == 404


def test_invalid_priority_returns_422(client):
    tokens, org_id = create_org(client)
    asset = create_asset(client, tokens, org_id)

    response = client.post(
        f"/orgs/{org_id}/work-orders",
        json={
            "asset_id": asset["id"],
            "title": "Weird",
            "description": "Bad priority",
            "priority": "asap",
        },
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 422
    # the 422 must be about priority specifically
    assert "priority" in [err["loc"][-1] for err in response.json()["detail"]]


def test_viewer_reads_but_cannot_write(client):
    admin_tokens, viewer_tokens, org_id = org_with_member(client, member_role="viewer")
    asset = create_asset(client, admin_tokens, org_id)
    create_work_order(client, admin_tokens, org_id, asset["id"])

    listed = client.get(
        f"/orgs/{org_id}/work-orders",
        headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    denied = client.post(
        f"/orgs/{org_id}/work-orders",
        json={"asset_id": asset["id"], "title": "Nope", "description": "x"},
        headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "Insufficient permissions"


def test_agent_can_update_but_not_delete(client):
    admin_tokens, agent_tokens, org_id = org_with_member(client, member_role="agent")
    asset = create_asset(client, admin_tokens, org_id)
    work_order = create_work_order(client, agent_tokens, org_id, asset["id"])

    patched = client.patch(
        f"/orgs/{org_id}/work-orders/{work_order['id']}",
        json={"status": "in_progress", "priority": "high"},
        headers={"Authorization": f"Bearer {agent_tokens['access_token']}"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "in_progress"
    assert patched.json()["priority"] == "high"

    denied = client.delete(
        f"/orgs/{org_id}/work-orders/{work_order['id']}",
        headers={"Authorization": f"Bearer {agent_tokens['access_token']}"},
    )
    assert denied.status_code == 403


def test_admin_can_delete_work_order(client):
    admin_tokens, member_tokens, org_id = org_with_member(client)
    asset = create_asset(client, admin_tokens, org_id)
    work_order = create_work_order(client, admin_tokens, org_id, asset["id"])

    deleted = client.delete(
        f"/orgs/{org_id}/work-orders/{work_order['id']}",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert deleted.status_code == 204

    gone = client.get(
        f"/orgs/{org_id}/work-orders/{work_order['id']}",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert gone.status_code == 404


def test_work_order_list_filters(client):
    tokens, org_id = create_org(client)
    asset_a = create_asset(client, tokens, org_id, name="Pump A")
    asset_b = create_asset(client, tokens, org_id, name="Pump B")

    wo1 = create_work_order(client, tokens, org_id, asset_a["id"], title="WO 1")
    create_work_order(client, tokens, org_id, asset_a["id"], title="WO 2")
    create_work_order(client, tokens, org_id, asset_b["id"], title="WO 3")

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    by_asset = client.get(f"/orgs/{org_id}/work-orders?asset_id={asset_a['id']}", headers=headers)
    assert by_asset.status_code == 200
    assert by_asset.json()["total"] == 2
    assert {item["title"] for item in by_asset.json()["items"]} == {"WO 1", "WO 2"}

    # move WO 1 to in_progress, then filter by status
    client.patch(
        f"/orgs/{org_id}/work-orders/{wo1['id']}",
        json={"status": "in_progress"},
        headers=headers,
    )
    by_status = client.get(f"/orgs/{org_id}/work-orders?status=in_progress", headers=headers)
    assert by_status.status_code == 200
    assert by_status.json()["total"] == 1
    assert by_status.json()["items"][0]["title"] == "WO 1"


def test_work_order_list_is_paginated(client):
    tokens, org_id = create_org(client)
    asset = create_asset(client, tokens, org_id)
    for i in range(3):
        create_work_order(client, tokens, org_id, asset["id"], title=f"WO {i}")

    page1 = client.get(
        f"/orgs/{org_id}/work-orders?page=1&size=2",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert page1.status_code == 200
    assert page1.json()["total"] == 3
    assert len(page1.json()["items"]) == 2

    page2 = client.get(
        f"/orgs/{org_id}/work-orders?page=2&size=2",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert page2.status_code == 200
    assert len(page2.json()["items"]) == 1
    assert page2.json()["page"] == 2


def test_org_scoping_on_get_one(client):
    # Admin B must not be able to read admin A's work order by id inside B's own org
    admin_a, org_a = create_org(client, email="wo-scope-a@test.com")
    asset_a = create_asset(client, admin_a, org_a)
    work_order = create_work_order(client, admin_a, org_a, asset_a["id"])

    admin_b, org_b = create_org(client, email="wo-scope-b@test.com")
    response = client.get(
        f"/orgs/{org_b}/work-orders/{work_order['id']}",
        headers={"Authorization": f"Bearer {admin_b['access_token']}"},
    )
    assert response.status_code == 404
