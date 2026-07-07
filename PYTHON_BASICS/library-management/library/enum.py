from enum import Enum


class Categories(Enum):
    FICTION = "Fiction"
    NON_FICTION = "Non-Fiction"
    SCIENCE_FICTION = "Science Fiction"
    FANTASY = "Fantasy"
    MYSTERY = "Mystery"
    THRILLER = "Thriller"
    ROMANCE = "Romance"
    BIOGRAPHY = "Biography"
    HISTORY = "History"
    CHILDREN = "Children"
    POETRY = "Poetry"
    COOKBOOKS = "Cookbooks"
    SELF_HELP = "Self-Help"
    TECHNOLOGY = "Technology"
    SCIENCE = "Science"
    GENERAL = "General"

class TypeOfBook(Enum):
    HARDCOVER = "Hardcover"
    PAPERBACK = "Paperback"
    EBOOK = "Ebook"
    AUDIOBOOK = "Audiobook"

