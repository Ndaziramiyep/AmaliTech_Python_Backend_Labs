from abc import ABC, abstractmethod

from .enum import Categories, TypeOfBook


class LibraryResource(ABC):
    def __init__(self,title):
        self.title = title

    """abstract class for library resources"""

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

class Book(LibraryResource):
    """class for books"""
    def __init__(self, title, author,isbn,year,category :Categories=Categories.GENERAL,book_type:TypeOfBook=TypeOfBook.HARDCOVER,copies=1):

        self._title=None

        self._isbn=None
        self._category=None
        self._book_type=None
        self._author=None



        self.title = title
        self.author = author
        self.isbn = isbn
        self.year = year
        self.category = category
        self.book_type = book_type
        self.copies = copies

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self,value):
        if not value.replace(" ","").isalpha():
            raise ValueError("title must contain only space and letters")
        if not value:
            raise ValueError("Title cannot be empty")
        self._title = value



    @property
    def isbn(self):
        return self._isbn

    @isbn.setter
    def isbn(self,value):
        if not value:
            raise ValueError("ISBN cannot be empty")
        self._isbn = value

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self,value):
        if isinstance(value,Categories):
            self._category = value
        elif isinstance(value,str):
            self._category = Categories(value)
        else:
            raise ValueError("invalid category")

    @property
    def book_type(self):
        return self._book_type

    @book_type.setter
    def book_type(self,value):
        if isinstance(value,TypeOfBook):
            self._book_type = value
        elif isinstance(value,str):
            self._book_type = TypeOfBook(value)
        else:
            raise ValueError("invalid book type")


    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, value):
        from .author import Author
        if not isinstance(value, Author):
            raise ValueError("author must be an Author object")
        self._author = value

    def __repr__(self):
        return (f"Book(title={self.title}, author={self.author}, isbn={self.isbn}, year={self.year}, category={self.category.value}, book_type={self.book_type.value}")

    def __eq__(self, other):
        if not isinstance(other, Book):
            return False

        return self.isbn == other.isbn
