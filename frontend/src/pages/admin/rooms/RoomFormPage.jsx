import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, TextField, MenuItem, Select, FormControl, InputLabel, Paper, Typography, Grid } from '@mui/material'
import { ArrowBack, Save } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetRoomQuery, useCreateRoomMutation, useUpdateRoomMutation } from '../../../features/rooms/roomsApi'
import { useGetPropertiesQuery } from '../../../features/properties/propertiesApi'

export default function RoomFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const { data: room } = useGetRoomQuery(id, { skip: !isEdit })
  const { data: propertiesData } = useGetPropertiesQuery()
  const [createRoom, { isLoading: creating, error: createError }] = useCreateRoomMutation()
  const [updateRoom, { isLoading: updating, error: updateError }] = useUpdateRoomMutation()

  const properties = propertiesData?.results || propertiesData || []
  const error = createError || updateError
  const isLoading = creating || updating

  const [form, setForm] = useState({ room_number: '', room_type: 'standard', capacity: 2, beds: 1, price_per_night: '', status: 'available', property: '', floor: '', description: '' })

  useEffect(() => {
    if (room) setForm({ room_number: room.room_number || '', room_type: room.room_type || 'standard', capacity: room.capacity || 2, beds: room.beds || 1, price_per_night: room.price_per_night || '', status: room.status || 'available', property: room.property || '', floor: room.floor || '', description: room.description || '' })
  }, [room])

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = isEdit ? await updateRoom({ id, ...form }) : await createRoom(form)
    if (!result.error) navigate(isEdit ? `/admin/rooms/${id}` : '/admin/rooms')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate(isEdit ? `/admin/rooms/${id}` : '/admin/rooms')}>Back</Button>
        <Typography variant="h5">{isEdit ? 'Edit Room' : 'Add Room'}</Typography>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth required label="Room Number" name="room_number" value={form.room_number} onChange={handleChange} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Room Type</InputLabel>
                <Select name="room_type" value={form.room_type} label="Room Type" onChange={handleChange}>
                  {['standard', 'deluxe', 'suite', 'penthouse'].map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} sm={3}>
              <TextField fullWidth type="number" label="Capacity" name="capacity" value={form.capacity} onChange={handleChange} inputProps={{ min: 1 }} />
            </Grid>
            <Grid item xs={6} sm={3}>
              <TextField fullWidth type="number" label="Beds" name="beds" value={form.beds} onChange={handleChange} inputProps={{ min: 1 }} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth required type="number" label="Price per Night (€)" name="price_per_night" value={form.price_per_night} onChange={handleChange} inputProps={{ min: 0, step: '0.01' }} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select name="status" value={form.status} label="Status" onChange={handleChange}>
                  {['available', 'occupied', 'maintenance', 'cleaning', 'blocked'].map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Property</InputLabel>
                <Select name="property" value={form.property} label="Property" onChange={handleChange}>
                  {properties.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Floor" name="floor" value={form.floor} onChange={handleChange} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth multiline rows={3} label="Description" name="description" value={form.description} onChange={handleChange} />
            </Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button type="submit" variant="contained" startIcon={<Save />} disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Room'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
