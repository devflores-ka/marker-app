// frontend/src/components/Dashboard.js
import React, { useState, useEffect } from 'react';
import {
  Box, Grid, Card, CardContent, CardActions, Typography, Button,
  TextField, Dialog, DialogTitle, DialogContent, DialogActions,
  List, ListItem, ListItemText, ListItemSecondaryAction,
  IconButton, Alert, Chip, Fab, Tooltip
} from '@mui/material';
import {
  Add, FolderOpen, Upload, Science, TableChart,
  Delete, Edit, Visibility, Download
} from '@mui/icons-material';

const Dashboard = () => {
  // Estados principales
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [samples, setSamples] = useState([]);
  const [backendStatus, setBackendStatus] = useState('checking...');
  
  // Estados para modales
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [uploadFilesOpen, setUploadFilesOpen] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  
  // Estados para notificaciones
  const [notification, setNotification] = useState({ show: false, message: '', type: 'info' });

  // Verificar estado del backend al cargar
  useEffect(() => {
    checkBackendStatus();
  }, []);

  const checkBackendStatus = async () => {
    try {
      const response = await fetch('http://localhost:8888/api/health');
      if (response.ok) {
        setBackendStatus('Connected');
      } else {
        setBackendStatus('Error');
      }
    } catch (error) {
      setBackendStatus('Not connected');
    }
  };

  const showNotification = (message, type = 'info') => {
    setNotification({ show: true, message, type });
    setTimeout(() => {
      setNotification({ show: false, message: '', type: 'info' });
    }, 4000);
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
        const newProject = {
          id: result.project_id,
          name: projectName,
          created: new Date().toLocaleDateString(),
          samples: 0
        };
        setProjects([...projects, newProject]);
        setProjectName('');
        setCreateProjectOpen(false);
        showNotification('Proyecto creado exitosamente', 'success');
      } else {
        showNotification('Error al crear el proyecto', 'error');
      }
    } catch (error) {
      showNotification('Error de conexión con el backend', 'error');
    }
  };

  const selectProject = (project) => {
    setCurrentProject(project);
    // Aquí cargarías las muestras del proyecto desde el backend
    loadProjectSamples(project.id);
  };

  const loadProjectSamples = async (projectId) => {
    // Por ahora simulamos datos, después esto vendría del backend
    setSamples([
      { id: '1', filename: 'sample001.fsa', status: 'analyzed', alleles: 12 },
      { id: '2', filename: 'sample002.fsa', status: 'pending', alleles: 0 },
    ]);
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
        showNotification(`${result.samples.length} archivos subidos exitosamente`, 'success');
        setSelectedFiles([]);
        setUploadFilesOpen(false);
        loadProjectSamples(currentProject.id);
      } else {
        showNotification('Error al subir archivos', 'error');
      }
    } catch (error) {
      showNotification('Error de conexión con el backend', 'error');
    }
  };

  // Vista principal si no hay proyecto seleccionado
  if (!currentProject) {
    return (
      <Box sx={{ p: 3 }}>
        {/* Header con estado del backend */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            GenotypeR 
          </Typography>
          <Chip 
            label={`Backend: ${backendStatus}`}
            color={backendStatus === 'Connected' ? 'success' : 'error'}
            variant="outlined"
          />
        </Box>

        {/* Notificaciones */}
        {notification.show && (
          <Alert severity={notification.type} sx={{ mb: 3 }}>
            {notification.message}
          </Alert>
        )}

        {/* Acciones rápidas */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Science sx={{ fontSize: 40, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Nuevo Proyecto
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Crea un nuevo proyecto de análisis genético y comienza a subir tus archivos FSA.
                </Typography>
              </CardContent>
              <CardActions>
                <Button 
                  variant="contained" 
                  startIcon={<Add />}
                  onClick={() => setCreateProjectOpen(true)}
                >
                  Crear Proyecto
                </Button>
              </CardActions>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <FolderOpen sx={{ fontSize: 40, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Abrir Proyecto
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Continúa trabajando en un proyecto existente. Analiza muestras y exporta resultados.
                </Typography>
              </CardContent>
              <CardActions>
                <Button variant="outlined" disabled={projects.length === 0}>
                  Ver Proyectos
                </Button>
              </CardActions>
            </Card>
          </Grid>
        </Grid>

        {/* Lista de proyectos existentes */}
        <Typography variant="h5" gutterBottom>
          Proyectos Recientes
        </Typography>
        
        {projects.length === 0 ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <FolderOpen sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No hay proyectos
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Crea tu primer proyecto para comenzar con el análisis genético
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <Grid container spacing={2}>
            {projects.map((project) => (
              <Grid item xs={12} sm={6} md={4} key={project.id}>
                <Card sx={{ cursor: 'pointer' }} onClick={() => selectProject(project)}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom noWrap>
                      {project.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Creado: {project.created}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Muestras: {project.samples}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button size="small" startIcon={<Visibility />}>
                      Abrir
                    </Button>
                    <IconButton size="small" color="error">
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
          <DialogTitle>Crear Nuevo Proyecto</DialogTitle>
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
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Este nombre se usará para identificar tu proyecto y generar reportes.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateProjectOpen(false)}>Cancelar</Button>
            <Button variant="contained" onClick={createProject}>Crear</Button>
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
          <Typography variant="h4" component="h1">
            {currentProject.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {samples.length} muestras • Creado: {currentProject.created}
          </Typography>
        </Box>
        <Box>
          <Button 
            variant="outlined" 
            sx={{ mr: 1 }}
            onClick={() => setCurrentProject(null)}
          >
            Volver
          </Button>
          <Button 
            variant="contained"
            startIcon={<Download />}
            disabled={samples.length === 0}
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

      {/* Estadísticas rápidas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary">
                {samples.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Muestras
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="success.main">
                {samples.filter(s => s.status === 'analyzed').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Analizadas
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="warning.main">
                {samples.filter(s => s.status === 'pending').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Pendientes
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Lista de muestras */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Muestras del Proyecto
            </Typography>
            <Button 
              variant="contained" 
              startIcon={<Upload />}
              onClick={() => setUploadFilesOpen(true)}
            >
              Subir Archivos
            </Button>
          </Box>
          
          {samples.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Upload sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No hay muestras
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sube archivos FSA para comenzar el análisis
              </Typography>
            </Box>
          ) : (
            <List>
              {samples.map((sample) => (
                <ListItem key={sample.id} divider>
                  <ListItemText
                    primary={sample.filename}
                    secondary={
                      <Box>
                        <Chip 
                          label={sample.status === 'analyzed' ? 'Analizada' : 'Pendiente'}
                          size="small"
                          color={sample.status === 'analyzed' ? 'success' : 'warning'}
                          sx={{ mr: 1 }}
                        />
                        {sample.alleles > 0 && (
                          <Typography component="span" variant="caption">
                            {sample.alleles} alelos detectados
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton edge="end">
                      <Science />
                    </IconButton>
                    <IconButton edge="end">
                      <Edit />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* FAB para acciones rápidas */}
      <Tooltip title="Subir archivos">
        <Fab 
          color="primary" 
          sx={{ position: 'fixed', bottom: 24, right: 24 }}
          onClick={() => setUploadFilesOpen(true)}
        >
          <Upload />
        </Fab>
      </Tooltip>

      {/* Modal subir archivos */}
      <Dialog open={uploadFilesOpen} onClose={() => setUploadFilesOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Subir Archivos FSA</DialogTitle>
        <DialogContent>
          <input
            type="file"
            multiple
            accept=".fsa,.ab1,.txt"
            onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
            style={{ width: '100%', padding: '20px', border: '2px dashed #ccc', borderRadius: '8px', textAlign: 'center', marginTop: '16px' }}
          />
          {selectedFiles.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                Archivos seleccionados:
              </Typography>
              {selectedFiles.map((file, index) => (
                <Chip 
                  key={index} 
                  label={file.name} 
                  size="small" 
                  sx={{ mr: 1, mb: 1 }}
                />
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadFilesOpen(false)}>Cancelar</Button>
          <Button variant="contained" onClick={handleFileUpload}>
            Subir {selectedFiles.length} archivo(s)
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Dashboard;
