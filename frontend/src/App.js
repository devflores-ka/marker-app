import React, { useState, useEffect } from 'react';
import './App.css';

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
    <div className="App">
      <header className="App-header">
        <h1>Marker App</h1>
        <p>Genetic Analysis Software</p>
        <p>Backend status: {backendStatus}</p>
      </header>
    </div>
  );
}

export default App;