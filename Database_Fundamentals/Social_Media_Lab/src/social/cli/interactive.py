"""Menu-driven REPL for `python main.py` with no arguments.

Reuses the same App composition root and service calls as the argparse
subcommands in __main__.py - this is just a friendlier front end over them.
Every action operates as the logged-in user (no author_id/user_id prompts),
and any other entity it needs (who to follow, which post to react to) is
picked from a displayed list rather than typed in blind as a raw id.
"""
import getpass

AUTH_MENU = """
1) login
2) register
q) quit
"""

MENU = """
1) create a post
2) follow a user
3) like a post
4) comment on a post
5) view my timeline
q) quit
"""


def run(app) -> None:
    print("Social Media Lab - interactive mode. Ctrl-D or 'q' to quit.")
    try:
        current_user = _login_or_register(app)
    except EOFError:
        print()
        return
    if current_user is None:
        return

    print(f"\nLogged in as {current_user.username!r} (id={current_user.id}).")
    while True:
        print(MENU)
        try:
            choice = input("> ").strip().lower()
        except EOFError:
            print()
            return

        if choice in ("q", "quit", "exit"):
            return

        handler = _HANDLERS.get(choice)
        if handler is None:
            print(f"Unrecognized choice: {choice!r}")
            continue

        try:
            handler(app, current_user)
        except EOFError:
            print()
            return
        except Exception as exc:
            print(f"Error: {exc}")


def _login_or_register(app):
    while True:
        print(AUTH_MENU)
        choice = input("> ").strip().lower()

        if choice in ("q", "quit", "exit"):
            return None

        if choice in ("1", "login"):
            email = input("email: ").strip()
            password = getpass.getpass("password: ")
            user = app.users.authenticate(email, password)
            if user is None:
                print("Invalid email or password.")
                continue
            return user

        if choice in ("2", "register"):
            username = input("username: ").strip()
            email = input("email: ").strip()
            password = getpass.getpass("password: ")
            try:
                return app.users.register(username, email, password)
            except Exception as exc:
                print(f"Error: {exc}")
                continue

        print(f"Unrecognized choice: {choice!r}")


def _pick_from(items, *, prompt):
    """Show a 1-based numbered list and let the caller pick a position -
    never a raw database id."""
    selection = input(f"{prompt} (1-{len(items)}): ").strip()
    if not selection.isdigit() or not (1 <= int(selection) <= len(items)):
        print("Not a valid choice.")
        return None
    return items[int(selection) - 1]


def _pick_user(app, *, exclude_id):
    candidates = [u for u in app.users.list_users() if u.id != exclude_id]
    if not candidates:
        print("No other users yet.")
        return None
    print("Users you can follow:")
    for i, user in enumerate(candidates, start=1):
        print(f"  {i}) {user.username}")
    return _pick_from(candidates, prompt="pick a user")


def _pick_post(app):
    posts = app.posts.list_recent()
    if not posts:
        print("No posts yet.")
        return None
    print("Posts:")
    for i, post in enumerate(posts, start=1):
        print(f"  {i}) {post.body}  (by user {post.author_id})")
    return _pick_from(posts, prompt="pick a post")


def _post(app, current_user) -> None:
    body = input("body: ").strip()
    print(app.posts.create_post(current_user.id, body))


def _follow(app, current_user) -> None:
    followee = _pick_user(app, exclude_id=current_user.id)
    if followee is not None:
        print(app.follows.follow(current_user.id, followee.id))


def _like(app, current_user) -> None:
    post = _pick_post(app)
    if post is not None:
        print(app.likes.like(current_user.id, post.id))


def _comment(app, current_user) -> None:
    post = _pick_post(app)
    if post is None:
        return
    body = input("body: ").strip()
    print(app.comments.create_comment(post.id, current_user.id, body))


def _timeline(app, current_user) -> None:
    posts = app.feed.get_timeline(current_user.id)
    if not posts:
        print("Nothing here yet - follow someone, or check back after they post.")
        return
    for post in posts:
        print(f"  [{post.id}] user {post.author_id}: {post.body}")


_HANDLERS = {
    "1": _post,
    "2": _follow,
    "3": _like,
    "4": _comment,
    "5": _timeline,
}
