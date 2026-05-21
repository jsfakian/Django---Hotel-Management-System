import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, TextField, Paper, Typography, Grid, FormControl, InputLabel, Select, MenuItem } from '@mui/material'
import { ArrowBack, Save } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetEventQuery, useCreateEventMutation, useUpdateEventMutation } from '../../../features/events/eventsApi'
import { useGetPropertiesQuery } from '../../../features/properties/propertiesApi'

export default function EventFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)
  const { data: event } = useGetEventQuery(id, { skip: !isEdit })
  const { data: propsData } = useGetPropertiesQuery()
  const [createEvent, { isLoading: creating, error: createError }] = useCreateEventMutation()
  const [updateEvent, { isLoading: updating, error: updateError }] = useUpdateEventMutation()
  const properties = propsData?.results || propsData || []
  const error = createError || updateError

  const [form, setForm] = useState({ title: '', description: '', date: '', time: '', location: '', capacity: '', property: '' })

  useEffect(() => {
    if (event) setForm({ title: event.title || '', description: event.description || '', date: event.date || '', time: event.time || '', location: event.location || '', capacity: event.capacity || '', property: event.property || '' })
  }, [event])

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = isEdit ? await updateEvent({ id, ...form }) : await createEvent(form)
    if (!result.error) navigate(isEdit ? `/admin/events/${id}` : '/admin/events')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate(isEdit ? `/admin/events/${id}` : '/admin/events')}>Back</Button>
        <Typography variant="h5">{isEdit ? 'Edit Event' : 'Create Event'}</Typography>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12}><TextField fullWidth required label="Title" name="title" value={form.title} onChange={handleChange} /></Grid>
            <Grid item xs={12}><TextField fullWidth multiline rows={3} label="Description" name="description" value={form.description} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth required label="Date" name="date" type="date" InputLabelProps={{ shrink: true }} value={form.date} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth label="Time" name="time" type="time" InputLabelProps={{ shrink: true }} value={form.time} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth label="Location" name="location" value={form.location} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth type="number" label="Capacity" name="capacity" value={form.capacity} onChange={handleChange} inputProps={{ min: 1 }} /></Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Property</InputLabel>
                <Select name="property" value={form.property} label="Property" onChange={handleChange}>
                  {properties.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button type="submit" variant="contained" startIcon={<Save />} disabled={creating || updating}>
              {creating || updating ? 'Saving...' : 'Save Event'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
