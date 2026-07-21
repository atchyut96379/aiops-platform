import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Chip,
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

interface LiveAsset {
  asset_id: number;
  hostname: string;
  metrics: Record<string, { value: number; unit?: string; recorded_at?: string }>;
}

interface LiveSnapshot {
  as_of: string;
  assets: LiveAsset[];
}

export function MonitoringPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [selectedAssetId, setSelectedAssetId] = useState('');
  const [liveEnabled, setLiveEnabled] = useState(true);
  const [form, setForm] = useState({ metric_type: 'cpu.percent', metric_value: 50 });

  const { data: assets } = useQuery({
    queryKey: ['assets'],
    queryFn: async () => {
      const { data } = await api.get<Asset[]>('/api/v1/organizations/me/assets');
      return data;
    },
  });

  const assetId = selectedAssetId || (assets?.[0] ? String(assets[0].id) : '');

  const { data: live } = useQuery({
    queryKey: ['live-metrics'],
    queryFn: async () => {
      const { data: snapshot } = await api.get<LiveSnapshot>('/api/v1/organizations/me/monitoring/live?minutes=15');
      return snapshot;
    },
    refetchInterval: liveEnabled ? 5000 : false,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['metrics', assetId],
    queryFn: async () => {
      const { data: metrics } = await api.get<Metric[]>(
        `/api/v1/organizations/me/monitoring/assets/${assetId}/metrics`,
      );
      return metrics;
    },
    enabled: Boolean(assetId),
    refetchInterval: liveEnabled ? 10000 : false,
  });

  const ingestMutation = useMutation({
    mutationFn: () =>
      api.post(`/api/v1/organizations/me/monitoring/assets/${assetId}/metrics`, {
        metric_type: form.metric_type,
        metric_value: Number(form.metric_value),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['metrics', assetId] });
      qc.invalidateQueries({ queryKey: ['live-metrics'] });
      qc.invalidateQueries({ queryKey: ['alerts'] });
      setOpen(false);
    },
  });

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Stack>
          <Typography variant="h5" fontWeight={700}>Monitoring metrics</Typography>
          {live?.as_of && (
            <Typography variant="caption" color="text.secondary">
              Live updated {new Date(live.as_of).toLocaleTimeString()}
            </Typography>
          )}
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <Chip
            label={liveEnabled ? 'Live (5s)' : 'Paused'}
            color={liveEnabled ? 'success' : 'default'}
            onClick={() => setLiveEnabled((v) => !v)}
            clickable
          />
          <TextField
            select
            size="small"
            label="Asset"
            value={assetId}
            onChange={(e) => setSelectedAssetId(e.target.value)}
            sx={{ minWidth: 220 }}
          >
            {(assets ?? []).map((a) => (
              <MenuItem key={a.id} value={String(a.id)}>{a.hostname}</MenuItem>
            ))}
          </TextField>
          <Button variant="contained" onClick={() => setOpen(true)} disabled={!assetId}>Ingest metric</Button>
        </Stack>
      </Stack>

      {(live?.assets ?? []).length > 0 && (
        <Stack direction="row" spacing={1} mb={2} flexWrap="wrap" useFlexGap>
          {live!.assets.map((a) => (
            <Chip
              key={a.asset_id}
              variant="outlined"
              label={`${a.hostname}: CPU ${a.metrics['cpu.percent']?.value ?? '—'}% / MEM ${a.metrics['memory.percent']?.value ?? '—'}%`}
            />
          ))}
        </Stack>
      )}

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
            <TableRow><TableCell colSpan={4}>Loading…</TableCell></TableRow>
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
              <MenuItem value="disk.percent">Disk %</MenuItem>
            </TextField>
            <TextField label="Value" type="number" value={form.metric_value} onChange={(e) => setForm({ ...form, metric_value: Number(e.target.value) })} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => ingestMutation.mutate()} disabled={!assetId}>Submit</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
