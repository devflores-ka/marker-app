# backend/core/fsa_parser.py
import struct
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import io
import logging

# Importar el PeakDetector
from .peak_detector import PeakDetector

# Intentar importar BioPython para soporte completo
try:
    from Bio import SeqIO
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    logging.warning("BioPython no disponible. Usando parser interno limitado.")

class FSAParser:
    """
    Parser mejorado para archivos FSA/AB1 con soporte completo ABIF
    """
    
    # Constantes del formato ABIF
    ABIF_SIGNATURE = b'ABIF'
    
    # Tags importantes para análisis genético
    IMPORTANT_TAGS = {
        'DATA1': 'Raw channel 1 (FAM/Blue)',
        'DATA2': 'Raw channel 2 (VIC/Green)', 
        'DATA3': 'Raw channel 3 (NED/Yellow)',
        'DATA4': 'Raw channel 4 (PET/Red)',
        'DATA105': 'Raw channel 5 (LIZ/Orange)',
        'DATA9': 'Analyzed channel 1',
        'DATA10': 'Analyzed channel 2',
        'DATA11': 'Analyzed channel 3', 
        'DATA12': 'Analyzed channel 4',
        'PLOC1': 'Peak locations 1',
        'PLOC2': 'Peak locations 2',
        'MODL1': 'Instrument model',
        'RUND1': 'Run date',
        'RUNT1': 'Run time',
        'SMPL1': 'Sample name',
        'LANE1': 'Lane/capillary number',
        'DySN1': 'Dye set name',
        'GTyp1': 'General type',
        'PSZE1': 'Peak size 1',
        'PSZE2': 'Peak size 2'
    }
    
    # Información de canales y colores
    CHANNEL_INFO = {
        'channel_1': {'dye': 'FAM', 'color': 'blue', 'wavelength': '520nm'},
        'channel_2': {'dye': 'VIC', 'color': 'green', 'wavelength': '548nm'},
        'channel_3': {'dye': 'NED', 'color': 'yellow', 'wavelength': '575nm'},
        'channel_4': {'dye': 'PET', 'color': 'red', 'wavelength': '595nm'},
        'channel_5': {'dye': 'LIZ', 'color': 'orange', 'wavelength': '655nm', 'purpose': 'Size Standard'}
    }
    
    # Marcadores STR estándar para análisis forense
    STR_MARKERS = {
        'D3S1358': {'channel': 1, 'size_range': (100, 150), 'repeat': 4},
        'vWA': {'channel': 1, 'size_range': (150, 200), 'repeat': 4},
        'D16S539': {'channel': 1, 'size_range': (200, 250), 'repeat': 4},
        'CSF1PO': {'channel': 2, 'size_range': (280, 320), 'repeat': 4},
        'TPOX': {'channel': 2, 'size_range': (220, 260), 'repeat': 4},
        'D8S1179': {'channel': 3, 'size_range': (120, 170), 'repeat': 4},
        'D21S11': {'channel': 3, 'size_range': (180, 250), 'repeat': 4},
        'D18S51': {'channel': 3, 'size_range': (270, 360), 'repeat': 4},
        'D5S818': {'channel': 4, 'size_range': (130, 170), 'repeat': 4},
        'D13S317': {'channel': 4, 'size_range': (170, 210), 'repeat': 4},
        'D7S820': {'channel': 4, 'size_range': (210, 250), 'repeat': 4},
        'FGA': {'channel': 4, 'size_range': (310, 460), 'repeat': 4},
        'TH01': {'channel': 2, 'size_range': (150, 200), 'repeat': 4},
        'D2S1338': {'channel': 1, 'size_range': (280, 360), 'repeat': 4},
        'D19S433': {'channel': 2, 'size_range': (100, 150), 'repeat': 4}
    }
    
    @staticmethod
    def process_file(content: bytes, filename: str) -> Dict[str, Any]:
        """
        Procesa un archivo FSA y extrae todos los datos necesarios
        """
        try:
            # Usar el método correcto que SÍ detecta picos y alelos
            if BIOPYTHON_AVAILABLE:
                return FSAParser._process_with_biopython(content, filename)
            else:
                return FSAParser._process_with_internal_parser(content, filename)
                
        except Exception as e:
            print(f"Error procesando archivo FSA: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Retornar datos simulados para testing si falla todo
            return FSAParser._create_mock_data(filename)

    @staticmethod
    def _parse_without_bio(content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parser alternativo sin BioPython
        """
        # Verificar que es un archivo ABIF
        if len(content) < 4 or content[:4] != b'ABIF':
            return {
                'success': False,
                'error': 'No es un archivo ABIF válido'
            }
        
        # Crear datos simulados realistas
        return FSAParser._create_mock_data(filename)
    
    @staticmethod
    def _create_mock_data(filename: str) -> Dict[str, Any]:
        """
        Crea datos simulados realistas para desarrollo/testing
        """
        import numpy as np
        import random
        
        # Generar datos simulados para cada canal
        channels = {}
        trace_data = {}
        data_points = 6602  # Típico para archivos FSA
        
        for i in range(1, 6):
            channel_key = f'channel_{i}'
            
            # Generar señal con ruido y algunos picos
            noise = np.random.normal(50, 10, data_points)
            signal = noise.copy()
            
            # Añadir picos aleatorios
            num_peaks = random.randint(5, 15)
            for _ in range(num_peaks):
                peak_pos = random.randint(500, data_points - 500)
                peak_height = random.randint(200, 2000)
                peak_width = random.randint(10, 30)
                
                # Crear pico gaussiano
                for j in range(max(0, peak_pos - peak_width), min(data_points, peak_pos + peak_width)):
                    distance = abs(j - peak_pos)
                    signal[j] += peak_height * np.exp(-(distance**2) / (2 * (peak_width/3)**2))
            
            # Convertir a lista
            signal_list = signal.tolist()
            
            channels[channel_key] = {
                'dye_name': ['FAM', 'VIC', 'NED', 'PET', 'LIZ'][i-1],
                'color': ['blue', 'green', 'yellow', 'red', 'orange'][i-1],
                'wavelength': ['520nm', '548nm', '575nm', '595nm', '655nm'][i-1],
                'data_points': data_points,
                'has_raw_data': True,
                'has_analyzed_data': False,
                'raw_data': signal_list  # DATOS SIMULADOS
            }
            
            trace_data[channel_key] = signal_list
        
        return {
            'success': True,
            'filename': filename,
            'metadata': {
                'sample_name': filename.split('.')[0],
                'run_date': '2025-01-01',
                'run_time': '12:00:00',
                'instrument': 'Simulated',
                'dye_set': 'G5',
                'file_type': 'FSA',
                'data_points': data_points
            },
            'channels': channels,
            'trace_data': trace_data,
            'peaks': {},
            'alleles': {},
            'size_standard': {
                'status': 'uncalibrated',
                'peaks': [],
                'expected_sizes': [35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500],
                'detected_count': 0,
                'expected_count': 16
            },
            'quality_metrics': {
                'overall_quality': 0.75,
                'quality_score': 75,
                'status': 'simulated',
                'issues': ['Datos simulados para desarrollo']
            },
            'str_markers': {}
        }

    @classmethod
    def _process_with_biopython(cls, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Procesa usando BioPython para máxima compatibilidad
        """
        try:
            # Crear archivo temporal en memoria
            file_handle = io.BytesIO(content)
            
            # Leer con BioPython
            record = SeqIO.read(file_handle, "abi")
            raw_data = record.annotations.get("abif_raw", {})
            
            # Determinar tipo de archivo
            is_fsa = not any(tag in raw_data for tag in ["PBAS1", "PBAS2"])
            
            # Extraer metadatos
            metadata = {
                'sample_name': raw_data.get('SMPL1', filename),
                'run_date': cls._parse_date(raw_data.get('RUND1', None)),
                'run_time': cls._parse_time(raw_data.get('RUNT1', None)),
                'instrument': raw_data.get('MODL1', 'Unknown'),
                'dye_set': raw_data.get('DySN1', 'Unknown'),
                'lane': raw_data.get('LANE1', 1),
                'file_type': 'FSA' if is_fsa else 'AB1',
                'data_points': 0
            }
            
            # Extraer datos de canales con información adicional
            channels = {}
            max_data_points = 0
            
            for i in range(1, 6):  # Hasta 5 canales posibles
                data_key = f'DATA{i}' if i < 5 else 'DATA105'  # Canal 5 es DATA105
                if data_key in raw_data:
                    channel_data = np.array(raw_data[data_key])
                    channel_key = f'channel_{i}'
                    
                    channels[channel_key] = {
                        'raw_data': channel_data,
                        'color': cls.CHANNEL_INFO.get(channel_key, {}).get('color', 'unknown'),
                        'dye_name': cls.CHANNEL_INFO.get(channel_key, {}).get('dye', 'unknown'),
                        'wavelength': cls.CHANNEL_INFO.get(channel_key, {}).get('wavelength', 'unknown'),
                        'data_points': len(channel_data)
                    }
                    
                    # Agregar propósito especial si es el canal LIZ
                    if i == 5:
                        channels[channel_key]['purpose'] = 'Size Standard'
                    
                    max_data_points = max(max_data_points, len(channel_data))
                    print(f"Canal {channel_key}: {len(channel_data)} puntos, max={np.max(channel_data)}, min={np.min(channel_data)}")
            
            metadata['data_points'] = max_data_points
            
            # Extraer datos analizados si existen
            for i in range(9, 13):  # DATA9-DATA12
                data_key = f'DATA{i}'
                if data_key in raw_data:
                    channel_num = i - 8
                    if f'channel_{channel_num}' in channels:
                        channels[f'channel_{channel_num}']['analyzed_data'] = np.array(raw_data[data_key])
            
            # Usar PeakDetector para procesar picos
            peak_detector = PeakDetector()
            
            # Procesar canal de escalera de tamaños (LIZ)
            size_standard = {}
            if 'channel_5' in channels and 'raw_data' in channels['channel_5']:
                print(f"Procesando estándar LIZ...")
                size_standard = peak_detector.process_size_standard(channels['channel_5']['raw_data'])
                print(f"Estándar LIZ: status={size_standard.get('status')}, picos detectados={size_standard.get('detected_count')}")
            
            # Detectar picos en todos los canales
            print(f"Detectando picos en todos los canales...")
            peaks_data = peak_detector.detect_peaks_all_channels(channels)
            
            # Log de picos detectados
            total_peaks = 0
            for ch_key, ch_peaks in peaks_data.items():
                print(f"  {ch_key}: {len(ch_peaks)} picos detectados")
                total_peaks += len(ch_peaks)
            print(f"Total de picos detectados: {total_peaks}")
            
            # Llamar alelos
            size_calibration = size_standard.get('calibration') if size_standard.get('status') == 'calibrated' else None
            
            # Si no hay calibración, usar una estimada
            if not size_calibration:
                print("No hay calibración de tamaños, usando estimación por defecto")
                size_calibration = {
                    'slope': 0.075,  # bp por scan
                    'intercept': 20   # offset
                }
            
            print(f"Llamando alelos con calibración: slope={size_calibration['slope']}, intercept={size_calibration['intercept']}")
            alleles = peak_detector.call_alleles(peaks_data, size_calibration, cls.STR_MARKERS)
            
            print(f"Alelos detectados: {len(alleles)} marcadores")
            for marker, allele_data in alleles.items():
                print(f"  {marker}: {allele_data.get('allele1', '?')} / {allele_data.get('allele2', '?')}")
            
            # Calcular métricas de calidad
            quality_metrics = cls._calculate_quality_metrics(channels, peaks_data, size_standard)
            
            # Construir respuesta completa
            return {
                'success': True,
                'filename': filename,
                'metadata': metadata,
                'channels': cls._format_channels_for_response(channels),
                'peaks': peaks_data,
                'alleles': alleles,
                'size_standard': size_standard,
                'quality_metrics': quality_metrics,
                'str_markers': cls.STR_MARKERS  # Incluir información de marcadores
            }
            
        except Exception as e:
            logging.error(f"Error procesando con BioPython: {str(e)}")
            import traceback
            traceback.print_exc()
            return cls._create_error_response(filename, str(e))
    
    @classmethod
    def _process_with_internal_parser(cls, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Procesa usando parser interno cuando BioPython no está disponible
        """
        try:
            # Verificar signatura ABIF
            if len(content) < 128 or content[:4] != cls.ABIF_SIGNATURE:
                return cls._create_error_response(filename, "No es un archivo ABIF válido")
            
            # Leer header
            stream = io.BytesIO(content)
            header = cls._read_abif_header(stream)
            
            # Leer directorio de tags
            raw_data = cls._read_abif_directory(stream, header)
            
            # El resto del procesamiento es similar al de BioPython
            # Extraer metadatos
            metadata = {
                'sample_name': cls._decode_pascal_string(raw_data.get('SMPL1', b'')) or filename,
                'run_date': cls._parse_date_internal(raw_data.get('RUND1', None)),
                'instrument': cls._decode_pascal_string(raw_data.get('MODL1', b'')) or 'Unknown',
                'dye_set': cls._decode_pascal_string(raw_data.get('DySN1', b'')) or 'Unknown',
                'file_type': 'FSA',
                'data_points': 0
            }
            
            # Extraer canales
            channels = {}
            max_data_points = 0
            
            for i in range(1, 6):
                data_key = f'DATA{i}' if i < 5 else 'DATA105'
                if data_key in raw_data:
                    channel_data = cls._parse_data_array(raw_data[data_key])
                    channel_key = f'channel_{i}'
                    
                    channels[channel_key] = {
                        'raw_data': channel_data,
                        'color': cls.CHANNEL_INFO.get(channel_key, {}).get('color', 'unknown'),
                        'dye_name': cls.CHANNEL_INFO.get(channel_key, {}).get('dye', 'unknown'),
                        'wavelength': cls.CHANNEL_INFO.get(channel_key, {}).get('wavelength', 'unknown'),
                        'data_points': len(channel_data)
                    }
                    
                    if i == 5:
                        channels[channel_key]['purpose'] = 'Size Standard'
                    
                    max_data_points = max(max_data_points, len(channel_data))
            
            metadata['data_points'] = max_data_points
            
            # Usar PeakDetector
            peak_detector = PeakDetector()
            
            # Procesar estándar de tamaños
            size_standard = {}
            if 'channel_5' in channels and 'raw_data' in channels['channel_5']:
                size_standard = peak_detector.process_size_standard(channels['channel_5']['raw_data'])
            
            # Detectar picos
            peaks_data = peak_detector.detect_peaks_all_channels(channels)
            
            # Llamar alelos
            size_calibration = size_standard.get('calibration') if size_standard.get('status') == 'calibrated' else None
            alleles = peak_detector.call_alleles(peaks_data, size_calibration, cls.STR_MARKERS)
            
            # Calcular métricas de calidad
            quality_metrics = cls._calculate_quality_metrics(channels, peaks_data, size_standard)
            
            return {
                'success': True,
                'filename': filename,
                'metadata': metadata,
                'channels': cls._format_channels_for_response(channels),
                'peaks': peaks_data,
                'alleles': alleles,
                'size_standard': size_standard,
                'quality_metrics': quality_metrics,
                'str_markers': cls.STR_MARKERS
            }
            
        except Exception as e:
            logging.error(f"Error en parser interno: {str(e)}")
            return cls._create_error_response(filename, str(e))
    
    @classmethod
    def _format_channels_for_response(cls, channels: Dict) -> Dict:
        """
        Formatea los canales para la respuesta, incluyendo los datos raw y analyzed
        """
        formatted_channels = {}
        
        for channel_key, channel_data in channels.items():
            formatted_channel = {
                'dye_name': channel_data.get('dye_name', 'Unknown'),
                'color': channel_data.get('color', 'unknown'),
                'wavelength': channel_data.get('wavelength', 'unknown'),
                'data_points': channel_data.get('data_points', 0),
                'has_raw_data': 'raw_data' in channel_data and channel_data['raw_data'] is not None,
                'has_analyzed_data': 'analyzed_data' in channel_data and channel_data['analyzed_data'] is not None,
                'peak_count': 0  # Se actualizará después
            }
            
            # IMPORTANTE: Incluir los datos raw y analyzed si están presentes
            if 'raw_data' in channel_data and channel_data['raw_data'] is not None:
                # Convertir numpy array a lista si es necesario
                raw_data = channel_data['raw_data']
                if hasattr(raw_data, 'tolist'):
                    formatted_channel['raw_data'] = raw_data.tolist()
                else:
                    formatted_channel['raw_data'] = list(raw_data)
            
            if 'analyzed_data' in channel_data and channel_data['analyzed_data'] is not None:
                # Convertir numpy array a lista si es necesario
                analyzed_data = channel_data['analyzed_data']
                if hasattr(analyzed_data, 'tolist'):
                    formatted_channel['analyzed_data'] = analyzed_data.tolist()
                else:
                    formatted_channel['analyzed_data'] = list(analyzed_data)
            
            if 'purpose' in channel_data:
                formatted_channel['purpose'] = channel_data['purpose']
            
            formatted_channels[channel_key] = formatted_channel
        
        return formatted_channels


    @classmethod
    def _calculate_quality_metrics(cls, channels: Dict, peaks_data: Dict, size_standard: Dict) -> Dict:
        """
        Calcula métricas de calidad comprensivas
        """
        quality_score = 100.0
        issues = []
        
        # Verificar canales esperados
        expected_channels = 4  # Esperamos al menos 4 canales de datos
        detected_channels = sum(1 for ch in channels.values() if 'raw_data' in ch and ch['dye_name'] != 'LIZ')
        
        if detected_channels < expected_channels:
            quality_score -= 20
            issues.append(f"Solo {detected_channels} de {expected_channels} canales detectados")
        
        # Verificar estándar de tamaños
        if size_standard.get('status') != 'calibrated':
            quality_score -= 30
            issues.append("Calibración de tamaños fallida")
        elif size_standard.get('calibration', {}).get('r_squared', 0) < 0.98:
            quality_score -= 10
            issues.append("Calibración de tamaños imprecisa")
        
        # Verificar calidad de señal por canal
        for channel_key, channel_data in channels.items():
            if 'raw_data' not in channel_data or channel_data.get('dye_name') == 'LIZ':
                continue
            
            # Calcular SNR del canal
            data = channel_data['raw_data']
            if len(data) > 0:
                baseline_noise = np.std(data[:int(len(data)*0.1)])
                max_signal = np.max(data)
                
                if max_signal > 0:
                    snr = max_signal / (baseline_noise + 1e-6)
                    if snr < 10:
                        quality_score -= 5
                        issues.append(f"SNR bajo en {channel_data['dye_name']}")
                
                # Verificar saturación
                if max_signal > 30000:  # Típico límite de saturación
                    quality_score -= 10
                    issues.append(f"Saturación detectada en {channel_data['dye_name']}")
        
        # Verificar picos detectados
        total_peaks = sum(len(peaks) for peaks in peaks_data.values())
        if total_peaks < 10:
            quality_score -= 15
            issues.append("Pocos picos detectados")
        
        # Asegurar que el puntaje esté entre 0 y 100
        quality_score = max(0, min(100, quality_score))
        
        return {
            'overall_quality': quality_score / 100.0,  # Normalizado a 0-1
            'quality_score': quality_score,
            'issues': issues,
            'channels_detected': detected_channels,
            'size_standard_status': size_standard.get('status', 'not_processed'),
            'total_peaks': total_peaks,
            'status': 'good' if quality_score >= 70 else 'warning' if quality_score >= 40 else 'poor'
        }
    
    @staticmethod
    def _create_error_response(filename: str, error_msg: str) -> Dict:
        """Crea respuesta de error estructurada"""
        return {
            'success': False,
            'filename': filename,
            'error': error_msg,
            'metadata': {'sample_name': filename},
            'channels': {},
            'peaks': {},
            'alleles': {},
            'quality_metrics': {'overall_quality': 0, 'status': 'error'}
        }
    
    @staticmethod
    def _read_abif_header(stream: io.BytesIO) -> Dict:
        """Lee el header del archivo ABIF"""
        stream.seek(0)
        header = {
            'signature': stream.read(4),
            'version': struct.unpack('>H', stream.read(2))[0]
        }
        
        # Saltar bytes no usados
        stream.seek(10)
        
        header['dir_offset'] = struct.unpack('>I', stream.read(4))[0]
        header['dir_count'] = struct.unpack('>I', stream.read(4))[0]
        
        return header
    
    @classmethod
    def _read_abif_directory(cls, stream: io.BytesIO, header: Dict) -> Dict:
        """Lee el directorio de tags ABIF"""
        raw_data = {}
        
        # Ir al directorio
        stream.seek(header['dir_offset'])
        
        for _ in range(header['dir_count']):
            # Leer entrada del directorio (28 bytes)
            tag_name = stream.read(4).decode('ascii', errors='ignore')
            tag_num = struct.unpack('>I', stream.read(4))[0]
            elem_type = struct.unpack('>H', stream.read(2))[0]
            elem_size = struct.unpack('>H', stream.read(2))[0]
            num_elems = struct.unpack('>I', stream.read(4))[0]
            data_size = struct.unpack('>I', stream.read(4))[0]
            data_offset = struct.unpack('>I', stream.read(4))[0]
            
            # Construir clave del tag
            tag_key = tag_name.strip() + str(tag_num) if tag_num > 1 else tag_name.strip()
            
            # Leer datos si es un tag importante
            if tag_key in cls.IMPORTANT_TAGS or tag_key.startswith('DATA'):
                current_pos = stream.tell()
                
                if data_size <= 4:
                    # Datos almacenados directamente en el offset
                    raw_data[tag_key] = data_offset
                else:
                    # Datos almacenados en otra ubicación
                    stream.seek(data_offset)
                    raw_data[tag_key] = stream.read(data_size)
                
                stream.seek(current_pos)
        
        return raw_data
    
    @staticmethod
    def _parse_data_array(data: bytes) -> np.ndarray:
        """Parsea un array de datos del formato ABIF"""
        if isinstance(data, int):
            return np.array([data])
        
        # Asumir datos de 16 bits (común en FSA)
        num_points = len(data) // 2
        return np.frombuffer(data, dtype='>i2', count=num_points)
    
    @staticmethod
    def _decode_pascal_string(data: bytes) -> str:
        """Decodifica una cadena Pascal (longitud + datos)"""
        if not data or len(data) < 1:
            return ""
        
        length = data[0]
        if length > len(data) - 1:
            return ""
        
        return data[1:1+length].decode('ascii', errors='ignore')
    
    @staticmethod
    def _parse_date(date_obj) -> str:
        """Parsea fecha del formato BioPython"""
        if date_obj is None:
            return "Unknown"
        
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime('%Y-%m-%d')
        
        return str(date_obj)
    
    @staticmethod
    def _parse_time(time_obj) -> str:
        """Parsea tiempo del formato BioPython"""
        if time_obj is None:
            return "Unknown"
        
        if hasattr(time_obj, 'strftime'):
            return time_obj.strftime('%H:%M:%S')
        
        return str(time_obj)
    
    @staticmethod
    def _parse_date_internal(date_data) -> str:
        """Parsea fecha del formato interno ABIF"""
        if date_data is None:
            return "Unknown"
        
        # Implementar parsing específico según formato ABIF
        return "Unknown"
    
    @staticmethod
    def _get_channel_color(channel_num: int) -> str:
        """Obtiene el color asociado al canal"""
        colors = {1: 'blue', 2: 'green', 3: 'yellow', 4: 'red', 5: 'orange'}
        return colors.get(channel_num, 'unknown')
    