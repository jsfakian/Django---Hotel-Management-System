import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, TextField, Paper, Typography, Grid } from '@mui/material'
import { ArrowBack, Save } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetGuestQuery, useCreateGuestMutation, useUpdateGuestMutation } from '../../../features/guests/guestsApi'

const FIELDS = [
  { name: 'first_name', label: 'First Name', required: true, sm: 6 },
  { name: 'last_name', label: 'Last Name', required: true, sm: 6 },
  { name: 'email', label: 'Email', type: 'email', required: true, sm: 6 },
  { name: 'phone', label: 'Phone', sm: 6 },
  { name: 'address', label: 'Address', sm: 12 },
  { name: 'city', label: 'City', sm: 6 },
  { name: 'country', label: 'Country', sm: 6 },
  { name: 'nationality', label: 'Nationality', sm: 6 },
  { name: 'date_of_birth', label: 'Date of Birth', type: 'date', sm: 6 },
  { name: 'passport_number', label: 'Passport / ID Number', sm: 6 },
]

const INIT = { first_name: '', last_name: '', email: '', phone: '', address: '', city: '', country: '', nationality: '', date_of_birth: '', passport_number: '' }

export default function GuestFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)
  const { data: guest } = useGetGuestQuery(id, { skip: !isEdit })
  const [createGuest, { isLoading: creating, error: createError }] = useCreateGuestMutation()
  const [updateGuest, { isLoading: updating, error: updateError }] = useUpdateGuestMutation()
  const [form, setForm] = useState(INIT)
  const error = createError || updateError

  useEffect(() => {
    if (guest) setForm(Object.fromEntries(Object.keys(INIT).map((k) => [k, guest[k] || ''])))
  }, [guest])

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = isEdit ? await updateGuest({ id, ...form }) : await createGuest(form)
    if (!result.error) navigate(isEdit ? `/admin/guests/${id}` : '/admin/guests')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate(isEdit ? `/admin/guests/${id}` : '/admin/guests')}>Back</Button>
        <Typography variant="h5">{isEdit ? 'Edit Guest' : 'Add Guest'}</Typography>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            {FIELDS.map(({ name, label, type, required, sm }) => (
              <Grid item xs={12} sm={sm} key={name}>
                <TextField fullWidth required={required} label={label} name={name} type={type || 'text'} value={form[name]} onChange={handleChange} InputLabelProps={type === 'date' ? { shrink: true } : undefined} />
              </Grid>
            ))}
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button type="submit" variant="contained" startIcon={<Save />} disabled={creating || updating}>
              {creating || updating ? 'Saving...' : 'Save Guest'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
