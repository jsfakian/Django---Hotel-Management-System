<template>
  <div class="scenario-analyzer-card card">
    <div class="card-header bg-purple text-white" style="background-color: #6f42c1;">
      <h5 class="mb-0">Scenario Analyzer (What-If)</h5>
      <small>Adjust Parameters and See Price Impact</small>
    </div>
    <div class="card-body">
      <div class="row">
        <!-- Parameter Controls -->
        <div class="col-md-6">
          <div class="scenario-controls">
            <!-- Occupancy Slider -->
            <div class="control-group">
              <label for="occupancy-slider" class="control-label">
                Occupancy Rate: <strong>{{ occupancyOverride }}%</strong>
              </label>
              <input 
                v-model.number="occupancyOverride"
                id="occupancy-slider"
                type="range"
                min="0"
                max="100"
                step="5"
                class="form-range slider"
              >
              <small class="text-muted d-block mt-1">Current: {{ currentOccupancy }}%</small>
            </div>

            <!-- Season Select -->
            <div class="control-group mt-3">
              <label for="season-select" class="control-label">Season</label>
              <select v-model="seasonOverride" id="season-select" class="form-control">
                <option value="">Current: {{ currentSeason }}</option>
                <option value="low">Low Season (winter)</option>
                <option value="medium">Medium Season (spring/fall)</option>
                <option value="high">High Season (summer)</option>
                <option value="peak">Peak Season (holidays)</option>
              </select>
            </div>

            <!-- Competitor Price -->
            <div class="control-group mt-3">
              <label for="competitor-price" class="control-label">
                Market Price: <strong>${{ formatPrice(competitorPriceOverride) }}</strong>
              </label>
              <div class="input-group">
                <div class="input-group-prepend">
                  <span class="input-group-text">$</span>
                </div>
                <input 
                  v-model.number="competitorPriceOverride"
                  id="competitor-price"
                  type="number"
                  step="1"
                  min="0"
                  class="form-control"
                >
              </div>
              <small class="text-muted d-block mt-1">Current: ${{ formatPrice(currentCompetitorPrice) }}</small>
            </div>

            <!-- Action Buttons -->
            <div class="mt-4 d-flex gap-2">
              <button 
                @click="analyzeScenario"
                class="btn btn-primary"
                :disabled="analyzing"
              >
                <i v-if="analyzing" class="fas fa-spinner fa-spin"></i>
                <span v-else>Analyze Scenario</span>
              </button>
              <button 
                @click="resetScenario"
                class="btn btn-secondary"
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        <!-- Results Display -->
        <div class="col-md-6">
          <div v-if="scenarioResult" class="scenario-results">
            <h6>Scenario Result</h6>
            
            <div class="result-box">
              <div class="result-label">New Recommendation</div>
              <div class="result-value">
                ${{ formatPrice(scenarioResult.scenario_price) }}
              </div>
            </div>

            <div class="result-box">
              <div class="result-label">Price Change</div>
              <div :class="['result-value', scenarioResult.price_change >= 0 ? 'text-success' : 'text-danger']">
                {{ scenarioResult.price_change >= 0 ? '+' : ''}}${{ formatPrice(scenarioResult.price_change) }}
                <small> ({{ formatPercent(scenarioResult.price_change_percent) }}%)</small>
              </div>
            </div>

            <div class="result-box">
              <div class="result-label">Revenue Impact (per night)</div>
              <div :class="['result-value', scenarioResult.revenue_impact_per_night >= 0 ? 'text-success' : 'text-danger']">
                {{ scenarioResult.revenue_impact_per_night >= 0 ? '+' : ''}}${{ formatPrice(scenarioResult.revenue_impact_per_night) }}
              </div>
            </div>

            <div class="result-box">
              <div class="result-label">Revenue Impact (3-night stay)</div>
              <div :class="['result-value', scenarioResult.revenue_impact_per_3night_stay >= 0 ? 'text-success' : 'text-danger']">
                {{ scenarioResult.revenue_impact_per_3night_stay >= 0 ? '+' : ''}}${{ formatPrice(scenarioResult.revenue_impact_per_3night_stay) }}
              </div>
            </div>

            <!-- Recommendation -->
            <div class="mt-3 p-2 bg-light rounded">
              <small><strong>Interpretation:</strong></small>
              <p class="text-muted small mb-0">
                {{ scenarioInterpretation }}
              </p>
            </div>

            <!-- Save Scenario Button -->
            <button 
              @click="useScenarioPrice"
              class="btn btn-success btn-sm btn-block mt-3"
            >
              Use This Price
            </button>
          </div>

          <div v-else class="text-center text-muted py-4">
            <i class="fas fa-inbox"></i>
            <p>Adjust parameters and analyze to see results</p>
          </div>
        </div>
      </div>

      <!-- Saved Scenarios Table -->
      <div v-if="savedScenarios.length > 0" class="mt-4 pt-3 border-top">
        <h6>Saved Scenarios</h6>
        <div class="scenarios-table">
          <div class="scenario-header">
            <div>Scenario</div>
            <div>New Price</div>
            <div>3-night Impact</div>
            <div>Action</div>
          </div>
          <div v-for="(scenario, idx) in savedScenarios" :key="idx" class="scenario-row">
            <div>{{ scenario.name }}</div>
            <div>${{ formatPrice(scenario.price) }}</div>
            <div :class="scenario.impact >= 0 ? 'text-success' : 'text-danger'">
              {{ scenario.impact >= 0 ? '+' : ''}}${{ formatPrice(scenario.impact) }}
            </div>
            <div>
              <button 
                class="btn btn-sm btn-outline-primary"
                @click="useScenarioPrice(scenario.price)"
              >
                Use
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="alert alert-danger mt-3 mb-0">
        <i class="fas fa-exclamation-circle"></i> {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ScenarioAnalyzer',
  props: {
    currentOccupancy: {
      type: Number,
      default: 75
    },
    currentSeason: {
      type: String,
      default: 'high'
    },
    currentCompetitorPrice: {
      type: Number,
      default: 150
    },
    currentPrice: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      occupancyOverride: this.currentOccupancy,
      seasonOverride: '',
      competitorPriceOverride: this.currentCompetitorPrice,
      scenarioResult: null,
      savedScenarios: [],
      analyzing: false,
      error: ''
    };
  },
  computed: {
    scenarioInterpretation() {
      if (!this.scenarioResult) return '';
      
      const impactPct = this.scenarioResult.price_change_percent || 0;
      const impact3night = this.scenarioResult.revenue_impact_per_3night_stay || 0;

      if (impact3night > 100) {
        return `✓ Strong revenue boost: This scenario increases 3-night booking revenue by $${this.formatPrice(impact3night)}. Good potential for profitability.`;
      }
      if (impact3night > 20) {
        return `→ Moderate revenue impact: This scenario increases 3-night booking revenue by $${this.formatPrice(impact3night)}. Reasonable pricing strategy.`;
      }
      if (impact3night > -20) {
        return `≈ Minimal impact: This scenario slightly adjusts revenue. Pricing remains competitive.`;
      }
      if (impact3night > -100) {
        return `↘ Modest revenue decrease: This scenario reduces 3-night revenue by $${this.formatPrice(Math.abs(impact3night))}. May attract more bookings.`;
      }
      return `↘ Significant revenue decrease: This scenario substantially reduces revenue. Consider competitive trade-offs.`;
    }
  },
  methods: {
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2);
    },
    formatPercent(pct) {
      return parseFloat(pct || 0).toFixed(1);
    },
    async analyzeScenario() {
      this.error = '';
      this.analyzing = true;

      try {
        // Emit to parent component to call API
        const result = await new Promise((resolve) => {
          this.$emit('analyze-scenario', {
            occupancy_override: this.occupancyOverride,
            override_season: this.seasonOverride || null,
            override_competitor_price: this.competitorPriceOverride
          }, (result) => {
            resolve(result);
          });
        });

        this.scenarioResult = result;
      } catch (err) {
        this.error = err.message || 'Failed to analyze scenario';
      } finally {
        this.analyzing = false;
      }
    },
    resetScenario() {
      this.occupancyOverride = this.currentOccupancy;
      this.seasonOverride = '';
      this.competitorPriceOverride = this.currentCompetitorPrice;
      this.scenarioResult = null;
      this.error = '';
    },
    useScenarioPrice(price = null) {
      const priceToUse = price || (this.scenarioResult?.scenario_price || this.currentPrice);
      this.$emit('use-scenario-price', priceToUse);
    }
  }
};
</script>

