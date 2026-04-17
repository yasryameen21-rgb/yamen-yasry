import json
import uuid

from fastapi.testclient import TestClient

from database import SessionLocal, startup_event
from main import app
from models import Story, User, UserRole

startup_event()
client = TestClient(app)


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def register(first_name: str, last_name: str):
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
    response.raise_for_status()
    payload = response.json()
    return payload["user_id"], payload["access_token"]


def make_admin(user_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.role = UserRole.ADMIN
        db.commit()
    finally:
        db.close()


def get_story_view_count(story_id: str) -> int:
    db = SessionLocal()
    try:
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            return -1
        return len(story.viewed_by_users or [])
    finally:
        db.close()


def main():
    admin_id, admin_token = register("Admin", "Check")
    member_id, member_token = register("Member", "Check")
    make_admin(admin_id)

    results = {}

    group_resp = client.post(
        "/api/groups",
        headers=auth_headers(admin_token),
        json={"name": "QA Group", "description": "group smoke test", "group_type": "custom"},
    )
    group_resp.raise_for_status()
    group = group_resp.json()
    group_id = group["id"]
    results["groups_create"] = group_resp.status_code == 201

    join_resp = client.post(f"/api/groups/{group_id}/join", headers=auth_headers(member_token))
    leave_resp = client.post(f"/api/groups/{group_id}/leave", headers=auth_headers(member_token))
    results["groups_join_leave"] = join_resp.status_code == 200 and leave_resp.status_code == 200

    post_resp = client.post(
        "/api/posts",
        headers=auth_headers(member_token),
        json={"content": "منشور قابل للتعديل", "post_type": "text"},
    )
    post_resp.raise_for_status()
    post_id = post_resp.json()["id"]

    edit_resp = client.put(
        f"/api/posts/{post_id}",
        headers=auth_headers(member_token),
        json={"content": "تم تعديل المنشور"},
    )
    results["posts_edit"] = edit_resp.status_code == 200 and edit_resp.json()["content"] == "تم تعديل المنشور"

    story_resp = client.post(
        "/api/stories",
        headers=auth_headers(member_token),
        json={"media_url": "https://example.com/story.jpg", "media_type": "image"},
    )
    story_resp.raise_for_status()
    story_id = story_resp.json()["id"]
    story_view_resp = client.put(f"/api/stories/{story_id}/view", headers=auth_headers(admin_token))
    results["stories_view_endpoint"] = story_view_resp.status_code == 200
    results["stories_view_count"] = get_story_view_count(story_id) == 1

    ban_resp = client.post(f"/api/users/ban/{member_id}", headers=auth_headers(admin_token))
    unban_resp = client.post(f"/api/users/unban/{member_id}", headers=auth_headers(admin_token))
    results["ban_unban"] = ban_resp.status_code == 200 and unban_resp.status_code == 200

    delete_resp = client.delete(f"/api/posts/{post_id}", headers=auth_headers(member_token))
    results["posts_delete"] = delete_resp.status_code == 200

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
