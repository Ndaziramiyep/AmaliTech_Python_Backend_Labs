# tests/test_main.py

from main import main


def test_main_exit(monkeypatch):
    # Simulate user input: API key, then "exit"
    inputs = iter(["valid_key", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    # Run main (should exit immediately after "exit")
    main()


def test_main_valid_city(monkeypatch, capsys):
    inputs = iter(["valid_key", "Kigali", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    main()

    captured = capsys.readouterr()
    assert "Forecast for Kigali" in captured.out
