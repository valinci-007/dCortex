from fastapi import FastAPI

app = FastAPI(
    title="dCortex Crew Ops Advisor",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}