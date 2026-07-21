import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Button, Card, CardContent, Grid, Skeleton, Stack, Typography } from '@mui/material';
import { api } from '../api/client';
import type { DashboardSummary } from '../api/types';

interface DashboardTrends {
  days: number;
  alerts_by_day: Record<string, number>;
  incidents_by_day: Record<string, number>;
  metrics_by_day: Record<string, number>;
}

function StatCard({ title, value, subtitle }: { title: string; value: number | string; subtitle?: string }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="body2" color="text.secondary">{title}</Typography>
        <Typography variant="h4" fontWeight={700} mt={1}>{value}</Typography>
        {subtitle && <Typography variant="caption" color="text.secondary">{subtitle}</Typography>}
      </CardContent>
    </Card>
  );
}

function TrendChart({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data).slice(-7);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="subtitle2" gutterBottom>{title}</Typography>
        <Stack direction="row" alignItems="flex-end" spacing={1} sx={{ height: 120 }}>
          {entries.length === 0 ? (
            <Typography variant="body2" color="text.secondary">No data yet</Typography>
          ) : (
            entries.map(([day, count]) => (
              <Box key={day} sx={{ flex: 1, textAlign: 'center' }}>
                <Box
                  sx={{
                    height: `${(count / max) * 80}px`,
                    minHeight: count > 0 ? 8 : 2,
                    bgcolor: 'primary.main',
                    borderRadius: 1,
                    mx: 'auto',
                    width: '70%',
                  }}
                />
                <Typography variant="caption" display="block" mt={0.5}>
                  {day.slice(5)}
                </Typography>
                <Typography variant="caption" color="text.secondary">{count}</Typography>
              </Box>
            ))
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const { data: summary } = await api.get<DashboardSummary>('/api/v1/organizations/me/dashboard');
      return summary;
    },
  });

  const { data: trends } = useQuery({
    queryKey: ['dashboard-trends'],
    queryFn: async () => {
      const { data: t } = await api.get<DashboardTrends>('/api/v1/organizations/me/dashboard/trends?days=14');
      return t;
    },
  });

  const downloadReport = async (format: 'csv' | 'pdf' | 'xlsx') => {
    const path =
      format === 'csv'
        ? '/api/v1/organizations/me/reports/incidents'
        : `/api/v1/organizations/me/reports/incidents.${format}`;
    const response = await api.get(path, { responseType: 'blob' });
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `incidents.${format === 'csv' ? 'csv' : format}`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  if (error) return <Alert severity="error">Failed to load dashboard</Alert>;

  return (
    <Box>
      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ sm: 'center' }} mb={2}>
        <Typography variant="h5" fontWeight={700}>Operations overview</Typography>
        <Stack direction="row" spacing={1}>
          <Button size="small" variant="outlined" onClick={() => downloadReport('csv')}>CSV</Button>
          <Button size="small" variant="outlined" onClick={() => downloadReport('pdf')}>PDF</Button>
          <Button size="small" variant="outlined" onClick={() => downloadReport('xlsx')}>Excel</Button>
        </Stack>
      </Stack>
      <Grid container spacing={2}>
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rounded" height={120} />
            </Grid>
          ))
        ) : (
          <>
            <Grid item xs={12} sm={6} md={4}>
              <StatCard title="Total assets" value={data?.total_assets ?? 0} subtitle={`${data?.healthy_assets ?? 0} healthy`} />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <StatCard title="Open alerts" value={data?.open_alerts ?? 0} subtitle={`${data?.critical_alerts ?? 0} critical`} />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <StatCard title="Open incidents" value={data?.open_incidents ?? 0} subtitle={`${data?.closed_incidents ?? 0} closed`} />
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>Alerts by level</Typography>
                  {Object.entries(data?.alerts_by_level ?? {}).map(([level, count]) => (
                    <Typography key={level} variant="body2">{level}: {count}</Typography>
                  ))}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>Incidents by severity</Typography>
                  {Object.entries(data?.incidents_by_severity ?? {}).map(([sev, count]) => (
                    <Typography key={sev} variant="body2">{sev}: {count}</Typography>
                  ))}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>Assets by status</Typography>
                  {Object.entries(data?.assets_by_status ?? {}).map(([status, count]) => (
                    <Typography key={status} variant="body2">{status}: {count}</Typography>
                  ))}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <TrendChart title="Alerts (14 days)" data={trends?.alerts_by_day ?? {}} />
            </Grid>
            <Grid item xs={12} md={4}>
              <TrendChart title="Incidents (14 days)" data={trends?.incidents_by_day ?? {}} />
            </Grid>
            <Grid item xs={12} md={4}>
              <TrendChart title="Metrics ingested (14 days)" data={trends?.metrics_by_day ?? {}} />
            </Grid>
          </>
        )}
      </Grid>
    </Box>
  );
}
