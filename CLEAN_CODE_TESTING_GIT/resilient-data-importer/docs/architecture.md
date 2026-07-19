# System Architecture

## Overview
Resilient Data Importer follows a layered architecture with separation of concerns.

## Layers
1. **CLI Layer**: `main.py` – User interaction.
2. **Business Logic Layer**: `parser.py`, `validator.py` – Parsing and validation.
3. **Data Access Layer**: `storage.py` – JSON storage.
4. **Domain Layer**: `models.py`, `exceptions.py` – Data structures & exceptions.
5. **Infrastructure Layer**: Logging system, file I/O.


## Architecture Diagram
```mermaid
graph TB
    subgraph "Presentation Layer"
        CLI[CLI Interface / main.py]
    end

    subgraph "Business Logic Layer"
        Parser[CSVParser / parser.py]
        Validator[UserValidator / validator.py]
    end

    subgraph "Data Access Layer"
        Repository[UserRepository / storage.py]
    end

    subgraph "Domain Layer"
        UserModel[User Model / models.py]
        Exceptions[Exceptions / exceptions.py]
    end

    subgraph "Data Storage"
        JSONDB[(JSON Database)]
    end

    Logger[Logger / logging system]

    CLI --> Parser
    CLI --> Validator
    CLI --> Logger
    Parser --> Validator
    Parser --> Exceptions
    Parser --> Logger
    Parser --> UserModel
    Validator --> Repository
    Validator --> Exceptions
    Validator --> Logger
    Validator --> UserModel
    Repository --> JSONDB
    Repository --> Exceptions
    Repository --> Logger
    Repository --> UserModel
```
