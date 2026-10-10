import React, { useState } from 'react'
import { Box, Button, TextField, Paper, Typography, Grid, FormControl, InputLabel, Select, MenuItem, Table, TableBody, TableCell, TableHead, TableRow, Alert, Divider } from '@mui/material'
import { Search } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import PageHeader from '../../../components/common/PageHeader'
import {
  useGetPricingAnalysisQuery,
  useGetPricingModelsQuery,
  useAnalyzePricingScenarioMutation,
} from '../../../features/pricing/pricingApi'

const eur = (v) => `€${Number(v || 0).toFixed(2)}`

function QueryForm({ query, setQuery, onSubmit, busy }) {
  const setField = (key) => (e) => setQuery((q) => ({ ...q, [key]: e.target.value }))
  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box component="form" onSubmit={onSubmit}>
        <Grid container spacing={2} alignItems="flex-end">
          <Grid item xs={12} sm={3}>
            <TextField fullWidth required label="Room ID" type="number" value={query.room_id} onChange={setField('room_id')} />
          </Grid>
          <Grid item xs={12} sm={3}><TextField fullWidth required label="Date" type="date" InputLabelProps={{ shrink: true }} value={query.date} onChange={setField('date')} /></Grid>
          <Grid item xs={12} sm={3}><TextField fullWidth label="Occupancy Rate (%)" type="number" value={query.occupancy_rate} onChange={setField('occupancy_rate')} /></Grid>
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth>
              <InputLabel>Season</InputLabel>
              <Select value={query.season} label="Season" onChange={setField('season')}>
                <MenuItem value="">Auto</MenuItem>
                {['low', 'medium', 'high', 'peak'].map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}><Button type="submit" variant="contained" startIcon={<Search />} fullWidth disabled={busy}>Analyze</Button></Grid>
        </Grid>
      </Box>
    </Paper>
  )
}

function ScenarioPanel({ scenario, setScenario, onRun, disabled, running, modelList }) {
  return (
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
          <Button variant="outlined" onClick={onRun} disabled={disabled}>
            {running ? 'Running...' : 'Run Scenario'}
          </Button>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Typography variant="body2" color="text.secondary">
            Models: {modelList.map((m) => `${m.name} (${Math.round((m.accuracy || 0) * 100)}%)`).join(', ') || 'No models'}
          </Typography>
        </Grid>
      </Grid>
    </Paper>
  )
}

function RecommendedPrice({ price }) {
  return (
    <Paper sx={{ p: 3, mb: 3, textAlign: 'center' }}>
      <Typography variant="h6" color="text.secondary">Recommended Price</Typography>
      <Typography variant="h2" fontWeight={700} color={price > 200 ? 'warning.main' : 'success.main'}>€{Number(price).toFixed(2)}</Typography>
      <Typography variant="body2" color="text.secondary">per night</Typography>
    </Paper>
  )
}

function FactorsTable({ factors }) {
  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Typography variant="h6" gutterBottom>Price Factors</Typography>
      <Divider sx={{ mb: 2 }} />
      <Table size="small">
        <TableHead><TableRow>{['Factor', 'Weight', 'Impact'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
        <TableBody>{factors.map((f, i) => <TableRow key={i}><TableCell>{f.factor}</TableCell><TableCell>{f.weight}</TableCell><TableCell>{f.impact}</TableCell></TableRow>)}</TableBody>
      </Table>
    </Paper>
  )
}

function ScenarioResult({ result }) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>Scenario Result</Typography>
      <Divider sx={{ mb: 2 }} />
      <Typography variant="body2">Scenario price: {eur(result.ensemble_prediction)}</Typography>
      <Typography variant="body2">Price change: {eur(result.price_change)} ({Number(result.price_change_percent || 0).toFixed(2)}%)</Typography>
      <Typography variant="body2">3-night revenue impact: {eur(result.revenue_impact_per_3night_stay)}</Typography>
    </Paper>
  )
}

function AnalysisResults({ data, scenarioResult }) {
  const price = data.ensemble_prediction
  const factors = data.price_factors || []
  return (
    <Box>
      {price && <RecommendedPrice price={price} />}
      {data.summary && <Alert severity="info" sx={{ mb: 3 }}>{data.summary}</Alert>}
      {factors.length > 0 && <FactorsTable factors={factors} />}
      {scenarioResult && <ScenarioResult result={scenarioResult} />}
    </Box>
  )
}

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

  return (
    <AppLayout>
      <PageHeader
        title="Dynamic pricing"
        subtitle="Model recommendations and scenario analysis for a room and date"
      />
      <QueryForm query={query} setQuery={setQuery} onSubmit={handleSubmit} busy={isLoading} />
      <ScenarioPanel
        scenario={scenario}
        setScenario={setScenario}
        onRun={handleScenario}
        disabled={scenarioLoading || !query.room_id || !query.date}
        running={scenarioLoading}
        modelList={modelsData?.models || []}
      />
      {isLoading && <LoadingSpinner />}
      {data && <AnalysisResults data={data} scenarioResult={scenarioResult} />}
    </AppLayout>
  )
}
