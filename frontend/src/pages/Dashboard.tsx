import { useEffect, useState } from 'react';
import { Grid, Paper, Typography, Box, CircularProgress } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import api from '../api/axios';
import PollIcon from '@mui/icons-material/Poll';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

// Definición de tipos para los reportes
interface DashboardStats {
  total_encuestas_completadas: number;
  total_respuestas_procesadas: number;
  ultime_actualizacion_etl: string;
}

interface ParticipacionFacultad {
  facultad: string;
  cantidad_respuestas: number;
}

const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [graficoData, setGraficoData] = useState<ParticipacionFacultad[]>([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const [resStats, resGrafico] = await Promise.all([
          api.get('/reportes/stats-generales'),
          api.get('/reportes/participacion-por-facultad')
        ]);
        setStats(resStats.data);
        setGraficoData(resGrafico.data);
      } catch (error) {
        console.error("Error cargando dashboard:", error);
      } finally {
        setCargando(false);
      }
    };

    cargarDatos();
  }, []);

  if (cargando) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 'bold', color: 'text.primary' }}>
        Resumen General
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Tarjeta 1: Encuestas Completadas */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, display: 'flex', alignItems: 'center', borderRadius: 4, background: 'linear-gradient(135deg, #023E8A 0%, #0077B6 100%)', color: 'white' }}>
            <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.2)', borderRadius: 2, mr: 2 }}>
              <CheckCircleIcon sx={{ fontSize: 40 }} />
            </Box>
            <Box>
              <Typography variant="h3" fontWeight="bold">{stats?.total_encuestas_completadas}</Typography>
              <Typography variant="body1" sx={{ opacity: 0.9 }}>Encuestas Completadas</Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Tarjeta 2: Respuestas Procesadas */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, display: 'flex', alignItems: 'center', borderRadius: 4, background: 'linear-gradient(135deg, #0096C7 0%, #48CAE4 100%)', color: 'white' }}>
            <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.2)', borderRadius: 2, mr: 2 }}>
              <PollIcon sx={{ fontSize: 40 }} />
            </Box>
            <Box>
              <Typography variant="h3" fontWeight="bold">{stats?.total_respuestas_procesadas}</Typography>
              <Typography variant="body1" sx={{ opacity: 0.9 }}>Respuestas Analizadas (OLAP)</Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Gráfico de Barras */}
      <Typography variant="h5" gutterBottom sx={{ mb: 2, fontWeight: 600 }}>
        Participación por Facultad
      </Typography>
      <Paper sx={{ p: 3, borderRadius: 3, height: 400 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={graficoData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" />
            <YAxis dataKey="facultad" type="category" width={150} style={{ fontSize: '12px', fontWeight: 500 }} />
            <Tooltip 
              contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
              cursor={{ fill: 'rgba(0,0,0,0.05)' }}
            />
            <Bar dataKey="cantidad_respuestas" fill="#023E8A" radius={[0, 4, 4, 0]}>
              {graficoData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#023E8A' : '#0077B6'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Paper>
    </Box>
  );
};

export default Dashboard;