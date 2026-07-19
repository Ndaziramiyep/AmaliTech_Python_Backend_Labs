from dataclasses import dataclass, asdict


@dataclass
class User:
    """Represents a system user."""
    user_id: int
    name: str
    email: str

    def to_dict(self) -> dict:
        """Convert the user object to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create a User object from a dictionary."""
        return cls(
            user_id=data["user_id"],
            name=data["name"],
            email=data["email"]
        )

    def __eq__(self, other: object) -> bool:
        """Check equality between two user objects."""
        if not isinstance(other, User):
            return NotImplemented
        return (
            self.user_id == other.user_id and
            self.name == other.name and
            self.email == other.email
        )
