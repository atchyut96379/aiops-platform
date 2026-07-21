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
  Tab,
  Tabs,
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
  sync_status: string;
  last_sync_at: string | null;
}

interface PlatformConnection {
  id: number;
  connection_type: string;
  name: string;
  endpoint: string | null;
  collect_status: string;
  last_collect_at: string | null;
}

export function IntegrationsPage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState(0);
  const [open, setOpen] = useState(false);
  const [platformOpen, setPlatformOpen] = useState(false);
  const [form, setForm] = useState({ provider: 'aws', name: '', access_key: '', secret_key: '', region: 'us-east-1' });
  const [platformForm, setPlatformForm] = useState({ connection_type: 'docker', name: '', endpoint: 'unix:///var/run/docker.sock' });
  const [error, setError] = useState('');
  const [syncResult, setSyncResult] = useState('');

  const { data: integrations } = useQuery({
    queryKey: ['integrations'],
    queryFn: async () => {
      const { data } = await api.get<Integration[]>('/api/v1/organizations/me/integrations');
      return data;
    },
  });

  const { data: platforms } = useQuery({
    queryKey: ['platforms'],
    queryFn: async () => {
      const { data } = await api.get<PlatformConnection[]>('/api/v1/organizations/me/platforms');
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
          region: form.region,
        },
      }),
    onSuccess: () => {
      setOpen(false);
      setError('');
      qc.invalidateQueries({ queryKey: ['integrations'] });
    },
    onError: (err) => setError(getApiErrorMessage(err, 'Failed to connect integration')),
  });

  const platformMutation = useMutation({
    mutationFn: () =>
      api.post('/api/v1/organizations/me/platforms', {
        connection_type: platformForm.connection_type,
        name: platformForm.name,
        endpoint: platformForm.connection_type === 'docker' ? platformForm.endpoint : undefined,
        config: platformForm.connection_type === 'kubernetes' ? { kubeconfig: '' } : {},
      }),
    onSuccess: () => {
      setPlatformOpen(false);
      qc.invalidateQueries({ queryKey: ['platforms'] });
    },
    onError: (err) => setSyncResult(getApiErrorMessage(err, 'Failed to add platform')),
  });

  const syncMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/organizations/me/integrations/${id}/sync`),
    onSuccess: (res) => {
      setSyncResult(res.data.message);
      qc.invalidateQueries({ queryKey: ['integrations'] });
      qc.invalidateQueries({ queryKey: ['assets'] });
    },
    onError: (err) => setSyncResult(getApiErrorMessage(err, 'Sync failed')),
  });

  const collectMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/organizations/me/platforms/${id}/collect`),
    onSuccess: (res) => setSyncResult(res.data.message),
    onError: (err) => setSyncResult(getApiErrorMessage(err, 'Collect failed')),
  });

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>Integrations</Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        Phase 4: real AWS EC2 discovery (with boto3), cloud asset import, Docker and Kubernetes monitoring.
      </Typography>
      {syncResult && <Alert severity="info" sx={{ mb: 2 }} onClose={() => setSyncResult('')}>{syncResult}</Alert>}

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Cloud (AWS/Azure/GCP)" />
        <Tab label="Docker / Kubernetes" />
      </Tabs>

      {tab === 0 && (
        <>
          <Stack direction="row" justifyContent="flex-end" mb={2}>
            <Button variant="contained" onClick={() => setOpen(true)}>Connect cloud</Button>
          </Stack>
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
                        <Button size="small" onClick={() => syncMutation.mutate(item.id)}>Sync & import</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {!integrations?.length && (
                    <TableRow><TableCell colSpan={5}>No cloud integrations. Sync imports VMs into Assets inventory.</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}

      {tab === 1 && (
        <>
          <Stack direction="row" justifyContent="flex-end" mb={2}>
            <Button variant="contained" onClick={() => setPlatformOpen(true)}>Add platform</Button>
          </Stack>
          <Card variant="outlined">
            <CardContent>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Endpoint</TableCell>
                    <TableCell>Last collect</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(platforms ?? []).map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>{p.connection_type}</TableCell>
                      <TableCell>{p.name}</TableCell>
                      <TableCell>{p.endpoint ?? '—'}</TableCell>
                      <TableCell>{p.last_collect_at ? new Date(p.last_collect_at).toLocaleString() : 'Never'}</TableCell>
                      <TableCell align="right">
                        <Button size="small" onClick={() => collectMutation.mutate(p.id)}>Collect metrics</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {!platforms?.length && (
                    <TableRow><TableCell colSpan={5}>Add a Docker host or Kubernetes cluster to monitor containers/pods.</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Connect cloud provider</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Stack spacing={2} mt={1}>
            <TextField select label="Provider" value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} fullWidth>
              <MenuItem value="aws">AWS (real EC2 via boto3)</MenuItem>
              <MenuItem value="azure">Azure (stub)</MenuItem>
              <MenuItem value="gcp">GCP (stub)</MenuItem>
            </TextField>
            <TextField label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} fullWidth />
            <TextField label="Access key ID" value={form.access_key} onChange={(e) => setForm({ ...form, access_key: e.target.value })} fullWidth />
            <TextField label="Secret access key" type="password" value={form.secret_key} onChange={(e) => setForm({ ...form, secret_key: e.target.value })} fullWidth />
            <TextField label="Region" value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })} fullWidth helperText="AWS only, e.g. us-east-1" />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => createMutation.mutate()} disabled={!form.name}>Connect</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={platformOpen} onClose={() => setPlatformOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Docker / Kubernetes</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField select label="Type" value={platformForm.connection_type} onChange={(e) => setPlatformForm({ ...platformForm, connection_type: e.target.value })} fullWidth>
              <MenuItem value="docker">Docker host</MenuItem>
              <MenuItem value="kubernetes">Kubernetes cluster</MenuItem>
            </TextField>
            <TextField label="Name" value={platformForm.name} onChange={(e) => setPlatformForm({ ...platformForm, name: e.target.value })} fullWidth />
            {platformForm.connection_type === 'docker' && (
              <TextField label="Docker endpoint" value={platformForm.endpoint} onChange={(e) => setPlatformForm({ ...platformForm, endpoint: e.target.value })} fullWidth />
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPlatformOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => platformMutation.mutate()} disabled={!platformForm.name}>Add</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
