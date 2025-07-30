# backend/app.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
from typing import List, Dict, Any, Optional
import sys
import os
import uuid
import json
import traceback
import asyncio
from datetime import datetime
import numpy as np
from decimal import Decimal
import io
import os
import pickle
from pathlib import Path

# Directorio para persistencia
DATA_DIR = Path("./genotyper_data")
DATA_DIR.mkdir(exist_ok=True)

# Archivos de persistencia
PROJECTS_FILE = DATA_DIR / "projects.json"
SAMPLES_FILE = DATA_DIR / "samples.json"
CACHE_FILE = DATA_DIR / "analysis_cache.pkl"

def load_data():
    """Cargar datos persistidos"""
    global projects, samples, analysis_cache
    
    try:
        # Cargar proyectos
        if PROJECTS_FILE.exists():
            with open(PROJECTS_FILE, 'r') as f:
                projects = json.load(f)
            print(f"✅ Cargados {len(projects)} proyectos")
        
        # Cargar muestras
        if SAMPLES_FILE.exists():
            with open(SAMPLES_FILE, 'r') as f:
                samples = json.load(f)
            print(f"✅ Cargadas {len(samples)} muestras")
        
        # Cargar caché de análisis
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'rb') as f:
                analysis_cache = pickle.load(f)
            print(f"✅ Cargados {len(analysis_cache)} análisis en caché")
                
    except Exception as e:
        print(f"⚠️  Error cargando datos: {e}")
        print("   Iniciando con datos vacíos")

def save_data():
    """Guardar datos a disco"""
    try:
        # Guardar proyectos
        with open(PROJECTS_FILE, 'w') as f:
            json.dump(projects, f, indent=2, default=str)
        
        # Guardar muestras
        with open(SAMPLES_FILE, 'w') as f:
            json.dump(samples, f, indent=2, default=str)
        
        # Guardar caché (usar pickle para numpy arrays)
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(analysis_cache, f)
            
        print("💾 Datos guardados exitosamente")
        
    except Exception as e:
        print(f"❌ Error guardando datos: {e}")

# Importar el parser mejorado
try:
    from core.fsa_parser_enhanced import EnhancedFSAParser
    PARSER_AVAILABLE = True
except ImportError:
    print("Warning: Enhanced FSA Parser no encontrado")
    PARSER_AVAILABLE = False
    # Fallback al parser simple si existe
    try:
        from core.fsa_reader import FSAReader
        EnhancedFSAParser = FSAReader  # Usar el simple como fallback
    except ImportError:
        EnhancedFSAParser = None

# Para el ejecutable
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

