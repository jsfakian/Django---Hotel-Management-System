import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Chip, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import { ArrowBack, Edit, Delete } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetEmployeeQuery, useDeleteEmployeeMutation, useUpdateEmployeeMutation } from '../../../features/employees/employeesApi'

const STATUS_COLORS = { active: 'success', inactive: 'default', on_leave: 'warning', terminated: 'error' }

export default function EmployeeDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { data: emp, isLoading, error } = useGetEmployeeQuery(id)
  const [deleteEmployee, { isLoading: deleting }] = useDeleteEmployeeMutation()
  const [updateEmployee] = useUpdateEmployeeMutation()

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!emp) return null

  const name = `${emp.user?.first_name || ''} ${emp.user?.last_name || ''}`.trim() || `Employee #${id}`

  const handleDelete = async () => {
    await deleteEmployee(id)
    navigate('/admin/employees')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/employees')}>Back</Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<Edit />} onClick={() => navigate(`/admin/employees/${id}/edit`)}>Edit</Button>
          <Button variant="outlined" color="error" startIcon={<Delete />} onClick={() => setDeleteOpen(true)}>Delete</Button>
        </Box>
      </Box>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Typography variant="h5">{name}</Typography>
          <Chip label={emp.status} color={STATUS_COLORS[emp.status] || 'default'} />
        </Box>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[['Position', emp.position], ['Department', emp.department], ['Property', emp.property_name || emp.property], ['Hire Date', emp.hire_date], ['Salary', `€${Number(emp.salary || 0).toFixed(2)}`], ['Phone', emp.phone_number], ['Email', emp.user?.email]].map(([label, val]) => (
            <Grid item xs={12} sm={6} md={4} key={label}>
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <Typography>{val || '—'}</Typography>
            </Grid>
          ))}
        </Grid>
        {emp.status === 'active' && (
          <Button variant="outlined" color="warning" onClick={() => updateEmployee({ id, status: 'inactive' })}>Set Inactive</Button>
        )}
        {emp.status === 'inactive' && (
          <Button variant="outlined" color="success" onClick={() => updateEmployee({ id, status: 'active' })}>Set Active</Button>
        )}
      </Paper>
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <DialogTitle>Delete {name}?</DialogTitle>
        <DialogContent>This cannot be undone.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)}>Cancel</Button>
          <Button color="error" onClick={handleDelete} disabled={deleting}>Delete</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
