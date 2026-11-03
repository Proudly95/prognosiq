from tests.test_assets import create_asset
from tests.test_auth import register_and_login
from tests.test_orgs import create_org, org_with_member


def create_record(client, tokens, org_id, asset_id, notes="Oil change"):
    """Create one maintenance record as the given user. Fails loudly if setup breaks."""
    r = client.post(
        f"/orgs/{org_id}/assets/{asset_id}/maintenance-records",
        json={"performed_at": "2026-10-28T10:00:00Z", "notes": notes},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 201, f"setup failed: {r.status_code} {r.json()}"
    return r.json()


def test_outsider_cannot_list_records(client):
    tokens, org_id = create_org(client)
    asset = create_asset(client, tokens, org_id)
    outsider = register_and_login(client, email="record-outsider@test.com")

    response = client.get(
        f"/orgs/{org_id}/assets/{asset['id']}/maintenance-records",
        headers={"Authorization": f"Bearer {outsider['access_token']}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not a member of this organization"


def test_admin_can_create_record(client):
    tokens, org_id = create_org(client)
    asset = create_asset(client, tokens, org_id)

    response = client.post(
        f"/orgs/{org_id}/assets/{asset['id']}/maintenance-records",
        json={"performed_at": "2026-10-28T10:00:00Z", "notes": "Bearing swap"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["asset_id"] == asset["id"]
    assert body["notes"] == "Bearing swap"
    assert body["performed_at"].startswith("2026-10-28T10:00:00")


def test_record_on_missing_asset_returns_404(client):
    tokens, org_id = create_org(client)

    response = client.post(
        f"/orgs/{org_id}/assets/999999/maintenance-records",
        json={"performed_at": "2026-10-28T10:00:00Z"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Asset not found"


def test_viewer_reads_but_cannot_write(client):
    admin_tokens, viewer_tokens, org_id = org_with_member(client, member_role="viewer")
    asset = create_asset(client, admin_tokens, org_id)
    create_record(client, admin_tokens, org_id, asset["id"])

    listed = client.get(
        f"/orgs/{org_id}/assets/{asset['id']}/maintenance-records",
        headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    denied = client.post(
        f"/orgs/{org_id}/assets/{asset['id']}/maintenance-records",
        json={"performed_at": "2026-10-28T11:00:00Z"},
        headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "Insufficient permissions"


def test_agent_can_create_but_not_delete(client):
    admin_tokens, agent_tokens, org_id = org_with_member(client, member_role="agent")
    asset = create_asset(client, admin_tokens, org_id)

    created = create_record(client, agent_tokens, org_id, asset["id"])

    denied = client.delete(
        f"/orgs/{org_id}/assets/{asset['id']}/maintenance-records/{created['id']}",
        headers={"Authorization": f"Bearer {agent_tokens['access_token']}"},
    )
    assert denied.status_code == 403


def test_agent_can_patch_record(client):
    admin_tokens, agent_tokens, org_id = org_with_member(client, member_role="agent")
    asset = create_asset(client, admin_tokens, org_id)
    record = create_record(client, agent_tokens, org_id, asset["id"])

    patched = client.patch(
        f"/orgs/{org_id}/assets/{asset['id']}/maintenance-records/{record['id']}",
        json={"notes": "Impeller replaced"},
        headers={"Authorization": f"Bearer {agent_tokens['access_token']}"},
    )
    assert patched.status_code == 200
    assert patched.json()["notes"] == "Impeller replaced"
    assert patched.json()["performed_at"].startswith("2026-10-28T10:00:00")


def test_admin_can_delete_record(client):
    admin_tokens, member_tokens, org_id = org_with_member(client)
    asset = create_asset(client, admin_tokens, org_id)
    record = create_record(client, admin_tokens, org_id, asset["id"])

    deleted = client.delete(
        f"/orgs/{org_id}/assets/{asset['id']}/maintenance-records/{record['id']}",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert deleted.status_code == 204

    gone = client.get(
        f"/orgs/{org_id}/assets/{asset['id']}/maintenance-records/{record['id']}",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert gone.status_code == 404


def test_record_list_is_paginated(client):
    tokens, org_id = create_org(client)
    asset = create_asset(client, tokens, org_id)
    for i in range(3):
        create_record(client, tokens, org_id, asset["id"], notes=f"Service {i}")

    page1 = client.get(
        f"/orgs/{org_id}/assets/{asset['id']}/maintenance-records?page=1&size=2",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert page1.status_code == 200
    assert page1.json()["total"] == 3
    assert len(page1.json()["items"]) == 2

    page2 = client.get(
        f"/orgs/{org_id}/assets/{asset['id']}/maintenance-records?page=2&size=2",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert page2.status_code == 200
    assert len(page2.json()["items"]) == 1
    assert page2.json()["page"] == 2


def test_org_scoping_on_get_one(client):
    # Admin B must not be able to read admin A's record by id inside B's own org
    admin_a, org_a = create_org(client, email="record-admin-a@test.com")
    asset_a = create_asset(client, admin_a, org_a)
    record = create_record(client, admin_a, org_a, asset_a["id"])

    admin_b, org_b = create_org(client, email="record-admin-b@test.com")
    asset_b = create_asset(client, admin_b, org_b)
    response = client.get(
        f"/orgs/{org_b}/assets/{asset_b['id']}/maintenance-records/{record['id']}",
        headers={"Authorization": f"Bearer {admin_b['access_token']}"},
    )
    assert response.status_code == 404
