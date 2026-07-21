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

export function AssetsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    asset_type: 'linux_server',
    hostname: '',
    ip_address: '',
    environment: 'production',
    status: 'healthy',
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['assets'],
    queryFn: async () => {
      const { data: assets } = await api.get<Asset[]>('/api/v1/organizations/me/assets');
      return assets;
    },
  });

  const createMutation = useMutation({
    mutationFn: () => api.post('/api/v1/organizations/me/assets', form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] });
      setOpen(false);
    },
  });

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={700}>
          Infrastructure assets
        </Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>
          Add asset
        </Button>
      </Stack>
      {error && <Alert severity="error">Failed to load assets</Alert>}
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Hostname</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>IP</TableCell>
            <TableCell>Environment</TableCell>
            <TableCell>Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={5}>Loading…</TableCell>
            </TableRow>
          ) : (
            (data ?? []).map((asset) => (
              <TableRow key={asset.id}>
                <TableCell>{asset.hostname}</TableCell>
                <TableCell>{asset.asset_type}</TableCell>
                <TableCell>{asset.ip_address ?? '—'}</TableCell>
                <TableCell>{asset.environment}</TableCell>
                <TableCell>
                  <Chip size="small" label={asset.status} color={asset.status === 'healthy' ? 'success' : 'warning'} />
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Add infrastructure asset</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField label="Hostname" value={form.hostname} onChange={(e) => setForm({ ...form, hostname: e.target.value })} fullWidth />
            <TextField label="IP address" value={form.ip_address} onChange={(e) => setForm({ ...form, ip_address: e.target.value })} fullWidth />
            <TextField select label="Type" value={form.asset_type} onChange={(e) => setForm({ ...form, asset_type: e.target.value })} fullWidth>
              <MenuItem value="linux_server">Linux server</MenuItem>
              <MenuItem value="windows_server">Windows server</MenuItem>
              <MenuItem value="database">Database</MenuItem>
            </TextField>
            <TextField select label="Environment" value={form.environment} onChange={(e) => setForm({ ...form, environment: e.target.value })} fullWidth>
              <MenuItem value="production">Production</MenuItem>
              <MenuItem value="staging">Staging</MenuItem>
              <MenuItem value="development">Development</MenuItem>
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => createMutation.mutate()} disabled={!form.hostname}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
