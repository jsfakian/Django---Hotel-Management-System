import React, { useState } from 'react'
import { Box, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Grid } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetStorageItemsQuery, useCreateStorageItemMutation, useDeleteStorageItemMutation } from '../../../features/storage/storageApi'

export default function StorageListPage() {
  const [newOpen, setNewOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [form, setForm] = useState({ name: '', category: '', quantity: '', unit: '', location: '' })
  const { data, isLoading, error } = useGetStorageItemsQuery()
  const [createStorageItem, { isLoading: creating }] = useCreateStorageItemMutation()
  const [deleteStorageItem, { isLoading: deleting }] = useDeleteStorageItemMutation()
  const rows = data?.results || data || []

  const columns = [
    { field: 'name', headerName: 'Item', width: 200 },
    { field: 'category', headerName: 'Category', width: 140 },
    { field: 'quantity', headerName: 'Quantity', width: 100 },
    { field: 'unit', headerName: 'Unit', width: 80 },
    { field: 'location', headerName: 'Location', width: 160 },
    { field: 'updated_at', headerName: 'Updated', width: 120, renderCell: (r) => r.updated_at ? new Date(r.updated_at).toLocaleDateString() : '—' },
    { field: 'del', headerName: '', width: 100, renderCell: (r) => <Button size="small" color="error" onClick={(e) => { e.stopPropagation(); setDeleteTarget(r) }}>Delete</Button> },
  ]

  const handleCreate = async (e) => {
    e.preventDefault()
    const result = await createStorageItem(form)
    if (!result.error) { setNewOpen(false); setForm({ name: '', category: '', quantity: '', unit: '', location: '' }) }
  }

  const handleDelete = async () => {
    await deleteStorageItem(deleteTarget.id)
    setDeleteTarget(null)
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<Add />} onClick={() => setNewOpen(true)}>Add Item</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Dialog open={newOpen} onClose={() => setNewOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Storage Item</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent>
            <Grid container spacing={2}>
              {[['name', 'Item Name', true], ['category', 'Category'], ['quantity', 'Quantity', true, 'number'], ['unit', 'Unit (e.g. kg, pcs)'], ['location', 'Location']].map(([field, label, required, type]) => (
                <Grid item xs={12} sm={6} key={field}>
                  <TextField fullWidth required={required} type={type || 'text'} label={label} value={form[field]} onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))} />
                </Grid>
              ))}
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setNewOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>Add</Button>
          </DialogActions>
        </Box>
      </Dialog>
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Delete "{deleteTarget?.name}"?</DialogTitle>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button color="error" onClick={handleDelete} disabled={deleting}>Delete</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
