import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { api } from '../api/client';

interface LogEntry {
  id: number;
  level: string;
  source: string;
  message: string;
  host: string | null;
  logged_at: string;
  asset_id: number | null;
}

interface LogSearchResponse {
  items: LogEntry[];
  total: number;
}

export function LogsPage() {
  const [query, setQuery] = useState('');
  const [level, setLevel] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['logs', query, level],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (query) params.set('q', query);
      if (level) params.set('level', level);
      const { data: result } = await api.get<LogSearchResponse>(`/api/v1/organizations/me/logs?${params}`);
      return result;
    },
  });

  if (error) return <Alert severity="error">Failed to load logs</Alert>;

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Centralized logs
      </Typography>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} mb={2}>
        <TextField label="Search" value={query} onChange={(e) => setQuery(e.target.value)} fullWidth />
        <TextField label="Level filter" value={level} onChange={(e) => setLevel(e.target.value)} placeholder="error, warning, info" sx={{ minWidth: 180 }} />
      </Stack>
      <Typography variant="body2" color="text.secondary" mb={1}>
        {data?.total ?? 0} log entries stored
      </Typography>
      <Card variant="outlined">
        <CardContent sx={{ p: 0 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Time</TableCell>
                <TableCell>Level</TableCell>
                <TableCell>Source</TableCell>
                <TableCell>Host</TableCell>
                <TableCell>Message</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={5}>Loading…</TableCell></TableRow>
              ) : (
                (data?.items ?? []).map((log) => (
                  <TableRow key={log.id}>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>{new Date(log.logged_at).toLocaleString()}</TableCell>
                    <TableCell><Chip size="small" label={log.level} color={log.level === 'error' ? 'error' : 'default'} /></TableCell>
                    <TableCell>{log.source}</TableCell>
                    <TableCell>{log.host ?? '—'}</TableCell>
                    <TableCell sx={{ maxWidth: 480, overflow: 'hidden', textOverflow: 'ellipsis' }}>{log.message}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Box>
  );
}
