"""Tests for GET /history — the caller's saved predictions."""

from app.models.prediction import Prediction


def _seed(db_session, user, count, label="PNEUMONIA"):
    """Insert ``count`` predictions for ``user``; return them oldest-first."""
    rows = [
        Prediction(user_id=user.id, label=label, probability=0.9, filename=f"x{i}.jpeg")
        for i in range(count)
    ]
    db_session.add_all(rows)
    db_session.commit()
    return rows


def test_history_requires_auth(client):
    assert client.get("/history").status_code == 401


def test_history_empty_for_new_user(client, make_user, as_user):
    as_user(make_user())
    resp = client.get("/history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_history_returns_rows_newest_first(client, db_session, make_user, as_user):
    user = make_user()
    _seed(db_session, user, 3)
    as_user(user)

    resp = client.get("/history")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3
    ids = [row["id"] for row in body]
    assert ids == sorted(ids, reverse=True)  # newest (highest id) first
    assert set(body[0]) == {"id", "label", "probability", "filename", "created_at"}


def test_history_is_scoped_to_current_user(client, db_session, make_user, as_user):
    alice = make_user(email="alice@example.com")
    bob = make_user(email="bob@example.com")
    _seed(db_session, alice, 2)

    as_user(bob)
    assert client.get("/history").json() == []

    as_user(alice)
    assert len(client.get("/history").json()) == 2


def test_history_pagination(client, db_session, make_user, as_user):
    user = make_user()
    _seed(db_session, user, 5)
    as_user(user)

    page1 = client.get("/history", params={"limit": 2, "offset": 0}).json()
    page2 = client.get("/history", params={"limit": 2, "offset": 2}).json()

    assert [r["id"] for r in page1] == sorted((r["id"] for r in page1), reverse=True)
    assert len(page1) == 2 and len(page2) == 2
    assert {r["id"] for r in page1}.isdisjoint({r["id"] for r in page2})


def test_history_rejects_bad_limit(client, make_user, as_user):
    as_user(make_user())
    assert client.get("/history", params={"limit": 0}).status_code == 422
    assert client.get("/history", params={"limit": 999}).status_code == 422
