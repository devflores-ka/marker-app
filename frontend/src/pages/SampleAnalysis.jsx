// frontend/src/pages/SampleAnalysis.jsx
import React, { useState } from 'react';
import {
  Box, Card, CardContent, Typography, Button,
  Grid, List, ListItem, ListItemText, Alert
} from '@mui/material';
import { CloudUpload, Science } from '@mui/icons-material';

export default function SampleAnalysis() {
  const [samples, setSamples] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setIsUploading(true);
    
    try {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));

      const response = await fetch('http://localhost:8888/api/projects/sample-project/samples/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setSamples([...samples, ...result.samples]);
      }
    } catch (error) {
      console.error('Error uploading files:', error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Análisis de Muestras
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Cargar Archivos FSA
          </Typography>
          <input
            accept=".fsa"
            style={{ display: 'none' }}
            id="file-upload"
            multiple
            type="file"
            onChange={handleFileUpload}
          />
          <label htmlFor="file-upload">
            <Button
              variant="contained"
              component="span"
              startIcon={<CloudUpload />}
              disabled={isUploading}
            >
              {isUploading ? 'Cargando...' : 'Seleccionar Archivos FSA'}
            </Button>
          </label>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Muestras Cargadas
          </Typography>
          
          {samples.length === 0 ? (
            <Alert severity="info">
              No hay muestras cargadas. Sube archivos FSA para comenzar el análisis.
            </Alert>
          ) : (
            <List>
              {samples.map((sample, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={sample.filename}
                    secondary={`ID: ${sample.sample_id}`}
                  />
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Science />}
                  >
                    Analizar
                  </Button>
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}