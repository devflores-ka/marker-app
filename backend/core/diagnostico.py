# Script para verificar el estado del backend y los datos
# Ejecutar este script para diagnosticar el problema

import requests
import json

BASE_URL = "http://localhost:8888"

def check_backend():
    """Verificar estado del backend y datos"""
    
    print("="*60)
    print("🔍 Verificando Backend GenotypeR")
    print("="*60)
    
    # 1. Verificar salud del backend
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.ok:
            data = response.json()
            print("✅ Backend conectado")
            print(f"   - Proyectos: {data['stats']['projects']}")
            print(f"   - Muestras: {data['stats']['samples']}")
            print(f"   - Análisis en caché: {data['stats']['cached_analyses']}")
        else:
            print("❌ Error conectando al backend")
            return
    except Exception as e:
        print(f"❌ No se puede conectar al backend: {e}")
        return
    
    print("\n" + "-"*60 + "\n")
    
    # 2. Listar proyectos
    try:
        response = requests.get(f"{BASE_URL}/api/projects")
        if response.ok:
            projects = response.json()['projects']
            print(f"📁 Proyectos encontrados: {len(projects)}")
            
            for project in projects:
                print(f"\n   Proyecto: {project['name']} (ID: {project['id']})")
                print(f"   - Creado: {project['created_at']}")
                print(f"   - Muestras: {len(project.get('samples', []))}")
                
                # Obtener detalles del proyecto
                detail_response = requests.get(f"{BASE_URL}/api/projects/{project['id']}")
                if detail_response.ok:
                    project_data = detail_response.json()
                    samples_data = project_data.get('samples_data', [])
                    
                    print(f"   - Muestras en detalle: {len(samples_data)}")
                    
                    for sample in samples_data:
                        print(f"\n      Muestra: {sample['filename']}")
                        print(f"      - ID: {sample['id']}")
                        print(f"      - Estado: {sample['status']}")
                        print(f"      - Tiene fsa_data: {'fsa_data' in sample}")
                        
                        if 'fsa_data' in sample and sample['fsa_data']:
                            channels = sample['fsa_data'].get('channels', {})
                            print(f"      - Canales: {len(channels)}")
                            for ch_name, ch_info in channels.items():
                                print(f"        • {ch_name}: {ch_info.get('dye_name', 'Unknown')} - {ch_info.get('wavelength', 'Unknown')}")
                        
                        # Verificar endpoint individual
                        sample_response = requests.get(f"{BASE_URL}/api/samples/{sample['id']}")
                        if sample_response.ok:
                            print(f"      - ✅ Endpoint individual funciona")
                        else:
                            print(f"      - ❌ Error 404 en endpoint individual")
                
    except Exception as e:
        print(f"❌ Error obteniendo proyectos: {e}")
    
    print("\n" + "="*60)

def test_upload():
    """Probar subida de archivo de prueba"""
    print("\n🧪 Probando subida de archivo...")
    
    # Primero crear un proyecto de prueba
    form_data = {
        'name': 'Proyecto de Prueba',
        'description': 'Proyecto para verificar funcionamiento'
    }
    
    response = requests.post(f"{BASE_URL}/api/projects/create", data=form_data)
    if response.ok:
        project = response.json()['project']
        print(f"✅ Proyecto creado: {project['name']} (ID: {project['id']})")
        
        # Crear un archivo FSA de prueba (vacío por ahora)
        # En producción, usar un archivo FSA real
        print("⚠️  Nota: Para probar completamente, sube un archivo FSA real desde la interfaz")
        
        return project['id']
    else:
        print("❌ Error creando proyecto de prueba")
        return None

def fix_missing_data():
    """Intentar arreglar datos faltantes"""
    print("\n🔧 Intentando reparar datos...")
    
    # Esta función podría implementar lógica para:
    # 1. Re-procesar archivos FSA
    # 2. Reconstruir el caché de análisis
    # 3. Actualizar referencias de proyectos
    
    print("ℹ️  Para reparar los datos:")
    print("   1. Reinicia el backend")
    print("   2. Vuelve a subir los archivos FSA")
    print("   3. O implementa persistencia en base de datos")

if __name__ == "__main__":
    check_backend()
    
    # Preguntar si quiere crear proyecto de prueba
    response = input("\n¿Crear proyecto de prueba? (s/n): ")
    if response.lower() == 's':
        test_upload()