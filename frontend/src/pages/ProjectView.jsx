// frontend/src/pages/ProjectView.jsx
import React, { useState } from 'react';
import {
  Box, Card, CardContent, Typography, Button,
  Grid, TextField, Alert
} from '@mui/material';
import { FolderOpen, Add } from '@mui/icons-material';

export default function ProjectView() {
  const [projectName, setProjectName] = useState('');
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState('');

  const createProject = async () => {
    if (!projectName.trim()) {
      setError('El nombre del proyecto es requerido');
      return;
    }

    try {
      const response = await fetch('http://localhost:8888/api/projects/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: projectName }),
      });
      
      if (response.ok) {
        const result = await response.json();
        setProjects([...projects, { id: result.project_id, name: projectName }]);
        setProjectName('');
        setError('');
      }
    } catch (err) {
      setError('Error al crear el proyecto');
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Gestión de Proyectos
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Crear Nuevo Proyecto
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={8}>
              <TextField
                fullWidth
                label="Nombre del Proyecto"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                error={!!error}
                helperText={error}
              />
            </Grid>
            <Grid item xs={4}>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={createProject}
                fullWidth
              >
                Crear Proyecto
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Typography variant="h6" sx={{ mb: 2 }}>
        Proyectos Existentes
      </Typography>

      {projects.length === 0 ? (
        <Alert severity="info">
          No hay proyectos creados. Crea tu primer proyecto para comenzar.
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {projects.map((project) => (
            <Grid item xs={12} md={6} lg={4} key={project.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <FolderOpen sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="h6">
                      {project.name}
                    </Typography>
                  </Box>
                  <Button variant="outlined" size="small">
                    Abrir Proyecto
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}