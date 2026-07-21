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
import type { NotificationChannel } from '../api/types';

export function NotificationsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: '',
    channel_type: 'email',
    min_alert_level: 'medium',
    config: { recipients: [''] as string[] },
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['notification-channels'],
    queryFn: async () => {
      const { data: channels } = await api.get<NotificationChannel[]>('/api/v1/organizations/me/notification-channels');
      return channels;
    },
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.post('/api/v1/organizations/me/notification-channels', {
        name: form.name,
        channel_type: form.channel_type,
        min_alert_level: form.min_alert_level,
        is_active: true,
        config: form.config,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notification-channels'] });
      setOpen(false);
    },
  });

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={700}>
          Notification channels
        </Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>
          Add channel
        </Button>
      </Stack>
      {error && <Alert severity="error">Failed to load notification channels</Alert>}
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Min level</TableCell>
            <TableCell>Active</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4}>Loading…</TableCell>
            </TableRow>
          ) : (
            (data ?? []).map((ch) => (
              <TableRow key={ch.id}>
                <TableCell>{ch.name}</TableCell>
                <TableCell>
                  <Chip size="small" label={ch.channel_type} />
                </TableCell>
                <TableCell>{ch.min_alert_level}</TableCell>
                <TableCell>{ch.is_active ? 'Yes' : 'No'}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Add notification channel</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} fullWidth />
            <TextField select label="Type" value={form.channel_type} onChange={(e) => setForm({ ...form, channel_type: e.target.value })} fullWidth>
              <MenuItem value="email">Email</MenuItem>
              <MenuItem value="slack">Slack</MenuItem>
              <MenuItem value="teams">Teams</MenuItem>
              <MenuItem value="webhook">Webhook</MenuItem>
            </TextField>
            <TextField
              label="Destination email"
              value={form.config.recipients[0]}
              onChange={(e) => setForm({ ...form, config: { recipients: [e.target.value] } })}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => createMutation.mutate()} disabled={!form.name}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
