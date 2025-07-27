# backend/app.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Dict, Any, Optional
import sys
import os
import uuid
import json
import traceback

# Importar nuestro parser FSA
try:
    from core.fsa_reader import FSAReader
except ImportError:
    print("Warning: FSA Reader no encontrado, usando modo simulado")
    FSAReader = None

# Para el ejecutable
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

app = FastAPI(
    title="GenotypeR Backend",
    description="API para análisis genético con archivos FSA",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "file://"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenamiento en memoria (después migrar a base de datos)
projects: Dict[str, Dict] = {}
samples: Dict[str, Dict] = {}

@app.get("/")
async def root():
    return {"message": "GenotypeR Backend - Running", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok", 
        "service": "GenotypeR-backend",
        "projects": len(projects),
        "samples": len(samples)
    }

@app.post("/api/projects/create")
async def create_project(name: str = Form(...)):
    """Crear un nuevo proyecto de análisis genético"""
    try:
        # Validar entrada
        if not name or not name.strip():
            return JSONResponse(
                status_code=400,
                content={"detail": "El nombre del proyecto es requerido"}
            )
        
        project_id = str(uuid.uuid4())
        projects[project_id] = {
            "id": project_id,
            "name": name.strip(),
            "created_at": "2025-01-27",  # En producción usar datetime.now()
            "samples": [],
            "status": "active",
            "metadata": {
                "total_samples": 0,
                "analyzed_samples": 0,
                "loci_detected": []
            }
        }
        
        return {
            "project_id": project_id, 
            "status": "success",
            "message": f"Proyecto '{name.strip()}' creado exitosamente"
        }
        
    except Exception as e:
        print(f"Error creando proyecto: {e}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error interno del servidor: {str(e)}"}
        )

@app.get("/api/projects")
async def list_projects():
    """Listar todos los proyectos"""
    try:
        return {"projects": list(projects.values())}
    except Exception as e:
        print(f"Error listando proyectos: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Obtener detalles de un proyecto específico"""
    try:
        if project_id not in projects:
            return JSONResponse(
                status_code=404,
                content={"detail": "Proyecto no encontrado"}
            )
        
        project = projects[project_id].copy()
        
        # Agregar datos de muestras
        samples_data = []
        for sample_id in project.get("samples", []):
            if sample_id in samples:
                samples_data.append(samples[sample_id])
        
        project["samples_data"] = samples_data
        
        return project
        
    except Exception as e:
        print(f"Error obteniendo proyecto {project_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )

@app.post("/api/projects/{project_id}/samples/upload")
async def upload_samples(project_id: str, files: List[UploadFile] = File(...)):
    """Subir y procesar archivos FSA a un proyecto"""
    try:
        if project_id not in projects:
            return JSONResponse(
                status_code=404,
                content={"detail": "Proyecto no encontrado"}
            )
        
        if not files:
            return JSONResponse(
                status_code=400,
                content={"detail": "No se proporcionaron archivos"}
            )
        
        results = []
        processed_count = 0
        
        for file in files:
            try:
                # Validar tipo de archivo
                if not file.filename:
                    results.append({
                        "filename": "archivo sin nombre",
                        "status": "error",
                        "message": "Archivo sin nombre válido"
                    })
                    continue
                
                if not file.filename.lower().endswith(('.fsa', '.ab1', '.txt')):
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": "Tipo de archivo no soportado. Use .fsa, .ab1 o .txt"
                    })
                    continue
                
                # Leer contenido del archivo
                content = await file.read()
                if len(content) == 0:
                    results.append({
                        "filename": file.filename,
                        "status": "error", 
                        "message": "Archivo vacío"
                    })
                    continue
                
                # Procesar archivo con FSAReader (o simulado)
                print(f"Procesando archivo: {file.filename} ({len(content)} bytes)")
                
                if FSAReader:
                    fsa_data = FSAReader.process_file(content, file.filename)
                else:
                    # Crear datos simulados si no hay FSAReader
                    fsa_data = create_mock_fsa_data(file.filename)
                
                # Crear entrada de muestra
                sample_id = str(uuid.uuid4())
                sample_data = {
                    "id": sample_id,
                    "filename": file.filename,
                    "project_id": project_id,
                    "file_size": len(content),
                    "upload_date": "2025-01-27",
                    "status": "analyzed" if fsa_data.get("success", True) else "error",
                    "fsa_data": fsa_data,
                    "metadata": {
                        "channels": fsa_data.get("channels", 0),
                        "data_points": fsa_data.get("data_points", 0),
                        "sample_name": fsa_data.get("sample_name", "Unknown"),
                        "instrument": fsa_data.get("instrument", "Unknown"),
                        "run_date": fsa_data.get("run_date", ""),
                        "quality_score": calculate_quality_score(fsa_data)
                    }
                }
                
                # Guardar muestra
                samples[sample_id] = sample_data
                projects[project_id]["samples"].append(sample_id)
                
                # Actualizar estadísticas del proyecto
                projects[project_id]["metadata"]["total_samples"] += 1
                if fsa_data.get("success", True):
                    projects[project_id]["metadata"]["analyzed_samples"] += 1
                    processed_count += 1
                    
                    # Agregar loci detectados
                    for channel_alleles in fsa_data.get("alleles", {}).values():
                        for locus in channel_alleles.keys():
                            if locus not in projects[project_id]["metadata"]["loci_detected"]:
                                projects[project_id]["metadata"]["loci_detected"].append(locus)
                
                # Calcular alelos detectados
                alleles_count = 0
                for channel in fsa_data.get("alleles", {}).values():
                    alleles_count += len(channel)
                
                results.append({
                    "filename": file.filename,
                    "sample_id": sample_id,
                    "status": "success" if fsa_data.get("success", True) else "error",
                    "message": "Archivo procesado exitosamente" if fsa_data.get("success", True) else fsa_data.get("error", "Error desconocido"),
                    "channels": fsa_data.get("channels", 0),
                    "alleles_detected": alleles_count
                })
                
            except Exception as e:
                print(f"Error procesando {file.filename}: {str(e)}")
                print(traceback.format_exc())
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"Error procesando archivo: {str(e)}"
                })
        
        return {
            "message": f"Procesados {processed_count} de {len(files)} archivos exitosamente",
            "samples": results,
            "project_summary": {
                "total_samples": projects[project_id]["metadata"]["total_samples"],
                "analyzed_samples": projects[project_id]["metadata"]["analyzed_samples"],
                "loci_detected": projects[project_id]["metadata"]["loci_detected"]
            }
        }
        
    except Exception as e:
        print(f"Error en upload_samples: {e}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error interno del servidor: {str(e)}"}
        )

