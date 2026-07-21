def test_end_to_end_registration_and_login():
    from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher
    from src.auth.implementation.memory_repo import InMemoryUserRepository
    from src.auth.service import UserService

    repo = InMemoryUserRepository()
    hasher = BcryptPasswordHasher()
    service = UserService(repo, hasher)

    user = service.register_user("Diane", "diane@example.com", "SecurePass123")
    assert user.password_hash != "SecurePass123"
    assert service.verify_user("diane@example.com", "SecurePass123") is True
