# Testing Strategy

## Tools

- **pytest**: Testing framework
- **pytest-mock**: Mocking and stubbing dependencies
- **coverage**: Code coverage analysis

---

## Approach

- Follow **TDD**: Write tests before implementation (Red → Green → Refactor)
- **Mock dependencies**: Repository and hasher are mocked to isolate logic
- **Coverage goal**: 100% on core service logic

---

## Test Cases

### Registration

- ✅ Successful registration
- ❌ Duplicate username raises `UserAlreadyExistsError`

### Login

- ✅ Successful login
- ❌ Non-existent username raises `UserNotFoundError`
- ❌ Wrong password raises `InvalidPasswordError`

---

## Example Test

```python
def test_register_user_success(mocker):
    # Arrange
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_username.return_value = None
    mock_hasher.hash_password.return_value = "hashed"

    service = UserService(mock_repo, mock_hasher)

    # Act
    user = service.register_user("diane", "secure123")

    # Assert
    assert user.username == "diane"
    assert user.password_hash == "hashed"
    mock_repo.add.assert_called_once()
```

---

## Running Tests

### Run all tests

```bash
pytest
```

### Run with coverage report

```bash
pytest --cov=src/auth tests/
```

### Run with detailed coverage

```bash
pytest --cov=src/auth --cov-report=html tests/
```

### Run specific test file

```bash
pytest tests/test_user_service.py
```

### Run with verbose output

```bash
pytest -v
```

---

## Coverage Report Interpretation

- **Green lines**: Executed during tests
- **Red lines**: Not covered by tests
- **Target**: Maintain 100% coverage on core business logic
- **Exclusions**: Configuration files, entry points, and trivial methods may be excluded

---

## Best Practices

1. **Isolation**: Each test should be independent and not rely on others
2. **Clarity**: Test names should clearly describe what they test
3. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification phases
4. **Mock external dependencies**: Database, network calls, file I/O should always be mocked
5. **Test edge cases**: Empty inputs, null values, boundary conditions
6. **Fast execution**: Unit tests should run in milliseconds
