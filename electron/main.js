const { app, BrowserWindow, ipcMain, Menu } = require('electron');
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
    titleBarStyle: 'default',
    frame: true,
    show: false,
    autoHideMenuBar: false,
    backgroundColor: '#ffffff'
  });

  // Mostrar la ventana cuando esté lista
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // DESARROLLO: Cargar desde localhost
  // PRODUCCIÓN: Cargar desde archivos build
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  
  if (isDev) {
    // En desarrollo - cargar desde localhost
    mainWindow.loadURL('http://localhost:3000');
    
    // Abrir DevTools en desarrollo
    mainWindow.webContents.openDevTools();
    
    // NO iniciar Python aquí porque ya está corriendo manualmente
    console.log('🚀 Modo desarrollo: Cargando desde http://localhost:3000');
    console.log('📝 Asegúrate de que React esté corriendo en localhost:3000');
    console.log('🐍 Asegúrate de que Python esté corriendo en localhost:8888');
  } else {
    // En producción - cargar el build de React
    mainWindow.loadFile(path.join(__dirname, '../frontend/build/index.html'));
    
    // Ejecutar el Python empaquetado
    const pythonPath = path.join(process.resourcesPath, 'backend/dist/app.exe');
    pythonProcess = spawn(pythonPath);
  }

  // Manejar errores de carga
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error('❌ Error cargando:', errorDescription, 'URL:', validatedURL);
    
    if (isDev) {
      console.log('💡 Solución: Asegúrate de que React esté corriendo en http://localhost:3000');
    }
  });
}

function createMenu() {
  const template = [
    {
      label: 'Archivo',
      submenu: [
        {
          label: 'Nuevo Proyecto',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            console.log('Nuevo proyecto');
          }
        },
        {
          label: 'Abrir Proyecto',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            console.log('Abrir proyecto');
          }
        },
        { type: 'separator' },
        {
          label: 'Salir',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Editar',
      submenu: [
        { role: 'undo', label: 'Deshacer' },
        { role: 'redo', label: 'Rehacer' },
        { type: 'separator' },
        { role: 'cut', label: 'Cortar' },
        { role: 'copy', label: 'Copiar' },
        { role: 'paste', label: 'Pegar' }
      ]
    },
    {
      label: 'Ver',
      submenu: [
        { role: 'reload', label: 'Recargar' },
        { role: 'toggledevtools', label: 'Herramientas de Desarrollador' },
        { type: 'separator' },
        { role: 'resetzoom', label: 'Zoom Normal' },
        { role: 'zoomin', label: 'Acercar' },
        { role: 'zoomout', label: 'Alejar' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'Pantalla Completa' }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

app.whenReady().then(() => {
  createWindow();
  createMenu();
});

app.on('window-all-closed', () => {
  // En desarrollo, no matamos Python porque está corriendo manualmente
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
