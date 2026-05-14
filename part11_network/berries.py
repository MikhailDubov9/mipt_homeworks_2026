from dataclasses import asdict, dataclass
from typing import Annotated

import uvicorn
from fastapi import Body, FastAPI, HTTPException, Path
from pydantic import BaseModel, Field


@dataclass(frozen=True, slots=True)
class Good:
    id: int
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class Review:
    id: int
    good_id: int
    body: str


class GoodSchema(BaseModel):
    id: int
    title: str
    description: str


class ReviewSchema(BaseModel):
    id: int = Field(description="Идентификатор отзыва")
    good_id: int = Field(description="Идентификатор товара")
    body: str = Field(description="Текст отзыва")


class CreateReviewSchema(BaseModel):
    body: str = Field(min_length=30, max_length=500)


class ListReviewSchema(BaseModel):
    reviews: list[ReviewSchema]


goods: dict[int, Good] = {
    1: Good(1, "Шампунь Жумайсынба", "Не можете здороваться с братками? Наш шампунь вам поможет!"),
    2: Good(2, "Слон", "А ты купи слона"),
    3: Good(3, "Бананы", "Шучу, не бананы"),
}

reviews: dict[int, Review] = {
    1: Review(1, 1, "От этого шампуня волосы дыбом! Куплю ешё!"),
    2: Review(2, 1, "Доставили быстро, ещё не открывал"),
    3: Review(3, 2, "Бананы хорошие, но кот напрудил мне в тапки, поэтому 4"),
}

app = FastAPI(
    title="API ДомашниеЯгоды",
    version="0.1.0",
)


@app.get("/goods/{good_id}")
def get_good(good_id: int) -> GoodSchema:
    """
    Возвращает товар по идентификатору
    """
    good = goods.get(good_id)
    if good is None:
        raise HTTPException(status_code=404, detail="Good not found!")
    return GoodSchema(**asdict(good))


@app.get("/goods/{good_id}/reviews")
def get_reviews_for_good(good_id: int, phrase: str | None = None) -> ListReviewSchema:
    """
    Возвращает все отзывы для товара с опциональным поиском по фразе
    """
    needle = phrase or None
    found_reviews = (r for r in reviews.values() if r.good_id == good_id and (needle is None or needle in r.body))
    return ListReviewSchema(
        reviews=[ReviewSchema(**asdict(review)) for review in found_reviews],
    )


@app.post("/goods/{good_id}/reviews")
def create_review(
    good_id: Annotated[int, Path(title="The ID of good", ge=0)],
    create_review: Annotated[CreateReviewSchema, Body()],
) -> ReviewSchema:
    """
    Создаёт новый отзыв
    """
    if good_id not in goods:
        raise HTTPException(status_code=404, detail="Good not found!")
    new_review = Review(max(reviews.keys(), default=0) + 1, good_id, **create_review.model_dump())
    reviews[new_review.id] = new_review
    return ReviewSchema(**asdict(new_review))


def main() -> None:
    uvicorn.run(app)


if __name__ == "__main__":
    main()
