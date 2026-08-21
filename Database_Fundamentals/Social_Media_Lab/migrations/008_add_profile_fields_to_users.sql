-- Profile screen needs a display name, bio, and active flag beyond the
-- login-only username/email/password columns.
ALTER TABLE users
    ADD COLUMN full_name VARCHAR(150) NOT NULL DEFAULT '',
    ADD COLUMN bio TEXT NOT NULL DEFAULT '',
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
