import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { 
  Box, Toolbar, AppBar, IconButton, Typography, Drawer, List, 
  ListItem, ListItemButton, ListItemIcon, ListItemText, Divider, Avatar 
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import LogoutIcon from '@mui/icons-material/Logout';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PollIcon from '@mui/icons-material/Poll';
import { usarAuthStore } from '../context/authStore';

const ANCHO_DRAWER = 260;

const LayoutDashboard = () => {
  const [movilOpen, setMovilOpen] = useState(false);
  const cerrarSesion = usarAuthStore(state => state.cerrarSesion);
  const usuario = usarAuthStore(state => state.usuario);
  const navegar = useNavigate();
  const location = useLocation();

  const handleCerrarSesion = () => {
    cerrarSesion();
    navegar('/login');
  };

  const menuItems = [
    { texto: 'Dashboard', icono: <DashboardIcon />, ruta: '/dashboard' },
    { texto: 'Encuestas', icono: <PollIcon />, ruta: '/encuestas' },
  ];

  const drawerContent = (
    <Box sx={{ height: '100%', backgroundColor: 'primary.main', color: 'white' }}>
      <Toolbar sx={{ display: 'flex', flexDirection: 'column', alignItems: 'start', py: 2 }}>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold' }}>
          SAPIENTIA
        </Typography>
        <Typography variant="caption" noWrap component="div" sx={{ opacity: 0.8 }}>
          Panel Administrativo
        </Typography>
      </Toolbar>
      <Divider sx={{ borderColor: 'rgba(255,255,255,0.2)' }} />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.texto} disablePadding>
            <ListItemButton 
              onClick={() => navegar(item.ruta)}
              selected={location.pathname === item.ruta}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'secondary.main',
                  color: 'primary.dark',
                  '&:hover': { backgroundColor: 'secondary.light' }
                },
                '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
              }}
            >
              <ListItemIcon sx={{ color: 'inherit' }}>{item.icono}</ListItemIcon>
              <ListItemText primary={item.texto} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Barra Superior (AppBar) */}
      <AppBar position="fixed" sx={{ width: { sm: `calc(100% - ${ANCHO_DRAWER}px)` }, ml: { sm: `${ANCHO_DRAWER}px` }, bgcolor: 'background.paper', color: 'text.primary', boxShadow: 1 }}>
        <Toolbar>
          <IconButton color="inherit" edge="start" onClick={() => setMovilOpen(!movilOpen)} sx={{ mr: 2, display: { sm: 'none' } }}>
            <MenuIcon />
          </IconButton>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" noWrap component="div" color="primary.main" fontWeight="bold">
              {menuItems.find(m => m.ruta === location.pathname)?.texto || 'Inicio'}
            </Typography>
          </Box>
          
          {/* Info Usuario */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main', fontSize: 14 }}>
              {usuario?.sub?.charAt(0).toUpperCase()}
            </Avatar>
            <Typography variant="body2" sx={{ mr: 2, display: { xs: 'none', md: 'block' } }}>
              {usuario?.sub}
            </Typography>
            <IconButton onClick={handleCerrarSesion} color="primary" title="Cerrar Sesión">
              <LogoutIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Menú Lateral (Drawer) */}
      <Box component="nav" sx={{ width: { sm: ANCHO_DRAWER }, flexShrink: { sm: 0 } }}>
        {/* Drawer Móvil */}
        <Drawer variant="temporary" open={movilOpen} onClose={() => setMovilOpen(false)} ModalProps={{ keepMounted: true }} sx={{ display: { xs: 'block', sm: 'none' }, '& .MuiDrawer-paper': { boxSizing: 'border-box', width: ANCHO_DRAWER } }}>
          {drawerContent}
        </Drawer>
        {/* Drawer Escritorio */}
        <Drawer variant="permanent" sx={{ display: { xs: 'none', sm: 'block' }, '& .MuiDrawer-paper': { boxSizing: 'border-box', width: ANCHO_DRAWER } }} open>
          {drawerContent}
        </Drawer>
      </Box>

      {/* Contenido Principal */}
      <Box component="main" sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${ANCHO_DRAWER}px)` }, minHeight: '100vh', bgcolor: 'background.default' }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};

export default LayoutDashboard;