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
0) exit
"""

_MAIN_MENU_ITEMS = ["Profile", "Posts", "Follows", "Timeline", "Logout"]
_POSTS_MENU_ITEMS = ["Create Post", "Browse All Posts", "Like a Post", "Comment on a Post"]


def _box(lines) -> str:
    width = max(len(line) for line in lines) + 4
    top = "╔" + "═" * width + "╗"
    bottom = "╚" + "═" * width + "╝"
    divider = "╟" + "─" * width + "╢"
    body = []
    for i, line in enumerate(lines):
        body.append("║" + line.center(width) + "║")
        if i < len(lines) - 1:
            body.append(divider)
    return "\n".join([top, *body, bottom])


def _section_header(title: str) -> str:
    return f"{title}\n{'─' * (len(title) + 10)}"


def _display_menu(items, *, choice_label="Choice") -> str:
    print()
    for i, label in enumerate(items, start=1):
        print(f"   {i}. {label}")
    print()
    return input(f"   {choice_label} (1-{len(items)}, 0=back): ").strip()


def run(app) -> None:
    print("Social Media Lab - interactive mode. Ctrl-D or 'q' to quit.")
    try:
        current_user = _login_or_register(app)
    except EOFError:
        print()
        return

    while current_user is not None:
        print()
        print(_box(["SOCIAL MEDIA CLI", f"{current_user.full_name or current_user.username} <{current_user.email}>"]))
        print()
        print(_section_header("Main Menu"))
        try:
            choice = _display_menu(_MAIN_MENU_ITEMS)
        except EOFError:
            print()
            return

        if choice in ("0", "q", "quit", "exit"):
            return

        try:
            if choice == "1":
                current_user = _profile_menu(app, current_user)
            elif choice == "2":
                _posts_menu(app, current_user)
            elif choice == "3":
                _follows_menu(app, current_user)
            elif choice == "4":
                _timeline(app, current_user)
            elif choice == "5":
                print("\nLogged out.")
                current_user = _login_or_register(app)
            else:
                print("Not a valid choice.")
        except EOFError:
            print()
            return
        except Exception as exc:
            print(f"Error: {exc}")


def _login_or_register(app):
    while True:
        print(AUTH_MENU)
        choice = input("> ").strip().lower()

        if choice in ("0", "q", "quit", "exit"):
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
            full_name = input("full name: ").strip()
            email = input("email: ").strip()
            password = getpass.getpass("password: ")
            bio = input("bio (optional): ").strip()
            try:
                return app.users.register(username, email, password, full_name, bio)
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


def _usernames_by_id(app):
    return {user.id: user.username for user in app.users.list_users()}


def _pick_post(app):
    posts = app.posts.list_recent()
    if not posts:
        print("No posts yet.")
        return None
    usernames = _usernames_by_id(app)
    print("Posts:")
    for i, post in enumerate(posts, start=1):
        author = usernames.get(post.author_id, f"user {post.author_id}")
        print(f"  {i}) {post.body}  (by {author})")
    return _pick_from(posts, prompt="pick a post")


def _profile_menu(app, current_user):
    while True:
        print()
        print(_box(["My Profile"]))
        print()
        print(f"{'Name':<8}: {current_user.full_name or current_user.username}")
        print(f"{'Email':<8}: {current_user.email}")
        print(f"{'Bio':<8}: {current_user.bio or '-'}")
        print(f"{'User ID':<8}: {current_user.id}")
        print(f"{'Active':<8}: {current_user.is_active}")
        print()
        print(_section_header("Profile Actions"))
        choice = _display_menu(["Edit Profile"])

        if choice == "0":
            return current_user
        if choice == "1":
            current_user = _edit_profile(app, current_user)
        else:
            print("Not a valid choice.")


def _edit_profile(app, current_user):
    full_name = input(f"full name [{current_user.full_name}]: ").strip()
    bio = input(f"bio [{current_user.bio}]: ").strip()
    return app.users.update_profile(
        current_user.id,
        full_name=full_name or current_user.full_name,
        bio=bio or current_user.bio,
    )


def _posts_menu(app, current_user) -> None:
    while True:
        print()
        print(_section_header("Posts"))
        choice = _display_menu(_POSTS_MENU_ITEMS)

        if choice == "0":
            return
        if choice == "1":
            _post(app, current_user)
        elif choice == "2":
            _browse_posts(app)
        elif choice == "3":
            _like(app, current_user)
        elif choice == "4":
            _comment(app, current_user)
        else:
            print("Not a valid choice.")


_FOLLOWS_MENU_ITEMS = ["Follow a User", "Unfollow a User", "Who I Follow", "My Followers"]


def _follows_menu(app, current_user) -> None:
    while True:
        print()
        print(_section_header("Follows"))
        choice = _display_menu(_FOLLOWS_MENU_ITEMS)

        if choice == "0":
            return
        if choice == "1":
            _follow(app, current_user)
        elif choice == "2":
            _unfollow(app, current_user)
        elif choice == "3":
            _who_i_follow(app, current_user)
        elif choice == "4":
            _my_followers(app, current_user)
        else:
            print("Not a valid choice.")


def _post(app, current_user) -> None:
    body = input("body: ").strip()
    app.posts.create_post(current_user.id, body)
    print("Post created successfully.")


def _browse_posts(app) -> None:
    posts = app.posts.list_recent()
    if not posts:
        print("No posts yet.")
        return
    usernames = _usernames_by_id(app)
    for post in posts:
        author = usernames.get(post.author_id, f"user {post.author_id}")
        print(f"  [{post.id}] {author}: {post.body}")


def _follow(app, current_user) -> None:
    followee = _pick_user(app, exclude_id=current_user.id)
    if followee is not None:
        app.follows.follow(current_user.id, followee.id)
        print(f"You are now following {followee.username}.")


def _unfollow(app, current_user) -> None:
    usernames = _usernames_by_id(app)
    following_ids = app.follows.list_following(current_user.id)
    if not following_ids:
        print("You aren't following anyone yet.")
        return
    print("Users you follow:")
    for i, user_id in enumerate(following_ids, start=1):
        print(f"  {i}) {usernames.get(user_id, f'user {user_id}')}")
    chosen_id = _pick_from(following_ids, prompt="pick a user to unfollow")
    if chosen_id is not None:
        app.follows.unfollow(current_user.id, chosen_id)
        print(f"You have unfollowed {usernames.get(chosen_id, f'user {chosen_id}')}.")


def _who_i_follow(app, current_user) -> None:
    usernames = _usernames_by_id(app)
    following_ids = app.follows.list_following(current_user.id)
    if not following_ids:
        print("You aren't following anyone yet.")
        return
    for user_id in following_ids:
        print(f"  - {usernames.get(user_id, f'user {user_id}')}")


def _my_followers(app, current_user) -> None:
    usernames = _usernames_by_id(app)
    follower_ids = app.follows.list_followers(current_user.id)
    if not follower_ids:
        print("No one is following you yet.")
        return
    for user_id in follower_ids:
        print(f"  - {usernames.get(user_id, f'user {user_id}')}")


def _like(app, current_user) -> None:
    post = _pick_post(app)
    if post is not None:
        app.likes.like(current_user.id, post.id)
        print("❤️  Post liked successfully.")


def _comment(app, current_user) -> None:
    post = _pick_post(app)
    if post is None:
        return
    body = input("body: ").strip()
    app.comments.create_comment(post.id, current_user.id, body)
    print("💬 Comment added successfully.")


_DEFAULT_TIMELINE_LIMIT = 20


def _timeline(app, current_user) -> None:
    raw = input(f"How many posts to show (default {_DEFAULT_TIMELINE_LIMIT}): ").strip()
    if not raw:
        limit = _DEFAULT_TIMELINE_LIMIT
    elif raw.isdigit() and int(raw) > 0:
        limit = int(raw)
    else:
        print("Not a valid limit.")
        return

    posts = app.feed.get_timeline(current_user.id, limit)
    if not posts:
        print("Nothing here yet - follow someone, or check back after they post.")
        return
    usernames = _usernames_by_id(app)
    for post in posts:
        author = usernames.get(post.author_id, f"user {post.author_id}")
        print(f"  [{post.id}] {author}: {post.body}")
