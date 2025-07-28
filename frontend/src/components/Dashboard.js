// frontend/src/components/Dashboard.js
import React, { useState, useEffect } from 'react';
import {
  Box, Grid, Card, CardContent, CardActions, Typography, Button,
  TextField, Dialog, DialogTitle, DialogContent, DialogActions,
  List, ListItem, ListItemText, ListItemSecondaryAction,
  IconButton, Alert, Chip, Fab, Tooltip, LinearProgress,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Collapse, Avatar
} from '@mui/material';
// Agregar Close a los imports de @mui/icons-material
import {
  Add, FolderOpen, Upload, Science, TableChart,
  Delete, Edit, Visibility, Download, ExpandMore, ExpandLess,
  CheckCircle, Error, Pending, Analytics, Settings, Close  // <- Agregar Close aquí
} from '@mui/icons-material';

// Agregar este import DESPUÉS de todos los imports de MUI
import ComprehensiveElectropherogramViewer from '../components/EnhancedElectropherogramViewer';

const Dashboard = () => {
  // Estados principales
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [samples, setSamples] = useState([]);
  const [projectStats, setProjectStats] = useState({});
  const [backendStatus, setBackendStatus] = useState('checking...');
  
  // Estados para modales
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [uploadFilesOpen, setUploadFilesOpen] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // Estados para detalles
  const [expandedSample, setExpandedSample] = useState(null);
  const [alleleMatrix, setAlleleMatrix] = useState(null);

  // Estados para el visualizador de electroferogramas
  const [selectedSampleId, setSelectedSampleId] = useState(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  
  // Estados para notificaciones
  const [notification, setNotification] = useState({ show: false, message: '', type: 'info' });

  // Verificar estado del backend al cargar
  useEffect(() => {
    checkBackendStatus();
    loadProjects();
  }, []);

  const checkBackendStatus = async () => {
    try {
      const response = await fetch('http://localhost:8888/api/health');
      if (response.ok) {
        const data = await response.json();
        setBackendStatus('Connected');
        console.log('Backend status:', data);
      } else {
        setBackendStatus('Error');
      }
    } catch (error) {
      setBackendStatus('Not connected');
    }
  };

  const loadProjects = async () => {
    try {
      const response = await fetch('http://localhost:8888/api/projects');
      if (response.ok) {
        const data = await response.json();
        setProjects(data.projects || []);
      }
    } catch (error) {
      console.error('Error loading projects:', error);
    }
  };

  const showNotification = (message, type = 'info') => {
    // Manejar diferentes tipos de mensajes de error
    let displayMessage = message;
    
    if (typeof message === 'object') {
      if (message.detail) {
        displayMessage = message.detail;
      } else if (Array.isArray(message)) {
        displayMessage = message[0]?.msg || 'Error desconocido';
      } else {
        displayMessage = 'Error en el servidor';
      }
    }
    
    setNotification({ show: true, message: displayMessage, type });
    setTimeout(() => {
      setNotification({ show: false, message: '', type: 'info' });
    }, 5000);
  };

  // Funciones para proyectos
  const createProject = async () => {
    if (!projectName.trim()) {
      showNotification('El nombre del proyecto es requerido', 'error');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('name', projectName);
      
      const response = await fetch('http://localhost:8888/api/projects/create', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        setProjectName('');
        setCreateProjectOpen(false);
        loadProjects(); // Recargar lista
        showNotification(result.message || 'Proyecto creado exitosamente', 'success');
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        console.error('Error response:', errorData);
        showNotification(errorData, 'error');
      }
    } catch (error) {
      showNotification('Error de conexión con el backend', 'error');
    }
  };

  const selectProject = async (project) => {
    setCurrentProject(project);
    await loadProjectDetails(project.id);
  };

  const loadProjectDetails = async (projectId) => {
    try {
      const response = await fetch(`http://localhost:8888/api/projects/${projectId}`);
      if (response.ok) {
        const data = await response.json();
        setSamples(data.samples_data || []);
        setProjectStats(data.metadata || {});
        
        // Cargar matriz de alelos
        const matrixResponse = await fetch(`http://localhost:8888/api/projects/${projectId}/allele_matrix`);
        if (matrixResponse.ok) {
          const matrixData = await matrixResponse.json();
          setAlleleMatrix(matrixData);
        }
      }
    } catch (error) {
      showNotification('Error cargando detalles del proyecto', 'error');
    }
  };

  // Funciones para archivos
  const handleFileUpload = async () => {
    if (!currentProject) {
      showNotification('Selecciona un proyecto primero', 'error');
      return;
    }
    
    if (selectedFiles.length === 0) {
      showNotification('Selecciona al menos un archivo', 'error');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch(`http://localhost:8888/api/projects/${currentProject.id}/samples/upload`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        showNotification(result.message, 'success');
        setSelectedFiles([]);
        setUploadFilesOpen(false);
        await loadProjectDetails(currentProject.id); // Recargar datos del proyecto
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        console.error('Error uploading files:', errorData);
        showNotification(errorData, 'error');
      }
    } catch (error) {
      showNotification('Error de conexión con el backend', 'error');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'analyzed':
        return <CheckCircle color="success" />;
      case 'error':
        return <Error color="error" />;
      case 'manually_reviewed':
        return <Settings color="primary" />;
      default:
        return <Pending color="warning" />;
    }
  };

  const getQualityColor = (score) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  // Funciones para el visualizador
  const handleOpenViewer = (sampleId) => {
    setSelectedSampleId(sampleId);
    setViewerOpen(true);
  };

  const handleCloseViewer = () => {
    setViewerOpen(false);
    setSelectedSampleId(null);
  };

  // Vista principal si no hay proyecto seleccionado
  if (!currentProject) {
    return (
      <Box sx={{ p: 3 }}>
        {/* Header con estado del backend */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              🧬 GenotypeR
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Software de Análisis Genético Profesional
            </Typography>
          </Box>
          <Chip 
            label={`Backend: ${backendStatus}`}
            color={backendStatus === 'Connected' ? 'success' : 'error'}
            variant="outlined"
            icon={backendStatus === 'Connected' ? <CheckCircle /> : <Error />}
          />
        </Box>

        {/* Notificaciones */}
        {notification.show && (
          <Alert severity={notification.type} sx={{ mb: 3 }}>
            {notification.message}
          </Alert>
        )}

        {/* Estadísticas globales */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="primary">
                  {projects.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Proyectos Totales
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="success.main">
                  {projects.reduce((acc, p) => acc + (p.metadata?.total_samples || 0), 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Muestras Procesadas
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="info.main">
                  {projects.reduce((acc, p) => acc + (p.metadata?.analyzed_samples || 0), 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Análisis Completados
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Acciones rápidas */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <CardContent>
                <Science sx={{ fontSize: 40, mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Nuevo Proyecto
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Crea un nuevo proyecto de análisis genético y comienza a subir tus archivos FSA.
                </Typography>
              </CardContent>
              <CardActions>
                <Button 
                  variant="contained" 
                  startIcon={<Add />}
                  onClick={() => setCreateProjectOpen(true)}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.2)', '&:hover': { backgroundColor: 'rgba(255,255,255,0.3)' } }}
                >
                  Crear Proyecto
                </Button>
              </CardActions>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
              <CardContent>
                <Analytics sx={{ fontSize: 40, mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Análisis Avanzado
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Herramientas de análisis genético con detección automática de alelos y control de calidad.
                </Typography>
              </CardContent>
              <CardActions>
                <Button 
                  variant="contained" 
                  disabled={projects.length === 0}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.2)', '&:hover': { backgroundColor: 'rgba(255,255,255,0.3)' } }}
                >
                  Ver Análisis
                </Button>
              </CardActions>
            </Card>
          </Grid>
        </Grid>

        {/* Lista de proyectos existentes */}
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <FolderOpen sx={{ mr: 1 }} />
          Proyectos Recientes
        </Typography>
        
        {projects.length === 0 ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <FolderOpen sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h5" color="text.secondary" gutterBottom>
                No hay proyectos
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Crea tu primer proyecto para comenzar con el análisis genético
              </Typography>
              <Button 
                variant="contained" 
                startIcon={<Add />}
                onClick={() => setCreateProjectOpen(true)}
                size="large"
              >
                Crear Primer Proyecto
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Grid container spacing={3}>
            {projects.map((project) => (
              <Grid item xs={12} sm={6} md={4} key={project.id}>
                <Card 
                  sx={{ 
                    cursor: 'pointer',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4
                    }
                  }} 
                  onClick={() => selectProject(project)}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                        <Science />
                      </Avatar>
                      <Box>
                        <Typography variant="h6" noWrap>
                          {project.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {project.created_at}
                        </Typography>
                      </Box>
                    </Box>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Muestras:
                      </Typography>
                      <Chip 
                        label={project.metadata?.total_samples || 0} 
                        size="small" 
                        color="primary"
                      />
                    </Box>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Analizadas:
                      </Typography>
                      <Chip 
                        label={project.metadata?.analyzed_samples || 0} 
                        size="small" 
                        color="success"
                      />
                    </Box>
                    
                    {project.metadata?.loci_detected?.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Loci detectados:
                        </Typography>
                        <Box sx={{ mt: 0.5 }}>
                          {project.metadata.loci_detected.slice(0, 3).map((locus) => (
                            <Chip 
                              key={locus} 
                              label={locus} 
                              size="small" 
                              variant="outlined"
                              sx={{ mr: 0.5, mb: 0.5 }}
                            />
                          ))}
                          {project.metadata.loci_detected.length > 3 && (
                            <Chip 
                              label={`+${project.metadata.loci_detected.length - 3}`} 
                              size="small" 
                              variant="outlined"
                            />
                          )}
                        </Box>
                      </Box>
                    )}
                  </CardContent>
                  <CardActions>
                    <Button size="small" startIcon={<Visibility />}>
                      Abrir
                    </Button>
                    <IconButton size="small" color="error" onClick={(e) => {
                      e.stopPropagation();
                      // TODO: Implementar borrado de proyecto
                    }}>
                      <Delete />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {/* Modal crear proyecto */}
        <Dialog open={createProjectOpen} onClose={() => setCreateProjectOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Science sx={{ mr: 1, color: 'primary.main' }} />
              Crear Nuevo Proyecto
            </Box>
          </DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Nombre del Proyecto"
              fullWidth
              variant="outlined"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Ej: Análisis Forense Caso 001"
              sx={{ mt: 2 }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Este nombre se usará para identificar tu proyecto y generar reportes.
              Se recomienda usar nombres descriptivos que incluyan fecha o número de caso.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateProjectOpen(false)}>Cancelar</Button>
            <Button 
              variant="contained" 
              onClick={createProject}
              disabled={!projectName.trim()}
            >
              Crear
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    );
  }

  // Vista del proyecto seleccionado
  return (
    <Box sx={{ p: 3 }}>
      {/* Header del proyecto */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center' }}>
            <Science sx={{ mr: 1, color: 'primary.main' }} />
            {currentProject.name}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {projectStats.total_samples || 0} muestras • Creado: {currentProject.created_at}
          </Typography>
        </Box>
        <Box>
          <Button 
            variant="outlined" 
            sx={{ mr: 1 }}
            onClick={() => setCurrentProject(null)}
          >
            ← Volver
          </Button>
          <Button 
            variant="contained"
            startIcon={<Download />}
            disabled={(projectStats.analyzed_samples || 0) === 0}
          >
            Exportar
          </Button>
        </Box>
      </Box>

      {/* Notificaciones */}
      {notification.show && (
        <Alert severity={notification.type} sx={{ mb: 3 }}>
          {notification.message}
        </Alert>
      )}

      {/* Estadísticas del proyecto */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary">
                {projectStats.total_samples || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Muestras
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="success.main">
                {projectStats.analyzed_samples || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Analizadas
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="info.main">
                {projectStats.loci_detected?.length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Loci Detectados
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="warning.main">
                {samples.filter(s => s.status === 'error').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Con Errores
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Lista de muestras */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
              <Science sx={{ mr: 1 }} />
              Muestras del Proyecto
            </Typography>
            <Button 
              variant="contained" 
              startIcon={<Upload />}
              onClick={() => setUploadFilesOpen(true)}
            >
              Subir Archivos FSA
            </Button>
          </Box>
          
          {samples.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Upload sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No hay muestras
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Sube archivos FSA para comenzar el análisis automático
              </Typography>
              <Button 
                variant="contained" 
                startIcon={<Upload />}
                onClick={() => setUploadFilesOpen(true)}
              >
                Subir Primer Archivo
              </Button>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Archivo</TableCell>
                    <TableCell>Estado</TableCell>
                    <TableCell>Canales</TableCell>
                    <TableCell>Calidad</TableCell>
                    <TableCell>Alelos</TableCell>
                    <TableCell>Acciones</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {samples.map((sample) => (
                    <React.Fragment key={sample.id}>
                      <TableRow>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {getStatusIcon(sample.status)}
                            <Box sx={{ ml: 1 }}>
                              <Typography variant="body2" fontWeight="medium">
                                {sample.filename}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {sample.metadata?.sample_name || 'Unknown'}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={sample.status === 'analyzed' ? 'Analizada' : 
                                  sample.status === 'error' ? 'Error' : 
                                  sample.status === 'manually_reviewed' ? 'Revisada' : 'Pendiente'}
                            size="small"
                            color={sample.status === 'analyzed' ? 'success' : 
                                  sample.status === 'error' ? 'error' : 
                                  sample.status === 'manually_reviewed' ? 'primary' : 'warning'}
                          />
                        </TableCell>
                        <TableCell>{sample.metadata?.channels || 0}</TableCell>
                        <TableCell>
                          <Chip 
                            label={`${Math.round((sample.metadata?.quality_score || 0) * 100)}%`}
                            size="small"
                            color={getQualityColor(sample.metadata?.quality_score || 0)}
                          />
                        </TableCell>
                        <TableCell>
                          {Object.values(sample.fsa_data?.alleles || {}).reduce((acc, channelAlleles) => 
                            acc + Object.keys(channelAlleles).length, 0
                          )}
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            {/* Botón para expandir/contraer detalles básicos */}
                            <Tooltip title={expandedSample === sample.id ? "Ocultar detalles" : "Ver detalles"}>
                              <IconButton 
                                size="small"
                                onClick={() => setExpandedSample(expandedSample === sample.id ? null : sample.id)}
                              >
                                {expandedSample === sample.id ? <ExpandLess /> : <ExpandMore />}
                              </IconButton>
                            </Tooltip>
                            
                            {/* Botón para abrir el visualizador completo */}
                            <Tooltip title="Ver electroferograma">
                              <IconButton 
                                size="small"
                                color="primary"
                                onClick={() => handleOpenViewer(sample.id)}
                                disabled={sample.status !== 'analyzed'}
                              >
                                <Visibility />
                              </IconButton>
                            </Tooltip>
                            
                            {/* Botón para editar */}
                            <Tooltip title="Editar muestra">
                              <IconButton 
                                size="small"
                                onClick={() => handleOpenViewer(sample.id)}
                                disabled={sample.status !== 'analyzed'}
                              >
                                <Edit />
                              </IconButton>
                            </Tooltip>
                            
                            {/* Botón para descargar datos */}
                            <Tooltip title="Descargar datos">
                              <IconButton 
                                size="small"
                                onClick={() => {
                                  window.open(`http://localhost:8888/api/samples/${sample.id}/download`, '_blank');
                                }}
                                disabled={sample.status !== 'analyzed'}
                              >
                                <Download />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                      
                      {/* Detalles expandidos */}
                      <TableRow>
                        <TableCell colSpan={6} sx={{ p: 0 }}>
                          <Collapse in={expandedSample === sample.id}>
                            <Box sx={{ p: 3, bgcolor: 'grey.50' }}>
                              <Typography variant="h6" gutterBottom>
                                Detalles de la Muestra
                              </Typography>
                              
                              <Grid container spacing={3}>
                                <Grid item xs={12} md={6}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Información General
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Instrumento:</strong> {sample.metadata?.instrument || 'N/A'}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Fecha de corrida:</strong> {sample.metadata?.run_date || 'N/A'}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Puntos de datos:</strong> {sample.metadata?.data_points || 0}
                                  </Typography>
                                </Grid>
                                
                                <Grid item xs={12} md={6}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Alelos Detectados
                                  </Typography>
                                  {Object.entries(sample.fsa_data?.alleles || {}).map(([channel, channelAlleles]) => (
                                    <Box key={channel} sx={{ mb: 1 }}>
                                      <Typography variant="caption" color="text.secondary">
                                        {channel}:
                                      </Typography>
                                      {Object.entries(channelAlleles).map(([locus, alleles]) => (
                                        <Box key={locus} sx={{ ml: 1 }}>
                                          <Chip 
                                            label={`${locus}: ${alleles.join('/')}`}
                                            size="small"
                                            variant="outlined"
                                            sx={{ mr: 0.5, mb: 0.5 }}
                                          />
                                        </Box>
                                      ))}
                                    </Box>
                                  ))}
                                </Grid>
                              </Grid>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Matriz de alelos */}
      {alleleMatrix && alleleMatrix.loci.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <TableChart sx={{ mr: 1 }} />
              Matriz de Genotipos
            </Typography>
            
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Muestra</TableCell>
                    {alleleMatrix.loci.map((locus) => (
                      <TableCell key={locus} align="center">{locus}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {alleleMatrix.samples.map((sample) => (
                    <TableRow key={sample.sample_id}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {sample.filename}
                        </Typography>
                      </TableCell>
                      {alleleMatrix.loci.map((locus) => (
                        <TableCell key={locus} align="center">
                          {sample[locus] ? (
                            <Chip 
                              label={sample[locus]} 
                              size="small" 
                              color="primary"
                              variant="outlined"
                            />
                          ) : (
                            <Typography variant="caption" color="text.disabled">
                              -
                            </Typography>
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* FAB para acciones rápidas */}
      <Tooltip title="Subir archivos FSA">
        <Fab 
          color="primary" 
          sx={{ position: 'fixed', bottom: 24, right: 24 }}
          onClick={() => setUploadFilesOpen(true)}
        >
          <Upload />
        </Fab>
      </Tooltip>

      {/* Modal subir archivos */}
      <Dialog open={uploadFilesOpen} onClose={() => setUploadFilesOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Upload sx={{ mr: 1, color: 'primary.main' }} />
            Subir Archivos FSA
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Selecciona archivos FSA (.fsa) o AB1 (.ab1) para análisis automático.
              El sistema detectará automáticamente picos y llamará alelos.
            </Typography>
          </Box>
          
          <input
            type="file"
            multiple
            accept=".fsa,.ab1"
            onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
            style={{ 
              width: '100%', 
              padding: '40px', 
              border: '2px dashed #ccc', 
              borderRadius: '12px', 
              textAlign: 'center', 
              marginTop: '16px',
              backgroundColor: '#fafafa',
              cursor: 'pointer'
            }}
          />
          
          {selectedFiles.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Archivos seleccionados ({selectedFiles.length}):
              </Typography>
              <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                {selectedFiles.map((file, index) => (
                  <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1 }}>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {file.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </Typography>
                    </Box>
                    <Chip 
                      label={file.name.split('.').pop().toUpperCase()} 
                      size="small" 
                      color="primary"
                      variant="outlined"
                    />
                  </Box>
                ))}
              </Box>
              
              <Box sx={{ mt: 2, p: 2, bgcolor: 'primary.50', borderRadius: 1 }}>
                <Typography variant="body2" color="primary.main">
                  <strong>Análisis automático incluye:</strong>
                </Typography>
                <Typography variant="caption" display="block">
                  • Detección automática de picos
                </Typography>
                <Typography variant="caption" display="block">
                  • Llamado de alelos por locus
                </Typography>
                <Typography variant="caption" display="block">
                  • Control de calidad de señales
                </Typography>
                <Typography variant="caption" display="block">
                  • Calibración de tamaños automática
                </Typography>
              </Box>
            </Box>
          )}
          
          {uploading && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                Procesando archivos...
              </Typography>
              <LinearProgress variant="indeterminate" />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadFilesOpen(false)} disabled={uploading}>
            Cancelar
          </Button>
          <Button 
            variant="contained" 
            onClick={handleFileUpload}
            disabled={selectedFiles.length === 0 || uploading}
            startIcon={uploading ? <Science /> : <Upload />}
          >
            {uploading ? 'Analizando...' : `Subir y Analizar ${selectedFiles.length} archivo(s)`}
          </Button>
        </DialogActions>
      </Dialog>
      {/* Dialog para el visualizador de electroferogramas */}
      <Dialog 
        open={viewerOpen} 
        onClose={handleCloseViewer}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: {
            height: '90vh',
            maxHeight: '90vh'
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          borderBottom: 1,
          borderColor: 'divider'
        }}>
          <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center' }}>
            <Science sx={{ mr: 1 }} />
            Análisis de Electroferograma
            {selectedSampleId && samples.find(s => s.id === selectedSampleId) && (
              <Typography variant="subtitle1" sx={{ ml: 2, color: 'text.secondary' }}>
                - {samples.find(s => s.id === selectedSampleId).filename}
              </Typography>
            )}
          </Typography>
          <IconButton onClick={handleCloseViewer}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ p: 0, overflow: 'hidden' }}>
          {selectedSampleId && (
            <ComprehensiveElectropherogramViewer 
              sampleId={selectedSampleId}
              onUpdate={() => {
                // Recargar los datos del proyecto si es necesario
                loadProjectDetails(currentProject.id);
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default Dashboard;
