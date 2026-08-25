"""Seed the database with a small, realistic set of demo data.

Deliberately goes through `App` and its services - the same path
`main.py`/`social-cli` use - rather than raw SQL, so seeding exercises the
real password hashing, activity logging, and cache invalidation instead of
a parallel, potentially-drifting code path. Coexists with unrelated,
already-registered users (it only looks for its own fixed usernames) and
is safe to re-run: once all of `_USERS` exist it skips seeding entirely,
rather than half-inserting and hitting a UNIQUE-constraint error.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from social.app import App

_USERS = [
    {
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123",
        "full_name": "Alice Anderson",
        "bio": "Coffee, code, and cats.",
    },
    {
        "username": "bob",
        "email": "bob@example.com",
        "password": "password123",
        "full_name": "Bob Baker",
        "bio": "Building things, badly, on purpose.",
    },
    {
        "username": "carol",
        "email": "carol@example.com",
        "password": "password123",
        "full_name": "Carol Chen",
        "bio": "Photographer. Occasional hiker.",
    },
    {
        "username": "dave",
        "email": "dave@example.com",
        "password": "password123",
        "full_name": "Dave Diaz",
        "bio": "Just here for the timeline.",
    },
]

_FOLLOWS = [  # (follower_username, followee_username)
    ("alice", "bob"),
    ("alice", "carol"),
    ("bob", "carol"),
    ("dave", "alice"),
    ("dave", "bob"),
]

_POSTS = [  # (author_username, body)
    ("alice", "Just set up my profile - hello, world!"),
    ("bob", "Debugging a race condition for three hours. It was a typo."),
    ("bob", "Coffee count today: 4. Send help."),
    ("carol", "Sunrise over the ridge this morning. Worth the early alarm."),
    ("carol", "New lens arrived. Expect way too many photos this week."),
    ("dave", "Lurking, as usual."),
]

_LIKES = [  # (username, post_index into the list this seed just created)
    ("alice", 3),
    ("dave", 0),
    ("dave", 3),
    ("bob", 4),
]

_COMMENTS = [  # (post_index, author_username, body)
    (3, "alice", "This is gorgeous!"),
    (0, "bob", "Welcome!"),
]


def main() -> None:
    app = App()

    seed_usernames = {spec["username"] for spec in _USERS}
    existing_usernames = {user.username for user in app.users.list_users()}
    if seed_usernames <= existing_usernames:
        print("Seed users already exist - skipping seed (safe to re-run once removed).")
        return

    users_by_username = {}
    for spec in _USERS:
        existing = app.users.find_by_username(spec["username"])
        if existing is not None:
            users_by_username[spec["username"]] = existing
            print(f"user      {existing.username} (id={existing.id}, already existed)")
            continue
        user = app.users.register(
            spec["username"], spec["email"], spec["password"], spec["full_name"], spec["bio"]
        )
        users_by_username[spec["username"]] = user
        print(f"user      {user.username} (id={user.id})")

    for follower, followee in _FOLLOWS:
        app.follows.follow(users_by_username[follower].id, users_by_username[followee].id)
        print(f"follow    {follower} -> {followee}")

    posts = []
    for author, body in _POSTS:
        post = app.posts.create_post(users_by_username[author].id, body)
        posts.append(post)
        print(f"post      {author}: {body!r} (id={post.id})")

    for username, post_index in _LIKES:
        app.likes.like(users_by_username[username].id, posts[post_index].id)
        print(f"like      {username} -> post {posts[post_index].id}")

    for post_index, author, body in _COMMENTS:
        app.comments.create_comment(posts[post_index].id, users_by_username[author].id, body)
        print(f"comment   {author} on post {posts[post_index].id}: {body!r}")

    print("Seed complete.")


if __name__ == "__main__":
    main()
