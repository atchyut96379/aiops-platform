import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Card, CardContent, Grid, Skeleton, Typography } from '@mui/material';
import { api } from '../api/client';
import type { DashboardSummary } from '../api/types';

function StatCard({ title, value, subtitle }: { title: string; value: number | string; subtitle?: string }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h4" fontWeight={700} mt={1}>
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
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

  if (error) {
    return <Alert severity="error">Failed to load dashboard</Alert>;
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Operations overview
      </Typography>
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
                  <Typography variant="subtitle2" gutterBottom>
                    Alerts by level
                  </Typography>
                  {Object.entries(data?.alerts_by_level ?? {}).map(([level, count]) => (
                    <Typography key={level} variant="body2">
                      {level}: {count}
                    </Typography>
                  ))}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Incidents by severity
                  </Typography>
                  {Object.entries(data?.incidents_by_severity ?? {}).map(([sev, count]) => (
                    <Typography key={sev} variant="body2">
                      {sev}: {count}
                    </Typography>
                  ))}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Assets by status
                  </Typography>
                  {Object.entries(data?.assets_by_status ?? {}).map(([status, count]) => (
                    <Typography key={status} variant="body2">
                      {status}: {count}
                    </Typography>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
      </Grid>
    </Box>
  );
}
