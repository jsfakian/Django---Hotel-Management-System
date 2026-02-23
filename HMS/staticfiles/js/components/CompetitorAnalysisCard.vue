<template>
  <div class="competitor-analysis-card card">
    <div class="card-header bg-warning text-dark">
      <h5 class="mb-0">Competitor & Market Analysis</h5>
      <small>Your Pricing Position vs Market</small>
    </div>
    <div class="card-body">
      <!-- Market Range Overview -->
      <div class="market-overview">
        <div class="range-label">
          <strong>Market Price Range</strong>
          <small class="text-muted float-right">Updated: {{ lastUpdate }}</small>
        </div>
        
        <div class="price-range-visualization">
          <!-- Min marker -->
          <div class="range-marker min-marker">
            <span class="marker-value">${{ formatPrice(marketRange.min) }}</span>
            <span class="marker-label">Low</span>
          </div>

          <!-- Market bar -->
          <div class="market-bar">
            <div class="bar-section low" :style="{ flex: lowPercent }"></div>
            <div class="bar-section mid" :style="{ flex: midPercent }"></div>
            <div class="bar-section high" :style="{ flex: highPercent }"></div>
            
            <!-- Your price indicator -->
            <div 
              v-if="showYourPrice" 
              class="price-indicator your-price"
              :style="{ left: yourPricePercent + '%' }"
              :class="pricePositioningClass"
            >
              <div class="indicator-marker"></div>
              <div class="indicator-label">Your Price: ${{ formatPrice(yourPrice) }}</div>
            </div>
            
            <!-- Average price marker -->
            <div 
              class="price-indicator avg-price"
              :style="{ left: avgPricePercent + '%' }"
            >
              <div class="indicator-marker"></div>
              <div class="indicator-label">Avg: ${{ formatPrice(marketRange.average) }}</div>
            </div>
          </div>

          <!-- Max marker -->
          <div class="range-marker max-marker">
            <span class="marker-value">${{ formatPrice(marketRange.max) }}</span>
            <span class="marker-label">High</span>
          </div>
        </div>

        <!-- Statistics Row -->
        <div class="row mt-3 text-center">
          <div class="col-md-3">
            <div class="stat-item">
              <small class="text-muted">Minimum</small>
              <p class="stat-value">${{ formatPrice(marketRange.min) }}</p>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-item">
              <small class="text-muted">Average</small>
              <p class="stat-value">${{ formatPrice(marketRange.average) }}</p>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-item">
              <small class="text-muted">Maximum</small>
              <p class="stat-value">${{ formatPrice(marketRange.max) }}</p>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-item">
              <small class="text-muted">Std Dev</small>
              <p class="stat-value">${{ formatPrice(marketRange.stddev) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Price Positioning Analysis -->
      <div class="mt-4 p-3 bg-light rounded positioning-analysis">
        <h6>Your Market Position</h6>
        
        <div class="positioning-item">
          <div class="positioning-header">
            <span>Position Relative to Average</span>
            <span :class="['positioning-badge', positionClass]">
              {{ positionLabel }}
            </span>
          </div>
          <small class="text-muted">
            {{ positionDescription }}
          </small>
        </div>

        <div class="positioning-item mt-3">
          <div class="positioning-header">
            <span>Price Difference</span>
            <span class="text-primary font-weight-bold">${{ formatPrice(priceDifference) }}</span>
          </div>
          <small class="text-muted">
            {{ priceDifferencePercent > 0 ? '+' : ''}}{{ priceDifferencePercent.toFixed(1) }}% 
            vs market average
          </small>
        </div>

        <div class="positioning-item mt-3">
          <div class="positioning-header">
            <span>Competitive Strength</span>
            <span :class="['strength-score', strengthClass]">
              {{ strengthScore }}/10
            </span>
          </div>
          <div class="progress mt-2" style="height: 6px;">
            <div 
              class="progress-bar" 
              :style="{ width: strengthScore * 10 + '%' }"
              :class="strengthClass"
            ></div>
          </div>
          <small class="text-muted">{{ strengthInterpretation }}</small>
        </div>
      </div>

      <!-- Risk Indicators -->
      <div v-if="showRiskAlerts" class="mt-3">
        <div v-if="priceAboveMarket" class="alert alert-warning mb-2">
          <i class="fas fa-exclamation-triangle"></i>
          <strong>Above Market:</strong> Consider reviewing if you're losing bookings.
        </div>
        <div v-if="priceBelowMarket" class="alert alert-info mb-2">
          <i class="fas fa-info-circle"></i>
          <strong>Below Market:</strong> Opportunity to increase revenue with higher pricing.
        </div>
        <div v-if="priceOutlier" class="alert alert-danger mb-0">
          <i class="fas fa-exclamation-circle"></i>
          <strong>Outlier Price:</strong> Significantly different from market. Verify intentionality.
        </div>
      </div>

      <!-- Last Updated Info -->
      <div class="mt-3 pt-3 border-top small text-muted">
        <p class="mb-0">
          Market data is based on <strong>{{ competitorCount }}</strong> similar properties sampled daily.
          <br>Last updated: <strong>{{ lastUpdate }}</strong>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CompetitorAnalysisCard',
  props: {
    yourPrice: {
      type: Number,
      required: true
    },
    competitorPrice: {
      type: Number,
      required: true
    },
    marketRange: {
      type: Object,
      default: () => ({
        min: 0,
        max: 0,
        average: 0,
        stddev: 0
      })
    },
    lastUpdate: {
      type: String,
      default: 'Today'
    },
    competitorCount: {
      type: Number,
      default: 150
    }
  },
  computed: {
    showYourPrice() {
      return this.yourPrice > 0;
    },
    priceDifference() {
      return this.yourPrice - this.marketRange.average;
    },
    priceDifferencePercent() {
      if (this.marketRange.average === 0) return 0;
      return (this.priceDifference / this.marketRange.average) * 100;
    },
    priceAboveMarket() {
      return this.priceDifferencePercent > 10;
    },
    priceBelowMarket() {
      return this.priceDifferencePercent < -10;
    },
    priceOutlier() {
      const zScore = Math.abs(this.priceDifference / this.marketRange.stddev);
      return zScore > 2; // More than 2 standard deviations
    },
    showRiskAlerts() {
      return this.priceAboveMarket || this.priceBelowMarket || this.priceOutlier;
    },
    positionLabel() {
      if (this.priceDifferencePercent > 20) return 'Premium Positioning';
      if (this.priceDifferencePercent > 5) return 'Above Average';
      if (this.priceDifferencePercent > -5) return 'Market Rate';
      if (this.priceDifferencePercent > -20) return 'Below Average';
      return 'Discount Positioning';
    },
    positionClass() {
      if (Math.abs(this.priceDifferencePercent) <= 5) return 'badge-success';
      if (Math.abs(this.priceDifferencePercent) <= 15) return 'badge-info';
      if (Math.abs(this.priceDifferencePercent) <= 25) return 'badge-warning';
      return 'badge-danger';
    },
    positionDescription() {
      const diff = this.priceDifferencePercent;
      if (Math.abs(diff) <= 5) {
        return 'Your price aligns well with market competition. Good positioning for market share and profitability.';
      }
      if (diff > 5) {
        return 'Your price is above market average. This may attract quality guests but could reduce booking volume.';
      }
      return 'Your price is below market average. This may increase bookings but reduce profit margins.';
    },
    yourPricePercent() {
      const range = this.marketRange.max - this.marketRange.min;
      if (range === 0) return 50;
      return ((this.yourPrice - this.marketRange.min) / range) * 100;
    },
    avgPricePercent() {
      const range = this.marketRange.max - this.marketRange.min;
      if (range === 0) return 50;
      return ((this.marketRange.average - this.marketRange.min) / range) * 100;
    },
    lowPercent() {
      const avg = this.marketRange.average || 0;
      const min = this.marketRange.min || 0;
      const range = this.marketRange.max - this.marketRange.min;
      return ((avg - min) / range) * 100;
    },
    midPercent() {
      return 0; // Simplified for visualization
    },
    highPercent() {
      const avg = this.marketRange.average || 0;
      const max = this.marketRange.max || 0;
      const range = this.marketRange.max - this.marketRange.min;
      return ((max - avg) / range) * 100;
    },
    strengthScore() {
      // Calculate 1-10 score based on positioning
      if (Math.abs(this.priceDifferencePercent) <= 5) return 10;
      if (Math.abs(this.priceDifferencePercent) <= 10) return 8;
      if (Math.abs(this.priceDifferencePercent) <= 15) return 6;
      if (Math.abs(this.priceDifferencePercent) <= 25) return 4;
      return 2;
    },
    strengthClass() {
      if (this.strengthScore >= 8) return 'bg-success';
      if (this.strengthScore >= 6) return 'bg-info';
      if (this.strengthScore >= 4) return 'bg-warning';
      return 'bg-danger';
    },
    strengthInterpretation() {
      if (this.strengthScore >= 8) return 'Excellent competitive positioning';
      if (this.strengthScore >= 6) return 'Good competitive positioning';
      if (this.strengthScore >= 4) return 'Fair competitive positioning - consider adjustments';
      return 'Weak competitive positioning - significant adjustment recommended';
    },
    pricePositioningClass() {
      if (this.priceAboveMarket) return 'above-market';
      if (this.priceBelowMarket) return 'below-market';
      return 'at-market';
    }
  },
  methods: {
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2);
    }
  }
};
</script>

