import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { api } from '../api/client';
import type { KnowledgeDocument } from '../api/types';

export function AIPage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState(0);
  const [logText, setLogText] = useState('');
  const [chatMessage, setChatMessage] = useState('');
  const [analysis, setAnalysis] = useState('');
  const [chatReply, setChatReply] = useState('');
  const [docForm, setDocForm] = useState({ title: '', content: '', category: 'runbook' });

  const { data: docs } = useQuery({
    queryKey: ['knowledge'],
    queryFn: async () => {
      const { data } = await api.get<KnowledgeDocument[]>('/api/v1/organizations/me/ai/knowledge');
      return data;
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: () => api.post('/api/v1/organizations/me/ai/analyze-logs', { log_text: logText }),
    onSuccess: (res) => setAnalysis(res.data.summary),
  });

  const chatMutation = useMutation({
    mutationFn: () => api.post('/api/v1/organizations/me/ai/chat', { message: chatMessage }),
    onSuccess: (res) => setChatReply(res.data.reply),
  });

  const docMutation = useMutation({
    mutationFn: () => api.post('/api/v1/organizations/me/ai/knowledge', docForm),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['knowledge'] });
      setDocForm({ title: '', content: '', category: 'runbook' });
    },
  });

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        AI Assistant
      </Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Log analysis" />
        <Tab label="Chat" />
        <Tab label="Knowledge base" />
      </Tabs>

      {tab === 0 && (
        <Stack spacing={2}>
          <TextField multiline rows={6} label="Paste log output" value={logText} onChange={(e) => setLogText(e.target.value)} fullWidth />
          <Button variant="contained" onClick={() => analyzeMutation.mutate()} disabled={!logText.trim()}>
            Analyze
          </Button>
          {analysis && (
            <Alert severity="info">
              <Typography whiteSpace="pre-wrap">{analysis}</Typography>
            </Alert>
          )}
        </Stack>
      )}

      {tab === 1 && (
        <Stack spacing={2}>
          <TextField label="Ask the operations assistant" value={chatMessage} onChange={(e) => setChatMessage(e.target.value)} fullWidth />
          <Button variant="contained" onClick={() => chatMutation.mutate()} disabled={!chatMessage.trim()}>
            Send
          </Button>
          {chatReply && (
            <Card variant="outlined">
              <CardContent>
                <Typography whiteSpace="pre-wrap">{chatReply}</Typography>
              </CardContent>
            </Card>
          )}
        </Stack>
      )}

      {tab === 2 && (
        <Stack spacing={2}>
          <Typography variant="subtitle1">Documents ({docs?.length ?? 0})</Typography>
          {(docs ?? []).map((d) => (
            <Card key={d.id} variant="outlined">
              <CardContent>
                <Typography fontWeight={600}>{d.title}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {d.category}
                </Typography>
              </CardContent>
            </Card>
          ))}
          <Typography variant="subtitle1" mt={2}>
            Add runbook
          </Typography>
          <TextField label="Title" value={docForm.title} onChange={(e) => setDocForm({ ...docForm, title: e.target.value })} fullWidth />
          <TextField multiline rows={4} label="Content" value={docForm.content} onChange={(e) => setDocForm({ ...docForm, content: e.target.value })} fullWidth />
          <Button variant="contained" onClick={() => docMutation.mutate()} disabled={!docForm.title || !docForm.content}>
            Save document
          </Button>
        </Stack>
      )}
    </Box>
  );
}
