import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
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

interface Invite {
  id: number;
  email: string;
  role_name: string;
  status: string;
  expires_at: string;
}

export function SettingsPage() {
  const qc = useQueryClient();
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('read_only');
  const [inviteError, setInviteError] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const { data: planInfo } = useQuery({
    queryKey: ['billing-plan'],
    queryFn: async () => {
      const { data: plan } = await api.get('/api/v1/organizations/me/billing/plan');
      return plan as { plan: string; limits: Record<string, number | boolean> };
    },
  });

  const passwordMutation = useMutation({
    mutationFn: () =>
      api.post('/api/v1/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      }),
    onSuccess: () => {
      setCurrentPassword('');
      setNewPassword('');
      setPasswordError('');
      setPasswordMessage('Password updated successfully');
    },
    onError: (err) => {
      setPasswordMessage('');
      setPasswordError(getApiErrorMessage(err, 'Failed to change password'));
    },
  });

  const { data, error } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const { data: profile } = await api.get('/api/v1/users/me');
      return profile;
    },
  });

  const { data: invites } = useQuery({
    queryKey: ['invites'],
    queryFn: async () => {
      const { data: list } = await api.get<Invite[]>('/api/v1/organizations/me/invites');
      return list;
    },
  });

  const inviteMutation = useMutation({
    mutationFn: () =>
      api.post('/api/v1/organizations/me/invites', {
        email: inviteEmail,
        role: inviteRole,
      }),
    onSuccess: () => {
      setInviteEmail('');
      setInviteError('');
      qc.invalidateQueries({ queryKey: ['invites'] });
    },
    onError: (err) => setInviteError(getApiErrorMessage(err, 'Failed to send invite')),
  });

  if (error) return <Alert severity="error">Failed to load profile</Alert>;

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Settings
      </Typography>
      <Stack spacing={2} maxWidth={720}>
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary">
              Profile
            </Typography>
            <Typography variant="h6">
              {data?.first_name} {data?.last_name}
            </Typography>
            <Typography>{data?.email}</Typography>
          </CardContent>
        </Card>
        {data?.memberships?.[0] && (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                Organization
              </Typography>
              <Typography variant="h6">{data.memberships[0].organization_name}</Typography>
              <Typography variant="body2">Role: {data.memberships[0].role_name}</Typography>
            </CardContent>
          </Card>
        )}

        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>Subscription plan</Typography>
            <Typography variant="body1">Current plan: <strong>{planInfo?.plan ?? 'free'}</strong></Typography>
            {planInfo?.limits && (
              <Typography variant="body2" color="text.secondary" mt={1}>
                Agents: {String(planInfo.limits.max_agents)} · Assets: {String(planInfo.limits.max_assets)} · Alert rules: {String(planInfo.limits.max_alert_rules)}
              </Typography>
            )}
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>Change password</Typography>
            {passwordError && <Alert severity="error" sx={{ mb: 2 }}>{passwordError}</Alert>}
            {passwordMessage && <Alert severity="success" sx={{ mb: 2 }}>{passwordMessage}</Alert>}
            <Stack spacing={2}>
              <TextField label="Current password" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} fullWidth />
              <TextField label="New password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} fullWidth />
              <Button variant="contained" onClick={() => passwordMutation.mutate()} disabled={!currentPassword || !newPassword}>
                Update password
              </Button>
            </Stack>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Invite team member
            </Typography>
            {inviteError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {inviteError}
              </Alert>
            )}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} mb={2}>
              <TextField
                label="Email"
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                fullWidth
              />
              <TextField
                select
                label="Role"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                sx={{ minWidth: 180 }}
              >
                <MenuItem value="read_only">Read only</MenuItem>
                <MenuItem value="support_engineer">Support engineer</MenuItem>
                <MenuItem value="devops_engineer">DevOps engineer</MenuItem>
                <MenuItem value="organization_admin">Org admin</MenuItem>
              </TextField>
              <Button
                variant="contained"
                onClick={() => inviteMutation.mutate()}
                disabled={!inviteEmail.trim()}
                sx={{ minWidth: 120 }}
              >
                Invite
              </Button>
            </Stack>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Pending invites
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(invites ?? []).map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell>{inv.email}</TableCell>
                    <TableCell>{inv.role_name}</TableCell>
                    <TableCell>
                      <Chip size="small" label={inv.status} />
                    </TableCell>
                  </TableRow>
                ))}
                {!invites?.length && (
                  <TableRow>
                    <TableCell colSpan={3}>No invites yet</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
