  const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    icon: path.join(__dirname, 'icon.ico'),
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#ffffff'
  });

  // En desarrollo
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
    pythonProcess = spawn('python', ['../backend/app.py']);
  } else {
    // En producción - cargar el build de React
    mainWindow.loadFile(path.join(__dirname, '../frontend/build/index.html'));
    // Ejecutar el Python empaquetado
    const pythonPath = path.join(process.resourcesPath, 'backend/dist/app.exe');
    pythonProcess = spawn(pythonPath);
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (pythonProcess) pythonProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});
