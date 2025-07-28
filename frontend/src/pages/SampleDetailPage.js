// frontend/src/pages/SampleDetailPage.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Button,
  IconButton,
  Typography,
  Breadcrumbs,
  Link,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  ArrowBack,
  Home,
  Science
} from '@mui/icons-material';

import ComprehensiveElectropherogramViewer from '../components/EnhancedElectropherogramViewer';

import Plot from 'react-plotly.js';

export default function SampleDetailPage() {
  const { projectId, sampleId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sampleInfo, setSampleInfo] = useState(null);

  useEffect(() => {
    loadSampleInfo();
  }, [sampleId]);

  const loadSampleInfo = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8888/api/samples/${sampleId}`);
      if (!response.ok) throw new Error('Error cargando muestra');
      
      const data = await response.json();
      setSampleInfo(data.sample);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = () => {
    // Recargar información si es necesario
    loadSampleInfo();
  };

  if (loading) {
    return (
      <Container>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Box sx={{ bgcolor: '#f5f5f5', minHeight: '100vh', py: 3 }}>
      <Container maxWidth="xl">
        {/* Navegación */}
        <Box sx={{ mb: 3 }}>
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate(`/projects/${projectId}`)}
            sx={{ mb: 2 }}
          >
            Volver al Proyecto
          </Button>
          
          <Breadcrumbs>
            <Link
              component="button"
              variant="body1"
              onClick={() => navigate('/')}
              sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
            >
              <Home sx={{ mr: 0.5, fontSize: 20 }} />
              Inicio
            </Link>
            <Link
              component="button"
              variant="body1"
              onClick={() => navigate('/projects')}
              sx={{ cursor: 'pointer' }}
            >
              Proyectos
            </Link>
            <Link
              component="button"
              variant="body1"
              onClick={() => navigate(`/projects/${projectId}`)}
              sx={{ cursor: 'pointer' }}
            >
              Proyecto
            </Link>
            <Typography color="text.primary">
              {sampleInfo?.filename || 'Muestra'}
            </Typography>
          </Breadcrumbs>
        </Box>

        {/* Título */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
          <Science sx={{ fontSize: 32, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4" gutterBottom>
              Análisis de Muestra
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Visualización completa y edición de electroferogramas
            </Typography>
          </Box>
        </Box>

        {/* Visualizador completo */}
        <ComprehensiveElectropherogramViewer 
          sampleId={sampleId}
          onUpdate={handleUpdate}
        />
      </Container>
    </Box>
  );
}

// Exportar también una versión simplificada para usar en el Dashboard
export function ElectropherogramPreview({ sampleId }) {
  const [sampleData, setSampleData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [sampleId]);

  const loadData = async () => {
    try {
      const response = await fetch(`http://localhost:8888/api/samples/${sampleId}/electropherogram`);
      if (response.ok) {
        const data = await response.json();
        setSampleData(data.data);
      }
    } catch (err) {
      console.error('Error cargando preview:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <CircularProgress size={24} />;
  if (!sampleData) return null;

  // Preparar datos simplificados para preview
  const traces = [];
  if (sampleData.channels) {
    Object.entries(sampleData.channels).forEach(([channelKey, channelData]) => {
      const data = channelData.analyzed_data || channelData.raw_data;
      if (data) {
        traces.push({
          x: Array.from({ length: data.length }, (_, i) => i),
          y: data,
          type: 'scatter',
          mode: 'lines',
          line: { color: channelData.color, width: 1 },
          name: `Ch ${channelKey.split('_')[1]}`
        });
      }
    });
  }

  return (
    <Box sx={{ height: 200, width: '100%' }}>
      <Plot
        data={traces}
        layout={{
          margin: { t: 0, r: 0, b: 30, l: 40 },
          xaxis: { title: 'Position' },
          yaxis: { title: 'RFU' },
          showlegend: false,
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'white'
        }}
        config={{
          displayModeBar: false,
          responsive: true
        }}
        style={{ width: '100%', height: '100%' }}
      />
    </Box>
  );
}