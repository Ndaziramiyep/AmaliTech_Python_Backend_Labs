from datetime import date

from book import LibraryResource


class Author(LibraryResource):
    """Represents a book author."""

    def __init__(self, name, nationality, birth_year):
        if not name or not str(name).strip():
            raise ValueError("Author name cannot be empty")
        if nationality is not None and not str(nationality).strip():
            raise ValueError("Nationality cannot be blank if provided")
        if birth_year is not None:
            try:
                birth_year = int(birth_year)
            except (ValueError, TypeError):
                raise ValueError("Birth year must be a number")
            if birth_year < 1 or birth_year > date.today().year:
                raise ValueError(f"Birth year must be between 1 and {date.today().year}")
        super().__init__(name)
        self.name = name.strip()
        self.nationality = nationality
        self.birth_year = birth_year

    def __str__(self):
        return (
            f"  Author : {self.name}\n"
            f"  Origin : {self.nationality or 'N/A'}\n"
            f"  Born   : {self.birth_year or 'N/A'}"
        )

    def __repr__(self):
        return f"Author(name={self.name}, nationality={self.nationality}, birth_year={self.birth_year})"

    def __eq__(self, other):
        if not isinstance(other, Author):
            return False
        return (
            self.name == other.name
            and self.nationality == other.nationality
            and self.birth_year == other.birth_year
        )
