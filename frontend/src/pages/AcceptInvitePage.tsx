import { useEffect, useState } from 'react';
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom';
import { Alert, Box, Button, Link, Paper, Stack, TextField, Typography } from '@mui/material';
import { getApiErrorMessage, storeAuth } from '../api/client';
import { api } from '../api/client';

export function AcceptInvitePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [token, setToken] = useState(searchParams.get('token') ?? '');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const t = searchParams.get('token');
    if (t) setToken(t);
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post('/api/v1/auth/accept-invite', {
        token,
        first_name: firstName || undefined,
        last_name: lastName || undefined,
        password: password || undefined,
      });
      storeAuth(data.tokens.access_token, data.tokens.refresh_token);
      navigate('/', { replace: true });
      window.location.reload();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to accept invite'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center" p={2}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 480 }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>
          Accept team invite
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={3}>
          Complete your profile if this is a new account.
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <TextField label="Invite token" value={token} onChange={(e) => setToken(e.target.value)} required fullWidth />
          <TextField label="First name" value={firstName} onChange={(e) => setFirstName(e.target.value)} fullWidth />
          <TextField label="Last name" value={lastName} onChange={(e) => setLastName(e.target.value)} fullWidth />
          <TextField label="Password (new users)" type="password" value={password} onChange={(e) => setPassword(e.target.value)} fullWidth helperText="Required for new accounts" />
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Joining…' : 'Accept invite'}
          </Button>
        </Stack>
        <Typography variant="body2" mt={2}>
          <Link component={RouterLink} to="/login">Back to sign in</Link>
        </Typography>
      </Paper>
    </Box>
  );
}
