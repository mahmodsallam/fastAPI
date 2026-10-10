from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()


class Book(BaseModel):
    id: int
    title: str
    author: str
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(ge=0, le=5)


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    description: str | None = Field(default=None, min_length=1, max_length=100)
    rating: int | None = Field(default=None, ge=0, le=5)


BOOKS = [
    Book(id=1, title="Computer Science Pro", author="codingwithroby", description="A very nice book", rating=5),
    Book(id=2, title="Be Fast with FastAPI", author="codingwithroby", description="A great book", rating=5),
    Book(id=3, title="Master Endpoints", author="codingwithroby", description="A awesome book", rating=5),
    Book(id=4, title="HP1", author="Author 1", description="Book Description", rating=2),
    Book(id=5, title="HP2", author="Author 2", description="Book Description", rating=3),
]


@app.get("/books")
async def read_all_books():
    return BOOKS


@app.get("/books/{book_id}")
async def read_book(book_id: int):
    for book in BOOKS:
        if book.id == book_id:
            return book
    raise HTTPException(status_code=404, detail="Book not found")


@app.post("/books", status_code=201)
async def create_book(book: Book):
    if any(b.id == book.id for b in BOOKS):
        raise HTTPException(status_code=400, detail="Book id already exists")
    BOOKS.append(book)
    return book


@app.put("/books/{book_id}")
async def update_book(book_id: int, book_update: BookUpdate):
    for index, book in enumerate(BOOKS):
        if book.id == book_id:
            updated = book.model_copy(update=book_update.model_dump(exclude_unset=True))
            BOOKS[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Book not found")


@app.delete("/books/{book_id}", status_code=204)
async def delete_book(book_id: int):
    for index, book in enumerate(BOOKS):
        if book.id == book_id:
            BOOKS.pop(index)
            return
    raise HTTPException(status_code=404, detail="Book not found")

@app.get("/books/author/{book_author}")
async def read_book_author(book_author: str):
    result = [book for book in BOOKS if book.author == book_author]
    if not result:
        raise HTTPException(status_code=404, detail="Book not found")
    return result
