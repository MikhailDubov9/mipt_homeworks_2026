import uvicorn
from fastapi import FastAPI, Response, status

app = FastAPI()


@app.get("/api/v1/healthcheck")
def healthcheck() -> Response:
    """Проверить, что сервер активен."""
    return Response(status_code=status.HTTP_200_OK)


def main() -> None:
    """Запустить сервер."""
    uvicorn.run(app)


if __name__ == "__main__":
    main()
