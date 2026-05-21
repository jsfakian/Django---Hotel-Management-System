import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, TextField, MenuItem, Select, FormControl, InputLabel, Paper, Typography, Grid } from '@mui/material'
import { ArrowBack, Save } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetPropertyQuery, useCreatePropertyMutation, useUpdatePropertyMutation } from '../../../features/properties/propertiesApi'

export default function PropertyFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const { data: property } = useGetPropertyQuery(id, { skip: !isEdit })
  const [createProperty, { isLoading: creating, error: createError }] = useCreatePropertyMutation()
  const [updateProperty, { isLoading: updating, error: updateError }] = useUpdatePropertyMutation()

  const error = createError || updateError
  const isLoading = creating || updating

  const [form, setForm] = useState({
    name: '',
    address: '',
    city: '',
    country: '',
    star_rating: 3,
    phone: '',
    email: '',
    description: '',
    amenities: '',
    policies: '',
  })

  useEffect(() => {
    if (property) {
      setForm({
        name: property.name || '',
        address: property.address || '',
        city: property.city || '',
        country: property.country || '',
        star_rating: property.star_rating || 3,
        phone: property.phone || '',
        email: property.email || '',
        description: property.description || '',
        amenities: Array.isArray(property.amenities) ? property.amenities.join(', ') : (property.amenities || ''),
        policies: property.policies || '',
      })
    }
  }, [property])

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const payload = {
      ...form,
      amenities: form.amenities
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
    }
    const result = isEdit ? await updateProperty({ id, ...payload }) : await createProperty(payload)
    if (!result.error) navigate(isEdit ? `/admin/properties/${id}` : '/admin/properties')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate(isEdit ? `/admin/properties/${id}` : '/admin/properties')}>Back</Button>
        <Typography variant="h5">{isEdit ? 'Edit Property' : 'Add Property'}</Typography>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={8}><TextField fullWidth required label="Property Name" name="name" value={form.name} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Star Rating</InputLabel>
                <Select name="star_rating" value={form.star_rating} label="Star Rating" onChange={handleChange}>
                  {[1, 2, 3, 4, 5].map((s) => <MenuItem key={s} value={s}>{s} Stars</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}><TextField fullWidth label="Address" name="address" value={form.address} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth label="City" name="city" value={form.city} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth label="Country" name="country" value={form.country} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth label="Phone" name="phone" value={form.phone} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth label="Email" name="email" type="email" value={form.email} onChange={handleChange} /></Grid>
            <Grid item xs={12}><TextField fullWidth multiline rows={4} label="Description" name="description" value={form.description} onChange={handleChange} /></Grid>
            <Grid item xs={12}><TextField fullWidth label="Amenities (comma separated)" name="amenities" value={form.amenities} onChange={handleChange} /></Grid>
            <Grid item xs={12}><TextField fullWidth multiline rows={4} label="Policies" name="policies" value={form.policies} onChange={handleChange} /></Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button type="submit" variant="contained" startIcon={<Save />} disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Property'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
