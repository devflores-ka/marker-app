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
  Divider,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Card,
  CardContent
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
  InfoOutlined,
  ExpandMore,
  Science,
  BubbleChart,
  Assessment,
  Timeline,
  Storage,
  Speed,
  Biotech,
  Analytics,
  Download
} from '@mui/icons-material';

// Configuración de marcadores STR
const STR_MARKERS = {
  'D3S1358': { channel: 1, color: '#1565C0', range: [100, 150], repeat: 4 },
  'vWA': { channel: 1, color: '#1565C0', range: [150, 200], repeat: 4 },
  'D16S539': { channel: 1, color: '#1565C0', range: [200, 250], repeat: 4 },
  'CSF1PO': { channel: 2, color: '#2E7D32', range: [280, 320], repeat: 4 },
  'TPOX': { channel: 2, color: '#2E7D32', range: [220, 260], repeat: 4 },
  'D8S1179': { channel: 3, color: '#F57C00', range: [120, 170], repeat: 4 },
  'D21S11': { channel: 3, color: '#F57C00', range: [180, 250], repeat: 4 },
  'D18S51': { channel: 3, color: '#F57C00', range: [270, 360], repeat: 4 },
  'D5S818': { channel: 4, color: '#C62828', range: [130, 170], repeat: 4 },
  'D13S317': { channel: 4, color: '#C62828', range: [170, 210], repeat: 4 },
  'D7S820': { channel: 4, color: '#C62828', range: [210, 250], repeat: 4 },
  'FGA': { channel: 4, color: '#C62828', range: [310, 460], repeat: 4 }
};

// Función para formatear valores numéricos
const formatNumber = (num, decimals = 2) => {
  if (typeof num !== 'number') return 'N/A';
  return num.toFixed(decimals);
};

