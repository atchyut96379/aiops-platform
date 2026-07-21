import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, Link, Paper, Stack, TextField, Typography } from '@mui/material';
import { getApiErrorMessage } from '../api/client';
import { api } from '../api/client';

export function VerifyEmailPage() {
  const [token, setToken] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const t = params.get('token');
    if (t) setToken(t);
  }, []);

  const handleVerify = async () => {
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const { data } = await api.post('/api/v1/auth/verify-email', { token });
      setMessage(data.message);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Verification failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    const email = prompt('Enter your email to resend verification:');
    if (!email) return;
    setError('');
    try {
      const { data } = await api.post('/api/v1/auth/resend-verification', { email });
      setMessage(data.message);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to resend'));
    }
  };

  return (
    <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center" p={2}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 420 }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>
          Verify email
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}
        <Stack spacing={2}>
          <TextField label="Verification token" value={token} onChange={(e) => setToken(e.target.value)} fullWidth />
          <Button variant="contained" onClick={handleVerify} disabled={loading || !token}>
            Verify email
          </Button>
          <Button variant="outlined" onClick={handleResend}>
            Resend verification email
          </Button>
        </Stack>
        <Typography variant="body2" mt={2}>
          <Link component={RouterLink} to="/login">Back to sign in</Link>
        </Typography>
      </Paper>
    </Box>
  );
}
