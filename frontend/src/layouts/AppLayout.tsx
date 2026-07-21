import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import DashboardIcon from '@mui/icons-material/Dashboard';
import StorageIcon from '@mui/icons-material/Storage';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import SettingsIcon from '@mui/icons-material/Settings';
import HistoryIcon from '@mui/icons-material/History';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import CampaignIcon from '@mui/icons-material/Campaign';
import DnsIcon from '@mui/icons-material/Dns';
import LogoutIcon from '@mui/icons-material/Logout';
import RuleIcon from '@mui/icons-material/Rule';
import ArticleIcon from '@mui/icons-material/Article';
import CloudQueueIcon from '@mui/icons-material/CloudQueue';
import { useAuth } from '../contexts/AuthContext';

const drawerWidth = 260;

const navItems = [
  { label: 'Dashboard', path: '/', icon: <DashboardIcon /> },
  { label: 'Assets', path: '/assets', icon: <StorageIcon /> },
  { label: 'Agents', path: '/agents', icon: <DnsIcon /> },
  { label: 'Monitoring', path: '/monitoring', icon: <MonitorHeartIcon /> },
  { label: 'Alerts', path: '/alerts', icon: <NotificationsActiveIcon /> },
  { label: 'Alert Rules', path: '/alert-rules', icon: <RuleIcon /> },
  { label: 'Logs', path: '/logs', icon: <ArticleIcon /> },
  { label: 'Incidents', path: '/incidents', icon: <ReportProblemIcon /> },
  { label: 'Notifications', path: '/notifications', icon: <CampaignIcon /> },
  { label: 'AI Assistant', path: '/ai', icon: <SmartToyIcon /> },
  { label: 'Integrations', path: '/integrations', icon: <CloudQueueIcon /> },
  { label: 'Audit Logs', path: '/audit', icon: <HistoryIcon /> },
  { label: 'Settings', path: '/settings', icon: <SettingsIcon /> },
];

export function AppLayout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [open, setOpen] = useState(!isMobile);
  const location = useLocation();
  const { user, logout } = useAuth();

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar>
        <Typography variant="h6" fontWeight={700} color="primary">
          AIOps Platform
        </Typography>
      </Toolbar>
      <List sx={{ flex: 1 }}>
        {navItems.map((item) => (
          <ListItemButton
            key={item.path}
            component={Link}
            to={item.path}
            selected={location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path))}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
      <ListItemButton onClick={logout}>
        <ListItemIcon>
          <LogoutIcon />
        </ListItemIcon>
        <ListItemText primary="Logout" />
      </ListItemButton>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        color="inherit"
        elevation={0}
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton edge="start" onClick={() => setOpen((v) => !v)} sx={{ mr: 1 }}>
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="subtitle1" sx={{ flex: 1 }}>
            {navItems.find((n) => n.path === location.pathname || (n.path !== '/' && location.pathname.startsWith(n.path)))?.label ?? 'AIOps'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {user?.first_name} {user?.last_name}
          </Typography>
        </Toolbar>
      </AppBar>

      <Drawer
        variant={isMobile ? 'temporary' : 'permanent'}
        open={open}
        onClose={() => setOpen(false)}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        {drawer}
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8, width: '100%' }}>
        <Outlet />
      </Box>
    </Box>
  );
}
