<template>
  <div class="pricing-factors-card card">
    <div class="card-header bg-success text-white">
      <h5 class="mb-0">Pricing Factors Breakdown</h5>
      <small>How AI Calculates the Recommended Price</small>
    </div>
    <div class="card-body">
      <!-- Base Price -->
      <div class="factor-item base-factor">
        <div class="factor-header">
          <span class="factor-name">
            <i class="fas fa-calculator"></i> Base Price
          </span>
          <span class="factor-value">${{ formatPrice(basePrice) }}</span>
        </div>
        <div class="factor-bar">
          <div class="factor-fill" style="width: 100%; background-color: #6c757d;"></div>
        </div>
      </div>

      <!-- Occupancy Impact -->
      <div class="factor-item" :class="occupancyClass">
        <div class="factor-header">
          <span class="factor-name">
            <i class="fas fa-hotel"></i> Occupancy Impact
            <span class="text-muted small">({{ factors.occupancy_rate }}% occupied)</span>
          </span>
          <span class="factor-value" :class="occupancyValueClass">
            {{ occupancySign }}${{ formatPrice(Math.abs(factors.occupancy_impact_dollars)) }}
          </span>
        </div>
        <div class="factor-details">
          <small class="text-muted">
            {{ factors.occupancy_impact_dollars > 0 ? 'Increases' : 'Decreases' }} price by 
            <strong>{{ formatPercent(factors.occupancy_impact_percent) }}%</strong>
          </small>
          <div class="factor-explanation text-muted small mt-1">
            High occupancy allows premium pricing; low occupancy suggests discounts to attract bookings.
          </div>
        </div>
      </div>

      <!-- Seasonal Impact -->
      <div class="factor-item" :class="seasonalClass">
        <div class="factor-header">
          <span class="factor-name">
            <i class="fas fa-calendar-alt"></i> Seasonal Impact
            <span class="text-muted small">({{ factors.season }})</span>
          </span>
          <span class="factor-value" :class="seasonalValueClass">
            {{ seasonalSign }}${{ formatPrice(Math.abs(factors.seasonal_impact_dollars)) }}
          </span>
        </div>
        <div class="factor-details">
          <small class="text-muted">
            {{ factors.seasonal_impact_dollars > 0 ? 'Increases' : 'Decreases' }} price by 
            <strong>{{ formatPercent(factors.seasonal_impact_percent) }}%</strong>
          </small>
          <div class="factor-explanation text-muted small mt-1">
            Prices vary by season (peak, high, medium, low).
          </div>
        </div>
      </div>

      <!-- Demand Impact -->
      <div class="factor-item" :class="demandClass">
        <div class="factor-header">
          <span class="factor-name">
            <i class="fas fa-fire"></i> Demand Impact
            <span class="text-muted small">({{ factors.demand_score }} demand)</span>
          </span>
          <span class="factor-value" :class="demandValueClass">
            {{ demandSign }}${{ formatPrice(Math.abs(factors.demand_impact_dollars)) }}
          </span>
        </div>
        <div class="factor-details">
          <small class="text-muted">
            {{ factors.demand_impact_dollars > 0 ? 'Increases' : 'Decreases' }} price by 
            <strong>{{ formatPercent(factors.demand_impact_percent) }}%</strong>
          </small>
          <div class="factor-explanation text-muted small mt-1">
            Rising demand for similar rooms enables price increases.
          </div>
        </div>
      </div>

      <!-- Competitor Impact -->
      <div class="factor-item" :class="competitorClass">
        <div class="factor-header">
          <span class="factor-name">
            <i class="fas fa-chart-line"></i> Competitor Impact
            <span class="text-muted small">(Market: ${{ formatPrice(factors.market_range?.average) }})</span>
          </span>
          <span class="factor-value" :class="competitorValueClass">
            {{ competitorSign }}${{ formatPrice(Math.abs(factors.competitor_impact_dollars)) }}
          </span>
        </div>
        <div class="factor-details">
          <small class="text-muted">
            {{ factors.competitor_impact_dollars > 0 ? 'Increases' : 'Decreases' }} price by 
            <strong>{{ formatPercent(factors.competitor_impact_percent) }}%</strong>
          </small>
          <div class="factor-explanation text-muted small mt-1">
            Competitive pricing analysis moves price toward market average by 30-50%.
          </div>
        </div>
      </div>

      <!-- Total Recommendation -->
      <div class="factor-item recommendation-factor">
        <div class="factor-header">
          <span class="factor-name" style="font-size: 1.1em;">
            <i class="fas fa-star"></i> <strong>Final Recommendation</strong>
          </span>
          <span class="factor-value text-success font-weight-bold" style="font-size: 1.25em;">
            ${{ formatPrice(totalRecommendation) }}
          </span>
        </div>
        <div class="factor-details">
          <small class="text-muted">
            Base: ${{ formatPrice(basePrice) }} 
            <strong>{{ totalChangeSign }}${{ formatPrice(Math.abs(totalChange))</strong> }}
            ({{ formatPercent(totalChangePercent) }}%)
          </small>
        </div>
      </div>

      <!-- Impact Summary -->
      <div class="mt-4 p-3 bg-light rounded">
        <h6>Summary</h6>
        <div class="row">
          <div class="col-md-3">
            <small><strong>Positive Factors:</strong></small>
            <p class="text-success">
              <i v-if="occupancyImpact > 0" class="fas fa-check"></i> {{ occupancyImpact > 0 ? 'Occupancy +' : '' }}
              <i v-if="seasonalImpact > 0" class="fas fa-check"></i> {{ seasonalImpact > 0 ? 'Seasonal +' : '' }}
              <i v-if="demandImpact > 0" class="fas fa-check"></i> {{ demandImpact > 0 ? 'Demand +' : '' }}
            </p>
          </div>
          <div class="col-md-3">
            <small><strong>Negative Factors:</strong></small>
            <p class="text-danger">
              <i v-if="occupancyImpact < 0" class="fas fa-times"></i> {{ occupancyImpact < 0 ? 'Occupancy -' : '' }}
              <i v-if="seasonalImpact < 0" class="fas fa-times"></i> {{ seasonalImpact < 0 ? 'Seasonal -' : '' }}
              <i v-if="demandImpact < 0" class="fas fa-times"></i> {{ demandImpact < 0 ? 'Demand -' : '' }}
            </p>
          </div>
          <div class="col-md-6">
            <small><strong>Market Positioning:</strong></small>
            <p class="text-muted small">
              {{ competitorFeedback }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PricingFactorsBreakdown',
  props: {
    basePrice: {
      type: Number,
      required: true
    },
    factors: {
      type: Object,
      required: true
    }
  },
  computed: {
    occupancySign() {
      return this.factors.occupancy_impact_dollars >= 0 ? '+' : '';
    },
    seasonalSign() {
      return this.factors.seasonal_impact_dollars >= 0 ? '+' : '';
    },
    demandSign() {
      return this.factors.demand_impact_dollars >= 0 ? '+' : '';
    },
    competitorSign() {
      return this.factors.competitor_impact_dollars >= 0 ? '+' : '';
    },
    occupancyValueClass() {
      return this.factors.occupancy_impact_dollars > 0 ? 'text-success' : 'text-danger';
    },
    seasonalValueClass() {
      return this.factors.seasonal_impact_dollars > 0 ? 'text-success' : 'text-danger';
    },
    demandValueClass() {
      return this.factors.demand_impact_dollars > 0 ? 'text-success' : 'text-danger';
    },
    competitorValueClass() {
      return this.factors.competitor_impact_dollars > 0 ? 'text-success' : 'text-danger';
    },
    occupancyClass() {
      return this.factors.occupancy_impact_dollars > 0 ? 'positive-factor' : 'negative-factor';
    },
    seasonalClass() {
      return this.factors.seasonal_impact_dollars > 0 ? 'positive-factor' : 'negative-factor';
    },
    demandClass() {
      return this.factors.demand_impact_dollars > 0 ? 'positive-factor' : 'negative-factor';
    },
    competitorClass() {
      return this.factors.competitor_impact_dollars > 0 ? 'positive-factor' : 'negative-factor';
    },
    occupancyImpact() {
      return this.factors.occupancy_impact_dollars || 0;
    },
    seasonalImpact() {
      return this.factors.seasonal_impact_dollars || 0;
    },
    demandImpact() {
      return this.factors.demand_impact_dollars || 0;
    },
    competitorImpact() {
      return this.factors.competitor_impact_dollars || 0;
    },
    totalChange() {
      return this.occupancyImpact + this.seasonalImpact + this.demandImpact + this.competitorImpact;
    },
    totalChangeSign() {
      return this.totalChange >= 0 ? '+' : '';
    },
    totalChangePercent() {
      return (this.totalChange / this.basePrice) * 100;
    },
    totalRecommendation() {
      return this.basePrice + this.totalChange;
    },
    competitorFeedback() {
      const market = this.factors.market_range?.average || 0;
      const diff = this.totalRecommendation - market;
      const pct = (diff / market) * 100;
      
      if (pct > 15) return '⬆️ Price is significantly above market average';
      if (pct > 5) return '↗️ Price is moderately above market average';
      if (pct > -5) return '➡️ Price aligns with market average';
      if (pct > -15) return '↘️ Price is moderately below market average';
      return '⬇️ Price is significantly below market average';
    }
  },
  methods: {
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2);
    },
    formatPercent(pct) {
      const val = parseFloat(pct || 0);
      return Math.abs(val).toFixed(1);
    }
  }
};
</script>

