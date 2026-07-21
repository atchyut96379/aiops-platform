import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
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
import type { Asset } from '../api/types';

interface Metric {
  id: number;
  metric_type: string;
  metric_value: number;
  asset_id?: number;
  recorded_at?: string;
}

export function MonitoringPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [selectedAssetId, setSelectedAssetId] = useState('');
  const [form, setForm] = useState({ metric_type: 'cpu.percent', metric_value: 50 });

  const { data: assets } = useQuery({
    queryKey: ['assets'],
    queryFn: async () => {
      const { data } = await api.get<Asset[]>('/api/v1/organizations/me/assets');
      return data;
    },
  });

  const assetId = selectedAssetId || (assets?.[0] ? String(assets[0].id) : '');

  const { data, isLoading, error } = useQuery({
    queryKey: ['metrics', assetId],
    queryFn: async () => {
      const { data: metrics } = await api.get<Metric[]>(
        `/api/v1/organizations/me/monitoring/assets/${assetId}/metrics`,
      );
      return metrics;
    },
    enabled: Boolean(assetId),
  });

  const ingestMutation = useMutation({
    mutationFn: () =>
      api.post(`/api/v1/organizations/me/monitoring/assets/${assetId}/metrics`, {
        metric_type: form.metric_type,
        metric_value: Number(form.metric_value),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['metrics', assetId] });
      qc.invalidateQueries({ queryKey: ['alerts'] });
      setOpen(false);
    },
  });

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={700}>
          Monitoring metrics
        </Typography>
        <Stack direction="row" spacing={1}>
          <TextField
            select
            size="small"
            label="Asset"
            value={assetId}
            onChange={(e) => setSelectedAssetId(e.target.value)}
            sx={{ minWidth: 220 }}
          >
            {(assets ?? []).map((a) => (
              <MenuItem key={a.id} value={String(a.id)}>
                {a.hostname}
              </MenuItem>
            ))}
          </TextField>
          <Button variant="contained" onClick={() => setOpen(true)} disabled={!assetId}>
            Ingest metric
          </Button>
        </Stack>
      </Stack>
      {error && <Alert severity="error">Failed to load metrics</Alert>}
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Metric</TableCell>
            <TableCell>Value</TableCell>
            <TableCell>Asset ID</TableCell>
            <TableCell>Recorded</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4}>Loading…</TableCell>
            </TableRow>
          ) : (
            (data ?? []).map((m) => (
              <TableRow key={m.id}>
                <TableCell>{m.metric_type}</TableCell>
                <TableCell>{m.metric_value}</TableCell>
                <TableCell>{m.asset_id ?? '—'}</TableCell>
                <TableCell>{m.recorded_at ? new Date(m.recorded_at).toLocaleString() : '—'}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Ingest metric</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField select label="Metric type" value={form.metric_type} onChange={(e) => setForm({ ...form, metric_type: e.target.value })} fullWidth>
              <MenuItem value="cpu.percent">CPU %</MenuItem>
              <MenuItem value="memory.percent">Memory %</MenuItem>
            </TextField>
            <TextField label="Value" type="number" value={form.metric_value} onChange={(e) => setForm({ ...form, metric_value: Number(e.target.value) })} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => ingestMutation.mutate()} disabled={!assetId}>
            Submit
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
