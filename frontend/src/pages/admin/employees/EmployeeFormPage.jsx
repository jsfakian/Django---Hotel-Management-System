import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, TextField, Paper, Typography, Grid, FormControl, InputLabel, Select, MenuItem } from '@mui/material'
import { ArrowBack, Save } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetEmployeeQuery, useCreateEmployeeMutation, useUpdateEmployeeMutation } from '../../../features/employees/employeesApi'
import { useGetPropertiesQuery } from '../../../features/properties/propertiesApi'

export default function EmployeeFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)
  const { data: emp } = useGetEmployeeQuery(id, { skip: !isEdit })
  const { data: propsData } = useGetPropertiesQuery()
  const [createEmployee, { isLoading: creating, error: createError }] = useCreateEmployeeMutation()
  const [updateEmployee, { isLoading: updating, error: updateError }] = useUpdateEmployeeMutation()
  const properties = propsData?.results || propsData || []
  const error = createError || updateError

  const [form, setForm] = useState({ position: '', department: '', property: '', hire_date: '', status: 'active', salary: '', phone_number: '' })

  useEffect(() => {
    if (emp) setForm({ position: emp.position || '', department: emp.department || '', property: emp.property || '', hire_date: emp.hire_date || '', status: emp.status || 'active', salary: emp.salary || '', phone_number: emp.phone_number || '' })
  }, [emp])

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = isEdit ? await updateEmployee({ id, ...form }) : await createEmployee(form)
    if (!result.error) navigate(isEdit ? `/admin/employees/${id}` : '/admin/employees')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate(isEdit ? `/admin/employees/${id}` : '/admin/employees')}>Back</Button>
        <Typography variant="h5">{isEdit ? 'Edit Employee' : 'Add Employee'}</Typography>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}><TextField fullWidth label="Position" name="position" value={form.position} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth label="Department" name="department" value={form.department} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Property</InputLabel>
                <Select name="property" value={form.property} label="Property" onChange={handleChange}>
                  {properties.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth label="Hire Date" name="hire_date" type="date" InputLabelProps={{ shrink: true }} value={form.hire_date} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select name="status" value={form.status} label="Status" onChange={handleChange}>
                  {['active', 'inactive', 'on_leave', 'terminated'].map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth type="number" label="Salary (€)" name="salary" value={form.salary} onChange={handleChange} inputProps={{ min: 0, step: '0.01' }} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth label="Phone Number" name="phone_number" value={form.phone_number} onChange={handleChange} /></Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button type="submit" variant="contained" startIcon={<Save />} disabled={creating || updating}>
              {creating || updating ? 'Saving...' : 'Save Employee'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
