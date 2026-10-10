import React, { useState } from 'react'
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Card,
  CardContent,
  Grid,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material'
import { Add, RoomService } from '@mui/icons-material'
import GuestLayout from '../../components/layout/GuestLayout'
import ErrorAlert from '../../components/common/ErrorAlert'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import EmptyState from '../../components/common/EmptyState'
import {
  useGetRoomServicesQuery,
  useGetCurrentRoomServicesQuery,
  useGetActiveRoomServicesQuery,
  useCreateRoomServiceMutation,
} from '../../features/room-services/roomServicesApi'

const STATUS_COLORS = {
  pending: 'warning',
  in_progress: 'info',
  completed: 'success',
  cancelled: 'error',
}

const SERVICE_LABELS = {
  cleaning: 'Housekeeping',
  maintenance: 'Maintenance',
  food: 'In-room dining',
  laundry: 'Laundry',
  other: 'Other',
}

function ServiceCard({ row }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography fontWeight={700}>
            {SERVICE_LABELS[row.service_type] || row.service_type}
          </Typography>
          <Chip
            size="small"
            label={(row.status || '').replace('_', ' ')}
            color={STATUS_COLORS[row.status] || 'default'}
            sx={{ textTransform: 'capitalize' }}
          />
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {row.description || '—'}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {row.requested_at ? new Date(row.requested_at).toLocaleString() : ''}
        </Typography>
      </CardContent>
    </Card>
  )
}

function ServiceGrid({ rows }) {
  return (
    <Grid container spacing={2}>
      {rows.map((row) => (
        <Grid item xs={12} sm={6} key={row.id || `${row.service_type}-${row.requested_at}`}>
          <ServiceCard row={row} />
        </Grid>
      ))}
    </Grid>
  )
}

function RequestServiceDialog({ open, form, setForm, onClose, onSubmit, creating }) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Request a service</DialogTitle>
      <Box component="form" onSubmit={onSubmit}>
        <DialogContent>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Service type</InputLabel>
            <Select
              value={form.service_type}
              label="Service type"
              onChange={(e) => setForm((f) => ({ ...f, service_type: e.target.value }))}
            >
              {Object.entries(SERVICE_LABELS).map(([value, label]) => (
                <MenuItem key={value} value={value}>
                  {label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            multiline
            rows={3}
            required
            label="How can we help?"
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={creating}>
            Submit
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

export default function RoomServicesPage() {
  const [viewMode, setViewMode] = useState('current')
  const [newOpen, setNewOpen] = useState(false)
  const [form, setForm] = useState({ service_type: 'cleaning', description: '' })
  const allQuery = useGetRoomServicesQuery({}, { skip: viewMode !== 'all' })
  const currentQuery = useGetCurrentRoomServicesQuery({}, { skip: viewMode !== 'current' })
  const activeQuery = useGetActiveRoomServicesQuery({}, { skip: viewMode !== 'active' })
  const selectedQuery =
    viewMode === 'current' ? currentQuery : viewMode === 'active' ? activeQuery : allQuery
  const { data, isLoading, error } = selectedQuery
  const [createRoomService, { isLoading: creating }] = useCreateRoomServiceMutation()
  const rows = data?.results || data || []

  const handleCreate = async (e) => {
    e.preventDefault()
    const result = await createRoomService(form)
    if (!result.error) {
      setNewOpen(false)
      setForm({ service_type: 'cleaning', description: '' })
    }
  }

  return (
    <GuestLayout>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 2,
          mb: 3,
        }}
      >
        <Box>
          <Typography variant="h4" sx={{ fontFamily: '"Fraunces", Georgia, serif' }}>
            Concierge services
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Request housekeeping, dining, or maintenance for your room
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setNewOpen(true)}>
          Request service
        </Button>
      </Box>

      <ToggleButtonGroup
        exclusive
        size="small"
        value={viewMode}
        onChange={(_, v) => v && setViewMode(v)}
        sx={{ mb: 3 }}
      >
        <ToggleButton value="current">Current stay</ToggleButton>
        <ToggleButton value="active">In progress</ToggleButton>
        <ToggleButton value="all">All</ToggleButton>
      </ToggleButtonGroup>

      {error && <ErrorAlert error={error} />}
      {isLoading ? (
        <LoadingSpinner />
      ) : rows.length === 0 ? (
        <EmptyState
          title="No service requests"
          description="Ask for housekeeping, dining, or a quick fix — our team will follow up."
          actionLabel="Request service"
          onAction={() => setNewOpen(true)}
          icon={<RoomService fontSize="large" />}
        />
      ) : (
        <ServiceGrid rows={rows} />
      )}

      <RequestServiceDialog open={newOpen} form={form} setForm={setForm} onClose={() => setNewOpen(false)} onSubmit={handleCreate} creating={creating} />
    </GuestLayout>
  )
}
