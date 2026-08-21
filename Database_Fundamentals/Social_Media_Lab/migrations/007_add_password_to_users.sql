-- Login now happens by email + password instead of username lookup alone.
-- Existing rows get a placeholder '' that can never match a real password
-- hash, so pre-existing users must re-register (or have a real hash set
-- directly) before they can log in again.
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE users ALTER COLUMN password_hash DROP DEFAULT;
