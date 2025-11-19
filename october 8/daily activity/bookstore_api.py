
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()


class Book(BaseModel):
    id: int
    title: str
    author: str
    price: float = Field(..., gt=0, description="Price must be greater than zero")
    in_stock: bool


books = [
    Book(id=1, title="Deep Learning", author="Ian Goodfellow", price=1200.00, in_stock=True),
    Book(id=2, title="Python Tricks", author="Dan Bader", price=700.00, in_stock=False),
    Book(id=3, title="Designing Data-Intensive Applications", author="Martin Kleppmann", price=1500.00, in_stock=True)
]


# Helper to find a book by ID
def find_book_by_id(book_id: int):
    for book in books:
        if book.id == book_id:
            return book
    return None


# Helper to find the index of a book by ID
def find_book_index_by_id(book_id: int):
    for i, book in enumerate(books):
        if book.id == book_id:
            return i
    return -1


# GET - Retrieve all books
@app.get("/books", response_model=List[Book])
async def get_all_books():
    return books


# GET - Retrieve a book by ID
@app.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: int):
    book = find_book_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


# POST - Add a new book
@app.post("/books", response_model=Book, status_code=201)
async def add_book(book: Book):
    if find_book_by_id(book.id):
        raise HTTPException(status_code=400, detail=f"Book with id {book.id} already exists")

    books.append(book)
    return book


# PUT - Update a book's details (price or availability)
@app.put("/books/{book_id}", response_model=Book)
async def update_book(book_id: int, updated_book: Book):
    book_index = find_book_index_by_id(book_id)
    if book_index == -1:
        raise HTTPException(status_code=404, detail="Book not found")

    books[book_index] = updated_book
    return updated_book


# DELETE - Remove a book
@app.delete("/books/{book_id}", status_code=204)  # 204 No Content for successful deletion
async def delete_book(book_id: int):
    book_index = find_book_index_by_id(book_id)
    if book_index == -1:
        raise HTTPException(status_code=404, detail="Book not found")
    del books[book_index]
    return


# GET - Search books
@app.get("/books/search", response_model=List[Book])
async def search_books(author: Optional[str] = None, max_price: Optional[float] = None):
    filtered_books = []
    for book in books:
        match = True
        if author and author.lower() not in book.author.lower():
            match = False
        if max_price is not None and book.price > max_price:
            match = False

        if match:
            filtered_books.append(book)

    return filtered_books

# Add a route /books/available -> return only books where in_stock = true
@app.get("/books/available", response_model=List[Book])
async def get_available_books():
    return [book for book in books if book.in_stock]

# Add a route /books/count -> return total number of books
@app.get("/books/count")
async def get_books_count():
    return {"total_books": len(books)}
