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
