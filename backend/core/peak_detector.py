# backend/core/peak_detector.py
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.signal import savgol_filter, find_peaks
from scipy.ndimage import gaussian_filter1d
import logging

class PeakDetector:
    """
    Detector avanzado de picos para electroferogramas
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Parámetros de detección ajustables
        self.params = {
            'min_height_ratio': 0.05,  # Altura mínima como fracción del máximo
            'min_distance': 10,         # Distancia mínima entre picos
            'min_prominence_ratio': 0.025,  # Prominencia mínima
            'smoothing_window': 5,      # Ventana para suavizado
            'baseline_sigma': 50,       # Sigma para corrección de línea base
            'min_snr': 3.0,            # Relación señal/ruido mínima
        }
        
        # Estándar de tamaños LIZ-500
        self.liz_500_sizes = [35, 50, 75, 100, 139, 150, 160, 200, 250, 
                             300, 340, 350, 400, 450, 490, 500]
    
    def detect_peaks_all_channels(self, channels: Dict) -> Dict[str, List[Dict]]:
        """
        Detecta picos en todos los canales
        """
        peaks_data = {}
        
        for channel_name, channel_data in channels.items():
            if 'raw_data' not in channel_data:
                continue
            
            # Usar datos analizados si están disponibles, sino usar raw
            data = channel_data.get('analyzed_data', channel_data['raw_data'])
            
            # Detección de picos
            peaks = self.detect_peaks(data)
            
            # Filtrar picos por calidad
            filtered_peaks = self.filter_peaks_by_quality(data, peaks)
            
            # Agregar información del canal
            for peak in filtered_peaks:
                peak['channel'] = channel_name
                peak['dye'] = channel_data.get('dye_name', 'Unknown')
            
            peaks_data[channel_name] = filtered_peaks
        
        return peaks_data
    
    def detect_peaks(self, signal_data: np.ndarray, method: str = 'scipy') -> List[Dict]:
        """
        Detecta picos usando el método especificado
        """
        if method == 'scipy':
            return self._scipy_peak_detection(signal_data)
        elif method == 'derivative':
            return self._derivative_peak_detection(signal_data)
        else:
            return self._scipy_peak_detection(signal_data)
    
    def _scipy_peak_detection(self, signal_data: np.ndarray) -> List[Dict]:
        """
        Detección de picos usando scipy
        """
        # Pre-procesamiento
        smoothed = savgol_filter(signal_data, 
                               window_length=self.params['smoothing_window'], 
                               polyorder=2)
        baseline = gaussian_filter1d(smoothed, sigma=self.params['baseline_sigma'])
        corrected = smoothed - baseline
        
        # Normalizar
        if np.max(corrected) > 0:
            normalized = corrected / np.max(corrected)
        else:
            return []
        
        # Detectar picos
        min_height = self.params['min_height_ratio'] * np.max(normalized)
        peaks, properties = find_peaks(
            normalized,
            height=min_height,
            distance=self.params['min_distance'],
            prominence=min_height * 0.5
        )
        
        # Construir lista de picos
        peak_list = []
        for i, peak_idx in enumerate(peaks):
            peak_list.append({
                'position': int(peak_idx),
                'height': float(signal_data[peak_idx]),
                'height_normalized': float(normalized[peak_idx]),
                'prominence': float(properties['prominences'][i]),
                'width': float(properties.get('widths', [0])[i] if 'widths' in properties else 0),
                'area': self._calculate_peak_area(signal_data, peak_idx)
            })
        
        return peak_list
    
    def _derivative_peak_detection(self, signal_data: np.ndarray) -> List[Dict]:
        """
        Detección de picos basada en derivadas
        """
        # Suavizar señal
        smoothed = savgol_filter(signal_data, 
                               window_length=self.params['smoothing_window'], 
                               polyorder=2)
        
        # Calcular primera derivada
        first_derivative = np.gradient(smoothed)
        
        # Encontrar cruces por cero (cambios de signo)
        zero_crossings = np.where(np.diff(np.signbit(first_derivative)))[0]
        
        # Filtrar por criterios de amplitud y pendiente
        valid_peaks = []
        for crossing in zero_crossings:
            if 0 < crossing < len(smoothed) - 1:
                peak_height = smoothed[crossing]
                
                # Verificar que sea un máximo (derivada cambia de + a -)
                if first_derivative[crossing-1] > 0 and first_derivative[crossing+1] < 0:
                    # Calcular cambio de pendiente
                    slope_change = abs(first_derivative[crossing-1] - first_derivative[crossing+1])
                    
                    if peak_height > 100 and slope_change > 10:
                        valid_peaks.append({
                            'position': int(crossing),
                            'height': float(peak_height),
                            'slope_change': float(slope_change),
                            'area': self._calculate_peak_area(signal_data, crossing)
                        })
        
        return valid_peaks
    
    def filter_peaks_by_quality(self, data: np.ndarray, peaks: List[Dict], 
                              min_snr: Optional[float] = None) -> List[Dict]:
        """
        Filtra picos por criterios de calidad
        """
        if not peaks:
            return []
        
        if min_snr is None:
            min_snr = self.params['min_snr']
        
        # Calcular ruido de fondo (primeros 10% de los datos)
        baseline_region = data[:int(len(data)*0.1)]
        baseline_std = np.std(baseline_region) if len(baseline_region) > 0 else 1.0
        
        # Filtrar por SNR
        filtered = []
        for peak in peaks:
            snr = peak['height'] / (baseline_std + 1e-6)
            if snr >= min_snr:
                peak['snr'] = float(snr)
                peak['quality_score'] = self._calculate_peak_quality(peak, snr)
                filtered.append(peak)
        
        return filtered
    
    def _calculate_peak_area(self, data: np.ndarray, peak_pos: int, 
                           window: int = 10) -> float:
        """
        Calcula el área bajo el pico
        """
        start = max(0, peak_pos - window)
        end = min(len(data), peak_pos + window + 1)
        
        if end > start:
            peak_region = data[start:end]
            # Área simple usando regla del trapecio
            area = float(np.trapz(peak_region))
            return max(0, area)
        
        return 0.0
    
    def _calculate_peak_quality(self, peak: Dict, snr: float) -> float:
        """
        Calcula un puntaje de calidad para el pico
        """
        # Factores de calidad
        height_score = min(1.0, peak.get('height_normalized', 0))
        snr_score = min(1.0, snr / 10.0)  # Normalizar SNR
        prominence_score = min(1.0, peak.get('prominence', 0) / 0.5)
        
        # Puntaje combinado
        quality = (height_score * 0.3 + snr_score * 0.4 + prominence_score * 0.3)
        
        return float(quality * 100)  # Convertir a porcentaje
    
    def process_size_standard(self, liz_data: np.ndarray) -> Dict:
        """
        Procesa el estándar de tamaños LIZ
        """
        # Detectar picos en el estándar
        peaks = self.detect_peaks(liz_data)
        
        # Filtrar con criterios más estrictos para el estándar
        filtered_peaks = self.filter_peaks_by_quality(liz_data, peaks, min_snr=5.0)
        
        # Ordenar por posición
        filtered_peaks.sort(key=lambda x: x['position'])
        
        # Verificar si tenemos suficientes picos
        expected_count = len(self.liz_500_sizes)
        detected_count = len(filtered_peaks)
        
        if detected_count >= expected_count * 0.8:  # Al menos 80% detectados
            # Emparejar con tamaños esperados
            positions = [p['position'] for p in filtered_peaks[:expected_count]]
            
            # Regresión lineal para calibración
            coeffs = np.polyfit(positions, self.liz_500_sizes[:len(positions)], 1)
            
            # Calcular R²
            predicted = np.poly1d(coeffs)(positions)
            r_squared = 1 - (np.sum((self.liz_500_sizes[:len(positions)] - predicted)**2) / 
                           np.sum((self.liz_500_sizes[:len(positions)] - np.mean(self.liz_500_sizes[:len(positions)]))**2))
            
            return {
                'status': 'calibrated',
                'peaks': filtered_peaks,
                'expected_sizes': self.liz_500_sizes,
                'detected_count': detected_count,
                'expected_count': expected_count,
                'calibration': {
                    'slope': float(coeffs[0]),
                    'intercept': float(coeffs[1]),
                    'r_squared': float(r_squared)
                }
            }
        else:
            return {
                'status': 'insufficient_peaks',
                'peaks': filtered_peaks,
                'expected_sizes': self.liz_500_sizes,
                'detected_count': detected_count,
                'expected_count': expected_count,
                'message': f'Solo se detectaron {detected_count} de {expected_count} picos esperados'
            }
    
    def call_alleles(self, peaks_data: Dict, size_calibration: Optional[Dict] = None,
                    str_markers: Optional[Dict] = None) -> Dict[str, Dict]:
        """
        Llama alelos basándose en los picos detectados
        """
        if str_markers is None:
            # Usar marcadores por defecto
            str_markers = {
                'D3S1358': {'channel': 1, 'size_range': (100, 150), 'repeat': 4},
                'vWA': {'channel': 1, 'size_range': (150, 200), 'repeat': 4},
                'D16S539': {'channel': 1, 'size_range': (200, 250), 'repeat': 4},
                'CSF1PO': {'channel': 2, 'size_range': (280, 320), 'repeat': 4},
                'TPOX': {'channel': 2, 'size_range': (220, 260), 'repeat': 4},
            }
        
        alleles = {}
        
        for marker_name, marker_info in str_markers.items():
            channel_key = f"channel_{marker_info['channel']}"
            
            if channel_key not in peaks_data:
                continue
            
            # Buscar picos en el rango del marcador
            marker_peaks = []
            for peak in peaks_data[channel_key]:
                # Convertir posición a tamaño en bp
                if size_calibration:
                    size_bp = self._position_to_size(peak['position'], size_calibration)
                else:
                    size_bp = peak['position'] * 0.5  # Estimación aproximada
                
                # Verificar rango
                if marker_info['size_range'][0] <= size_bp <= marker_info['size_range'][1]:
                    marker_peaks.append({
                        'size': size_bp,
                        'height': peak['height'],
                        'position': peak['position'],
                        'quality': peak.get('quality_score', 0)
                    })
            
            # Seleccionar los 2 picos más altos
            if marker_peaks:
                marker_peaks.sort(key=lambda x: x['height'], reverse=True)
                
                if len(marker_peaks) >= 2:
                    allele1 = self._size_to_allele(marker_peaks[0]['size'], 
                                                  marker_info['repeat'])
                    allele2 = self._size_to_allele(marker_peaks[1]['size'], 
                                                  marker_info['repeat'])
                    
                    alleles[marker_name] = {
                        'allele1': allele1,
                        'allele2': allele2,
                        'peaks': marker_peaks[:2],
                        'heterozygous': allele1 != allele2
                    }
                elif len(marker_peaks) == 1:
                    allele = self._size_to_allele(marker_peaks[0]['size'], 
                                                marker_info['repeat'])
                    alleles[marker_name] = {
                        'allele1': allele,
                        'allele2': allele,
                        'peaks': marker_peaks,
                        'heterozygous': False
                    }
        
        return alleles
    
    def _position_to_size(self, position: int, calibration: Dict) -> float:
        """
        Convierte posición a tamaño usando calibración
        """
        return position * calibration['slope'] + calibration['intercept']
    
    def _size_to_allele(self, size_bp: float, repeat_length: int) -> str:
        """
        Convierte tamaño en bp a nomenclatura de alelo
        """
        # Calcular número de repeticiones
        allele_number = round(size_bp / repeat_length, 1)
        
        # Formatear según convención
        if allele_number == int(allele_number):
            return str(int(allele_number))
        else:
            # Microvariant (e.g., 9.3)
            return f"{allele_number:.1f}"  
