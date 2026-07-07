from .resources import LibraryResource


class Author(LibraryResource):
    """class for Author"""

    def __init__(self,name,nationality,birth_year):
        super().__init__(name)
        self.nationality = nationality
        self.birth_year = birth_year
        self.name = name

    def __repr__(self):
        return (f"Author(name={self.name}, nationality={self.nationality}, birth_year={self.birth_year})")

    def __eq__(self, other):
        if not isinstance(other, Author):
            return False
        return (self.name == other.name and self.nationality == other.nationality and self.birth_year == other.birth_year)
