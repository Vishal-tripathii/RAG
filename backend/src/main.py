from fastapi import FastAPI
6
from src.config import settings

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=True)
