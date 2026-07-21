import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
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

interface Agent {
  id: number;
  name: string;
  hostname: string | null;
  asset_id: number | null;
  api_key_prefix: string;
  is_active: boolean;
  last_heartbeat_at: string | null;
}

interface Asset {
  id: number;
  hostname: string;
}

export function AgentsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [assetId, setAssetId] = useState<number | ''>('');
  const [newApiKey, setNewApiKey] = useState('');
  const [error, setError] = useState('');

  const { data: agents, error: listError } = useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const { data } = await api.get<Agent[]>('/api/v1/organizations/me/agents');
      return data;
    },
  });

  const { data: assets } = useQuery({
    queryKey: ['assets-for-agents'],
    queryFn: async () => {
      const { data } = await api.get<Asset[]>('/api/v1/organizations/me/assets');
      return data;
    },
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.post('/api/v1/organizations/me/agents', {
        name,
        asset_id: assetId || null,
        hostname: typeof window !== 'undefined' ? window.location.hostname : null,
      }),
    onSuccess: (resp) => {
      setNewApiKey(resp.data.api_key);
      setName('');
      setAssetId('');
      qc.invalidateQueries({ queryKey: ['agents'] });
    },
    onError: (err) => setError(getApiErrorMessage(err, 'Failed to create agent')),
  });

  const revokeMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/organizations/me/agents/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['agents'] }),
  });

  if (listError) return <Alert severity="error">Failed to load agents</Alert>;

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={700}>
          Monitoring agents
        </Typography>
        <Button variant="contained" onClick={() => { setOpen(true); setError(''); setNewApiKey(''); }}>
          Create agent
        </Button>
      </Stack>

      <Card variant="outlined">
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Asset</TableCell>
                <TableCell>Key prefix</TableCell>
                <TableCell>Last heartbeat</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(agents ?? []).map((agent) => (
                <TableRow key={agent.id}>
                  <TableCell>{agent.name}</TableCell>
                  <TableCell>{agent.asset_id ?? '—'}</TableCell>
                  <TableCell>{agent.api_key_prefix}…</TableCell>
                  <TableCell>{agent.last_heartbeat_at ? new Date(agent.last_heartbeat_at).toLocaleString() : 'Never'}</TableCell>
                  <TableCell>{agent.is_active ? 'Active' : 'Revoked'}</TableCell>
                  <TableCell align="right">
                    {agent.is_active && (
                      <Button size="small" color="error" onClick={() => revokeMutation.mutate(agent.id)}>
                        Revoke
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create monitoring agent</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {newApiKey ? (
            <Alert severity="warning">
              Save this API key now — it will not be shown again:
              <Typography component="pre" sx={{ mt: 1, fontSize: 12, wordBreak: 'break-all' }}>{newApiKey}</Typography>
            </Alert>
          ) : (
            <Stack spacing={2} mt={1}>
              <TextField label="Agent name" value={name} onChange={(e) => setName(e.target.value)} fullWidth />
              <TextField select label="Linked asset" value={assetId} onChange={(e) => setAssetId(e.target.value ? Number(e.target.value) : '')} fullWidth>
                <MenuItem value="">None</MenuItem>
                {(assets ?? []).map((a) => (
                  <MenuItem key={a.id} value={a.id}>{a.hostname} (#{a.id})</MenuItem>
                ))}
              </TextField>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>{newApiKey ? 'Done' : 'Cancel'}</Button>
          {!newApiKey && (
            <Button variant="contained" onClick={() => createMutation.mutate()} disabled={!name || createMutation.isPending}>
              Create
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}
