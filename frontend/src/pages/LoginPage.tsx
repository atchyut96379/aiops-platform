import { useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Link,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { getApiErrorCode, getApiErrorMessage } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [needsTotp, setNeedsTotp] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password, needsTotp ? totpCode : undefined);
      navigate('/', { replace: true });
    } catch (err) {
      const code = getApiErrorCode(err);
      if (code === 'totp_required') {
        setNeedsTotp(true);
        setError('Enter the 6-digit code from your authenticator app');
      } else if (code === 'invalid_credentials') {
        setError(
          'Invalid email or password. On a new server, register first — your local account is not copied to the VM database.',
        );
      } else {
        setError(getApiErrorMessage(err, 'Sign in failed — check that deploy finished (docker compose ps)'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center" p={2}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 420 }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>
          Sign in to AIOps
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={3}>
          Monitor infrastructure, manage incidents, and use AI assistance.
        </Typography>
        {error && (
          <Alert severity={needsTotp ? 'info' : 'error'} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required fullWidth />
          <TextField label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required fullWidth />
          {needsTotp && (
            <TextField
              label="Authenticator code"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value)}
              required
              fullWidth
              inputProps={{ inputMode: 'numeric', autoComplete: 'one-time-code' }}
            />
          )}
          <Button type="submit" variant="contained" size="large" disabled={loading}>
            {loading ? 'Signing in…' : needsTotp ? 'Verify & sign in' : 'Sign in'}
          </Button>
        </Stack>
        <Typography variant="body2" mt={1}>
          <Link component={RouterLink} to="/forgot-password">Forgot password?</Link>
        </Typography>
        <Typography variant="body2" mt={2}>
          No account?{' '}
          <Link component={RouterLink} to="/register">
            Register
          </Link>
        </Typography>
      </Paper>
    </Box>
  );
}