export default function ComprehensiveElectropherogramViewer({ sampleId, onUpdate }) {
  // Estados principales
  const [sampleData, setSampleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTab, setSelectedTab] = useState(0);
  
  // Estados de visualización
  const [selectedChannel, setSelectedChannel] = useState('all');
  const [selectedMarker, setSelectedMarker] = useState('');
  const [showPeaks, setShowPeaks] = useState(true);
  const [showSizeStandard, setShowSizeStandard] = useState(false);
  const [showRawData, setShowRawData] = useState(true);
  const [showAnalyzedData, setShowAnalyzedData] = useState(false);
  const [peakThreshold, setPeakThreshold] = useState(50);
  const [zoomRegion, setZoomRegion] = useState(null);
  
  // Estados de edición
  const [editMode, setEditMode] = useState(false);
  const [editedAlleles, setEditedAlleles] = useState({});
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  // Cargar datos
  useEffect(() => {
    loadSampleData();
  }, [sampleId]);

  const loadSampleData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`http://localhost:8888/api/samples/${sampleId}`);
      if (!response.ok) throw new Error('Error cargando datos');
      
      const data = await response.json();
      setSampleData(data.analysis);
      setEditedAlleles(data.analysis.alleles || {});
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Preparar datos para el gráfico
  const prepareTraces = () => {
    if (!sampleData?.channels) return [];
    
    const traces = [];
    const channels = sampleData.channels;
    
    Object.entries(channels).forEach(([channelKey, channelData]) => {
      if (selectedChannel !== 'all' && selectedChannel !== channelKey) return;
      
      const channelNum = channelKey.split('_')[1];
      const color = channelData.color || '#666666';
      
      // Datos crudos
      if (showRawData && channelData.raw_data) {
        const data = channelData.raw_data;
        traces.push({
          x: Array.from({ length: data.length }, (_, i) => i),
          y: data,
          type: 'scatter',
          mode: 'lines',
          name: `Canal ${channelNum} (Raw)`,
          line: { color: color, width: 1 },
          opacity: showAnalyzedData ? 0.5 : 1,
          visible: true
        });
      }
      
      // Datos analizados
      if (showAnalyzedData && channelData.analyzed_data) {
        const data = channelData.analyzed_data;
        traces.push({
          x: Array.from({ length: data.length }, (_, i) => i),
          y: data,
          type: 'scatter',
          mode: 'lines',
          name: `Canal ${channelNum} (Analizado)`,
          line: { color: color, width: 2 },
          visible: true
        });
      }
      
      // Picos detectados
      if (showPeaks && sampleData.peaks?.[channelKey]) {
        const data = channelData.analyzed_data || channelData.raw_data;
        const peaks = sampleData.peaks[channelKey].filter(p => p.height >= peakThreshold);
        
        traces.push({
          x: peaks.map(p => p.position),
          y: peaks.map(p => data[p.position]),
          type: 'scatter',
          mode: 'markers+text',
          name: `Picos Canal ${channelNum}`,
          marker: { 
            color: color,
            size: 10,
            symbol: 'triangle-up',
            line: { color: 'white', width: 1 }
          },
          text: peaks.map(p => `${p.height.toFixed(0)}\nSNR: ${p.snr?.toFixed(1) || 'N/A'}`),
          textposition: 'top center',
          textfont: { size: 9 },
          hovertemplate: 
            'Pico #%{pointNumber}<br>' +
            'Posición: %{x}<br>' +
            'Altura: %{text}<br>' +
            'Prominencia: %{customdata[0]:.1f}<br>' +
            'Ancho: %{customdata[1]:.1f}<extra></extra>',
          customdata: peaks.map(p => [p.prominence || 0, p.width || 0])
        });
      }
    });
    
    // Estándar de tamaños LIZ
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
          size: 12,
          symbol: 'diamond',
          line: { color: 'white', width: 2 }
        },
        text: expectedSizes.slice(0, lizPeaks.length).map(s => `${s}bp`),
        textposition: 'top center'
      });
    }
    
    // Región del marcador seleccionado
    if (selectedMarker && STR_MARKERS[selectedMarker]) {
      const marker = STR_MARKERS[selectedMarker];
      const maxY = Math.max(...traces.filter(t => t.y).flatMap(t => t.y));
      
      traces.push({
        x: [marker.range[0], marker.range[0], marker.range[1], marker.range[1]],
        y: [0, maxY * 1.1, maxY * 1.1, 0],
        fill: 'toself',
        fillcolor: 'rgba(100, 100, 100, 0.1)',
        line: { color: 'rgba(100, 100, 100, 0.3)', dash: 'dot' },
        type: 'scatter',
        mode: 'lines',
        name: `Región ${selectedMarker}`,
        showlegend: false,
        hoverinfo: 'skip'
      });
    }
    
    return traces;
  };

  // Layout del gráfico
  const getLayout = () => {
    const hasCalibration = sampleData?.size_standard?.calibration;
    let xTitle = 'Posición (scans)';
    let xRange = undefined;
    
    if (hasCalibration && selectedMarker && STR_MARKERS[selectedMarker]) {
      xTitle = 'Tamaño (bp)';
      const marker = STR_MARKERS[selectedMarker];
      xRange = [marker.range[0] - 20, marker.range[1] + 20];
    } else if (zoomRegion) {
      xRange = zoomRegion;
    }
    
    return {
      title: {
        text: `${sampleData?.metadata?.sample_name || 'Electroferograma'} - ${sampleData?.metadata?.instrument || ''}`,
        font: { size: 16 }
      },
      xaxis: { 
        title: xTitle,
        gridcolor: '#e0e0e0',
        zeroline: false,
        range: xRange
      },
      yaxis: { 
        title: 'RFU (Unidades de Fluorescencia Relativa)',
        gridcolor: '#e0e0e0',
        zeroline: true
      },
      paper_bgcolor: '#fafafa',
      plot_bgcolor: 'white',
      height: 500,
      margin: { t: 50, r: 50, b: 60, l: 80 },
      hovermode: 'closest',
      showlegend: true,
      legend: {
        x: 1.02,
        y: 1,
        bgcolor: 'rgba(255, 255, 255, 0.9)',
        bordercolor: '#e0e0e0',
        borderwidth: 1,
        font: { size: 11 }
      },
      annotations: sampleData?.quality_metrics?.overall_quality ? [{
        xref: 'paper',
        yref: 'paper',
        x: 0.02,
        y: 0.98,
        text: `Calidad: ${sampleData.quality_metrics.overall_quality.toUpperCase()}`,
        showarrow: false,
        bgcolor: sampleData.quality_metrics.overall_quality === 'excellent' ? '#4caf50' :
                 sampleData.quality_metrics.overall_quality === 'good' ? '#2196f3' :
                 sampleData.quality_metrics.overall_quality === 'acceptable' ? '#ff9800' : '#f44336',
        bordercolor: 'white',
        borderwidth: 2,
        font: { color: 'white', size: 12 }
      }] : []
    };
  };

  // Guardar cambios de alelos
  const handleSaveAlleles = async () => {
    try {
      const response = await fetch(`http://localhost:8888/api/samples/${sampleId}/alleles`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editedAlleles)
      });
      
      if (response.ok) {
        setEditMode(false);
        setUnsavedChanges(false);
        if (onUpdate) onUpdate();
      }
    } catch (err) {
      console.error('Error guardando alelos:', err);
    }
  };

  // Manejar cambios en alelos
  const handleAlleleChange = (marker, alleleNum, value) => {
    setEditedAlleles(prev => ({
      ...prev,
      [marker]: {
        ...prev[marker],
        [`allele${alleleNum}`]: value
      }
    }));
    setUnsavedChanges(true);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error cargando datos: {error}
      </Alert>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 0, mb: 3 }}>
      {/* Header con información principal */}
      <Box sx={{ p: 3, bgcolor: 'primary.main', color: 'white' }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Biotech sx={{ mr: 1 }} />
              {sampleData?.metadata?.sample_name || 'Muestra sin nombre'}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              {sampleData?.filename} • {sampleData?.metadata?.run_date} • {sampleData?.metadata?.run_time}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">{sampleData?.channels ? Object.keys(sampleData.channels).length : 0}</Typography>
                  <Typography variant="caption">Canales</Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">
                    {sampleData?.peaks ? Object.values(sampleData.peaks).reduce((sum, p) => sum + p.length, 0) : 0}
                  </Typography>
                  <Typography variant="caption">Picos Totales</Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">
                    {sampleData?.alleles ? Object.keys(sampleData.alleles).length : 0}
                  </Typography>
                  <Typography variant="caption">Marcadores</Typography>
                </Box>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Box>

      {/* Tabs de navegación */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={selectedTab} onChange={(e, v) => setSelectedTab(v)}>
          <Tab icon={<Timeline />} label="Electroferograma" />
          <Tab icon={<Storage />} label="Datos de Alelos" />
          <Tab icon={<Analytics />} label="Análisis Detallado" />
          <Tab icon={<Assessment />} label="Métricas de Calidad" />
          <Tab icon={<Science />} label="Datos Técnicos" />
        </Tabs>
      </Box>

      {/* Panel de Electroferograma */}
      {selectedTab === 0 && (
        <Box sx={{ p: 3 }}>
          {/* Controles superiores */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={8}>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Canal</InputLabel>
                    <Select
                      value={selectedChannel}
                      onChange={(e) => setSelectedChannel(e.target.value)}
                      label="Canal"
                    >
                      <MenuItem value="all">Todos</MenuItem>
                      {sampleData?.channels && Object.keys(sampleData.channels).map(ch => (
                        <MenuItem key={ch} value={ch}>Canal {ch.split('_')[1]}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <FormControl fullWidth size="small">
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
                </Grid>
                <Grid item xs={6} sm={3}>
                  <FormControlLabel
                    control={<Switch checked={showPeaks} onChange={(e) => setShowPeaks(e.target.checked)} />}
                    label="Picos"
                  />
                </Grid>
                <Grid item xs={6} sm={3}>
                  <FormControlLabel
                    control={<Switch checked={showSizeStandard} onChange={(e) => setShowSizeStandard(e.target.checked)} />}
                    label="LIZ-500"
                  />
                </Grid>
              </Grid>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                <ToggleButtonGroup
                  size="small"
                  value={showRawData ? 'raw' : 'analyzed'}
                  exclusive
                  onChange={(e, v) => {
                    setShowRawData(v === 'raw');
                    setShowAnalyzedData(v === 'analyzed');
                  }}
                >
                  <ToggleButton value="raw">Datos Crudos</ToggleButton>
                  <ToggleButton value="analyzed">Analizados</ToggleButton>
                </ToggleButtonGroup>
                <Tooltip title="Resetear vista">
                  <IconButton onClick={() => { setSelectedMarker(''); setZoomRegion(null); }}>
                    <RestartAlt />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>
          </Grid>

          {/* Gráfico principal */}
          <Paper variant="outlined" sx={{ p: 1, mb: 2 }}>
            <Plot
              data={prepareTraces()}
              layout={getLayout()}
              config={{
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToAdd: ['drawrect', 'eraseshape'],
                toImageButtonOptions: {
                  format: 'png',
                  filename: `electropherogram_${sampleData?.metadata?.sample_name}`
                }
              }}
              style={{ width: '100%', height: '500px' }}
            />
          </Paper>

          {/* Control de umbral */}
          {showPeaks && (
            <Box sx={{ px: 2 }}>
              <Typography variant="body2" gutterBottom>
                Umbral de detección: {peakThreshold} RFU
              </Typography>
              <Slider
                value={peakThreshold}
                onChange={(e, v) => setPeakThreshold(v)}
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
        </Box>
      )}

      {/* Panel de Datos de Alelos */}
      {selectedTab === 1 && (
        <Box sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Alelos Detectados</Typography>
            <Box>
              {editMode ? (
                <>
                  <Button variant="contained" onClick={handleSaveAlleles} startIcon={<Save />} sx={{ mr: 1 }}>
                    Guardar
                  </Button>
                  <Button variant="outlined" onClick={() => { setEditMode(false); setEditedAlleles(sampleData.alleles || {}); }}>
                    Cancelar
                  </Button>
                </>
              ) : (
                <Button variant="outlined" onClick={() => setEditMode(true)} startIcon={<Edit />}>
                  Editar Alelos
                </Button>
              )}
            </Box>
          </Box>

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Marcador</TableCell>
                  <TableCell>Canal</TableCell>
                  <TableCell>Rango (bp)</TableCell>
                  <TableCell>Alelo 1</TableCell>
                  <TableCell>Alelo 2</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell>Picos</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(STR_MARKERS).map(([marker, info]) => {
                  const alleleData = editedAlleles[marker] || {};
                  const peaksInMarker = alleleData.peaks || [];
                  
                  return (
                    <TableRow key={marker}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{ width: 16, height: 16, bgcolor: info.color, borderRadius: '50%', mr: 1 }} />
                          <strong>{marker}</strong>
                        </Box>
                      </TableCell>
                      <TableCell>{info.channel}</TableCell>
                      <TableCell>{info.range[0]}-{info.range[1]}</TableCell>
                      <TableCell>
                        {editMode ? (
                          <TextField
                            size="small"
                            value={alleleData.allele1 || ''}
                            onChange={(e) => handleAlleleChange(marker, 1, e.target.value)}
                            sx={{ width: 80 }}
                          />
                        ) : (
                          alleleData.allele1 || '-'
                        )}
                      </TableCell>
                      <TableCell>
                        {editMode ? (
                          <TextField
                            size="small"
                            value={alleleData.allele2 || ''}
                            onChange={(e) => handleAlleleChange(marker, 2, e.target.value)}
                            sx={{ width: 80 }}
                          />
                        ) : (
                          alleleData.allele2 || '-'
                        )}
                      </TableCell>
                      <TableCell>
                        {alleleData.allele1 && alleleData.allele2 ? (
                          <Chip label="Completo" color="success" size="small" />
                        ) : alleleData.allele1 || alleleData.allele2 ? (
                          <Chip label="Parcial" color="warning" size="small" />
                        ) : (
                          <Chip label="Sin llamar" color="default" size="small" />
                        )}
                      </TableCell>
                      <TableCell>
                        {peaksInMarker.length > 0 ? (
                          <Tooltip title={`Tamaños: ${peaksInMarker.map(p => p.size?.toFixed(1) + 'bp').join(', ')}`}>
                            <Chip label={`${peaksInMarker.length} picos`} size="small" variant="outlined" />
                          </Tooltip>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Panel de Análisis Detallado */}
      {selectedTab === 2 && (
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Análisis Detallado por Canal</Typography>
          
          {sampleData?.channels && Object.entries(sampleData.channels).map(([channelKey, channelData]) => {
            const channelPeaks = sampleData.peaks?.[channelKey] || [];
            const channelMetrics = sampleData.quality_metrics?.signal_strength?.[channelKey] || {};
            
            return (
              <Accordion key={channelKey}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    <Box sx={{ width: 20, height: 20, bgcolor: channelData.color, borderRadius: '50%', mr: 2 }} />
                    <Typography sx={{ flexGrow: 1 }}>
                      Canal {channelKey.split('_')[1]} - {channelPeaks.length} picos detectados
                    </Typography>
                    <Chip 
                      label={`Max: ${channelMetrics.max?.toFixed(0) || 'N/A'} RFU`} 
                      size="small" 
                      sx={{ mr: 1 }}
                    />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>Estadísticas del Canal</Typography>
                      <List dense>
                        <ListItem>
                          <ListItemText 
                            primary="Intensidad máxima"
                            secondary={`${channelMetrics.max?.toFixed(0) || 'N/A'} RFU`}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Intensidad media"
                            secondary={`${channelMetrics.mean?.toFixed(0) || 'N/A'} RFU`}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Desviación estándar"
                            secondary={`${channelMetrics.std?.toFixed(2) || 'N/A'}`}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Ruido de línea base"
                            secondary={`${sampleData.quality_metrics?.baseline_noise?.[channelKey]?.toFixed(2) || 'N/A'}`}
                          />
                        </ListItem>
                      </List>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>Picos Principales</Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Pos</TableCell>
                              <TableCell>Altura</TableCell>
                              <TableCell>SNR</TableCell>
                              <TableCell>Área</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {channelPeaks.slice(0, 5).map((peak, idx) => (
                              <TableRow key={idx}>
                                <TableCell>{peak.position}</TableCell>
                                <TableCell>{peak.height.toFixed(0)}</TableCell>
                                <TableCell>{peak.snr?.toFixed(1) || 'N/A'}</TableCell>
                                <TableCell>{peak.area?.toFixed(0) || 'N/A'}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </Box>
      )}

      {/* Panel de Métricas de Calidad */}
      {selectedTab === 3 && (
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Métricas de Calidad</Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography color="text.secondary" variant="h6">
                    Calidad General
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 3 }}>
                    <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                      <CircularProgress 
                        variant="determinate" 
                        value={sampleData?.quality_metrics?.overall_quality === 'excellent' ? 100 :
                               sampleData?.quality_metrics?.overall_quality === 'good' ? 75 :
                               sampleData?.quality_metrics?.overall_quality === 'acceptable' ? 50 : 25}
                        size={120}
                        thickness={4}
                        sx={{
                          color: sampleData?.quality_metrics?.overall_quality === 'excellent' ? '#4caf50' :
                                 sampleData?.quality_metrics?.overall_quality === 'good' ? '#2196f3' :
                                 sampleData?.quality_metrics?.overall_quality === 'acceptable' ? '#ff9800' : '#f44336'
                        }}
                      />
                      <Box sx={{ position: 'absolute', top: 0, left: 0, bottom: 0, right: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Typography variant="h4" component="div" color="text.secondary">
                          {sampleData?.quality_metrics?.overall_quality?.toUpperCase() || 'N/A'}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    SNR Promedio: <strong>{formatNumber(sampleData?.quality_metrics?.average_snr)}</strong>
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={8}>
              <Grid container spacing={2}>
                {/* Métricas por canal */}
                {sampleData?.channels && Object.entries(sampleData.channels).map(([channelKey, channelData]) => {
                  const signal = sampleData.quality_metrics?.signal_strength?.[channelKey] || {};
                  const noise = sampleData.quality_metrics?.baseline_noise?.[channelKey] || 0;
                  const snr = signal.max / (noise || 1);
                  
                  return (
                    <Grid item xs={6} key={channelKey}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Box sx={{ width: 16, height: 16, bgcolor: channelData.color, borderRadius: '50%', mr: 1 }} />
                          <Typography variant="subtitle2">Canal {channelKey.split('_')[1]}</Typography>
                        </Box>
                        <Grid container spacing={1}>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">Max RFU</Typography>
                            <Typography variant="body2" fontWeight="bold">{formatNumber(signal.max, 0)}</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">SNR</Typography>
                            <Typography variant="body2" fontWeight="bold">{formatNumber(snr, 1)}</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">Ruido Base</Typography>
                            <Typography variant="body2">{formatNumber(noise, 1)}</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">Resolución</Typography>
                            <Typography variant="body2">
                              {sampleData.quality_metrics?.resolution?.[channelKey] || 'N/A'}
                            </Typography>
                          </Grid>
                        </Grid>
                      </Paper>
                    </Grid>
                  );
                })}
              </Grid>
            </Grid>
          </Grid>

          {/* Estándar de tamaños */}
          {sampleData?.size_standard && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>Calibración del Estándar de Tamaños</Typography>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={3}>
                    <Typography variant="subtitle2" gutterBottom>Estado</Typography>
                    <Chip 
                      label={sampleData.size_standard.status === 'calibrated' ? 'Calibrado' : 
                             sampleData.size_standard.status === 'insufficient_peaks' ? 'Picos Insuficientes' : 
                             'No Encontrado'}
                      color={sampleData.size_standard.status === 'calibrated' ? 'success' : 'error'}
                    />
                  </Grid>
                  {sampleData.size_standard.calibration && (
                    <>
                      <Grid item xs={12} md={3}>
                        <Typography variant="subtitle2" gutterBottom>R²</Typography>
                        <Typography variant="h6">{formatNumber(sampleData.size_standard.calibration.r_squared, 3)}</Typography>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Typography variant="subtitle2" gutterBottom>Pendiente</Typography>
                        <Typography variant="body1">{formatNumber(sampleData.size_standard.calibration.slope, 4)}</Typography>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Typography variant="subtitle2" gutterBottom>Intercepto</Typography>
                        <Typography variant="body1">{formatNumber(sampleData.size_standard.calibration.intercept, 2)}</Typography>
                      </Grid>
                    </>
                  )}
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>Picos Detectados vs Esperados</Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={(sampleData.size_standard.peaks?.length || 0) / (sampleData.size_standard.expected_sizes?.length || 1) * 100}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {sampleData.size_standard.peaks?.length || 0} de {sampleData.size_standard.expected_sizes?.length || 0} picos
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>
            </Box>
          )}
        </Box>
      )}

      {/* Panel de Datos Técnicos */}
      {selectedTab === 4 && (
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Información Técnica Completa</Typography>
          
          <Grid container spacing={3}>
            {/* Metadatos del archivo */}
            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <InfoOutlined sx={{ mr: 1 }} />
                  Metadatos del Archivo
                </Typography>
                <Divider sx={{ my: 1 }} />
                <List dense>
                  <ListItem>
                    <ListItemText primary="Archivo" secondary={sampleData?.filename || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Tipo" secondary={sampleData?.metadata?.file_type || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Muestra" secondary={sampleData?.metadata?.sample_name || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Instrumento" secondary={sampleData?.metadata?.instrument || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Kit de Tintes" secondary={sampleData?.metadata?.dye_set || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Carril/Capilar" secondary={sampleData?.metadata?.lane || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Fecha de Corrida" secondary={sampleData?.metadata?.run_date || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Hora de Corrida" secondary={sampleData?.metadata?.run_time || 'N/A'} />
                  </ListItem>
                </List>
              </Paper>
            </Grid>

            {/* Datos ABIF crudos */}
            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <Storage sx={{ mr: 1 }} />
                  Datos ABIF Disponibles
                </Typography>
                <Divider sx={{ my: 1 }} />
                {sampleData?.raw_abif_data ? (
                  <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                    <List dense>
                      {Object.keys(sampleData.raw_abif_data).slice(0, 20).map(tag => (
                        <ListItem key={tag}>
                          <ListItemText 
                            primary={tag}
                            secondary={`Tipo: ${typeof sampleData.raw_abif_data[tag]}`}
                          />
                        </ListItem>
                      ))}
                      {Object.keys(sampleData.raw_abif_data).length > 20 && (
                        <ListItem>
                          <ListItemText 
                            primary={`... y ${Object.keys(sampleData.raw_abif_data).length - 20} tags más`}
                            secondary="Datos ABIF adicionales disponibles"
                          />
                        </ListItem>
                      )}
                    </List>
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No hay datos ABIF crudos disponibles
                  </Typography>
                )}
              </Paper>
            </Grid>

            {/* Estadísticas de procesamiento */}
            <Grid item xs={12}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <Speed sx={{ mr: 1 }} />
                  Estadísticas de Procesamiento
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Puntos de Datos</Typography>
                    <Typography variant="h6">
                      {sampleData?.channels?.channel_1?.raw_data?.length || 'N/A'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Canales Procesados</Typography>
                    <Typography variant="h6">
                      {sampleData?.channels ? Object.keys(sampleData.channels).length : 0}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Picos Totales</Typography>
                    <Typography variant="h6">
                      {sampleData?.peaks ? Object.values(sampleData.peaks).reduce((sum, p) => sum + p.length, 0) : 0}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Alelos Llamados</Typography>
                    <Typography variant="h6">
                      {sampleData?.alleles ? Object.values(sampleData.alleles).filter(a => a.allele1 && a.allele2).length : 0}
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* Información de depuración */}
            {sampleData?.simulation_note && (
              <Grid item xs={12}>
                <Alert severity="info" variant="outlined">
                  <Typography variant="subtitle2" gutterBottom>Nota de Procesamiento</Typography>
                  <Typography variant="body2">{sampleData.simulation_note}</Typography>
                </Alert>
              </Grid>
            )}
          </Grid>

          {/* Botón para exportar datos completos */}
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
            <Button 
              variant="outlined" 
              startIcon={<Download />}
              onClick={() => {
                const dataStr = JSON.stringify(sampleData, null, 2);
                const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                const exportName = `${sampleData?.metadata?.sample_name || 'sample'}_complete_data.json`;
                
                const linkElement = document.createElement('a');
                linkElement.setAttribute('href', dataUri);
                linkElement.setAttribute('download', exportName);
                linkElement.click();
              }}
            >
              Exportar Todos los Datos (JSON)
            </Button>
          </Box>
        </Box>
      )}

      {/* Indicador de cambios sin guardar */}
      {unsavedChanges && (
        <Box sx={{ position: 'fixed', bottom: 20, right: 20 }}>
          <Alert severity="warning" variant="filled" sx={{ boxShadow: 3 }}>
            Hay cambios sin guardar
          </Alert>
        </Box>
      )}
    </Paper>
  );
}