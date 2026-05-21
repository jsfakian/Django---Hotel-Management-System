import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Tabs, Tab, Dialog, DialogTitle, DialogContent, DialogActions, Chip, TextField } from '@mui/material'
import { Edit, Delete, ArrowBack, Star, Save, Close } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetPropertyQuery, useDeletePropertyMutation, useUpdatePropertyMutation } from '../../../features/properties/propertiesApi'

export default function PropertyDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tab, setTab] = useState(0)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [editingAmenities, setEditingAmenities] = useState(false)
  const [editingPolicies, setEditingPolicies] = useState(false)
  const [amenitiesDraft, setAmenitiesDraft] = useState('')
  const [policiesDraft, setPoliciesDraft] = useState('')
  const { data: property, isLoading, error } = useGetPropertyQuery(id)
  const [deleteProperty, { isLoading: deleting }] = useDeletePropertyMutation()
  const [updateProperty, { isLoading: saving }] = useUpdatePropertyMutation()

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!property) return null

  const handleDelete = async () => {
    await deleteProperty(id)
    navigate('/admin/properties')
  }

  const startAmenitiesEdit = () => {
    setAmenitiesDraft((property.amenities || []).join(', '))
    setEditingAmenities(true)
  }

  const startPoliciesEdit = () => {
    setPoliciesDraft(property.policies || '')
    setEditingPolicies(true)
  }

  const saveAmenities = async () => {
    const amenities = amenitiesDraft
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
    const result = await updateProperty({ id, amenities })
    if (!result.error) setEditingAmenities(false)
  }

  const savePolicies = async () => {
    const result = await updateProperty({ id, policies: policiesDraft })
    if (!result.error) setEditingPolicies(false)
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/properties')}>Back</Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<Edit />} onClick={() => navigate(`/admin/properties/${id}/edit`)}>Edit</Button>
          <Button variant="outlined" color="error" startIcon={<Delete />} onClick={() => setDeleteOpen(true)}>Delete</Button>
        </Box>
      </Box>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Typography variant="h5">{property.name}</Typography>
          {Array.from({ length: property.star_rating || 0 }).map((_, i) => <Star key={i} sx={{ color: 'gold', fontSize: 20 }} />)}
        </Box>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
          <Tab label="Overview" />
          <Tab label="Amenities" />
          <Tab label="Policies" />
        </Tabs>
        {tab === 0 && (
          <Grid container spacing={2}>
            {[
              ['Address', property.address],
              ['City', property.city],
              ['Country', property.country],
              ['Phone', property.phone],
              ['Email', property.email],
              ['Manager', property.manager_name || property.manager],
              ['Rooms', property.rooms_count],
            ].map(([label, val]) => (
              <Grid item xs={12} sm={6} md={4} key={label}>
                <Typography variant="caption" color="text.secondary">{label}</Typography>
                <Typography variant="body1">{val || '—'}</Typography>
              </Grid>
            ))}
            {property.description && (
              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">Description</Typography>
                <Typography variant="body2">{property.description}</Typography>
              </Grid>
            )}
          </Grid>
        )}
        {tab === 1 && (
          <Box>
            {!editingAmenities ? (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
                  <Button size="small" startIcon={<Edit />} onClick={startAmenitiesEdit}>Edit Amenities</Button>
                </Box>
                {(property.amenities || []).length > 0
                  ? <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>{(property.amenities || []).map((a, i) => <Chip key={i} label={a} />)}</Box>
                  : <Typography color="text.secondary">No amenities listed.</Typography>}
              </>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  fullWidth
                  label="Amenities (comma separated)"
                  value={amenitiesDraft}
                  onChange={(e) => setAmenitiesDraft(e.target.value)}
                />
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button variant="contained" startIcon={<Save />} onClick={saveAmenities} disabled={saving}>Save</Button>
                  <Button variant="outlined" startIcon={<Close />} onClick={() => setEditingAmenities(false)}>Cancel</Button>
                </Box>
              </Box>
            )}
          </Box>
        )}
        {tab === 2 && (
          <Box>
            {!editingPolicies ? (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
                  <Button size="small" startIcon={<Edit />} onClick={startPoliciesEdit}>Edit Policies</Button>
                </Box>
                {property.policies
                  ? <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{property.policies}</Typography>
                  : <Typography color="text.secondary">No policies defined.</Typography>}
              </>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={5}
                  label="Policies"
                  value={policiesDraft}
                  onChange={(e) => setPoliciesDraft(e.target.value)}
                />
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button variant="contained" startIcon={<Save />} onClick={savePolicies} disabled={saving}>Save</Button>
                  <Button variant="outlined" startIcon={<Close />} onClick={() => setEditingPolicies(false)}>Cancel</Button>
                </Box>
              </Box>
            )}
          </Box>
        )}
      </Paper>
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <DialogTitle>Delete {property.name}?</DialogTitle>
        <DialogContent>This action cannot be undone.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)}>Cancel</Button>
          <Button color="error" onClick={handleDelete} disabled={deleting}>Delete</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
