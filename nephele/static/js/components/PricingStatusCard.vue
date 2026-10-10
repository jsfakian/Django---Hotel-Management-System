<template>
  <div class="pricing-status-card card">
    <div class="card-header bg-primary text-white">
      <h5 class="mb-0">Current Pricing Status</h5>
    </div>
    <div class="card-body">
      <!-- Base Price Section -->
      <div class="row mb-4">
        <div class="col-md-4">
          <div class="pricing-item">
            <label class="text-muted small">Base Price</label>
            <div class="pricing-value">
              <span class="currency">$</span><span class="amount">{{ formatPrice(basePrice) }}</span>
            </div>
            <small class="text-muted d-block mt-1">Hotel's standard rate</small>
          </div>
        </div>

        <!-- AI Recommendation Section -->
        <div class="col-md-4">
          <div class="pricing-item highlight-success">
            <label class="text-muted small">AI Recommendation</label>
            <div class="pricing-value text-success">
              <span class="currency">$</span><span class="amount">{{ formatPrice(aiRecommendation) }}</span>
            </div>
            <small class="text-muted d-block mt-1">Ensemble model ({{ (confidence * 100).toFixed(0) }}% confident)</small>
          </div>
        </div>

        <!-- Competitor Price Section -->
        <div class="col-md-4">
          <div class="pricing-item">
            <label class="text-muted small">Market Price</label>
            <div class="pricing-value">
              <span class="currency">$</span><span class="amount">{{ formatPrice(competitorPrice) }}</span>
            </div>
            <small class="text-muted d-block mt-1">Average market rate</small>
          </div>
        </div>
      </div>

      <!-- Price Comparison Row -->
      <div class="row">
        <div class="col-md-6">
          <div class="comparison-badge">
            <strong>vs Market:</strong>
            <span :class="['ml-2', aiRecommendation > competitorPrice ? 'text-warning' : 'text-info']">
              {{ formatPrice(Math.abs(aiRecommendation - competitorPrice)) }} 
              <span class="text-muted">({{ aiRecommendation > competitorPrice ? '+' : '-' }}{{ ((Math.abs(aiRecommendation - competitorPrice) / competitorPrice) * 100).toFixed(1) }}%)</span>
            </span>
          </div>
        </div>
        <div class="col-md-6">
          <div class="confidence-indicator">
            <strong>Confidence:</strong>
            <div class="progress mt-2" style="height: 6px;">
              <div 
                class="progress-bar bg-success" 
                :style="{ width: (confidence * 100) + '%' }"
              ></div>
            </div>
            <small class="text-muted">{{ (confidence * 100).toFixed(1) }}% based on recent data</small>
          </div>
        </div>
      </div>

      <!-- Risk Indicator -->
      <div v-if="showRiskWarning" class="alert alert-warning mt-3 mb-0">
        <i class="fas fa-exclamation-triangle"></i>
        <strong>Market Alert:</strong> Your recommendation is significantly above market average. Consider reviewing competitor pricing.
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PricingStatusCard',
  props: {
    basePrice: {
      type: Number,
      required: true
    },
    aiRecommendation: {
      type: Number,
      required: true
    },
    competitorPrice: {
      type: Number,
      required: true
    },
    confidence: {
      type: Number,
      default: 0.92
    }
  },
  computed: {
    showRiskWarning() {
      // Show warning if price is >15% above market average
      const percentAbove = ((this.aiRecommendation - this.competitorPrice) / this.competitorPrice) * 100;
      return percentAbove > 15;
    }
  },
  methods: {
    formatPrice(price) {
      return parseFloat(price).toFixed(2);
    }
  }
};
</script>

<style scoped>
.pricing-status-card {
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.pricing-item {
  padding: 1.5rem;
  border-radius: 8px;
  background-color: #f8f9fa;
  text-align: center;
}

.pricing-item.highlight-success {
  background-color: #f0f8f5;
  border: 2px solid #28a745;
}

.pricing-value {
  font-size: 1.75rem;
  font-weight: bold;
  margin: 0.5rem 0;
}

.currency {
  font-size: 0.8em;
  margin-right: 2px;
}

.comparison-badge,
.confidence-indicator {
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.progress {
  background-color: #e9ecef;
}

@media (max-width: 768px) {
  .pricing-value {
    font-size: 1.25rem;
  }
  
  .col-md-4 {
    margin-bottom: 1rem;
  }
}
</style>
