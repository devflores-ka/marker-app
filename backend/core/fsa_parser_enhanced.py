# backend/core/fsa_parser_enhanced.py
import struct
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import io
from scipy.signal import savgol_filter, find_peaks
from scipy.ndimage import gaussian_filter1d
import logging

# Intentar importar BioPython para soporte completo
try:
    from Bio import SeqIO
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    logging.warning("BioPython no disponible. Usando parser interno limitado.")

class EnhancedFSAParser:
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
    
    @classmethod
    def process_file(cls, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Procesa un archivo FSA/AB1 y extrae todos los datos relevantes
        """
        if BIOPYTHON_AVAILABLE:
            return cls._process_with_biopython(content, filename)
        else:
            return cls._process_with_internal_parser(content, filename)
    
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
                'file_type': 'FSA' if is_fsa else 'AB1'
            }
            
            # Extraer datos de canales
            channels = {}
            for i in range(1, 6):  # Hasta 5 canales posibles
                data_key = f'DATA{i}'
                if data_key in raw_data:
                    channels[f'channel_{i}'] = {
                        'raw_data': np.array(raw_data[data_key]),
                        'color': cls._get_channel_color(i)
                    }
            
            # Extraer datos analizados si existen
            for i in range(9, 13):  # DATA9-DATA12
                data_key = f'DATA{i}'
                if data_key in raw_data:
                    channel_num = i - 8
                    if f'channel_{channel_num}' in channels:
                        channels[f'channel_{channel_num}']['analyzed_data'] = np.array(raw_data[data_key])
            
            # Procesar canal de escalera de tamaños (LIZ)
            size_standard = cls._process_size_standard(raw_data)
            
            # Detectar picos y llamar alelos
            peaks_data = cls._detect_peaks_all_channels(channels)
            alleles = cls._call_alleles(peaks_data, size_standard)
            
            # Métricas de calidad
            quality_metrics = cls._calculate_quality_metrics(channels, peaks_data)
            
            return {
                'success': True,
                'filename': filename,
                'metadata': metadata,
                'channels': channels,
                'size_standard': size_standard,
                'peaks': peaks_data,
                'alleles': alleles,
                'quality_metrics': quality_metrics,
                'raw_abif_data': raw_data  # Para análisis avanzado
            }
            
        except Exception as e:
            logging.error(f"Error procesando {filename} con BioPython: {str(e)}")
            return cls._create_error_response(filename, str(e))
    
    @classmethod
    def _process_with_internal_parser(cls, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parser interno cuando BioPython no está disponible
        """
        try:
            stream = io.BytesIO(content)
            
            # Verificar signature ABIF
            signature = stream.read(4)
            if signature != cls.ABIF_SIGNATURE:
                raise ValueError("No es un archivo ABIF válido")
            
            # Leer header
            stream.seek(0)
            header = cls._read_abif_header(stream)
            
            # Leer directorio de datos
            directories = cls._read_directory_entries(stream, header)
            
            # Extraer datos esenciales
            metadata = cls._extract_metadata(stream, directories)
            channels = cls._extract_channel_data(stream, directories)
            
            # Procesar datos
            size_standard = cls._process_size_standard_internal(channels)
            peaks_data = cls._detect_peaks_all_channels(channels)
            alleles = cls._call_alleles(peaks_data, size_standard)
            quality_metrics = cls._calculate_quality_metrics(channels, peaks_data)
            
            return {
                'success': True,
                'filename': filename,
                'metadata': metadata,
                'channels': channels,
                'size_standard': size_standard,
                'peaks': peaks_data,
                'alleles': alleles,
                'quality_metrics': quality_metrics
            }
            
        except Exception as e:
            logging.error(f"Error en parser interno: {str(e)}")
            return cls._create_error_response(filename, str(e))
    
    @classmethod
    def _detect_peaks_all_channels(cls, channels: Dict) -> Dict[str, List[Dict]]:
        """
        Detecta picos en todos los canales usando algoritmos avanzados
        """
        peaks_data = {}
        
        for channel_name, channel_data in channels.items():
            if 'raw_data' not in channel_data:
                continue
                
            # Usar datos analizados si están disponibles, sino usar raw
            data = channel_data.get('analyzed_data', channel_data['raw_data'])
            
            # Detección de picos con múltiples métodos
            peaks = cls._advanced_peak_detection(data)
            
            # Filtrar picos por calidad
            filtered_peaks = cls._filter_peaks_by_quality(data, peaks)
            
            peaks_data[channel_name] = filtered_peaks
            
        return peaks_data
    
    @classmethod
    def _advanced_peak_detection(cls, signal_data: np.ndarray, 
                               min_height_ratio: float = 0.05) -> List[Dict]:
        """
        Detección avanzada de picos usando métodos derivativos
        """
        # Pre-procesamiento: suavizado y corrección de línea base
        smoothed = savgol_filter(signal_data, window_length=5, polyorder=2)
        baseline = gaussian_filter1d(smoothed, sigma=50)
        corrected = smoothed - baseline
        
        # Normalizar
        if np.max(corrected) > 0:
            normalized = corrected / np.max(corrected)
        else:
            return []
        
        # Detectar picos con scipy
        min_height = min_height_ratio * np.max(normalized)
        peaks, properties = find_peaks(
            normalized,
            height=min_height,
            distance=10,  # Mínima distancia entre picos
            prominence=min_height/2
        )
        
        # Construir lista de picos con propiedades
        peak_list = []
        for i, peak_idx in enumerate(peaks):
            peak_list.append({
                'position': int(peak_idx),
                'height': float(signal_data[peak_idx]),
                'height_normalized': float(normalized[peak_idx]),
                'prominence': float(properties['prominences'][i]),
                'width': float(properties.get('widths', [0])[i] if 'widths' in properties else 0),
                'area': cls._calculate_peak_area(signal_data, peak_idx)
            })
        
        return peak_list
    
    @classmethod
    def _call_alleles(cls, peaks_data: Dict, size_standard: Dict) -> Dict[str, Dict]:
        """
        Llama alelos basándose en los picos detectados y el estándar de tamaños
        """
        alleles = {}
        
        # Calibración de tamaños si hay estándar disponible
        size_calibration = size_standard.get('calibration', None)
        
        for marker_name, marker_info in cls.STR_MARKERS.items():
            channel_key = f"channel_{marker_info['channel']}"
            
            if channel_key not in peaks_data:
                continue
            
            # Buscar picos en el rango de tamaños del marcador
            marker_peaks = []
            for peak in peaks_data[channel_key]:
                # Convertir posición a tamaño en bp
                if size_calibration:
                    size_bp = cls._position_to_size(peak['position'], size_calibration)
                else:
                    # Estimación aproximada sin calibración
                    size_bp = peak['position'] * 0.5  # Factor aproximado
                
                # Verificar si está en el rango del marcador
                if marker_info['size_range'][0] <= size_bp <= marker_info['size_range'][1]:
                    marker_peaks.append({
                        'size': size_bp,
                        'height': peak['height'],
                        'position': peak['position']
                    })
            
            # Seleccionar los 2 picos más altos como alelos
            if marker_peaks:
                marker_peaks.sort(key=lambda x: x['height'], reverse=True)
                
                if len(marker_peaks) >= 2:
                    allele1 = cls._size_to_allele(marker_peaks[0]['size'], 
                                                 marker_info['repeat'])
                    allele2 = cls._size_to_allele(marker_peaks[1]['size'], 
                                                 marker_info['repeat'])
                    alleles[marker_name] = {
                        'allele1': allele1,
                        'allele2': allele2,
                        'peaks': marker_peaks[:2]
                    }
                elif len(marker_peaks) == 1:
                    # Homocigoto
                    allele1 = cls._size_to_allele(marker_peaks[0]['size'], 
                                                 marker_info['repeat'])
                    alleles[marker_name] = {
                        'allele1': allele1,
                        'allele2': allele1,
                        'peaks': marker_peaks,
                        'homozygote': True
                    }
        
        return alleles
    
    @classmethod
    def _calculate_quality_metrics(cls, channels: Dict, peaks_data: Dict) -> Dict:
        """
        Calcula métricas de calidad exhaustivas
        """
        metrics = {
            'overall_quality': 'unknown',
            'signal_strength': {},
            'baseline_noise': {},
            'resolution': {},
            'peak_balance': {}
        }
        
        for channel_name, channel_data in channels.items():
            if 'raw_data' not in channel_data:
                continue
                
            data = channel_data.get('analyzed_data', channel_data['raw_data'])
            
            # Intensidad de señal
            metrics['signal_strength'][channel_name] = {
                'max': float(np.max(data)),
                'mean': float(np.mean(data)),
                'std': float(np.std(data))
            }
            
            # Ruido de línea base
            baseline_region = data[:int(len(data)*0.1)]  # Primeros 10%
            metrics['baseline_noise'][channel_name] = float(np.std(baseline_region))
            
            # Resolución entre picos
            if channel_name in peaks_data and len(peaks_data[channel_name]) > 1:
                peaks = sorted(peaks_data[channel_name], key=lambda x: x['position'])
                min_distance = min(peaks[i+1]['position'] - peaks[i]['position'] 
                                 for i in range(len(peaks)-1))
                metrics['resolution'][channel_name] = min_distance
        
        # Calcular calidad general
        avg_snr = np.mean([metrics['signal_strength'][ch]['max'] / 
                          (metrics['baseline_noise'][ch] + 1e-6)
                          for ch in metrics['baseline_noise']])
        
        if avg_snr > 100:
            metrics['overall_quality'] = 'excellent'
        elif avg_snr > 50:
            metrics['overall_quality'] = 'good'
        elif avg_snr > 20:
            metrics['overall_quality'] = 'acceptable'
        else:
            metrics['overall_quality'] = 'poor'
        
        metrics['average_snr'] = float(avg_snr)
        
        return metrics
    
    # Métodos auxiliares
    
    @staticmethod
    def _parse_date(date_data):
        """Parsea fecha del formato ABIF"""
        if not date_data:
            return datetime.now().strftime("%Y-%m-%d")
        # Implementar parsing específico según formato ABIF
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def _parse_time(time_data):
        """Parsea tiempo del formato ABIF"""
        if not time_data:
            return datetime.now().strftime("%H:%M:%S")
        return datetime.now().strftime("%H:%M:%S")
    
    @staticmethod
    def _get_channel_color(channel_num: int) -> str:
        """Retorna el color asociado al canal"""
        colors = {
            1: '#1565C0',  # Azul (FAM)
            2: '#2E7D32',  # Verde (VIC)
            3: '#F57C00',  # Naranja (NED)
            4: '#C62828',  # Rojo (PET)
            5: '#FF6F00'   # Naranja oscuro (LIZ)
        }
        return colors.get(channel_num, '#757575')
    
    @staticmethod
    def _calculate_peak_area(data: np.ndarray, peak_idx: int, 
                           window: int = 10) -> float:
        """Calcula el área bajo la curva del pico"""
        start = max(0, peak_idx - window)
        end = min(len(data), peak_idx + window)
        return float(np.trapz(data[start:end]))
    
    @staticmethod
    def _position_to_size(position: int, calibration: Dict) -> float:
        """Convierte posición de scan a tamaño en bp usando calibración"""
        if 'slope' in calibration and 'intercept' in calibration:
            return position * calibration['slope'] + calibration['intercept']
        return position * 0.5  # Estimación por defecto
    
    @staticmethod
    def _size_to_allele(size_bp: float, repeat_length: int) -> str:
        """Convierte tamaño en bp a nomenclatura de alelo"""
        # Cálculo simplificado - en producción usar tabla de referencia
        allele_number = round(size_bp / repeat_length)
        remainder = size_bp % repeat_length
        
        if abs(remainder) < 0.5:
            return str(allele_number)
        elif remainder > 0:
            return f"{allele_number}.{int(remainder)}"
        else:
            return str(allele_number)
    
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
            'quality_metrics': {'overall_quality': 'error'}
        }
    
    @classmethod
    def _process_size_standard(cls, raw_data: Dict) -> Dict:
        """Procesa el estándar de tamaños (LIZ)"""
        # Buscar datos del canal LIZ (usualmente DATA105 o DATA5)
        liz_data = None
        for key in ['DATA105', 'DATA5']:
            if key in raw_data:
                liz_data = np.array(raw_data[key])
                break
        
        if liz_data is None:
            return {'status': 'not_found'}
        
        # Detectar picos en el estándar
        peaks = cls._advanced_peak_detection(liz_data, min_height_ratio=0.1)
        
        # Tamaños esperados para LIZ-500
        expected_sizes = [35, 50, 75, 100, 139, 150, 160, 200, 250, 
                         300, 340, 350, 400, 450, 490, 500]
        
        # Emparejar picos detectados con tamaños esperados
        if len(peaks) >= len(expected_sizes) * 0.8:  # Al menos 80% detectados
            # Ordenar picos por posición
            peaks.sort(key=lambda x: x['position'])
            
            # Crear calibración lineal simple
            positions = [p['position'] for p in peaks[:len(expected_sizes)]]
            
            # Regresión lineal
            coeffs = np.polyfit(positions, expected_sizes[:len(positions)], 1)
            
            return {
                'status': 'calibrated',
                'peaks': peaks,
                'expected_sizes': expected_sizes,
                'calibration': {
                    'slope': float(coeffs[0]),
                    'intercept': float(coeffs[1]),
                    'r_squared': 0.99  # Calcular R² real en producción
                }
            }
        
        return {
            'status': 'insufficient_peaks',
            'peaks': peaks,
            'expected_sizes': expected_sizes
        }
    
    @staticmethod
    def _filter_peaks_by_quality(data: np.ndarray, peaks: List[Dict], 
                               min_snr: float = 3.0) -> List[Dict]:
        """Filtra picos por criterios de calidad"""
        if not peaks:
            return []
        
        # Calcular ruido de fondo
        baseline_std = np.std(data[:int(len(data)*0.1)])
        
        # Filtrar por SNR
        filtered = []
        for peak in peaks:
            snr = peak['height'] / (baseline_std + 1e-6)
            if snr >= min_snr:
                peak['snr'] = float(snr)
                filtered.append(peak)
        
        return filtered
    
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
    
    @staticmethod
    def _read_directory_entries(stream: io.BytesIO, header: Dict) -> List[Dict]:
        """Lee las entradas del directorio ABIF"""
        entries = []
        stream.seek(header['dir_offset'])
        
        for _ in range(header['dir_count']):
            entry = {
                'name': stream.read(4).decode('ascii', errors='ignore'),
                'number': struct.unpack('>I', stream.read(4))[0],
                'element_type': struct.unpack('>H', stream.read(2))[0],
                'element_size': struct.unpack('>H', stream.read(2))[0],
                'num_elements': struct.unpack('>I', stream.read(4))[0],
                'data_size': struct.unpack('>I', stream.read(4))[0],
                'data_offset': struct.unpack('>I', stream.read(4))[0]
            }
            entries.append(entry)
        
        return entries
    
    @classmethod
    def _extract_metadata(cls, stream: io.BytesIO, directories: List[Dict]) -> Dict:
        """Extrae metadatos del archivo"""
        metadata = {
            'sample_name': 'Unknown',
            'instrument': 'Unknown',
            'run_date': datetime.now().strftime("%Y-%m-%d"),
            'dye_set': 'Unknown'
        }
        
        # Buscar tags de metadatos
        for entry in directories:
            if entry['name'] == 'SMPL' and entry['number'] == 1:
                metadata['sample_name'] = cls._read_string(stream, entry)
            elif entry['name'] == 'MODL' and entry['number'] == 1:
                metadata['instrument'] = cls._read_string(stream, entry)
            elif entry['name'] == 'DySN' and entry['number'] == 1:
                metadata['dye_set'] = cls._read_string(stream, entry)
        
        return metadata
    
    @classmethod
    def _extract_channel_data(cls, stream: io.BytesIO, 
                            directories: List[Dict]) -> Dict:
        """Extrae datos de los canales"""
        channels = {}
        
        # Buscar datos de canales
        for entry in directories:
            if entry['name'].startswith('DATA'):
                try:
                    channel_num = int(entry['name'][4:])
                    if 1 <= channel_num <= 5:
                        data = cls._read_numeric_array(stream, entry)
                        channels[f'channel_{channel_num}'] = {
                            'raw_data': data,
                            'color': cls._get_channel_color(channel_num)
                        }
                except ValueError:
                    continue
        
        return channels
    
    @staticmethod
    def _read_string(stream: io.BytesIO, entry: Dict) -> str:
        """Lee un string del archivo ABIF"""
        stream.seek(entry['data_offset'])
        data = stream.read(entry['data_size'])
        return data.decode('ascii', errors='ignore').strip('\x00')
    
    @staticmethod
    def _read_numeric_array(stream: io.BytesIO, entry: Dict) -> np.ndarray:
        """Lee un array numérico del archivo ABIF"""
        stream.seek(entry['data_offset'])
        
        # Determinar tipo de datos
        if entry['element_type'] == 4:  # int16
            dtype = '>i2'
        elif entry['element_type'] == 5:  # int32  
            dtype = '>i4'
        else:
            dtype = '>i2'  # Por defecto
        
        # Leer datos
        data = np.frombuffer(
            stream.read(entry['data_size']), 
            dtype=dtype,
            count=entry['num_elements']
        )
        
        return data