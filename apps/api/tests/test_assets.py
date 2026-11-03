from tests.test_auth import register_and_login
from tests.test_orgs import create_org, org_with_member


def create_asset(client, tokens, org_id, name="Pump A"):
    """Create one asset as the given user. Fails loudly if setup breaks."""
    r = client.post(
        f"/orgs/{org_id}/assets",
        json={"name": name, "asset_type": "pump"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 201, f"setup failed: {r.status_code} {r.json()}"
    return r.json()


def test_outsider_cannot_list_assets(client):
    tokens, org_id = create_org(client)
    outsider = register_and_login(client, email="asset-outsider@test.com")

    response = client.get(
        f"/orgs/{org_id}/assets",
        headers={"Authorization": f"Bearer {outsider['access_token']}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not a member of this organization"


def test_admin_can_create_asset(client):
    tokens, org_id = create_org(client)

    response = client.post(
        f"/orgs/{org_id}/assets",
        json={"name": "Pump A", "asset_type": "pump"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Pump A"
    assert body["asset_type"] == "pump"
    assert body["organization_id"] == org_id
    assert body["is_active"] is True


def test_invalid_asset_type_returns_422(client):
    tokens, org_id = create_org(client)

    response = client.post(
        f"/orgs/{org_id}/assets",
        json={"name": "Weird", "asset_type": "hoverboard"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 422
    # the 422 must be about asset_type specifically
    assert "asset_type" in [err["loc"][-1] for err in response.json()["detail"]]


def test_viewer_reads_but_cannot_write(client):
    admin_tokens, viewer_tokens, org_id = org_with_member(client, member_role="viewer")
    create_asset(client, admin_tokens, org_id)

    listed = client.get(
        f"/orgs/{org_id}/assets",
        headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    denied = client.post(
        f"/orgs/{org_id}/assets",
        json={"name": "Nope", "asset_type": "motor"},
        headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "Insufficient permissions"


def test_agent_can_create_but_not_delete(client):
    admin_tokens, agent_tokens, org_id = org_with_member(client, member_role="agent")

    created = client.post(
        f"/orgs/{org_id}/assets",
        json={"name": "Motor B", "asset_type": "motor"},
        headers={"Authorization": f"Bearer {agent_tokens['access_token']}"},
    )
    assert created.status_code == 201

    denied = client.delete(
        f"/orgs/{org_id}/assets/{created.json()['id']}",
        headers={"Authorization": f"Bearer {agent_tokens['access_token']}"},
    )
    assert denied.status_code == 403


def test_admin_can_delete_asset(client):
    admin_tokens, member_tokens, org_id = org_with_member(client)
    asset = create_asset(client, admin_tokens, org_id)

    deleted = client.delete(
        f"/orgs/{org_id}/assets/{asset['id']}",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert deleted.status_code == 204

    gone = client.get(
        f"/orgs/{org_id}/assets/{asset['id']}",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert gone.status_code == 404


def test_asset_list_is_paginated(client):
    tokens, org_id = create_org(client)
    for i in range(3):
        create_asset(client, tokens, org_id, name=f"Pump {i}")

    page1 = client.get(
        f"/orgs/{org_id}/assets?page=1&size=2",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert page1.status_code == 200
    assert page1.json()["total"] == 3
    assert len(page1.json()["items"]) == 2

    page2 = client.get(
        f"/orgs/{org_id}/assets?page=2&size=2",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert page2.status_code == 200
    assert len(page2.json()["items"]) == 1
    assert page2.json()["page"] == 2


def test_org_scoping_on_get_one(client):
    # Admin B must not be able to read admin A's asset by id inside B's own org
    admin_a, org_a = create_org(client, email="asset-admin-a@test.com")
    asset = create_asset(client, admin_a, org_a)

    admin_b, org_b = create_org(client, email="asset-admin-b@test.com")
    response = client.get(
        f"/orgs/{org_b}/assets/{asset['id']}",
        headers={"Authorization": f"Bearer {admin_b['access_token']}"},
    )
    assert response.status_code == 404