<style scoped>
.scenario-analyzer-card {
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.scenario-controls {
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.control-group {
  margin-bottom: 1.5rem;
}

.control-group:last-child {
  margin-bottom: 0;
}

.control-label {
  font-weight: 500;
  margin-bottom: 0.75rem;
  display: block;
}

.slider {
  cursor: pointer;
}

.scenario-results {
  padding: 1.5rem;
  background-color: #f0f7ff;
  border-radius: 8px;
  border-left: 4px solid #6f42c1;
}

.result-box {
  margin-bottom: 1rem;
  padding: 1rem;
  background-color: white;
  border-radius: 6px;
  border-left: 3px solid #6f42c1;
}

.result-box:last-child {
  margin-bottom: 0;
}

.result-label {
  font-size: 0.85rem;
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.result-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
}

.result-value small {
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: normal;
}

.result-value.text-success {
  color: #28a745;
}

.result-value.text-danger {
  color: #dc3545;
}

.scenarios-table {
  display: flex;
  flex-direction: column;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  overflow: hidden;
}

.scenario-header,
.scenario-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 100px;
  gap: 1rem;
  padding: 1rem;
  align-items: center;
  border-bottom: 1px solid #dee2e6;
}

.scenario-header {
  background-color: #f8f9fa;
  font-weight: bold;
  font-size: 0.9rem;
}

.scenario-row:last-child {
  border-bottom: none;
}

.scenario-row:hover {
  background-color: #f8f9fa;
}

@media (max-width: 768px) {
  .scenario-analyzer-card {
    margin-bottom: 1rem;
  }

  .scenario-results {
    margin-top: 1.5rem;
  }

  .result-value {
    font-size: 1.25rem;
  }
}
</style>