app = FastAPI(
    title="GenotypeR Backend API",
    description="API para análisis genético con archivos FSA/AB1",
    version="2.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "file://"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# Almacenamiento en memoria (para desarrollo)
# En producción usar base de datos
projects: Dict[str, Dict] = {}
samples: Dict[str, Dict] = {}
analysis_cache: Dict[str, Dict] = {}

# Función auxiliar para manejar serialización
def safe_json_serialize(obj):
    """
    Convierte objetos Python a tipos serializables por JSON
    Maneja arrays numpy, decimales, objetos personalizados, etc.
    """
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {str(k): safe_json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [safe_json_serialize(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, 'isoformat'):  # datetime objects
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return safe_json_serialize(obj.__dict__)
    else:
        # Fallback: convertir a string
        try:
            return str(obj)
        except:
            return "No serializable"

@app.get("/")
async def root():
    return {
        "message": "GenotypeR Backend API - Running",
        "version": "2.0.0",
        "parser_available": PARSER_AVAILABLE,
        "features": [
            "FSA/AB1 file parsing",
            "Automatic peak detection",
            "STR allele calling",
            "Quality metrics",
            "Size standard calibration"
        ]
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "GenotypeR-backend",
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "projects": len(projects),
            "samples": len(samples),
            "cached_analyses": len(analysis_cache)
        }
    }

@app.post("/api/projects/create")
async def create_project(name: str = Form(...), description: str = Form("")):
    """Crear un nuevo proyecto de análisis genético"""
    try:
        if not name or not name.strip():
            raise HTTPException(400, "El nombre del proyecto es requerido")
        
        project_id = str(uuid.uuid4())
        project = {
            "id": project_id,
            "name": name.strip(),
            "description": description,
            "created_at": datetime.now().isoformat(),
            "samples": [],
            "status": "active"
        }
        
        projects[project_id] = project
        
        autosave()

        return {
            "success": True,
            "project": project,
            "message": f"Proyecto '{name}' creado exitosamente"
        }
        
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creando proyecto: {str(e)}")
        raise HTTPException(500, f"Error al crear proyecto: {str(e)}")

@app.get("/api/projects")
async def list_projects():
    """Listar todos los proyectos"""
    return {
        "success": True,
        "projects": list(projects.values()),
        "total": len(projects)
    }

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Obtener detalles de un proyecto específico con datos completos de FSA"""
    if project_id not in projects:
        raise HTTPException(404, "Proyecto no encontrado")
    
    project = projects[project_id]
    
    # Obtener información completa de las muestras incluyendo datos FSA
    project_samples = []
    for sample in samples.values():
        if sample.get("project_id") == project_id:
            # Crear copia de la muestra
            sample_with_fsa = sample.copy()
            
            # Agregar datos FSA si están en caché
            if sample["id"] in analysis_cache:
                fsa_data = analysis_cache[sample["id"]]
                sample_with_fsa["fsa_data"] = {
                    "channels": fsa_data.get("channels", {}),
                    "alleles": fsa_data.get("alleles", {}),
                    "peaks": fsa_data.get("peaks", {}),
                    "quality_metrics": fsa_data.get("quality_metrics", {})
                }
                
                # Actualizar conteo de canales con información real
                sample_with_fsa["metadata"]["channels"] = len([
                    ch for ch in fsa_data.get("channels", {}).values() 
                    if ch.get("has_raw_data", False)
                ])
                
                # Actualizar calidad
                sample_with_fsa["metadata"]["quality_score"] = fsa_data.get("quality_metrics", {}).get("overall_quality", 0)
            
            project_samples.append(sample_with_fsa)
    
    # Calcular estadísticas
    loci_detected = set()
    for sample in project_samples:
        if sample.get("fsa_data") and sample["fsa_data"].get("alleles"):
            loci_detected.update(sample["fsa_data"]["alleles"].keys())
    
    return {
        "success": True,
        "project": project,
        "samples_data": project_samples,
        "metadata": {
            "total_samples": len(project_samples),
            "analyzed_samples": len([s for s in project_samples if s["status"] == "analyzed"]),
            "loci_detected": list(loci_detected),
            "last_updated": project.get("updated_at", project["created_at"])
        }
    }

@app.get("/api/projects/{project_id}/allele_matrix")
async def get_project_allele_matrix(project_id: str):
    """Obtener matriz de alelos del proyecto"""
    try:
        if project_id not in projects:
            raise HTTPException(404, "Proyecto no encontrado")
        
        project = projects[project_id]
        project_samples = [s for s in samples.values() if s.get("project_id") == project_id]
        
        # Construir matriz de alelos
        allele_matrix = {
            "project_id": project_id,
            "project_name": project.get("name"),
            "samples": [],
            "markers": [],
            "generated_at": datetime.now().isoformat()
        }
        
        # Obtener todos los marcadores únicos
        all_markers = set()
        sample_alleles = {}
        
        for sample in project_samples:
            sample_id = sample["id"]
            if sample_id in analysis_cache:
                analysis = analysis_cache[sample_id]
                alleles = analysis.get("alleles", {})
                sample_alleles[sample_id] = {
                    "sample_name": sample.get("filename", sample_id),
                    "alleles": alleles
                }
                all_markers.update(alleles.keys())
        
        allele_matrix["markers"] = sorted(list(all_markers))
        allele_matrix["samples"] = list(sample_alleles.values())
        
        return {
            "success": True,
            "matrix": allele_matrix
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generando matriz de alelos: {str(e)}")
        raise HTTPException(500, f"Error al generar matriz: {str(e)}")

@app.post("/api/projects/{project_id}/samples/upload")
async def upload_samples(
    project_id: str,
    files: List[UploadFile] = File(...)
):
    """Subir y analizar archivos FSA/AB1"""
    try:
        if project_id not in projects:
            raise HTTPException(404, "Proyecto no encontrado")
        
        if not files:
            raise HTTPException(400, "No se recibieron archivos")
        
        results = []
        errors = []
        
        # Procesar archivos en paralelo
        tasks = []
        for file in files:
            # Validar extensión
            if not file.filename.lower().endswith(('.fsa', '.ab1')):
                errors.append({
                    "filename": file.filename,
                    "error": "Formato no soportado. Use archivos .fsa o .ab1"
                })
                continue
            
            tasks.append(process_single_file(file, project_id))
        
        autosave()
        
        # Ejecutar análisis en paralelo
        if tasks:
            processed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in processed_results:
                if isinstance(result, Exception):
                    errors.append({
                        "filename": "Unknown",
                        "error": str(result)
                    })
                elif result["success"]:
                    results.append(result)
                else:
                    errors.append(result)
        
        # Actualizar proyecto
        if project_id in projects:
            projects[project_id]["samples"].extend([r["sample"]["id"] for r in results])
            projects[project_id]["updated_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": f"Procesados {len(results)} archivos exitosamente",
            "results": results,
            "errors": errors,
            "summary": {
                "total_files": len(files),
                "successful": len(results),
                "failed": len(errors)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error procesando archivos: {str(e)}")
        traceback.print_exc()
        raise HTTPException(500, f"Error al procesar archivos: {str(e)}")

async def process_single_file(file: UploadFile, project_id: str) -> Dict:
    """Procesar un solo archivo FSA"""
    try:
        # Leer contenido
        content = await file.read()
        
        if len(content) == 0:
            return {
                "success": False,
                "filename": file.filename,
                "error": "Archivo vacío"
            }
        
        # Analizar archivo
        analysis_result = EnhancedFSAParser.process_file(content, file.filename)
        
        if not analysis_result.get("success", False):
            return {
                "success": False,
                "filename": file.filename,
                "error": analysis_result.get("error", "Error desconocido en el análisis")
            }
        
        # IMPORTANTE: Asegurarse de que trace_data esté en el resultado
        # Si el parser no lo incluye, intentar extraerlo
        if "trace_data" not in analysis_result and "raw_data" in analysis_result:
            analysis_result["trace_data"] = analysis_result["raw_data"]
        
        # Si aún no tenemos trace_data, intentar extraerlo de los canales
        if "trace_data" not in analysis_result:
            trace_data = {}
            channels = analysis_result.get("channels", {})
            for channel_key, channel_info in channels.items():
                if "raw_data" in channel_info:
                    trace_data[channel_key] = channel_info["raw_data"]
            if trace_data:
                analysis_result["trace_data"] = trace_data
        
        # Crear registro de muestra con estructura correcta
        sample_id = str(uuid.uuid4())
        sample = {
            "id": sample_id,
            "project_id": project_id,
            "filename": file.filename,
            "file_size": len(content),
            "uploaded_at": datetime.now().isoformat(),
            "status": "analyzed",
            "metadata": {
                **analysis_result.get("metadata", {}),
                "quality_score": analysis_result.get("quality_metrics", {}).get("overall_quality", 0),
                "channels": len([
                    ch for ch in analysis_result.get("channels", {}).values()
                    if ch.get("has_raw_data", False)
                ])
            },
            "quality": analysis_result.get("quality_metrics", {}).get("overall_quality", 0),
            "alleles_detected": len(analysis_result.get("alleles", {})),
            "channels": len(analysis_result.get("channels", {}))
        }
        
        # Guardar muestra y análisis
        samples[sample_id] = sample
        analysis_cache[sample_id] = analysis_result
        
        # Actualizar proyecto
        if project_id in projects:
            if sample_id not in projects[project_id]["samples"]:
                projects[project_id]["samples"].append(sample_id)
        
        return {
            "success": True,
            "sample": sample,
            "analysis_summary": {
                "channels_detected": len(analysis_result.get("channels", {})),
                "peaks_detected": sum(len(peaks) for peaks in analysis_result.get("peaks", {}).values()),
                "alleles_called": len(analysis_result.get("alleles", {})),
                "quality": analysis_result.get("quality_metrics", {}).get("overall_quality", 0)
            }
        }
        
    except Exception as e:
        print(f"Error procesando archivo {file.filename}: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "filename": file.filename,
            "error": str(e)
        }

@app.get("/api/samples/{sample_id}")
async def get_sample_details(sample_id: str):
    """Obtener detalles completos de una muestra incluyendo datos FSA"""
    if sample_id not in samples:
        raise HTTPException(404, f"Muestra no encontrada: {sample_id}")
    
    sample = samples[sample_id].copy()
    
    # IMPORTANTE: El frontend espera que la respuesta tenga una propiedad 'analysis'
    if sample_id in analysis_cache:
        analysis_data = analysis_cache[sample_id]
        
        # Crear estructura que el frontend espera
        analysis = {
            "channels": analysis_data.get("channels", {}),
            "alleles": analysis_data.get("alleles", {}),
            "peaks": analysis_data.get("peaks", {}),
            "quality_metrics": analysis_data.get("quality_metrics", {}),
            "size_standard": analysis_data.get("size_standard", {}),
            "str_markers": analysis_data.get("str_markers", {}),
            "metadata": analysis_data.get("metadata", {}),
            "filename": sample.get("filename", "")
        }
        
        # También mantener fsa_data para compatibilidad
        sample["fsa_data"] = analysis
    else:
        analysis = {
            "channels": {},
            "alleles": {},
            "peaks": {},
            "quality_metrics": {},
            "size_standard": {},
            "metadata": {},
            "filename": sample.get("filename", "")
        }
        sample["fsa_data"] = None
    
    # LA CLAVE: El frontend hace setSampleData(data.analysis)
    # Así que debemos retornar la estructura correcta
    return {
        "success": True,
        "sample": sample,
        "analysis": analysis  # Esta es la línea crítica
    }

@app.get("/api/debug/sample/{sample_id}")
async def debug_sample_data(sample_id: str):
    """Endpoint para debugging - ver estructura completa de datos"""
    data = {
        "sample_exists": sample_id in samples,
        "analysis_exists": sample_id in analysis_cache,
        "sample_data": samples.get(sample_id, {}),
        "analysis_keys": list(analysis_cache.get(sample_id, {}).keys()) if sample_id in analysis_cache else [],
        "analysis_preview": {}
    }
    
    if sample_id in analysis_cache:
        analysis = analysis_cache[sample_id]
        data["analysis_preview"] = {
            "has_channels": "channels" in analysis,
            "has_alleles": "alleles" in analysis,
            "has_peaks": "peaks" in analysis,
            "channels_count": len(analysis.get("channels", {})),
            "alleles_count": len(analysis.get("alleles", {})),
            "peaks_count": len(analysis.get("peaks", {}))
        }
    
    return data

@app.put("/api/samples/{sample_id}/alleles")
async def update_sample_alleles(sample_id: str, alleles: Dict[str, Dict]):
    """Actualizar alelos manualmente editados"""
    try:
        if sample_id not in samples:
            raise HTTPException(404, "Muestra no encontrada")
        
        if sample_id not in analysis_cache:
            raise HTTPException(404, "Análisis no encontrado")
        
        # Actualizar alelos en el caché
        analysis_cache[sample_id]["alleles"] = alleles
        analysis_cache[sample_id]["manual_review"] = True
        analysis_cache[sample_id]["reviewed_at"] = datetime.now().isoformat()
        
        # Actualizar estado de la muestra
        samples[sample_id]["status"] = "manually_reviewed"
        samples[sample_id]["reviewed_at"] = datetime.now().isoformat()
        
        autosave()

        return {
            "success": True,
            "message": "Alelos actualizados exitosamente",
            "alleles": alleles
        }
        
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error actualizando alelos: {str(e)}")
        raise HTTPException(500, f"Error al actualizar alelos: {str(e)}")

@app.get("/api/samples/{sample_id}/electropherogram")
async def get_electropherogram_data(sample_id: str, channel: Optional[str] = None):
    """Obtener datos del electroferograma para visualización"""
    if sample_id not in analysis_cache:
        raise HTTPException(404, "Datos de análisis no encontrados")
    
    analysis = analysis_cache[sample_id]
    
    # Filtrar por canal si se especifica
    if channel:
        channel_key = f"channel_{channel}"
        if channel_key not in analysis.get("channels", {}):
            raise HTTPException(404, f"Canal {channel} no encontrado")
        
        return {
            "success": True,
            "data": {
                "channels": {channel_key: analysis["channels"][channel_key]},
                "peaks": {channel_key: analysis.get("peaks", {}).get(channel_key, [])},
                "metadata": analysis.get("metadata", {})
            }
        }
    
    # Retornar todos los datos
    return {
        "success": True,
        "data": {
            "channels": analysis.get("channels", {}),
            "peaks": analysis.get("peaks", {}),
            "size_standard": analysis.get("size_standard", {}),
            "metadata": analysis.get("metadata", {}),
            "quality_metrics": analysis.get("quality_metrics", {})
        }
    }

@app.post("/api/analysis/batch")
async def batch_analysis(
    sample_ids: List[str],
    analysis_type: str = Form("comparison")
):
    """Análisis por lotes de múltiples muestras"""
    try:
        if not sample_ids:
            raise HTTPException(400, "No se especificaron muestras")
        
        # Verificar que todas las muestras existen
        missing_samples = [sid for sid in sample_ids if sid not in samples]
        if missing_samples:
            raise HTTPException(404, f"Muestras no encontradas: {missing_samples}")
        
        results = {}
        
        if analysis_type == "comparison":
            # Comparación de perfiles genéticos
            profiles = {}
            for sample_id in sample_ids:
                if sample_id in analysis_cache:
                    alleles = analysis_cache[sample_id].get("alleles", {})
                    profiles[sample_id] = {
                        "sample_name": samples[sample_id]["metadata"].get("sample_name", sample_id),
                        "alleles": alleles
                    }
            
            # Calcular coincidencias
            matches = calculate_profile_matches(profiles)
            results = {
                "type": "comparison",
                "profiles": profiles,
                "matches": matches
            }
            
        elif analysis_type == "quality_summary":
            # Resumen de calidad
            quality_data = []
            for sample_id in sample_ids:
                if sample_id in analysis_cache:
                    metrics = analysis_cache[sample_id].get("quality_metrics", {})
                    quality_data.append({
                        "sample_id": sample_id,
                        "filename": samples[sample_id]["filename"],
                        "quality": metrics.get("overall_quality", "unknown"),
                        "snr": metrics.get("average_snr", 0),
                        "channels": len(analysis_cache[sample_id].get("channels", {}))
                    })
            
            results = {
                "type": "quality_summary",
                "samples": quality_data,
                "summary": {
                    "total": len(quality_data),
                    "excellent": sum(1 for q in quality_data if q["quality"] == "excellent"),
                    "good": sum(1 for q in quality_data if q["quality"] == "good"),
                    "acceptable": sum(1 for q in quality_data if q["quality"] == "acceptable"),
                    "poor": sum(1 for q in quality_data if q["quality"] == "poor")
                }
            }
        
        return {
            "success": True,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en análisis batch: {str(e)}")
        raise HTTPException(500, f"Error en análisis: {str(e)}")

@app.get("/api/export/project/{project_id}")
async def export_project_data(
    project_id: str,
    format: str = "json"
):
    """Exportar datos del proyecto"""
    try:
        if project_id not in projects:
            raise HTTPException(404, "Proyecto no encontrado")
        
        project = projects[project_id]
        project_samples = [s for s in samples.values() if s.get("project_id") == project_id]
        
        # Preparar datos para exportar
        export_data = {
            "project": project,
            "samples": [],
            "export_date": datetime.now().isoformat(),
            "version": "2.0"
        }
        
        for sample in project_samples:
            sample_data = {
                **sample,
                "alleles": {}
            }
            
            # Incluir alelos si están disponibles
            if sample["id"] in analysis_cache:
                sample_data["alleles"] = analysis_cache[sample["id"]].get("alleles", {})
                sample_data["quality_metrics"] = analysis_cache[sample["id"]].get("quality_metrics", {})
            
            export_data["samples"].append(sample_data)
        
        if format == "json":
            # Exportar como JSON
            json_data = json.dumps(export_data, indent=2)
            return StreamingResponse(
                io.BytesIO(json_data.encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=project_{project_id}_export.json"
                }
            )
        
        elif format == "csv":
            # Exportar como CSV (tabla de genotipos)
            csv_content = generate_genotype_table_csv(export_data)
            return StreamingResponse(
                io.BytesIO(csv_content.encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=project_{project_id}_genotypes.csv"
                }
            )
        
        else:
            raise HTTPException(400, "Formato no soportado. Use 'json' o 'csv'")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error exportando proyecto: {str(e)}")
        raise HTTPException(500, f"Error al exportar: {str(e)}")

# Funciones auxiliares

def calculate_profile_matches(profiles: Dict[str, Dict]) -> List[Dict]:
    """Calcular coincidencias entre perfiles genéticos"""
    matches = []
    sample_ids = list(profiles.keys())
    
    for i in range(len(sample_ids)):
        for j in range(i + 1, len(sample_ids)):
            sample1_id = sample_ids[i]
            sample2_id = sample_ids[j]
            
            alleles1 = profiles[sample1_id]["alleles"]
            alleles2 = profiles[sample2_id]["alleles"]
            
            # Contar marcadores coincidentes
            matching_markers = 0
            total_markers = 0
            marker_details = []
            
            common_markers = set(alleles1.keys()) & set(alleles2.keys())
            
            for marker in common_markers:
                total_markers += 1
                
                # Verificar si los alelos coinciden
                set1 = {alleles1[marker].get("allele1"), alleles1[marker].get("allele2")}
                set2 = {alleles2[marker].get("allele1"), alleles2[marker].get("allele2")}
                
                # Eliminar None si existe
                set1.discard(None)
                set2.discard(None)
                
                if set1 and set2 and set1 == set2:
                    matching_markers += 1
                    marker_details.append({
                        "marker": marker,
                        "match": True,
                        "alleles": list(set1)
                    })
                else:
                    marker_details.append({
                        "marker": marker,
                        "match": False,
                        "sample1_alleles": list(set1),
                        "sample2_alleles": list(set2)
                    })
            
            match_percentage = (matching_markers / total_markers * 100) if total_markers > 0 else 0
            
            matches.append({
                "sample1": {
                    "id": sample1_id,
                    "name": profiles[sample1_id]["sample_name"]
                },
                "sample2": {
                    "id": sample2_id,
                    "name": profiles[sample2_id]["sample_name"]
                },
                "matching_markers": matching_markers,
                "total_markers": total_markers,
                "match_percentage": round(match_percentage, 2),
                "details": marker_details
            })
    
    return sorted(matches, key=lambda x: x["match_percentage"], reverse=True)

def generate_genotype_table_csv(export_data: Dict) -> str:
    """Generar tabla de genotipos en formato CSV"""
    import csv
    import io
    
    # Obtener lista de todos los marcadores
    all_markers = set()
    for sample in export_data["samples"]:
        if "alleles" in sample:
            all_markers.update(sample["alleles"].keys())
    
    all_markers = sorted(list(all_markers))
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    header = ["Sample ID", "Sample Name", "Quality"]
    for marker in all_markers:
        header.extend([f"{marker}_1", f"{marker}_2"])
    writer.writerow(header)
    
    # Datos
    for sample in export_data["samples"]:
        row = [
            sample["id"],
            sample.get("metadata", {}).get("sample_name", ""),
            sample.get("quality", "")
        ]
        
        for marker in all_markers:
            if marker in sample.get("alleles", {}):
                allele_data = sample["alleles"][marker]
                row.extend([
                    allele_data.get("allele1", ""),
                    allele_data.get("allele2", "")
                ])
            else:
                row.extend(["", ""])
        
        writer.writerow(row)
    
    return output.getvalue()

@app.delete("/api/samples/{sample_id}")
async def delete_sample(sample_id: str):
    """Eliminar una muestra"""
    try:
        if sample_id not in samples:
            raise HTTPException(404, "Muestra no encontrada")
        
        # Obtener proyecto asociado
        sample = samples[sample_id]
        project_id = sample.get("project_id")
        
        # Eliminar de proyecto si existe
        if project_id and project_id in projects:
            projects[project_id]["samples"] = [
                sid for sid in projects[project_id]["samples"] 
                if sid != sample_id
            ]
        
        # Eliminar muestra y análisis
        del samples[sample_id]
        if sample_id in analysis_cache:
            del analysis_cache[sample_id]
        
        autosave()

        return {
            "success": True,
            "message": "Muestra eliminada exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error eliminando muestra: {str(e)}")
        raise HTTPException(500, f"Error al eliminar muestra: {str(e)}")
    
@app.get("/api/samples/{sample_id}/channel/{channel_key}")
async def get_channel_data(sample_id: str, channel_key: str):
    """Obtener datos crudos y analizados de un canal específico"""
    try:
        if sample_id not in analysis_cache:
            raise HTTPException(404, "Muestra no encontrada")
        
        analysis = analysis_cache[sample_id]
        channels = analysis.get("channels", {})
        
        if channel_key not in channels:
            raise HTTPException(404, f"Canal {channel_key} no encontrado")
        
        channel_info = channels[channel_key]
        
        # Construir respuesta con los datos del canal
        response = {
            "success": True,
            "channel": channel_key,
            "info": channel_info,
            "raw_data": None,
            "analyzed_data": None
        }
        
        # Obtener datos crudos si están disponibles
        if channel_info.get("has_raw_data", False):
            # Los datos crudos deberían estar en el análisis
            # Buscar en diferentes posibles ubicaciones
            raw_data = None
            
            # Opción 1: Directamente en el canal
            if "raw_data" in channel_info:
                raw_data = channel_info["raw_data"]
            
            # Opción 2: En una estructura separada de raw_data
            elif "raw_data" in analysis:
                raw_data = analysis["raw_data"].get(channel_key)
            
            # Opción 3: En la estructura de datos del parser FSA
            # El parser guarda los datos en analysis["trace_data"]
            elif "trace_data" in analysis:
                # Mapear el número del canal
                channel_num = int(channel_key.split('_')[1])
                raw_data = analysis["trace_data"].get(f"channel_{channel_num}", [])
            
            response["raw_data"] = raw_data
        
        # Obtener datos analizados si están disponibles
        if channel_info.get("has_analyzed_data", False):
            analyzed_data = None
            
            # Opción 1: Directamente en el canal
            if "analyzed_data" in channel_info:
                analyzed_data = channel_info["analyzed_data"]
            
            # Opción 2: En una estructura separada
            elif "analyzed_data" in analysis:
                analyzed_data = analysis["analyzed_data"].get(channel_key)
            
            response["analyzed_data"] = analyzed_data
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error obteniendo datos del canal: {str(e)}")
        raise HTTPException(500, f"Error al obtener datos del canal: {str(e)}")

@app.get("/api/samples/{sample_id}/raw_data")
async def get_all_raw_data(sample_id: str):
    """Obtener todos los datos crudos de una muestra"""
    try:
        if sample_id not in analysis_cache:
            raise HTTPException(404, "Muestra no encontrada")
        
        analysis = analysis_cache[sample_id]
        channels = analysis.get("channels", {})
        
        # Construir respuesta con todos los datos
        all_data = {}
        
        for channel_key, channel_info in channels.items():
            channel_data = {
                "info": channel_info,
                "raw_data": None,
                "analyzed_data": None
            }
            
            # Buscar datos crudos
            if channel_info.get("has_raw_data", False):
                # Intentar diferentes ubicaciones
                if "trace_data" in analysis:
                    channel_num = int(channel_key.split('_')[1])
                    channel_data["raw_data"] = analysis["trace_data"].get(f"channel_{channel_num}", [])
                elif "raw_data" in channel_info:
                    channel_data["raw_data"] = channel_info["raw_data"]
            
            # Buscar datos analizados
            if channel_info.get("has_analyzed_data", False) and "analyzed_data" in channel_info:
                channel_data["analyzed_data"] = channel_info["analyzed_data"]
            
            all_data[channel_key] = channel_data
        
        return {
            "success": True,
            "sample_id": sample_id,
            "channels": all_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error obteniendo datos crudos: {str(e)}")
        raise HTTPException(500, f"Error al obtener datos: {str(e)}")
    
@app.post("/api/admin/save")
async def save_data_endpoint():
    """Guardar datos manualmente"""
    save_data()
    return {
        "success": True,
        "message": "Datos guardados exitosamente",
        "stats": {
            "projects": len(projects),
            "samples": len(samples),
            "analyses": len(analysis_cache)
        }
    }

# Agregar autosave después de operaciones importantes
def autosave():
    """Guardar datos automáticamente"""
    try:
        save_data()
    except:
        pass  # No interrumpir operaciones si falla el guardado

@app.on_event("startup")
async def startup_event():
    """Inicialización del servidor"""
    print("=" * 60)
    print("🧬 Iniciando GenotypeR Backend")
    print("URL: http://localhost:8888")
    print("Docs: http://localhost:8888/docs")
    print("=" * 60)
    
    # Cargar datos persistidos
    load_data()
    
    print("=" * 60)
    print("GenotypeR Backend API v2.0")
    print(f"Parser disponible: {PARSER_AVAILABLE}")
    print("Servidor iniciado correctamente")
    print("=" * 60)

# Modificar el evento de cierre para guardar datos
@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar"""
    print("\n🛑 Cerrando servidor...")
    save_data()
    print("✅ Servidor cerrado correctamente")

if __name__ == "__main__":
    print("="*60)
    print("🧬 Iniciando GenotypeR Backend")
    print("URL: http://localhost:8888")
    print("Docs: http://localhost:8888/docs")
    print("Ready for genetic analysis!")
    print("="*60)
    uvicorn.run(app, host="127.0.0.1", port=8888)
