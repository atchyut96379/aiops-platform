import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { getApiErrorMessage } from '../api/client';
import { api } from '../api/client';

interface PlanInfo {
  plan: string;
  limits: Record<string, number | boolean>;
  available_plans: string[];
}

const PLAN_LABELS: Record<string, string> = {
  free: 'Free',
  starter: 'Starter',
  professional: 'Professional',
  enterprise: 'Enterprise',
};

export function BillingPage() {
  const qc = useQueryClient();
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const { data: planInfo, isLoading } = useQuery({
    queryKey: ['billing-plan'],
    queryFn: async () => {
      const { data: plan } = await api.get<PlanInfo>('/api/v1/organizations/me/billing/plan');
      return plan;
    },
  });

  const checkoutMutation = useMutation({
    mutationFn: (plan: string) =>
      api.post('/api/v1/organizations/me/billing/checkout', { plan }),
    onSuccess: (res) => {
      setError('');
      const body = res.data as { upgraded?: boolean; checkout_url?: string | null; message?: string };
      if (body.checkout_url) {
        window.location.href = body.checkout_url;
        return;
      }
      setMessage(body.message ?? 'Plan updated successfully');
      qc.invalidateQueries({ queryKey: ['billing-plan'] });
    },
    onError: (err) => {
      setMessage('');
      setError(getApiErrorMessage(err, 'Checkout failed'));
    },
  });

  const currentPlan = planInfo?.plan ?? 'free';

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Billing & plans
      </Typography>
      {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Stack spacing={2} maxWidth={900}>
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary">Current plan</Typography>
            <Typography variant="h4" mt={1}>{PLAN_LABELS[currentPlan] ?? currentPlan}</Typography>
            {planInfo?.limits && (
              <Typography variant="body2" color="text.secondary" mt={1}>
                Assets: {String(planInfo.limits.max_assets)} · Agents: {String(planInfo.limits.max_agents)} ·
                AI: {planInfo.limits.ai_enabled ? 'enabled' : 'disabled'}
              </Typography>
            )}
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>Available plans</Typography>
            {isLoading ? (
              <Typography color="text.secondary">Loading…</Typography>
            ) : (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Plan</TableCell>
                    <TableCell>Assets</TableCell>
                    <TableCell>Agents</TableCell>
                    <TableCell>AI</TableCell>
                    <TableCell align="right">Action</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(planInfo?.available_plans ?? []).map((plan) => (
                    <TableRow key={plan} selected={plan === currentPlan}>
                      <TableCell>
                        {PLAN_LABELS[plan] ?? plan}
                        {plan === currentPlan && <Chip size="small" label="Current" sx={{ ml: 1 }} />}
                      </TableCell>
                      <TableCell>{plan === 'free' ? '10' : plan === 'starter' ? '50' : plan === 'professional' ? '200' : '10000+'}</TableCell>
                      <TableCell>{plan === 'free' ? '2' : plan === 'starter' ? '10' : plan === 'professional' ? '50' : '500'}</TableCell>
                      <TableCell>{plan === 'free' ? 'No' : 'Yes'}</TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          variant={plan === currentPlan ? 'outlined' : 'contained'}
                          disabled={plan === currentPlan || plan === 'free' || checkoutMutation.isPending}
                          onClick={() => checkoutMutation.mutate(plan)}
                        >
                          {plan === currentPlan ? 'Active' : 'Upgrade'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
            <Typography variant="caption" color="text.secondary" display="block" mt={2}>
              Without Stripe keys configured, upgrades apply immediately in demo mode.
            </Typography>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
