import uuid

from fastapi.testclient import TestClient

from database import startup_event
from main import app

startup_event()
client = TestClient(app)


def _register_user(first_name: str, last_name: str):
    unique = uuid.uuid4().hex[:8]
    response = client.post(
        "/api/auth/register-profile",
        json={
            "first_name": first_name,
            "last_name": last_name,
            "contact_method": "email",
            "contact": f"{first_name.lower()}.{last_name.lower()}.{unique}@example.com",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return payload["user_id"], payload["access_token"]


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_follow_and_friend_request_flow():
    user_a_id, token_a = _register_user("Ali", "One")
    user_b_id, token_b = _register_user("Mona", "Two")

    friend_request = client.post(
        f"/api/users/friend-requests/{user_b_id}",
        headers=_auth_headers(token_a),
        json={"message": "خلينا أصحاب"},
    )
    assert friend_request.status_code == 200, friend_request.text
    request_id = friend_request.json()["id"]

    incoming = client.get("/api/users/friend-requests/incoming", headers=_auth_headers(token_b))
    assert incoming.status_code == 200, incoming.text
    assert any(item["id"] == request_id for item in incoming.json())

    accepted = client.post(f"/api/users/friend-requests/{request_id}/accept", headers=_auth_headers(token_b))
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "accepted"

    friends_a = client.get(f"/api/users/{user_a_id}/friends")
    friends_b = client.get(f"/api/users/{user_b_id}/friends")
    assert any(friend["id"] == user_b_id for friend in friends_a.json())
    assert any(friend["id"] == user_a_id for friend in friends_b.json())

    follow_response = client.post(f"/api/users/follow/{user_b_id}", headers=_auth_headers(token_a))
    assert follow_response.status_code == 200, follow_response.text

    followers = client.get(f"/api/users/{user_b_id}/followers")
    assert followers.status_code == 200, followers.text
    assert any(user["id"] == user_a_id for user in followers.json())


def test_post_save_repost_report_and_live_request_flow():
    host_user_id, host_token = _register_user("Host", "Live")
    viewer_user_id, viewer_token = _register_user("Viewer", "Live")

    created_post = client.post(
        "/api/posts",
        headers=_auth_headers(host_token),
        json={"content": "أول منشور للتجربة", "post_type": "text"},
    )
    assert created_post.status_code == 200, created_post.text
    post_id = created_post.json()["id"]

    saved = client.post(f"/api/posts/{post_id}/save", headers=_auth_headers(viewer_token))
    assert saved.status_code == 200, saved.text

    comment = client.post(
        f"/api/posts/{post_id}/comments",
        headers=_auth_headers(viewer_token),
        json={"content": "تعليق للتجربة"},
    )
    assert comment.status_code == 200, comment.text

    like = client.post(f"/api/posts/{post_id}/reactions/like", headers=_auth_headers(viewer_token))
    assert like.status_code == 200, like.text

    stats_before_repost = client.get(f"/api/posts/{post_id}/stats")
    assert stats_before_repost.status_code == 200, stats_before_repost.text
    stats_payload = stats_before_repost.json()
    assert stats_payload["saves_count"] == 1
    assert stats_payload["comments_count"] == 1
    assert stats_payload["likes_count"] == 1

    repost = client.post(
        f"/api/posts/{post_id}/repost",
        headers=_auth_headers(viewer_token),
        json={"content": "أنصحكم تقروه"},
    )
    assert repost.status_code == 200, repost.text

    stats_after_repost = client.get(f"/api/posts/{post_id}/stats")
    assert stats_after_repost.status_code == 200, stats_after_repost.text
    assert stats_after_repost.json()["shares_count"] == 1

    report = client.post(
        "/api/reports",
        headers=_auth_headers(viewer_token),
        json={
            "target_type": "post",
            "target_id": post_id,
            "reason": "spam",
            "details": "اختبار نظام البلاغات",
        },
    )
    assert report.status_code == 200, report.text
    assert report.json()["target_id"] == post_id

    stream = client.post(
        "/api/live/start",
        headers=_auth_headers(host_token),
        json={"title": "بث اختبار"},
    )
    assert stream.status_code == 200, stream.text
    stream_id = stream.json()["id"]

    join_request = client.post(
        f"/api/live/{stream_id}/join-requests",
        headers=_auth_headers(viewer_token),
        json={"note": "حابب أشارك في البث"},
    )
    assert join_request.status_code == 200, join_request.text
    request_id = join_request.json()["id"]

    list_requests = client.get(f"/api/live/{stream_id}/join-requests", headers=_auth_headers(host_token))
    assert list_requests.status_code == 200, list_requests.text
    assert any(item["id"] == request_id for item in list_requests.json())

    approved = client.post(f"/api/live/join-requests/{request_id}/approve", headers=_auth_headers(host_token))
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    live_stats = client.get(f"/api/live/{stream_id}/stats")
    assert live_stats.status_code == 200, live_stats.text
    assert live_stats.json()["approved_join_requests"] == 1
