// electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

// Expone APIs seguras al renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Funciones para comunicación con el main process
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  saveFile: (data) => ipcRenderer.invoke('dialog:saveFile', data),
  
  // Funciones para el backend Python
  callPythonAPI: (endpoint, data) => ipcRenderer.invoke('python:api', endpoint, data),
  
  // Información de la aplicación
  getVersion: () => ipcRenderer.invoke('app:getVersion'),
  
  // Eventos de la aplicación
  onMenuAction: (callback) => ipcRenderer.on('menu:action', callback),
  
  // Para debugging
  log: (message) => console.log('[Preload]', message)
});  
