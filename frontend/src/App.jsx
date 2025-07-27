// frontend/src/App.jsx
import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import MainLayout from './layouts/MainLayout';

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
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <MainLayout />
    </ThemeProvider>
  );
}

// frontend/src/layouts/MainLayout.jsx
import React, { useState } from 'react';
import {
  Box, Drawer, AppBar, Toolbar, Typography,
  List, ListItem, ListItemIcon, ListItemText,
  IconButton, Divider
} from '@mui/material';
import {
  FolderOpen, Save, FileDownload, Settings,
  Science, TableChart, Menu as MenuIcon
} from '@mui/icons-material';
import ProjectView from '../pages/ProjectView';
import SampleAnalysis from '../pages/SampleAnalysis';

const drawerWidth = 240;

export default function MainLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [currentView, setCurrentView] = useState('project');

  const menuItems = [
    { text: 'Proyecto', icon: <FolderOpen />, view: 'project' },
    { text: 'Análisis', icon: <Science />, view: 'analysis' },
    { text: 'Tabla de Genotipos', icon: <TableChart />, view: 'genotypes' },
  ];

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap>
          GeneMarker Pro
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem 
            button 
            key={item.text}
            selected={currentView === item.view}
            onClick={() => setCurrentView(item.view)}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          backgroundColor: 'background.paper',
          color: 'text.primary',
          boxShadow: 1,
        }}
      >
        <Toolbar>
          <IconButton
            edge="start"
            onClick={() => setMobileOpen(!mobileOpen)}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Box sx={{ flexGrow: 1 }} />
          <IconButton color="inherit">
            <Save />
          </IconButton>
          <IconButton color="inherit">
            <FileDownload />
          </IconButton>
          <IconButton color="inherit">
            <Settings />
          </IconButton>
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
        }}
      >
        {currentView === 'project' && <ProjectView />}
        {currentView === 'analysis' && <SampleAnalysis />}
        {/* Otras vistas... */}
      </Box>
    </Box>
  );
}
