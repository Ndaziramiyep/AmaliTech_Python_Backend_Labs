# Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ POSTS : authors
    POSTS ||--o{ COMMENTS : receives
    USERS ||--o{ FOLLOWERS : "follows (follower_user_id)"
    USERS ||--o{ FOLLOWERS : "is followed by (followee_user_id)"

    USERS {
        bigint user_id PK
        varchar username UK
        varchar email UK
        text password_hash
        timestamptz created_at
    }

    POSTS {
        bigint post_id PK
        bigint author_user_id FK
        text content
        jsonb metadata
        timestamptz created_at
    }

    COMMENTS {
        bigint comment_id PK
        bigint post_id FK
        bigint commenter_user_id FK
        text content
        timestamptz created_at
    }

    FOLLOWERS {
        bigint follower_user_id PK,FK
        bigint followee_user_id PK,FK
        timestamptz created_at
    }
```

`followers` is a many-to-many self-relationship on `users`: each row means
`follower_user_id` follows `followee_user_id`. The composite primary key
`(follower_user_id, followee_user_id)` prevents duplicate follow edges and doubles as
a B-tree index for "who does this user follow"; `idx_followers_followee_follower`
covers the reverse "who follows this user" lookup.

Likes are intentionally **not** a relational table — per the lab's data-store split,
"like" activity lives only in MongoDB's activity log (see
`MongoActivityLogRepository`), not in PostgreSQL.
