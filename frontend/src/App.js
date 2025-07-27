import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import './App.css';

// Tema minimalista para científicos
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
});

function App() {
  const [backendStatus, setBackendStatus] = useState('checking...');

  useEffect(() => {
    // Verificar conexión con backend
    fetch('http://localhost:8888/api/health')
      .then(res => res.json())
      .then(data => setBackendStatus('Connected'))
      .catch(err => setBackendStatus('Not connected'));
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="App">
        <header className="App-header">
          <h1>Marker App</h1>
          <p>Genetic Analysis Software</p>
          <p>Backend status: {backendStatus}</p>
        </header>
      </div>
    </ThemeProvider>
  );
}

export default App;