@app.get("/api/projects/{project_id}/allele_matrix")
async def get_allele_matrix(project_id: str):
    """Generar matriz de alelos para el proyecto"""
    try:
        if project_id not in projects:
            return JSONResponse(
                status_code=404,
                content={"detail": "Proyecto no encontrado"}
            )
        
        project = projects[project_id]
        matrix = []
        all_loci = set()
        
        # Recopilar todos los loci encontrados
        for sample_id in project["samples"]:
            if sample_id in samples:
                sample = samples[sample_id]
                
                # Usar alelos manuales si existen, sino usar automáticos
                alleles_data = sample.get("manual_alleles", {})
                if not alleles_data:
                    for channel_alleles in sample["fsa_data"].get("alleles", {}).values():
                        alleles_data.update(channel_alleles)
                
                all_loci.update(alleles_data.keys())
        
        # Crear matriz
        for sample_id in project["samples"]:
            if sample_id in samples:
                sample = samples[sample_id]
                row = {
                    "sample_id": sample_id,
                    "filename": sample["filename"],
                    "status": sample["status"]
                }
                
                # Obtener alelos para cada locus
                alleles_data = sample.get("manual_alleles", {})
                if not alleles_data:
                    for channel_alleles in sample["fsa_data"].get("alleles", {}).values():
                        alleles_data.update(channel_alleles)
                
                for locus in sorted(all_loci):
                    if locus in alleles_data:
                        row[locus] = "/".join(map(str, sorted(alleles_data[locus])))
                    else:
                        row[locus] = ""
                
                matrix.append(row)
        
        return {
            "project_id": project_id,
            "project_name": project["name"],
            "loci": sorted(all_loci),
            "samples": matrix
        }
        
    except Exception as e:
        print(f"Error generando matriz de alelos: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )

def create_mock_fsa_data(filename: str) -> dict:
    """Crear datos FSA simulados para testing cuando no hay parser real"""
    import random
    
    # Simular diferentes loci para diferentes archivos
    sample_alleles = {}
    loci_examples = ['D3S1358', 'vWA', 'D16S539', 'CSF1PO']
    
    # Agregar algunos loci con alelos simulados
    for i, locus in enumerate(loci_examples[:2]):  # Solo 2 loci por simplicidad
        channel_name = f"channel_{i+1}"
        allele_values = random.sample(range(12, 25), random.randint(1, 2))
        sample_alleles[channel_name] = {
            locus: [str(a) for a in sorted(allele_values)]
        }
    
    return {
        "filename": filename,
        "success": True,
        "sample_name": filename.split('.')[0],
        "run_date": "2025-01-27",
        "instrument": "Simulador GenotypeR",
        "channels": 4,
        "data_points": 5000,
        "size_standard": "LIZ-500",
        "dye_set": "Simulado",
        "raw_data": {},  # Simplificado por ahora
        "size_ladder": {},
        "detected_peaks": {},
        "alleles": sample_alleles,
        "quality_metrics": {
            "channel_1": {"signal_to_noise": random.uniform(50, 100)},
            "channel_2": {"signal_to_noise": random.uniform(50, 100)}
        },
        "simulation_note": "Datos simulados para desarrollo"
    }

def calculate_quality_score(fsa_data: Dict[str, Any]) -> float:
    """Calcula un score de calidad simple basado en métricas del FSA"""
    if not fsa_data.get("success", False):
        return 0.0
    
    quality_metrics = fsa_data.get("quality_metrics", {})
    if not quality_metrics:
        return 0.7  # Score por defecto para datos simulados
    
    # Score basado en signal-to-noise ratio promedio
    snr_scores = []
    for channel_metrics in quality_metrics.values():
        snr = channel_metrics.get("signal_to_noise", 1)
        snr_scores.append(min(snr / 100, 1.0))  # Normalizar a 0-1
    
    if snr_scores:
        return sum(snr_scores) / len(snr_scores)
    
    return 0.7

if __name__ == "__main__":
    print("="*60)
    print("🧬 Iniciando GenotypeR Backend")
    print("URL: http://localhost:8888")
    print("Docs: http://localhost:8888/docs")
    print("Ready for genetic analysis!")
    print("="*60)
    uvicorn.run(app, host="127.0.0.1", port=8888)
    