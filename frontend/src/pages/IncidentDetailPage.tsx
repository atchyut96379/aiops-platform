import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { api } from '../api/client';
import type { Incident } from '../api/types';

interface Comment {
  id: number;
  author_name: string;
  body: string;
  created_at?: string;
}

interface Attachment {
  id: number;
  filename: string;
  file_size: number;
}

export function IncidentDetailPage() {
  const { id } = useParams();
  const incidentId = Number(id);
  const qc = useQueryClient();
  const [comment, setComment] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const { data: incident, error } = useQuery({
    queryKey: ['incident', incidentId],
    queryFn: async () => {
      const { data } = await api.get<Incident>(`/api/v1/organizations/me/incidents/${incidentId}`);
      return data;
    },
    enabled: Number.isFinite(incidentId),
  });

  const { data: comments } = useQuery({
    queryKey: ['incident-comments', incidentId],
    queryFn: async () => {
      const { data } = await api.get<Comment[]>(`/api/v1/organizations/me/incidents/${incidentId}/comments`);
      return data;
    },
    enabled: Number.isFinite(incidentId),
  });

  const { data: attachments } = useQuery({
    queryKey: ['incident-attachments', incidentId],
    queryFn: async () => {
      const { data } = await api.get<Attachment[]>(`/api/v1/organizations/me/incidents/${incidentId}/attachments`);
      return data;
    },
    enabled: Number.isFinite(incidentId),
  });

  const commentMutation = useMutation({
    mutationFn: () => api.post(`/api/v1/organizations/me/incidents/${incidentId}/comments`, { body: comment }),
    onSuccess: () => {
      setComment('');
      qc.invalidateQueries({ queryKey: ['incident-comments', incidentId] });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      await api.post(`/api/v1/organizations/me/incidents/${incidentId}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: () => {
      setFile(null);
      qc.invalidateQueries({ queryKey: ['incident-attachments', incidentId] });
    },
  });

  if (error) return <Alert severity="error">Incident not found</Alert>;
  if (!incident) return <Typography>Loading…</Typography>;

  return (
    <Box>
      <Stack direction="row" spacing={1} alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={700}>
          {incident.title}
        </Typography>
        <Chip label={incident.severity} color={incident.severity === 'critical' ? 'error' : 'default'} />
        <Chip label={incident.status} variant="outlined" />
      </Stack>
      <Typography color="text.secondary" mb={3}>
        {incident.description || 'No description'}
      </Typography>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
        <Card variant="outlined" sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Comments
            </Typography>
            <List dense>
              {(comments ?? []).map((c) => (
                <ListItem key={c.id} alignItems="flex-start">
                  <ListItemText primary={c.author_name} secondary={c.body} />
                </ListItem>
              ))}
            </List>
            <Stack direction="row" spacing={1} mt={2}>
              <TextField size="small" fullWidth placeholder="Add a comment" value={comment} onChange={(e) => setComment(e.target.value)} />
              <Button variant="contained" onClick={() => commentMutation.mutate()} disabled={!comment.trim()}>
                Post
              </Button>
            </Stack>
          </CardContent>
        </Card>

        <Card variant="outlined" sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Attachments
            </Typography>
            <List dense>
              {(attachments ?? []).map((a) => (
                <ListItem key={a.id}>
                  <ListItemText primary={a.filename} secondary={`${a.file_size} bytes`} />
                </ListItem>
              ))}
            </List>
            <Divider sx={{ my: 2 }} />
            <Stack direction="row" spacing={1}>
              <Button component="label" variant="outlined">
                Choose file
                <input hidden type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
              </Button>
              <Button variant="contained" onClick={() => uploadMutation.mutate()} disabled={!file}>
                Upload
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
