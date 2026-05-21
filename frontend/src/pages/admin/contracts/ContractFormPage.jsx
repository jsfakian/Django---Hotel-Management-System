import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, TextField, Paper, Typography, Grid, FormControl, InputLabel, Select, MenuItem } from '@mui/material'
import { ArrowBack, Save } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useCreateContractMutation } from '../../../features/contracts/contractsApi'
import { useGetTravelAgenciesQuery, useGetPropertiesQuery } from '../../../features/properties/propertiesApi'

export default function ContractFormPage() {
  const navigate = useNavigate()
  const { data: agenciesData } = useGetTravelAgenciesQuery()
  const { data: propsData } = useGetPropertiesQuery()
  const [createContract, { isLoading, error }] = useCreateContractMutation()
  const agencies = agenciesData?.results || agenciesData || []
  const properties = propsData?.results || propsData || []
  const [form, setForm] = useState({ travel_agency: '', property: '', commission_rate: '', start_date: '', end_date: '', terms: '' })

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await createContract(form)
    if (!result.error) navigate(`/admin/contracts/${result.data?.id || ''}`)
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/contracts')}>Back</Button>
        <Typography variant="h5">New Contract</Typography>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Travel Agency</InputLabel>
                <Select name="travel_agency" value={form.travel_agency} label="Travel Agency" onChange={handleChange}>
                  {agencies.map((a) => <MenuItem key={a.id} value={a.id}>{a.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Property</InputLabel>
                <Select name="property" value={form.property} label="Property" onChange={handleChange}>
                  {properties.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}><TextField fullWidth required type="number" label="Commission Rate (%)" name="commission_rate" value={form.commission_rate} onChange={handleChange} inputProps={{ min: 0, max: 100, step: '0.01' }} /></Grid>
            <Grid item xs={12} sm={4}><TextField fullWidth required label="Start Date" name="start_date" type="date" InputLabelProps={{ shrink: true }} value={form.start_date} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={4}><TextField fullWidth required label="End Date" name="end_date" type="date" InputLabelProps={{ shrink: true }} value={form.end_date} onChange={handleChange} /></Grid>
            <Grid item xs={12}><TextField fullWidth multiline rows={6} label="Terms & Conditions" name="terms" value={form.terms} onChange={handleChange} /></Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button type="submit" variant="contained" startIcon={<Save />} disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create Contract'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
