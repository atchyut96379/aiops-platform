import { useState } from 'react';
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom';
import { Alert, Box, Button, Link, Paper, Stack, TextField, Typography } from '@mui/material';
import { getApiErrorMessage } from '../api/client';
import { api } from '../api/client';

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [token, setToken] = useState(searchParams.get('token') ?? '');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/api/v1/auth/reset-password', { token, new_password: password });
      navigate('/login', { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to reset password'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center" p={2}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 420 }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>
          Set new password
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <TextField label="Reset token" value={token} onChange={(e) => setToken(e.target.value)} required fullWidth />
          <TextField label="New password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required fullWidth helperText="Min 8 chars, upper, lower, digit" />
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Saving…' : 'Reset password'}
          </Button>
        </Stack>
        <Typography variant="body2" mt={2}>
          <Link component={RouterLink} to="/login">Back to sign in</Link>
        </Typography>
      </Paper>
    </Box>
  );
}
