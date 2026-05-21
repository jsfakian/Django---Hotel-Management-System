import React, { useState } from 'react'
import { Box, Button, Grid, Card, CardContent, CardActions, Typography, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material'
import { Add, Delete } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetAnnouncementsQuery, useCreateAnnouncementMutation, useDeleteAnnouncementMutation } from '../../../features/announcements/announcementsApi'

export default function AnnouncementsListPage() {
  const [createOpen, setCreateOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [form, setForm] = useState({ title: '', content: '' })
  const { data, isLoading, error } = useGetAnnouncementsQuery()
  const [createAnnouncement, { isLoading: creating }] = useCreateAnnouncementMutation()
  const [deleteAnnouncement, { isLoading: deleting }] = useDeleteAnnouncementMutation()
  const announcements = data?.results || data || []

  const handleCreate = async (e) => {
    e.preventDefault()
    const result = await createAnnouncement(form)
    if (!result.error) { setCreateOpen(false); setForm({ title: '', content: '' }) }
  }

  const handleDelete = async () => {
    await deleteAnnouncement(deleteTarget.id)
    setDeleteTarget(null)
  }

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3 }}>
        <Button variant="contained" startIcon={<Add />} onClick={() => setCreateOpen(true)}>Create Announcement</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Grid container spacing={2}>
        {announcements.length === 0 && <Grid item xs={12}><Typography color="text.secondary">No announcements yet.</Typography></Grid>}
        {announcements.map((a) => (
          <Grid item xs={12} sm={6} md={4} key={a.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>{a.title}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>{a.content}</Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>{a.created_at ? new Date(a.created_at).toLocaleDateString() : ''}</Typography>
              </CardContent>
              <CardActions>
                <Button size="small" color="error" startIcon={<Delete />} onClick={() => setDeleteTarget(a)}>Delete</Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Announcement</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField required label="Title" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} />
            <TextField required multiline rows={4} label="Content" value={form.content} onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))} />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>Create</Button>
          </DialogActions>
        </Box>
      </Dialog>
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Delete "{deleteTarget?.title}"?</DialogTitle>
        <DialogContent>This cannot be undone.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button color="error" onClick={handleDelete} disabled={deleting}>Delete</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
