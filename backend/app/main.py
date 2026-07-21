from fastapi import FastAPI

app = FastAPI(title="Katecam Todo Tracker")


@app.get("/health")
def health():
    return {"status": "ok"}
