import React, { useState } from 'react'
import { Box, Button, TextField, Paper, Typography, Grid, FormControl, InputLabel, Select, MenuItem, Table, TableBody, TableCell, TableHead, TableRow, Alert, Divider } from '@mui/material'
import { Search } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import {
  useGetPricingAnalysisQuery,
  useGetPricingModelsQuery,
  useAnalyzePricingScenarioMutation,
} from '../../../features/pricing/pricingApi'

export default function PricingAnalysisPage() {
  const [query, setQuery] = useState({ room_id: '', date: '', occupancy_rate: '', season: '' })
  const [scenario, setScenario] = useState({ competitor_price: '' })
  const [submitted, setSubmitted] = useState(null)
  const [scenarioResult, setScenarioResult] = useState(null)
  const { data, isLoading } = useGetPricingAnalysisQuery(submitted, { skip: !submitted })
  const { data: modelsData } = useGetPricingModelsQuery()
  const [analyzeScenario, { isLoading: scenarioLoading }] = useAnalyzePricingScenarioMutation()

  const handleSubmit = (e) => {
    e.preventDefault()
    setSubmitted({
      room_id: query.room_id,
      date: query.date,
      occupancy_rate: query.occupancy_rate || undefined,
      season: query.season || undefined,
    })
    setScenarioResult(null)
  }

  const handleScenario = async () => {
    if (!query.room_id || !query.date) return
    const result = await analyzeScenario({
      room_id: Number(query.room_id),
      date: query.date,
      occupancy_rate: query.occupancy_rate ? Number(query.occupancy_rate) : undefined,
      season: query.season || undefined,
      competitor_price: scenario.competitor_price ? Number(scenario.competitor_price) : undefined,
    })

    if (!result.error) {
      setScenarioResult(result.data)
    }
  }

  const price = data?.ensemble_prediction
  const factors = data?.price_factors || []
  const modelList = modelsData?.models || []

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 3 }}>Dynamic Pricing Analysis</Typography>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2} alignItems="flex-end">
            <Grid item xs={12} sm={3}>
              <TextField fullWidth required label="Room ID" type="number" value={query.room_id} onChange={(e) => setQuery((q) => ({ ...q, room_id: e.target.value }))} />
            </Grid>
            <Grid item xs={12} sm={3}><TextField fullWidth required label="Date" type="date" InputLabelProps={{ shrink: true }} value={query.date} onChange={(e) => setQuery((q) => ({ ...q, date: e.target.value }))} /></Grid>
            <Grid item xs={12} sm={3}><TextField fullWidth label="Occupancy Rate (%)" type="number" value={query.occupancy_rate} onChange={(e) => setQuery((q) => ({ ...q, occupancy_rate: e.target.value }))} /></Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Season</InputLabel>
                <Select value={query.season} label="Season" onChange={(e) => setQuery((q) => ({ ...q, season: e.target.value }))}>
                  <MenuItem value="">Auto</MenuItem>
                  {['low', 'medium', 'high', 'peak'].map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}><Button type="submit" variant="contained" startIcon={<Search />} fullWidth disabled={isLoading}>Analyze</Button></Grid>
          </Grid>
        </Box>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Scenario Analysis</Typography>
        <Grid container spacing={2} alignItems="flex-end">
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Competitor Price"
              type="number"
              value={scenario.competitor_price}
              onChange={(e) => setScenario((s) => ({ ...s, competitor_price: e.target.value }))}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <Button variant="outlined" onClick={handleScenario} disabled={scenarioLoading || !query.room_id || !query.date}>
              {scenarioLoading ? 'Running...' : 'Run Scenario'}
            </Button>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="body2" color="text.secondary">
              Models: {modelList.map((m) => `${m.name} (${Math.round((m.accuracy || 0) * 100)}%)`).join(', ') || 'No models'}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {isLoading && <LoadingSpinner />}
      {data && (
        <Box>
          {price && (
            <Paper sx={{ p: 3, mb: 3, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary">Recommended Price</Typography>
              <Typography variant="h2" fontWeight={700} color={price > 200 ? 'warning.main' : 'success.main'}>€{Number(price).toFixed(2)}</Typography>
              <Typography variant="body2" color="text.secondary">per night</Typography>
            </Paper>
          )}
          {data.summary && <Alert severity="info" sx={{ mb: 3 }}>{data.summary}</Alert>}
          {factors.length > 0 && (
            <Paper sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" gutterBottom>Price Factors</Typography>
              <Divider sx={{ mb: 2 }} />
              <Table size="small">
                <TableHead><TableRow>{['Factor', 'Weight', 'Impact'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
                <TableBody>{factors.map((f, i) => <TableRow key={i}><TableCell>{f.factor}</TableCell><TableCell>{f.weight}</TableCell><TableCell>{f.impact}</TableCell></TableRow>)}</TableBody>
              </Table>
            </Paper>
          )}
          {scenarioResult && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Scenario Result</Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2">Scenario price: €{Number(scenarioResult.ensemble_prediction || 0).toFixed(2)}</Typography>
              <Typography variant="body2">Price change: €{Number(scenarioResult.price_change || 0).toFixed(2)} ({Number(scenarioResult.price_change_percent || 0).toFixed(2)}%)</Typography>
              <Typography variant="body2">3-night revenue impact: €{Number(scenarioResult.revenue_impact_per_3night_stay || 0).toFixed(2)}</Typography>
            </Paper>
          )}
        </Box>
      )}
    </AppLayout>
  )
}
