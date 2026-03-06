from fastapi import FastAPI

app = FastAPI(
    title="ExplainAI Video Engine",
    description="Backend API to orchestrate AI agents that convert research papers into explainable videos.",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "ExplainAI Video Engine is running."}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
