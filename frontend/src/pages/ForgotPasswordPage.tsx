import { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, Link, Paper, Stack, TextField, Typography } from '@mui/material';
import { getApiErrorMessage } from '../api/client';
import { api } from '../api/client';

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const { data } = await api.post('/api/v1/auth/forgot-password', { email });
      setMessage(data.message);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to send reset email'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center" p={2}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 420 }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>
          Reset password
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={3}>
          Enter your email and we will send a reset link if the account exists.
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required fullWidth />
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Sending…' : 'Send reset link'}
          </Button>
        </Stack>
        <Typography variant="body2" mt={2}>
          <Link component={RouterLink} to="/login">Back to sign in</Link>
        </Typography>
      </Paper>
    </Box>
  );
}
