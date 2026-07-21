import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Card, CardContent, Stack, Typography } from '@mui/material';
import { api } from '../api/client';

export function SettingsPage() {
  const { data, error } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const { data: profile } = await api.get('/api/v1/users/me');
      return profile;
    },
  });

  if (error) return <Alert severity="error">Failed to load profile</Alert>;

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Settings
      </Typography>
      <Stack spacing={2} maxWidth={640}>
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
      </Stack>
    </Box>
  );
}
