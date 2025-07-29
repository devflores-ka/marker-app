// frontend/src/components/ElectropherogramViewer.jsx
import React, { useState, useEffect } from 'react';
import { Box, Paper, TextField, Button, Chip } from '@mui/material';
import Plot from 'react-plotly.js';

export default function ElectropherogramViewer({ sampleId, locus }) {
  const [data, setData] = useState(null);
  const [alleles, setAlleles] = useState(['', '']);
  const [editMode, setEditMode] = useState(false);

  const plotData = data ? [{
    x: data.x,
    y: data.y,
    type: 'scatter',
    mode: 'lines',
    line: { color: '#1976d2', width: 1 },
    name: 'Signal'
  }] : [];

  const layout = {
    title: {
      text: locus,
      font: { size: 16 }
    },
    xaxis: { 
      title: 'Size (bp)',
      gridcolor: '#e0e0e0'
    },
    yaxis: { 
      title: 'RFU',
      gridcolor: '#e0e0e0'
    },
    paper_bgcolor: 'white',
    plot_bgcolor: 'white',
    height: 300,
    margin: { t: 40, r: 20, b: 40, l: 60 }
  };

  return (
    <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
      <Plot
        data={plotData}
        layout={layout}
        config={{ displayModeBar: false }}
        style={{ width: '100%' }}
      />
      
      <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField
          size="small"
          label="Alelo 1"
          value={alleles[0]}
          onChange={(e) => setAlleles([e.target.value, alleles[1]])}
          disabled={!editMode}
          sx={{ width: 100 }}
        />
        <TextField
          size="small"
          label="Alelo 2"
          value={alleles[1]}
          onChange={(e) => setAlleles([alleles[0], e.target.value])}
          disabled={!editMode}
          sx={{ width: 100 }}
        />
        <Button
          variant={editMode ? "contained" : "outlined"}
          size="small"
          onClick={() => {
            if (editMode) {
              // Guardar cambios
              saveAlleles(sampleId, locus, alleles);
            }
            setEditMode(!editMode);
          }}
        >
          {editMode ? 'Guardar' : 'Editar'}
        </Button>
        <Chip 
          label="Revisado" 
          color="success" 
          size="small"
          variant={alleles[0] && alleles[1] ? "filled" : "outlined"}
        />
      </Box>
    </Paper>
  );
}
