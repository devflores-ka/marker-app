from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
from typing import List
import sys
import os

# Para el ejecutable
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "file://"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datos temporales en memoria (para empezar)
projects = {}
samples = {}

@app.get("/")
async def root():
    return {"message": "Marker App Backend - Running"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "marker-app-backend"}

@app.post("/api/projects/create")
async def create_project(name: str):
    import uuid
    project_id = str(uuid.uuid4())
    projects[project_id] = {
        "id": project_id,
        "name": name,
        "samples": []
    }
    return {"project_id": project_id, "status": "success"}

@app.post("/api/projects/{project_id}/samples/upload")
async def upload_samples(project_id: str, files: List[UploadFile]):
    results = []
    for file in files:
        content = await file.read()
        # Por ahora solo guardamos metadata
        import uuid
        sample_id = str(uuid.uuid4())
        samples[sample_id] = {
            "id": sample_id,
            "filename": file.filename,
            "project_id": project_id,
            "size": len(content),
            "alleles": {}
        }
        if project_id in projects:
            projects[project_id]["samples"].append(sample_id)
        results.append({"filename": file.filename, "sample_id": sample_id})
    return {"samples": results}

@app.put("/api/samples/{sample_id}/alleles")
async def update_alleles(sample_id: str, locus: str, alleles: List[str]):
    if sample_id in samples:
        if "alleles" not in samples[sample_id]:
            samples[sample_id]["alleles"] = {}
        samples[sample_id]["alleles"][locus] = alleles
        return {"status": "updated"}
    return {"status": "error", "message": "Sample not found"}

@app.get("/api/projects/{project_id}/export/excel")
async def export_excel(project_id: str):
    # Por ahora retornamos un archivo de ejemplo
    return {"status": "not implemented", "project_id": project_id}

if __name__ == "__main__":
    print("="*50)
    print("Iniciando Marker App Backend")
    print("URL: http://localhost:8888")
    print("Docs: http://localhost:8888/docs")
    print("="*50)
    uvicorn.run(app, host="127.0.0.1", port=8888)
