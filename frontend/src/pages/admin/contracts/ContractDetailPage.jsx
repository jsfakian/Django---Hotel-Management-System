import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Chip, Dialog, DialogTitle, DialogContent, DialogActions, Alert } from '@mui/material'
import { ArrowBack, Gavel, PictureAsPdf } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetContractQuery, useSignContractMutation } from '../../../features/contracts/contractsApi'
import { downloadFile } from '../../../services/downloadFile'

const STATUS_COLORS = { draft: 'warning', active: 'success', expired: 'default', terminated: 'error' }

export default function ContractDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [signOpen, setSignOpen] = useState(false)
  const [msg, setMsg] = useState('')
  const [pdfLoading, setPdfLoading] = useState(false)
  const { data: contract, isLoading, error } = useGetContractQuery(id)
  const [signContract, { isLoading: signing }] = useSignContractMutation()

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!contract) return null

  const handleSign = async () => {
    const result = await signContract(id)
    if (!result.error) { setMsg('Contract signed successfully.'); setSignOpen(false) }
  }

  const handlePdf = async () => {
    setPdfLoading(true)
    try {
      await downloadFile(`/contracts/${id}/pdf/`, `contract-${id}.pdf`)
    } catch {
      setMsg('PDF download failed.')
    } finally {
      setPdfLoading(false)
    }
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/contracts')}>Back</Button>
        <Button startIcon={<PictureAsPdf />} variant="outlined" onClick={handlePdf} disabled={pdfLoading}>
          {pdfLoading ? 'Downloading…' : 'Download PDF'}
        </Button>
      </Box>
      {msg && <Alert severity={msg.includes('failed') ? 'error' : 'success'} sx={{ mb: 2 }} onClose={() => setMsg('')}>{msg}</Alert>}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Typography variant="h5">Contract #{contract.id}</Typography>
          <Chip label={contract.status} color={STATUS_COLORS[contract.status] || 'default'} />
          {contract.signed && <Chip label="Signed" color="success" size="small" />}
        </Box>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[['Travel Agency', contract.travel_agency_name || contract.travel_agency], ['Property', contract.property_name || contract.property], ['Commission Rate', `${contract.commission_rate || 0}%`], ['Start Date', contract.start_date], ['End Date', contract.end_date]].map(([label, val]) => (
            <Grid item xs={12} sm={6} md={4} key={label}>
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <Typography>{val || '—'}</Typography>
            </Grid>
          ))}
        </Grid>
        {contract.terms && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>Terms & Conditions</Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{contract.terms}</Typography>
            </Paper>
          </Box>
        )}
        {contract.status === 'draft' && !contract.signed && (
          <Button variant="contained" startIcon={<Gavel />} onClick={() => setSignOpen(true)}>Sign Contract</Button>
        )}
      </Paper>
      <Dialog open={signOpen} onClose={() => setSignOpen(false)}>
        <DialogTitle>Sign Contract #{contract.id}?</DialogTitle>
        <DialogContent>This will mark the contract as signed.</DialogContent>
        <DialogActions>
          <Button onClick={() => setSignOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSign} disabled={signing}>Sign</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
