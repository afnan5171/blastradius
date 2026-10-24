from fastapi import FastAPI
app = FastAPI(title="BlastRadius")
@app.get("/health")
def health(): return {"status": "ok"}
