import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { 
  Box, Toolbar, AppBar, IconButton, Typography, Drawer, List, 
  ListItem, ListItemButton, ListItemIcon, ListItemText, Divider, Avatar, Menu, MenuItem, Collapse
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import LogoutIcon from '@mui/icons-material/Logout';
import LockResetIcon from '@mui/icons-material/LockReset';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PollIcon from '@mui/icons-material/Poll';
import SettingsIcon from '@mui/icons-material/Settings';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import PeopleIcon from '@mui/icons-material/People';
import { usarAuthStore } from '../context/authStore';

const ANCHO_DRAWER = 260;

const LayoutDashboard = () => {
  const [movilOpen, setMovilOpen] = useState(false);
  const [anchorElUsuario, setAnchorElUsuario] = useState<null | HTMLElement>(null);
  const [configuracionOpen, setConfiguracionOpen] = useState(false); // Estado para menú desplegable de Configuración

  const cerrarSesion = usarAuthStore(state => state.cerrarSesion);
  const usuario = usarAuthStore(state => state.usuario);
  const navegar = useNavigate();
  const location = useLocation();

  const handleAbrirMenuUsuario = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElUsuario(event.currentTarget);
  };

  const handleCerrarMenuUsuario = () => {
    setAnchorElUsuario(null);
  };

  const handleCerrarSesion = () => {
    handleCerrarMenuUsuario();
    cerrarSesion();
    navegar('/login');
  };

  const handleIrACambiarClave = () => {
    handleCerrarMenuUsuario();
    navegar('/cambiar-clave');
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

        {/* Menú de Configuración - Solo Administradores */}
        {usuario?.rol === 'ADMINISTRADOR' && (
          <>
            <ListItem disablePadding onClick={() => setConfiguracionOpen(!configuracionOpen)}>
              <ListItemButton sx={{ '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' } }}>
                <ListItemIcon sx={{ color: 'inherit' }}>
                  <SettingsIcon />
                </ListItemIcon>
                <ListItemText primary="Configuración" />
                {configuracionOpen ? <ExpandLess /> : <ExpandMore />}
              </ListItemButton>
            </ListItem>
            <Collapse in={configuracionOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItemButton
                  sx={{ pl: 4, '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' } }}
                  onClick={() => navegar('/admin/usuarios')}
                  selected={location.pathname === '/admin/usuarios'}
                >
                  <ListItemIcon sx={{ color: 'inherit' }}>
                    <PeopleIcon />
                  </ListItemIcon>
                  <ListItemText primary="Usuarios" />
                </ListItemButton>
              </List>
            </Collapse>
          </>
        )}
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
            <IconButton onClick={handleAbrirMenuUsuario} sx={{ p: 0 }}>
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main', fontSize: 14 }}>
                {usuario?.sub?.charAt(0).toUpperCase()}
              </Avatar>
            </IconButton>
            <Typography
                variant="body2"
                sx={{ ml: 1, mr: 1, display: { xs: 'none', md: 'block' }, cursor: 'pointer' }}
                onClick={handleAbrirMenuUsuario}
            >
              {usuario?.sub}
            </Typography>

            <Menu
              sx={{ mt: '45px' }}
              id="menu-appbar"
              anchorEl={anchorElUsuario}
              anchorOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={Boolean(anchorElUsuario)}
              onClose={handleCerrarMenuUsuario}
            >
              <MenuItem onClick={handleIrACambiarClave}>
                <ListItemIcon>
                    <LockResetIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Cambiar Clave</ListItemText>
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleCerrarSesion}>
                <ListItemIcon>
                    <LogoutIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Cerrar Sesión</ListItemText>
              </MenuItem>
            </Menu>
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