import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link as RouterLink } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Link,
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
import type { Incident } from '../api/types';

export function IncidentsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    incident_type: 'outage',
    title: '',
    description: '',
    severity: 'medium',
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents'],
    queryFn: async () => {
      const { data: incidents } = await api.get<Incident[]>('/api/v1/organizations/me/incidents');
      return incidents;
    },
  });

  const createMutation = useMutation({
    mutationFn: () => api.post('/api/v1/organizations/me/incidents', form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['incidents'] });
      setOpen(false);
    },
  });

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={700}>
          Incidents
        </Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>
          New incident
        </Button>
      </Stack>
      {error && <Alert severity="error">Failed to load incidents</Alert>}
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Title</TableCell>
            <TableCell>Severity</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Type</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4}>Loading…</TableCell>
            </TableRow>
          ) : (
            (data ?? []).map((inc) => (
              <TableRow key={inc.id} hover>
                <TableCell>
                  <Link component={RouterLink} to={`/incidents/${inc.id}`}>
                    {inc.title}
                  </Link>
                </TableCell>
                <TableCell>
                  <Chip size="small" label={inc.severity} color={inc.severity === 'critical' ? 'error' : 'default'} />
                </TableCell>
                <TableCell>{inc.status}</TableCell>
                <TableCell>{inc.incident_type}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Create incident</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField label="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} fullWidth />
            <TextField label="Description" multiline rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} fullWidth />
            <TextField select label="Severity" value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })} fullWidth>
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => createMutation.mutate()} disabled={!form.title}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
