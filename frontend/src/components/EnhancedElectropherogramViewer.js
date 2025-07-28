import React, { useState, useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';
import { 
  Box, 
  Paper, 
  TextField, 
  Button, 
  Chip, 
  IconButton,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Slider,
  Grid,
  Alert,
  Tooltip,
  ToggleButton,
  ToggleButtonGroup,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  ZoomIn,
  ZoomOut,
  RestartAlt,
  Edit,
  Save,
  Cancel,
  CheckCircle,
  Warning,
  VisibilityOutlined,
  VisibilityOffOutlined,
  InfoOutlined
} from '@mui/icons-material';

// Configuración de marcadores STR
const STR_MARKERS = {
  'D3S1358': { channel: 1, color: '#1565C0', range: [100, 150] },
  'vWA': { channel: 1, color: '#1565C0', range: [150, 200] },
  'D16S539': { channel: 1, color: '#1565C0', range: [200, 250] },
  'CSF1PO': { channel: 2, color: '#2E7D32', range: [280, 320] },
  'TPOX': { channel: 2, color: '#2E7D32', range: [220, 260] },
  'D8S1179': { channel: 3, color: '#F57C00', range: [120, 170] },
  'D21S11': { channel: 3, color: '#F57C00', range: [180, 250] },
  'D18S51': { channel: 3, color: '#F57C00', range: [270, 360] },
  'D5S818': { channel: 4, color: '#C62828', range: [130, 170] },
  'D13S317': { channel: 4, color: '#C62828', range: [170, 210] },
  'D7S820': { channel: 4, color: '#C62828', range: [210, 250] },
  'FGA': { channel: 4, color: '#C62828', range: [310, 460] }
};

export default function EnhancedElectropherogramViewer({ sampleData, onAllelesUpdate }) {
  // Estados principales
  const [selectedChannel, setSelectedChannel] = useState('all');
  const [selectedMarker, setSelectedMarker] = useState('');
  const [showPeaks, setShowPeaks] = useState(true);
  const [showSizeStandard, setShowSizeStandard] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [alleles, setAlleles] = useState({});
  const [peakThreshold, setPeakThreshold] = useState(50);
  const [loading, setLoading] = useState(false);
  
  // Ref para el plot
  const plotRef = useRef(null);

  // Cargar alelos detectados
  useEffect(() => {
    if (sampleData?.alleles) {
      setAlleles(sampleData.alleles);
    }
  }, [sampleData]);

  // Preparar datos para visualización
  const prepareTraces = () => {
    if (!sampleData?.channels) return [];
    
    const traces = [];
    const channels = sampleData.channels;
    
    // Agregar canales de datos
    Object.entries(channels).forEach(([channelKey, channelData]) => {
      const channelNum = channelKey.split('_')[1];
      
      if (selectedChannel === 'all' || selectedChannel === channelKey) {
        const data = channelData.analyzed_data || channelData.raw_data;
        
        traces.push({
          x: Array.from({ length: data.length }, (_, i) => i),
          y: data,
          type: 'scatter',
          mode: 'lines',
          name: `Canal ${channelNum}`,
          line: { 
            color: channelData.color, 
            width: 1.5 
          },
          visible: true,
          hovertemplate: 'Posición: %{x}<br>Intensidad: %{y}<extra></extra>'
        });
        
        // Agregar picos si están habilitados
        if (showPeaks && sampleData.peaks?.[channelKey]) {
          const peaks = sampleData.peaks[channelKey].filter(
            peak => peak.height >= peakThreshold
          );
          
          traces.push({
            x: peaks.map(p => p.position),
            y: peaks.map(p => data[p.position]),
            type: 'scatter',
            mode: 'markers+text',
            name: `Picos Canal ${channelNum}`,
            marker: { 
              color: channelData.color,
              size: 8,
              symbol: 'triangle-up'
            },
            text: peaks.map(p => p.height.toFixed(0)),
            textposition: 'top center',
            textfont: { size: 10 },
            hovertemplate: 'Pico<br>Posición: %{x}<br>Altura: %{text}<extra></extra>'
          });
        }
      }
    });
    
    // Agregar estándar de tamaños si está habilitado
    if (showSizeStandard && sampleData.size_standard?.peaks) {
      const lizPeaks = sampleData.size_standard.peaks;
      const expectedSizes = sampleData.size_standard.expected_sizes || [];
      
      traces.push({
        x: lizPeaks.map(p => p.position),
        y: lizPeaks.map(p => p.height),
        type: 'scatter',
        mode: 'markers+text',
        name: 'LIZ-500',
        marker: { 
          color: '#FF6F00',
          size: 10,
          symbol: 'diamond'
        },
        text: expectedSizes.slice(0, lizPeaks.length).map(s => `${s}bp`),
        textposition: 'top center',
        hovertemplate: 'Estándar<br>Tamaño: %{text}<extra></extra>'
      });
    }
    
    // Resaltar región del marcador seleccionado
    if (selectedMarker && STR_MARKERS[selectedMarker]) {
      const marker = STR_MARKERS[selectedMarker];
      const maxY = Math.max(...traces.filter(t => t.y).flatMap(t => t.y));
      
      traces.push({
        x: [marker.range[0], marker.range[0], marker.range[1], marker.range[1]],
        y: [0, maxY * 1.1, maxY * 1.1, 0],
        fill: 'toself',
        fillcolor: 'rgba(158, 158, 158, 0.1)',
        line: { color: 'transparent' },
        type: 'scatter',
        mode: 'lines',
        name: selectedMarker,
        showlegend: false,
        hoverinfo: 'skip'
      });
    }
    
    return traces;
  };

  // Configuración del layout
  const layout = {
    title: {
      text: sampleData?.metadata?.sample_name || 'Electroferograma',
      font: { size: 18 }
    },
    xaxis: { 
      title: sampleData?.size_standard?.calibration ? 'Tamaño (bp)' : 'Posición (scans)',
      gridcolor: '#e0e0e0',
      zeroline: false,
      range: selectedMarker && STR_MARKERS[selectedMarker] 
        ? [STR_MARKERS[selectedMarker].range[0] - 20, STR_MARKERS[selectedMarker].range[1] + 20]
        : undefined
    },
    yaxis: { 
      title: 'RFU (Unidades de Fluorescencia Relativa)',
      gridcolor: '#e0e0e0',
      zeroline: true
    },
    paper_bgcolor: 'white',
    plot_bgcolor: 'white',
    height: 400,
    margin: { t: 50, r: 50, b: 50, l: 80 },
    hovermode: 'closest',
    showlegend: true,
    legend: {
      x: 1,
      y: 1,
      bgcolor: 'rgba(255, 255, 255, 0.8)',
      bordercolor: '#e0e0e0',
      borderwidth: 1
    }
  };

  // Manejar edición de alelos
  const handleAlleleEdit = (marker, alleleNum, value) => {
    setAlleles(prev => ({
      ...prev,
      [marker]: {
        ...prev[marker],
        [`allele${alleleNum}`]: value
      }
    }));
  };

  // Guardar cambios
  const handleSaveAlleles = () => {
    if (onAllelesUpdate) {
      onAllelesUpdate(alleles);
    }
    setEditMode(false);
  };

  // Resetear zoom
  const handleResetZoom = () => {
    setZoomLevel(1);
    setSelectedMarker('');
  };

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      {/* Controles superiores */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Canal</InputLabel>
          <Select
            value={selectedChannel}
            onChange={(e) => setSelectedChannel(e.target.value)}
            label="Canal"
          >
            <MenuItem value="all">Todos los canales</MenuItem>
            {sampleData?.channels && Object.keys(sampleData.channels).map(ch => (
              <MenuItem key={ch} value={ch}>
                Canal {ch.split('_')[1]}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Marcador STR</InputLabel>
          <Select
            value={selectedMarker}
            onChange={(e) => setSelectedMarker(e.target.value)}
            label="Marcador STR"
          >
            <MenuItem value="">Ninguno</MenuItem>
            {Object.keys(STR_MARKERS).map(marker => (
              <MenuItem key={marker} value={marker}>{marker}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Switch
              checked={showPeaks}
              onChange={(e) => setShowPeaks(e.target.checked)}
            />
          }
          label="Mostrar picos"
        />

        <FormControlLabel
          control={
            <Switch
              checked={showSizeStandard}
              onChange={(e) => setShowSizeStandard(e.target.checked)}
            />
          }
          label="Mostrar LIZ"
        />

        <Box sx={{ flexGrow: 1 }} />

        <Tooltip title="Resetear vista">
          <IconButton onClick={handleResetZoom}>
            <RestartAlt />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Gráfico principal */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Plot
          ref={plotRef}
          data={prepareTraces()}
          layout={layout}
          config={{
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToAdd: ['drawrect', 'eraseshape'],
            toImageButtonOptions: {
              format: 'png',
              filename: `electropherogram_${sampleData?.metadata?.sample_name}`
            }
          }}
          style={{ width: '100%', height: '400px' }}
        />
      )}

      {/* Control de umbral de picos */}
      {showPeaks && (
        <Box sx={{ mt: 2, px: 2 }}>
          <Typography variant="body2" gutterBottom>
            Umbral de detección de picos (RFU): {peakThreshold}
          </Typography>
          <Slider
            value={peakThreshold}
            onChange={(e, newValue) => setPeakThreshold(newValue)}
            min={0}
            max={500}
            step={10}
            marks={[
              { value: 0, label: '0' },
              { value: 100, label: '100' },
              { value: 300, label: '300' },
              { value: 500, label: '500' }
            ]}
          />
        </Box>
      )}

      <Divider sx={{ my: 3 }} />

      {/* Panel de alelos */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Alelos Detectados
          </Typography>
          <Button
            variant={editMode ? "contained" : "outlined"}
            startIcon={editMode ? <Save /> : <Edit />}
            onClick={editMode ? handleSaveAlleles : () => setEditMode(true)}
            size="small"
          >
            {editMode ? 'Guardar cambios' : 'Editar alelos'}
          </Button>
          {editMode && (
            <Button
              variant="outlined"
              startIcon={<Cancel />}
              onClick={() => {
                setEditMode(false);
                setAlleles(sampleData?.alleles || {});
              }}
              size="small"
              sx={{ ml: 1 }}
            >
              Cancelar
            </Button>
          )}
        </Box>

        <Grid container spacing={2}>
          {Object.entries(STR_MARKERS).map(([marker, info]) => {
            const markerAlleles = alleles[marker] || {};
            const hasAlleles = markerAlleles.allele1 || markerAlleles.allele2;
            
            return (
              <Grid item xs={12} sm={6} md={3} key={marker}>
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 2,
                    backgroundColor: selectedMarker === marker ? 'action.hover' : 'transparent',
                    cursor: 'pointer',
                    '&:hover': { backgroundColor: 'action.hover' }
                  }}
                  onClick={() => !editMode && setSelectedMarker(marker)}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box 
                      sx={{ 
                        width: 12, 
                        height: 12, 
                        borderRadius: '50%',
                        backgroundColor: info.color,
                        mr: 1
                      }} 
                    />
                    <Typography variant="subtitle2" fontWeight="bold">
                      {marker}
                    </Typography>
                    {hasAlleles && (
                      <CheckCircle 
                        sx={{ ml: 'auto', fontSize: 16, color: 'success.main' }} 
                      />
                    )}
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <TextField
                      size="small"
                      label="Alelo 1"
                      value={markerAlleles.allele1 || ''}
                      onChange={(e) => handleAlleleEdit(marker, 1, e.target.value)}
                      disabled={!editMode}
                      sx={{ flex: 1 }}
                      inputProps={{ style: { textAlign: 'center' } }}
                    />
                    <TextField
                      size="small"
                      label="Alelo 2"
                      value={markerAlleles.allele2 || ''}
                      onChange={(e) => handleAlleleEdit(marker, 2, e.target.value)}
                      disabled={!editMode}
                      sx={{ flex: 1 }}
                      inputProps={{ style: { textAlign: 'center' } }}
                    />
                  </Box>
                  
                  {markerAlleles.homozygote && (
                    <Chip 
                      label="Homocigoto" 
                      size="small" 
                      color="info"
                      sx={{ mt: 1 }}
                    />
                  )}
                </Paper>
              </Grid>
            );
          })}
        </Grid>
      </Box>

      {/* Métricas de calidad */}
      {sampleData?.quality_metrics && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Métricas de Calidad
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Calidad General
                </Typography>
                <Chip
                  label={sampleData.quality_metrics.overall_quality}
                  color={
                    sampleData.quality_metrics.overall_quality === 'excellent' ? 'success' :
                    sampleData.quality_metrics.overall_quality === 'good' ? 'primary' :
                    sampleData.quality_metrics.overall_quality === 'acceptable' ? 'warning' : 'error'
                  }
                  sx={{ mt: 1 }}
                />
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  SNR Promedio
                </Typography>
                <Typography variant="h6">
                  {sampleData.quality_metrics.average_snr?.toFixed(1) || 'N/A'}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Picos Detectados
                </Typography>
                <Typography variant="h6">
                  {Object.values(sampleData.peaks || {}).reduce((sum, peaks) => sum + peaks.length, 0)}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Marcadores Completos
                </Typography>
                <Typography variant="h6">
                  {Object.values(alleles).filter(a => a.allele1 && a.allele2).length} / {Object.keys(STR_MARKERS).length}
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Información adicional */}
      <Box sx={{ mt: 3, p: 2, bgcolor: 'info.lighter', borderRadius: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <InfoOutlined sx={{ mr: 1, color: 'info.main' }} />
          <Typography variant="subtitle2" color="info.main">
            Información del análisis
          </Typography>
        </Box>
        <Typography variant="caption" component="div">
          • Instrumento: {sampleData?.metadata?.instrument || 'Desconocido'}
        </Typography>
        <Typography variant="caption" component="div">
          • Fecha: {sampleData?.metadata?.run_date || 'No disponible'}
        </Typography>
        <Typography variant="caption" component="div">
          • Kit de tintes: {sampleData?.metadata?.dye_set || 'No especificado'}
        </Typography>
        {sampleData?.size_standard?.calibration && (
          <Typography variant="caption" component="div">
            • Calibración: R² = {sampleData.size_standard.calibration.r_squared?.toFixed(3) || 'N/A'}
          </Typography>
        )}
      </Box>
    </Paper>
  );
}