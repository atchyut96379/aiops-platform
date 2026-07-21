import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { api } from '../api/client';
import type { AuditLog } from '../api/types';

export function AuditPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: async () => {
      const { data: logs } = await api.get<AuditLog[]>('/api/v1/organizations/me/audit-logs');
      return logs;
    },
  });

  const handleExport = async () => {
    const response = await api.get('/api/v1/organizations/me/audit-logs/export', {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'audit-logs.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={700}>
          Audit logs
        </Typography>
        <Button variant="outlined" onClick={handleExport}>
          Export CSV
        </Button>
      </Box>
      {error && <Alert severity="error">Failed to load audit logs</Alert>}
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Action</TableCell>
            <TableCell>User</TableCell>
            <TableCell>Resource</TableCell>
            <TableCell>When</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4}>Loading…</TableCell>
            </TableRow>
          ) : (
            (data ?? []).map((log) => (
              <TableRow key={log.id}>
                <TableCell>{log.action}</TableCell>
                <TableCell>{log.user_id ?? '—'}</TableCell>
                <TableCell>
                  {log.resource_type ?? '—'} {log.resource_id ?? ''}
                </TableCell>
                <TableCell>{log.created_at ? new Date(log.created_at).toLocaleString() : '—'}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Box>
  );
}