<style scoped>
.pricing-factors-card {
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.factor-item {
  margin-bottom: 1.5rem;
  padding: 1rem;
  border-radius: 8px;
  background-color: #f8f9fa;
  border-left: 4px solid #6c757d;
}

.factor-item.base-factor {
  background-color: #f0f0f0;
  border-left-color: #495057;
}

.factor-item.positive-factor {
  background-color: #f0f8f5;
  border-left-color: #28a745;
}

.factor-item.negative-factor {
  background-color: #fdf8f8;
  border-left-color: #dc3545;
}

.factor-item.recommendation-factor {
  background-color: #f0f7ff;
  border-left-color: #007bff;
  border-left-width: 6px;
}

.factor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.factor-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.factor-value {
  font-weight: bold;
  font-size: 1.1rem;
}

.factor-bar {
  height: 4px;
  background-color: #e9ecef;
  border-radius: 2px;
  overflow: hidden;
  margin: 0.5rem 0;
}

.factor-fill {
  height: 100%;
}

.factor-details {
  margin-top: 0.5rem;
}

.factor-explanation {
  font-style: italic;
  margin-top: 0.5rem;
  padding-left: 1rem;
  border-left: 2px solid #dee2e6;
}

@media (max-width: 768px) {
  .factor-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .factor-value {
    align-self: flex-end;
    width: 100%;
    text-align: right;
  }
}
</style>