<style scoped>
.competitor-analysis-card {
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.market-overview {
  margin-bottom: 2rem;
}

.range-label {
  font-weight: bold;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.price-range-visualization {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 2rem 0;
}

.range-marker {
  text-align: center;
  min-width: 80px;
}

.range-marker.min-marker {
  text-align: right;
}

.range-marker.max-marker {
  text-align: left;
}

.marker-value {
  display: block;
  font-weight: bold;
  font-size: 0.95rem;
}

.marker-label {
  display: block;
  font-size: 0.75rem;
  color: #6c757d;
}

.market-bar {
  flex: 1;
  position: relative;
  height: 30px;
  background-color: #e9ecef;
  border-radius: 4px;
  display: flex;
  overflow: visible;
}

.bar-section {
  height: 100%;
  border-radius: 4px;
}

.bar-section.low {
  background: linear-gradient(90deg, #dc3545, #fd7e14);
}

.bar-section.mid {
  background: linear-gradient(90deg, #fd7e14, #28a745);
}

.bar-section.high {
  background: linear-gradient(90deg, #28a745, #17a2b8);
}

.price-indicator {
  position: absolute;
  top: -40px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.price-indicator.your-price {
  z-index: 10;
}

.price-indicator.your-price.above-market .indicator-marker {
  border-top-color: #ffc107;
}

.price-indicator.your-price.below-market .indicator-marker {
  border-top-color: #17a2b8;
}

.price-indicator.your-price.at-market .indicator-marker {
  border-top-color: #28a745;
}

.price-indicator.avg-price {
  opacity: 0.6;
}

.indicator-marker {
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 8px solid #333;
  margin-bottom: 4px;
}

.indicator-label {
  font-size: 0.75rem;
  font-weight: bold;
  white-space: nowrap;
  background-color: white;
  padding: 2px 6px;
  border-radius: 3px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-item {
  padding: 1rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: bold;
  margin: 0.5rem 0 0 0;
  color: #333;
}

.positioning-item {
  margin-bottom: 1rem;
}

.positioning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.positioning-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: bold;
  color: white;
}

.positioning-badge.badge-success {
  background-color: #28a745;
}

.positioning-badge.badge-info {
  background-color: #17a2b8;
}

.positioning-badge.badge-warning {
  background-color: #ffc107;
  color: #333;
}

.positioning-badge.badge-danger {
  background-color: #dc3545;
}

.strength-score {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-weight: bold;
  color: white;
}

.strength-score.bg-success {
  background-color: #28a745;
}

.strength-score.bg-info {
  background-color: #17a2b8;
}

.strength-score.bg-warning {
  background-color: #ffc107;
  color: #333;
}

.strength-score.bg-danger {
  background-color: #dc3545;
}

@media (max-width: 768px) {
  .price-range-visualization {
    flex-wrap: wrap;
  }

  .range-marker {
    min-width: 60px;
    font-size: 0.9rem;
  }

  .indicator-label {
    font-size: 0.65rem;
  }
}
</style>
