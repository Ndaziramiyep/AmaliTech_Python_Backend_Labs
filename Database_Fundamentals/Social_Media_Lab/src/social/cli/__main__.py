"""CLI entry point: parses argv into subcommands and dispatches to the
composition root's services. With no arguments, launches the menu-driven
REPL in `interactive.py` instead.
"""
import argparse
import json
import sys

from social.cli import interactive
from social.composition import App


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    if len(sys.argv) == 1:
        interactive.run(App())
        return

    parser = argparse.ArgumentParser(prog="social-cli")
    sub = parser.add_subparsers(dest="command", required=True)

    register = sub.add_parser("register")
    register.add_argument("username")
    register.add_argument("email")
    register.add_argument("password")

    post = sub.add_parser("post")
    post.add_argument("author_id", type=int)
    post.add_argument("body")

    follow = sub.add_parser("follow")
    follow.add_argument("follower_id", type=int)
    follow.add_argument("followee_id", type=int)

    like = sub.add_parser("like")
    like.add_argument("user_id", type=int)
    like.add_argument("post_id", type=int)

    comment = sub.add_parser("comment")
    comment.add_argument("post_id", type=int)
    comment.add_argument("author_id", type=int)
    comment.add_argument("body")

    timeline = sub.add_parser("timeline")
    timeline.add_argument("user_id", type=int)

    args = parser.parse_args()
    app = App()

    if args.command == "register":
        print(app.users.register(args.username, args.email, args.password))
    elif args.command == "post":
        print(app.posts.create_post(args.author_id, args.body))
    elif args.command == "follow":
        print(app.follows.follow(args.follower_id, args.followee_id))
    elif args.command == "like":
        print(app.likes.like(args.user_id, args.post_id))
    elif args.command == "comment":
        print(app.comments.create_comment(args.post_id, args.author_id, args.body))
    elif args.command == "timeline":
        posts = app.feed.get_timeline(args.user_id)
        print(json.dumps([p.body for p in posts], indent=2))


if __name__ == "__main__":
    main()
