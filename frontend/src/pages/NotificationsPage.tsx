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

interface NotificationLog {
  id: number;
  status: string;
  message: string;
  error?: string;
  created_at?: string;
}

export function NotificationsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: '',
    channel_type: 'email',
    min_alert_level: 'medium',
    config: {
      recipients: [''] as string[],
      webhook_url: '',
      url: '',
    },
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['notification-channels'],
    queryFn: async () => {
      const { data: channels } = await api.get<NotificationChannel[]>(
        '/api/v1/organizations/me/notification-channels',
      );
      return channels;
    },
  });

  const { data: logs } = useQuery({
    queryKey: ['notification-logs'],
    queryFn: async () => {
      const { data: entries } = await api.get<NotificationLog[]>(
        '/api/v1/organizations/me/notification-logs',
      );
      return entries;
    },
  });

  const buildConfig = () => {
    if (form.channel_type === 'email') {
      return { recipients: form.config.recipients.filter(Boolean) };
    }
    if (form.channel_type === 'slack' || form.channel_type === 'teams') {
      return { webhook_url: form.config.webhook_url };
    }
    return { url: form.config.url };
  };

  const createMutation = useMutation({
    mutationFn: () =>
      api.post('/api/v1/organizations/me/notification-channels', {
        name: form.name,
        channel_type: form.channel_type,
        min_alert_level: form.min_alert_level,
        is_active: true,
        config: buildConfig(),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notification-channels'] });
      qc.invalidateQueries({ queryKey: ['notification-logs'] });
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
      <Table size="small" sx={{ mb: 4 }}>
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

      <Typography variant="h6" fontWeight={600} gutterBottom>
        Delivery logs
      </Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Status</TableCell>
            <TableCell>Message</TableCell>
            <TableCell>When</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(logs ?? []).slice(0, 20).map((log) => (
            <TableRow key={log.id}>
              <TableCell>
                <Chip
                  size="small"
                  label={log.status}
                  color={log.status === 'sent' ? 'success' : log.status === 'failed' ? 'error' : 'default'}
                />
              </TableCell>
              <TableCell sx={{ maxWidth: 400, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {log.message}
              </TableCell>
              <TableCell>{log.created_at ? new Date(log.created_at).toLocaleString() : '—'}</TableCell>
            </TableRow>
          ))}
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
              <MenuItem value="teams">Microsoft Teams</MenuItem>
              <MenuItem value="webhook">Webhook</MenuItem>
            </TextField>
            <TextField select label="Min alert level" value={form.min_alert_level} onChange={(e) => setForm({ ...form, min_alert_level: e.target.value })} fullWidth>
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </TextField>
            {form.channel_type === 'email' && (
              <TextField
                label="Destination email"
                value={form.config.recipients[0]}
                onChange={(e) => setForm({ ...form, config: { ...form.config, recipients: [e.target.value] } })}
                fullWidth
              />
            )}
            {(form.channel_type === 'slack' || form.channel_type === 'teams') && (
              <TextField
                label="Webhook URL"
                value={form.config.webhook_url}
                onChange={(e) => setForm({ ...form, config: { ...form.config, webhook_url: e.target.value } })}
                fullWidth
                helperText="Incoming webhook URL from Slack or Teams"
              />
            )}
            {form.channel_type === 'webhook' && (
              <TextField
                label="Webhook URL"
                value={form.config.url}
                onChange={(e) => setForm({ ...form, config: { ...form.config, url: e.target.value } })}
                fullWidth
              />
            )}
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
