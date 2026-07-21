import uuid
from dataclasses import dataclass, field


@dataclass
class User:
    """
    Represents a registered user in the system.

    Attributes:
        id: Unique identifier (UUID) automatically generated.
        username: Display name of the user.
        email: Unique email address of the user.
        password_hash: Hashed password.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    password_hash: str = ""
