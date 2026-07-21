import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { api } from '../api/client';
import type { Alert as AlertItem } from '../api/types';

export function AlertsPage() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const { data: alerts } = await api.get<AlertItem[]>('/api/v1/organizations/me/alerts');
      return alerts;
    },
  });

  const ackMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/organizations/me/alerts/${id}/acknowledge`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  });

  const resolveMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/organizations/me/alerts/${id}/resolve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  });

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Alerts
      </Typography>
      {error && <Alert severity="error">Failed to load alerts</Alert>}
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Type</TableCell>
            <TableCell>Level</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Acknowledged</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={5}>Loading…</TableCell>
            </TableRow>
          ) : (
            (data ?? []).map((alert) => (
              <TableRow key={alert.id}>
                <TableCell>{alert.alert_type}</TableCell>
                <TableCell>
                  <Chip size="small" label={alert.level} color={alert.level === 'critical' ? 'error' : 'warning'} />
                </TableCell>
                <TableCell>{alert.status}</TableCell>
                <TableCell>{alert.acknowledged ? 'Yes' : 'No'}</TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    {!alert.acknowledged && (
                      <Button size="small" onClick={() => ackMutation.mutate(alert.id)}>
                        Ack
                      </Button>
                    )}
                    {!alert.resolved && (
                      <Button size="small" color="success" onClick={() => resolveMutation.mutate(alert.id)}>
                        Resolve
                      </Button>
                    )}
                  </Stack>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Box>
  );
}
