# backend/core/peak_detector.py

import numpy as np
from typing import List, Dict, Optional, Tuple
from scipy.signal import find_peaks, savgol_filter
from scipy import stats
import logging

class PeakDetector:
    """
    Detector de picos mejorado con umbrales adaptativos para archivos FSA reales
    """
    
    def __init__(self):
        # Tamaños estándar LIZ-500
        self.liz_500_sizes = [35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500]
        
        # Marcadores STR actualizados con rangos más flexibles
        self.str_markers_info = {
            'D3S1358': {
                'channel': 1, 
                'size_range': (95, 175),  # Ampliado
                'repeat': 4,
                'typical_alleles': {12: 114, 13: 118, 14: 122, 15: 126, 16: 130, 17: 134, 18: 138}
            },
            'vWA': {
                'channel': 1,
                'size_range': (145, 215),  # Ampliado
                'repeat': 4,
                'typical_alleles': {14: 169, 15: 173, 16: 177, 17: 181, 18: 185, 19: 189}
            },
            'D16S539': {
                'channel': 1,
                'size_range': (215, 285),  # Ampliado
                'repeat': 4,
                'typical_alleles': {9: 240, 10: 244, 11: 248, 12: 252, 13: 256}
            },
            'CSF1PO': {
                'channel': 2,
                'size_range': (275, 345),  # Ampliado
                'repeat': 4,
                'typical_alleles': {10: 305, 11: 309, 12: 313, 13: 317}
            },
            'TPOX': {
                'channel': 2,
                'size_range': (215, 275),  # Ampliado
                'repeat': 4,
                'typical_alleles': {8: 238, 9: 242, 10: 246, 11: 250}
            },
            # ... otros marcadores con rangos ampliados ...
        }
    
    def detect_peaks_adaptive(self, data: np.ndarray, channel_info: Dict = None) -> List[Dict]:
        """
        Detecta picos con umbrales adaptativos basados en las características de los datos
        """
        if len(data) == 0:
            return []
        
        # Convertir a numpy array si no lo es
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        
        # Calcular estadísticas robustas
        # Usar percentiles en lugar de media/std para ser más robusto a outliers
        p10 = np.percentile(data, 10)
        p15 = np.percentile(data, 15)
        p20 = np.percentile(data, 20)
        p25 = np.percentile(data, 25)
        p30 = np.percentile(data, 30)
        p35 = np.percentile(data, 35)
        p40 = np.percentile(data, 40)
        p45 = np.percentile(data, 45)
        p50 = np.percentile(data, 50)
        p55 = np.percentile(data, 55)
        p60 = np.percentile(data, 60)
        p65 = np.percentile(data, 65)
        p70 = np.percentile(data, 70)
        p75 = np.percentile(data, 75)
        p80 = np.percentile(data, 80)
        p85 = np.percentile(data, 85)
        p90 = np.percentile(data, 90)
        p95 = np.percentile(data, 95)
        p99 = np.percentile(data, 99)
        
        # Estimar el ruido de fondo usando MAD (Median Absolute Deviation)
        mad = np.median(np.abs(data - p50))
        noise_estimate = mad * 1.4826  # Factor para convertir MAD a std
        
        print(f"Estadísticas de datos:")
        print(f"  - Rango: [{np.min(data):.1f}, {np.max(data):.1f}]")
        print(f"  - Percentiles: P10={p10:.1f}, P50={p50:.1f}, P90={p90:.1f}, P99={p99:.1f}")
        print(f"  - Ruido estimado (MAD): {noise_estimate:.1f}")
        
        # Determinar umbrales adaptativos
        # Usar un umbral basado en el ruido de fondo
        min_height_adaptive = max(
            p50 + 5 * noise_estimate,  # 5 sigmas sobre la mediana
            p75,  # Al menos el percentil 75
            20  # Valor mínimo absoluto
        )
        
        # Si el canal es LIZ (size standard), usar umbrales más bajos
        if channel_info and channel_info.get('dye_name') == 'LIZ':
            min_height_adaptive = max(p50 + 3 * noise_estimate, p75)
        
        prominence_adaptive = max(2 * noise_estimate, (p90 - p10) * 0.1)
        
        print(f"  - Umbral altura: {min_height_adaptive:.1f}")
        print(f"  - Prominencia mínima: {prominence_adaptive:.1f}")
        
        # Aplicar suavizado adaptativo
        window_length = min(21, len(data) // 100)  # Ventana proporcional al tamaño
        if window_length % 2 == 0:
            window_length += 1
        if window_length >= 5:
            try:
                smoothed = savgol_filter(data, window_length=window_length, polyorder=3)
            except:
                smoothed = data
        else:
            smoothed = data
        
        # Detectar picos con parámetros adaptativos
        peaks, properties = find_peaks(
            smoothed,
            height=min_height_adaptive,
            distance=10,  # Distancia mínima entre picos
            prominence=prominence_adaptive,
            width=1  # Ancho mínimo más permisivo
        )
        
        print(f"  - Picos detectados (inicial): {len(peaks)}")
        
        # Si no se detectan suficientes picos, intentar con umbrales más bajos
        if len(peaks) < 5 and channel_info and channel_info.get('dye_name') != 'LIZ':
            # Segundo intento con umbrales más permisivos
            min_height_relaxed = max(p50 + 3 * noise_estimate, p70, 10)
            prominence_relaxed = noise_estimate
            
            peaks, properties = find_peaks(
                smoothed,
                height=min_height_relaxed,
                distance=8,
                prominence=prominence_relaxed
            )
            print(f"  - Picos detectados (relajado): {len(peaks)}")
        
        # Crear lista de picos con información detallada
        peak_list = []
        for i, peak_pos in enumerate(peaks):
            peak_height = float(data[peak_pos])
            
            # Calcular área del pico
            start = max(0, peak_pos - 15)
            end = min(len(data), peak_pos + 15)
            area = np.trapz(data[start:end] - p50)  # Restar baseline
            
            # Calcular SNR local
            local_start = max(0, peak_pos - 50)
            local_end = min(len(data), peak_pos + 50)
            local_baseline = np.median(data[local_start:local_end])
            snr = (peak_height - local_baseline) / (noise_estimate + 1e-6)
            
            # Solo incluir picos con SNR razonable
            if snr >= 3:  # SNR mínimo de 3
                peak_list.append({
                    'position': int(peak_pos),
                    'height': peak_height,
                    'area': float(area),
                    'width': float(properties.get('widths', [10])[i] if i < len(properties.get('widths', [])) else 10),
                    'quality_score': float(snr),
                    'snr': float(snr),
                    'prominence': float(properties.get('prominences', [0])[i] if i < len(properties.get('prominences', [])) else 0)
                })
        
        # Filtrar picos por calidad
        peak_list = [p for p in peak_list if p['snr'] >= 3 and p['area'] > 0]
        
        # Ordenar por altura
        peak_list.sort(key=lambda x: x['height'], reverse=True)
        
        print(f"  - Picos finales (SNR>3): {len(peak_list)}")
        
        return peak_list
    
    def detect_peaks_all_channels(self, channels: Dict) -> Dict[str, List[Dict]]:
        """
        Detecta picos en todos los canales con umbrales adaptativos
        """
        peaks_data = {}
        
        for channel_key, channel_info in channels.items():
            if 'raw_data' not in channel_info:
                continue
                
            # No procesar el canal LIZ aquí (se procesa aparte)
            if channel_key == 'channel_5':
                continue
                
            raw_data = channel_info['raw_data']
            if isinstance(raw_data, np.ndarray):
                data_array = raw_data
            else:
                data_array = np.array(raw_data)
            
            print(f"\nProcesando {channel_key} ({channel_info.get('dye_name', 'Unknown')})")
            
            # Detectar picos con método adaptativo
            peaks = self.detect_peaks_adaptive(data_array, channel_info)
            
            peaks_data[channel_key] = peaks if peaks else []
        
        return peaks_data
    
    def process_size_standard(self, data: np.ndarray, expected_sizes: Optional[List[float]] = None) -> Dict:
        """
        Procesa el estándar de tamaños LIZ con detección mejorada
        """
        if expected_sizes is None:
            expected_sizes = self.liz_500_sizes
        
        print("\nProcesando estándar de tamaños LIZ...")
        
        # Usar detección adaptativa para LIZ
        channel_info = {'dye_name': 'LIZ', 'purpose': 'Size Standard'}
        peaks = self.detect_peaks_adaptive(data, channel_info)
        
        # Para LIZ, queremos los picos más prominentes
        # Filtrar por altura relativa
        if peaks:
            max_height = max(p['height'] for p in peaks)
            filtered_peaks = [p for p in peaks if p['height'] > max_height * 0.1]  # Al menos 10% del máximo
        else:
            filtered_peaks = []
        
        detected_count = len(filtered_peaks)
        expected_count = len(expected_sizes)
        
        print(f"Picos LIZ detectados: {detected_count} de {expected_count} esperados")
        
        # Intentar calibración con los picos disponibles
        if detected_count >= 6:  # Mínimo 6 picos para calibración razonable
            # Ordenar picos por posición
            filtered_peaks.sort(key=lambda x: x['position'])
            
            # Estrategia mejorada de asignación
            if detected_count >= expected_count * 0.8:  # Si tenemos al menos 80% de los picos
                # Asignación directa si el número es similar
                peak_positions = [p['position'] for p in filtered_peaks[:expected_count]]
                assigned_sizes = expected_sizes
            else:
                # Asignación proporcional
                peak_positions = [p['position'] for p in filtered_peaks]
                # Estimar qué fragmentos tenemos basándonos en la distribución
                # Usar interpolación para asignar tamaños
                indices = np.linspace(0, len(expected_sizes)-1, len(peak_positions))
                assigned_sizes = [expected_sizes[int(round(i))] for i in indices]
            
            # Calibración robusta usando RANSAC o similar
            if len(peak_positions) >= 3:
                # Intentar ajuste lineal robusto
                coeffs = np.polyfit(peak_positions, assigned_sizes[:len(peak_positions)], 1)
                
                # Calcular R²
                predicted = np.polyval(coeffs, peak_positions)
                residuals = assigned_sizes[:len(peak_positions)] - predicted
                ss_res = np.sum(residuals ** 2)
                ss_tot = np.sum((assigned_sizes[:len(peak_positions)] - np.mean(assigned_sizes[:len(peak_positions)])) ** 2)
                r_squared = 1 - (ss_res / (ss_tot + 1e-6))
                
                # Verificar calidad de calibración
                max_residual = np.max(np.abs(residuals))
                calibration_quality = 'good' if r_squared > 0.98 and max_residual < 5 else 'acceptable'
                
                # Asignar tamaños calibrados a todos los picos
                for peak in filtered_peaks:
                    peak['size'] = float(np.polyval(coeffs, peak['position']))
                
                return {
                    'status': 'calibrated',
                    'quality': calibration_quality,
                    'peaks': filtered_peaks,
                    'expected_sizes': expected_sizes,
                    'detected_count': detected_count,
                    'expected_count': expected_count,
                    'calibration': {
                        'slope': float(coeffs[0]),
                        'intercept': float(coeffs[1]),
                        'r_squared': float(r_squared),
                        'max_residual': float(max_residual)
                    }
                }
        
        # Si no hay suficientes picos, usar calibración por defecto
        print(f"Calibración por defecto - insuficientes picos ({detected_count})")
        
        # Estimar calibración basada en el rango de datos
        if len(data) > 0:
            # Asumir que el rango de datos corresponde aproximadamente a 35-500 bp
            data_range = len(data)
            estimated_slope = (500 - 35) / data_range
            estimated_intercept = 35
        else:
            estimated_slope = 0.075
            estimated_intercept = 20
        
        for peak in filtered_peaks:
            peak['size'] = float(peak['position'] * estimated_slope + estimated_intercept)
        
        return {
            'status': 'estimated',
            'peaks': filtered_peaks,
            'expected_sizes': expected_sizes,
            'detected_count': detected_count,
            'expected_count': expected_count,
            'calibration': {
                'slope': estimated_slope,
                'intercept': estimated_intercept,
                'r_squared': 0.0
            },
            'message': f'Calibración estimada - solo {detected_count} picos detectados'
        }
    
    def call_alleles(self, peaks_data: Dict, size_calibration: Optional[Dict] = None,
                    str_markers: Optional[Dict] = None) -> Dict[str, Dict]:
        """
        Llama alelos con criterios más flexibles
        """
        if str_markers is None:
            str_markers = self.str_markers_info
        
        alleles = {}
        
        print("\nLlamando alelos con criterios adaptativos...")
        
        # Si no hay calibración, usar una estimación
        if not size_calibration or size_calibration.get('r_squared', 0) < 0.9:
            print("Usando calibración estimada para llamado de alelos")
            size_calibration = {
                'slope': 0.075,
                'intercept': 20
            }
        
        for marker_name, marker_info in str_markers.items():
            channel_key = f"channel_{marker_info['channel']}"
            
            if channel_key not in peaks_data or not peaks_data[channel_key]:
                continue
            
            # Buscar picos en el rango del marcador (con margen adicional)
            marker_peaks = []
            size_range = marker_info['size_range']
            extended_range = (size_range[0] - 10, size_range[1] + 10)  # Margen de 10 bp
            
            for peak in peaks_data[channel_key]:
                # Convertir posición a tamaño
                size_bp = peak['position'] * size_calibration['slope'] + size_calibration['intercept']
                
                # Verificar si está en el rango extendido
                if extended_range[0] <= size_bp <= extended_range[1]:
                    marker_peaks.append({
                        'size': size_bp,
                        'height': peak['height'],
                        'position': peak['position'],
                        'quality': peak.get('quality_score', peak.get('snr', 0)),
                        'area': peak.get('area', 0)
                    })
            
            # Procesar picos del marcador
            if marker_peaks:
                # Ordenar por altura
                marker_peaks.sort(key=lambda x: x['height'], reverse=True)
                
                # Filtrar picos significativos
                if len(marker_peaks) > 1:
                    max_height = marker_peaks[0]['height']
                    # Mantener picos que sean al menos 20% del máximo
                    significant_peaks = [p for p in marker_peaks if p['height'] >= max_height * 0.2]
                else:
                    significant_peaks = marker_peaks
                
                # Tomar máximo 2 picos (diploides)
                selected_peaks = significant_peaks[:2]
                
                if len(selected_peaks) >= 2:
                    # Heterocigoto - verificar que los alelos sean diferentes
                    allele1 = self._size_to_allele_flexible(selected_peaks[0]['size'], marker_name, marker_info)
                    allele2 = self._size_to_allele_flexible(selected_peaks[1]['size'], marker_name, marker_info)
                    
                    # Si los alelos son muy similares, podría ser homocigoto con stutter
                    if abs(float(allele1) - float(allele2)) < 0.5:
                        # Probablemente homocigoto
                        alleles[marker_name] = {
                            'allele1': allele1,
                            'allele2': allele1,
                            'peaks': selected_peaks[:1],
                            'heterozygous': False,
                            'confidence': 'medium'
                        }
                    else:
                        alleles[marker_name] = {
                            'allele1': allele1,
                            'allele2': allele2,
                            'peaks': selected_peaks,
                            'heterozygous': True,
                            'confidence': 'high' if len(significant_peaks) == 2 else 'medium'
                        }
                    
                    print(f"  {marker_name}: {allele1} / {allele2}")
                    
                elif len(selected_peaks) == 1:
                    # Un solo pico - probablemente homocigoto
                    allele = self._size_to_allele_flexible(selected_peaks[0]['size'], marker_name, marker_info)
                    
                    alleles[marker_name] = {
                        'allele1': allele,
                        'allele2': allele,
                        'peaks': selected_peaks,
                        'heterozygous': False,
                        'confidence': 'low' if selected_peaks[0]['quality'] < 5 else 'medium'
                    }
                    
                    print(f"  {marker_name}: {allele} / {allele} (un solo pico)")
        
        print(f"\nTotal de marcadores con alelos llamados: {len(alleles)}")
        
        return alleles
    
    def _size_to_allele_flexible(self, size_bp: float, marker_name: str, marker_info: Dict) -> str:
        """
        Conversión flexible de tamaño a alelo
        """
        typical_alleles = marker_info.get('typical_alleles', {})
        repeat_length = marker_info.get('repeat', 4)
        
        # Si tenemos alelos típicos, buscar el más cercano
        if typical_alleles:
            best_match = None
            min_diff = float('inf')
            
            for allele_num, expected_size in typical_alleles.items():
                diff = abs(size_bp - expected_size)
                if diff < min_diff:
                    min_diff = diff
                    best_match = allele_num
            
            # Si la diferencia es menor a 3 bp, usar el alelo conocido
            if best_match is not None and min_diff < 3.0:
                return str(best_match)
        
        # Si no hay coincidencia, calcular basándose en el tamaño
        # Estimar el número de repeticiones
        if typical_alleles:
            # Usar el primer alelo típico como referencia
            ref_allele = min(typical_alleles.keys())
            ref_size = typical_alleles[ref_allele]
            
            size_diff = size_bp - ref_size
            repeat_diff = size_diff / repeat_length
            calculated_allele = ref_allele + repeat_diff
            
            # Redondear al 0.1 más cercano
            return f"{calculated_allele:.1f}"
        else:
            # Sin referencia, usar estimación genérica
            estimated_repeats = (size_bp - 100) / repeat_length + 10
            return f"{estimated_repeats:.1f}"
