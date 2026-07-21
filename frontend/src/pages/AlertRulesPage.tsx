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

interface AlertRule {
  id: number;
  name: string;
  metric_type: string;
  operator: string;
  threshold: number;
  level: string;
  asset_id: number | null;
  enabled: boolean;
  cooldown_minutes: number;
}

export function AlertRulesPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: '',
    metric_type: 'cpu.percent',
    operator: 'gte',
    threshold: 80,
    level: 'warning',
    cooldown_minutes: 15,
  });
  const [error, setError] = useState('');

  const { data: rules, error: listError } = useQuery({
    queryKey: ['alert-rules'],
    queryFn: async () => {
      const { data } = await api.get<AlertRule[]>('/api/v1/organizations/me/alert-rules');
      return data;
    },
  });

  const createMutation = useMutation({
    mutationFn: () => api.post('/api/v1/organizations/me/alert-rules', form),
    onSuccess: () => {
      setOpen(false);
      setError('');
      qc.invalidateQueries({ queryKey: ['alert-rules'] });
    },
    onError: (err) => setError(getApiErrorMessage(err, 'Failed to create rule')),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      api.patch(`/api/v1/organizations/me/alert-rules/${id}`, { enabled }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alert-rules'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/organizations/me/alert-rules/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alert-rules'] }),
  });

  if (listError) return <Alert severity="error">Failed to load alert rules</Alert>;

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={700}>
          Alert rules
        </Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>Add rule</Button>
      </Stack>

      <Card variant="outlined">
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Metric</TableCell>
                <TableCell>Condition</TableCell>
                <TableCell>Level</TableCell>
                <TableCell>Cooldown</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(rules ?? []).map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell>{rule.name}</TableCell>
                  <TableCell>{rule.metric_type}</TableCell>
                  <TableCell>{rule.operator} {rule.threshold}</TableCell>
                  <TableCell><Chip size="small" label={rule.level} color={rule.level === 'critical' ? 'error' : 'warning'} /></TableCell>
                  <TableCell>{rule.cooldown_minutes}m</TableCell>
                  <TableCell>{rule.enabled ? 'Enabled' : 'Disabled'}</TableCell>
                  <TableCell align="right">
                    <Button size="small" onClick={() => toggleMutation.mutate({ id: rule.id, enabled: !rule.enabled })}>
                      {rule.enabled ? 'Disable' : 'Enable'}
                    </Button>
                    <Button size="small" color="error" onClick={() => deleteMutation.mutate(rule.id)}>Delete</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create alert rule</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Stack spacing={2} mt={1}>
            <TextField label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} fullWidth />
            <TextField label="Metric type" value={form.metric_type} onChange={(e) => setForm({ ...form, metric_type: e.target.value })} fullWidth helperText="e.g. cpu.percent, memory.percent, disk.percent" />
            <TextField select label="Operator" value={form.operator} onChange={(e) => setForm({ ...form, operator: e.target.value })} fullWidth>
              {['gte', 'lte', 'gt', 'lt', 'eq'].map((op) => <MenuItem key={op} value={op}>{op}</MenuItem>)}
            </TextField>
            <TextField label="Threshold" type="number" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: Number(e.target.value) })} fullWidth />
            <TextField select label="Level" value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} fullWidth>
              {['warning', 'critical', 'high', 'medium', 'low'].map((l) => <MenuItem key={l} value={l}>{l}</MenuItem>)}
            </TextField>
            <TextField label="Cooldown (minutes)" type="number" value={form.cooldown_minutes} onChange={(e) => setForm({ ...form, cooldown_minutes: Number(e.target.value) })} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => createMutation.mutate()} disabled={!form.name}>Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
