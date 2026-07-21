import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
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
import { getApiErrorMessage } from '../api/client';
import { api } from '../api/client';

interface Integration {
  id: number;
  provider: string;
  name: string;
  is_active: boolean;
  sync_status: string;
  last_sync_at: string | null;
}

export function IntegrationsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ provider: 'aws', name: '', access_key: '', secret_key: '' });
  const [error, setError] = useState('');
  const [syncResult, setSyncResult] = useState('');

  const { data: integrations, error: listError } = useQuery({
    queryKey: ['integrations'],
    queryFn: async () => {
      const { data } = await api.get<Integration[]>('/api/v1/organizations/me/integrations');
      return data;
    },
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.post('/api/v1/organizations/me/integrations', {
        provider: form.provider,
        name: form.name,
        credentials: {
          access_key_id: form.access_key,
          secret_access_key: form.secret_key,
        },
      }),
    onSuccess: () => {
      setOpen(false);
      setError('');
      qc.invalidateQueries({ queryKey: ['integrations'] });
    },
    onError: (err) => setError(getApiErrorMessage(err, 'Failed to connect integration')),
  });

  const syncMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/organizations/me/integrations/${id}/sync`),
    onSuccess: (res) => {
      setSyncResult(res.data.message);
      qc.invalidateQueries({ queryKey: ['integrations'] });
    },
    onError: (err) => setSyncResult(getApiErrorMessage(err, 'Sync failed')),
  });

  if (listError) return <Alert severity="error">Failed to load integrations</Alert>;

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={700}>Cloud integrations</Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>Connect provider</Button>
      </Stack>

      {syncResult && <Alert severity="info" sx={{ mb: 2 }} onClose={() => setSyncResult('')}>{syncResult}</Alert>}

      <Card variant="outlined">
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Provider</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last sync</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(integrations ?? []).map((item) => (
                <TableRow key={item.id}>
                  <TableCell><Chip size="small" label={item.provider.toUpperCase()} /></TableCell>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.sync_status}</TableCell>
                  <TableCell>{item.last_sync_at ? new Date(item.last_sync_at).toLocaleString() : 'Never'}</TableCell>
                  <TableCell align="right">
                    <Button size="small" onClick={() => syncMutation.mutate(item.id)} disabled={syncMutation.isPending}>
                      Sync assets
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!integrations?.length && (
                <TableRow><TableCell colSpan={5}>No cloud integrations yet. Connect AWS, Azure, or GCP.</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Connect cloud provider</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Stack spacing={2} mt={1}>
            <TextField select label="Provider" value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} fullWidth>
              <MenuItem value="aws">AWS</MenuItem>
              <MenuItem value="azure">Azure</MenuItem>
              <MenuItem value="gcp">GCP</MenuItem>
            </TextField>
            <TextField label="Integration name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} fullWidth />
            <TextField label="Access key / client ID" value={form.access_key} onChange={(e) => setForm({ ...form, access_key: e.target.value })} fullWidth />
            <TextField label="Secret key" type="password" value={form.secret_key} onChange={(e) => setForm({ ...form, secret_key: e.target.value })} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => createMutation.mutate()} disabled={!form.name}>Connect</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
