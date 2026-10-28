from tests.test_auth import register_and_login


def create_org(client, email="owner@test.com"):
    tokens = register_and_login(client, email)
    r = client.post(
        "/orgs",
        json={"name": "Acme"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    return tokens, r.json()["id"]


def org_with_member(client, member_role="agent"):
    """Org + admin + one added member. Fails loudly if setup breaks."""
    admin_tokens, org_id = create_org(client, email="org-admin@test.com")
    member_tokens = register_and_login(client, email="org-member@test.com")
    add = client.post(
        f"/orgs/{org_id}/members",
        json={"email": "org-member@test.com", "role": member_role},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert add.status_code == 201, f"setup failed: {add.status_code} {add.json()}"
    return admin_tokens, member_tokens, org_id


def test_create_org_creator_is_admin(client):
    tokens, org_id = create_org(client)
    members = client.get(
        f"/orgs/{org_id}/members",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert members.status_code == 200
    assert members.json()[0]["role"] == "admin"


def test_org_isolation_outsider_gets_403(client):
    # ARRANGE — two separate humans:
    owner_tokens, org_id = create_org(client, email="owner-a@test.com")  # user A, owns the org
    outsider_tokens = register_and_login(client, email="outsider-b@test.com")  # user B, nobody

    # ACT — B asks for A's org:
    response = client.get(
        f"/orgs/{org_id}/members",
        headers={"Authorization": f"Bearer {outsider_tokens['access_token']}"},
    )

    # ASSERT — the wall:
    assert response.status_code == 403
    assert response.json()["detail"] == "Not a member of this organization"


def test_list_my_orgs_contains_created_org(client):
    tokens, org_id = create_org(client)
    response = client.get("/orgs", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    assert org_id in [org["id"] for org in response.json()]


def test_admin_can_add_member(client):
    admin_tokens, org_id = create_org(client)
    register_and_login(client, email="invitee@test.com")  # invitee must EXIST as a user

    response = client.post(
        f"/orgs/{org_id}/members",
        json={"email": "invitee@test.com", "role": "agent"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert response.status_code == 201
    assert response.json()["role"] == "agent"


def test_new_member_sees_org(client):
    admin_tokens, member_tokens, org_id = org_with_member(client)

    response = client.get(
        "/orgs",
        headers={"Authorization": f"Bearer {member_tokens['access_token']}"},
    )

    assert response.status_code == 200
    assert org_id in [org["id"] for org in response.json()]


def test_agent_connot_add_member(client):
    admin_tokens, member_tokens, org_id = org_with_member(client, member_role="agent")

    response = client.post(
        f"/orgs/{org_id}/members",
        json={"email": "anyone@test.com", "role": "veiwer"},
        headers={"Authorization": f"Bearer {member_tokens['access_token']}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_member_sees_org_in_list(client):
    # ARRANGE - one org, one admin, one AGENT (all from the helper):
    admin_tokensm, member_tokens, org_id = org_with_member(client)

    # ACT - the AGENT asks "which orgs am I in?"
    response = client.get(
        "/orgs",
        headers={"Authorization": f"Bearer {member_tokens['access_token']}"},
    )

    # ASSERT - the org shows up for the member, not just the admin
    assert response.status_code == 200, response.text
    org_ids = [org["id"] for org in response.json()]
    assert org_id in org_ids


def test_agent_cannot_add_members(client):
    # ARANGE - one orgs, one admin, one AGENT:
    admin_tokens, agent_tokens, org_id = org_with_member(client)

    # ACT - the AGENT tries to invite someone.
    # (newcomer@test.com was never registerd - on purpose. The role wall)
    # Must fire BEFORE the endpoint ever looks the user up; if this test
    # ever returns 404 instead of 403, the wall has moved.)

    response = client.post(
        f"/orgs/{org_id}/members",
        json={"email": "newcomer@test.com", "role": "AGENT"},
        headers={"AUthorization": f"Bearer {agent_tokens['access_token']}"},
    )

    # ASSET - the role wall holds:
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Insufficient permissions"


def test_duplicate_member_return_409(client):
    admin_tokens, member_tokens, org_id = org_with_member(client)

    response = client.post(
        f"/orgs/{org_id}/members",
        json={"email": "org-member@test.com", "role": "viewer"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )

    assert response.status_code == 409
