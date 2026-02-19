<template>
  <div class="decision-form-card card">
    <div class="card-header bg-dark text-white">
      <h5 class="mb-0">Pricing Decision</h5>
      <small>Accept AI Recommendation or Override</small>
    </div>
    <div class="card-body">
      <form @submit.prevent="submitPrice">
        <!-- Decision Radio -->
        <div class="decision-options">
          <div class="form-check form-check-inline">
            <input 
              v-model="decisionType" 
              value="ai" 
              type="radio" 
              id="decision-ai"
              class="form-check-input"
              @change="onDecisionChange"
            >
            <label class="form-check-label" for="decision-ai">
              <strong>✓ Accept AI Recommendation</strong>
              <small class="d-block text-muted">Use ensemble model prediction: <strong>${{ formatPrice(recommendation) }}</strong></small>
            </label>
          </div>

          <div class="form-check form-check-inline mt-2">
            <input 
              v-model="decisionType" 
              value="manual" 
              type="radio" 
              id="decision-manual"
              class="form-check-input"
              @change="onDecisionChange"
            >
            <label class="form-check-label" for="decision-manual">
              <strong>✎ Override with Custom Price</strong>
              <small class="d-block text-muted">Enter your own price and reason</small>
            </label>
          </div>
        </div>

        <!-- AI Decision Section -->
        <div v-if="decisionType === 'ai'" class="mt-3 p-3 bg-success bg-opacity-10 rounded">
          <div class="row">
            <div class="col-md-4">
              <p class="small"><strong>Recommendation:</strong></p>
              <p class="mb-0" style="font-size: 1.5rem; color: #28a745; font-weight: bold;">
                ${{ formatPrice(recommendation) }}
              </p>
            </div>
            <div class="col-md-4">
              <p class="small"><strong>Model Accuracy:</strong></p>
              <p class="mb-0" style="font-size: 1.25rem; color: #333;">
                92%
              </p>
            </div>
            <div class="col-md-4">
              <p class="small"><strong>vs Base Price:</strong></p>
              <p class="mb-0" style="font-size: 1.25rem;" :class="{'text-success': recommendation > basePr ice, 'text-danger': recommendation < basePrice}">
                {{ recommendation > basePrice ? '+' : ''}}${{ formatPrice(recommendation - basePrice) }}
              </p>
            </div>
          </div>
        </div>

        <!-- Manual Override Section -->
        <div v-if="decisionType === 'manual'" class="mt-3 p-3 bg-warning bg-opacity-10 rounded">
          <div class="row">
            <div class="col-md-6">
              <div class="form-group">
                <label for="custom-price">Custom Price ($)</label>
                <div class="input-group">
                  <div class="input-group-prepend">
                    <span class="input-group-text">$</span>
                  </div>
                  <input 
                    v-model.number="customPrice"
                    id="custom-price"
                    type="number"
                    step="0.01"
                    min="0"
                    class="form-control"
                    placeholder="Enter custom price"
                    @input="calculateDifference"
                  >
                </div>
                <small class="text-muted">
                  vs Recommendation: 
                  <span :class="customPrice > recommendation ? 'text-danger' : 'text-success'">
                    {{ customPrice > recommendation ? '+' : ''}}${{ formatPrice(customPrice - recommendation) }}
                  </span>
                </small>
              </div>
            </div>
            <div class="col-md-6">
              <div class="form-group">
                <label for="override-reason">Reason for Override *</label>
                <select 
                  v-model="overrideReason"
                  id="override-reason"
                  class="form-control"
                  required
                >
                  <option value="">-- Select Reason --</option>
                  <option value="market-conditions">Market conditions changed</option>
                  <option value="competitor-adjustment">Competitor pricing strategy</option>
                  <option value="occupancy-target">Target occupancy level</option>
                  <option value="revenue-requirement">Revenue requirement</option>
                  <option value="seasonal-event">Seasonal event or promotion</option>
                  <option value="quality-positioning">Quality/brand positioning</option>
                  <option value="other">Other (specify below)</option>
                </select>
              </div>
            </div>
          </div>

          <div class="row">
            <div class="col-12">
              <div class="form-group">
                <label for="override-notes">Additional Notes (optional)</label>
                <textarea 
                  v-model="overrideNotes"
                  id="override-notes"
                  class="form-control"
                  rows="2"
                  placeholder="Explain your override decision..."
                ></textarea>
              </div>
            </div>
          </div>
        </div>

        <!-- Price Summary -->
        <div class="mt-3 price-summary">
          <div class="summary-row">
            <span>Base Price:</span>
            <span>${{ formatPrice(basePrice) }}</span>
          </div>
          <div class="summary-row">
            <span>Selected Price:</span>
            <strong class="text-primary">${{ formatPrice(selectedPrice) }}</strong>
          </div>
          <div class="summary-row">
            <span>Price Adjustment:</span>
            <span :class="{'text-success': selectedPrice > basePrice, 'text-danger': selectedPrice < basePrice}">
              {{ selectedPrice > basePrice ? '+' : ''}}${{ formatPrice(selectedPrice - basePrice) }}
              ({{ formatPercent((selectedPrice - basePrice) / basePrice * 100) }}%)
            </span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="mt-4 d-flex gap-2">
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
            <span v-else>{{ decisionType === 'ai' ? 'Accept & Save' : 'Override & Save' }}</span>
          </button>
          <button type="button" class="btn btn-secondary" @click="$emit('cancel')">
            Cancel
          </button>
        </div>

        <!-- Error Display -->
        <div v-if="error" class="alert alert-danger mt-3 mb-0">
          <i class="fas fa-exclamation-circle"></i> {{ error }}
        </div>

        <!-- Success Display -->
        <div v-if="success" class="alert alert-success mt-3 mb-0">
          <i class="fas fa-check-circle"></i> Price saved successfully!
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PricingDecisionForm',
  props: {
    basePrice: {
      type: Number,
      required: true
    },
    recommendation: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      decisionType: 'ai',
      customPrice: null,
      overrideReason: '',
      overrideNotes: '',
      submitting: false,
      error: '',
      success: false
    };
  },
  computed: {
    selectedPrice() {
      return this.decisionType === 'ai' 
        ? this.recommendation 
        : (this.customPrice || this.recommendation);
    }
  },
  methods: {
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2);
    },
    formatPercent(pct) {
      return parseFloat(pct || 0).toFixed(1);
    },
    onDecisionChange() {
      this.error = '';
      this.success = false;
      if (this.decisionType === 'manual' && !this.customPrice) {
        this.customPrice = this.recommendation;
      }
    },
    calculateDifference() {
      // Auto-calculate, used for display
    },
    async submitPrice() {
      this.error = '';
      this.success = false;

      // Validation
      if (this.decisionType === 'manual') {
        if (!this.customPrice || this.customPrice <= 0) {
          this.error = 'Please enter a valid custom price';
          return;
        }
        if (!this.overrideReason) {
          this.error = 'Please select a reason for override';
          return;
        }
      }

      this.submitting = true;

      try {
        // Emit decision to parent component
        this.$emit('save', {
          price: this.selectedPrice,
          decisionType: this.decisionType,
          overrideReason: this.overrideReason,
          overrideNotes: this.overrideNotes,
          modelUsed: this.decisionType === 'ai' ? 'ensemble' : null
        });

        this.success = true;
        
        // Reset form after delay
        setTimeout(() => {
          this.customPrice = null;
          this.overrideReason = '';
          this.overrideNotes = '';
          this.decisionType = 'ai';
        }, 1500);
      } catch (err) {
        this.error = err.message || 'Failed to save price';
      } finally {
        this.submitting = false;
      }
    }
  }
};
</script>

<style scoped>
.decision-form-card {
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.decision-options {
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.form-check {
  padding-left: 0;
  margin-left: 0;
}

.form-check-input {
  margin-left: 0;
  margin-right: 0.5rem;
}

.form-check-label {
  cursor: pointer;
  margin-left: 0.5rem;
}

.price-summary {
  padding: 1.5rem;
  background-color: #f0f7ff;
  border-left: 4px solid #007bff;
  border-radius: 4px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-weight: 500;
}

.summary-row:last-child {
  margin-bottom: 0;
}

.summary-row span:first-child {
  color: #6c757d;
}

.summary-row strong {
  color: #007bff;
}

.input-group {
  margin-bottom: 0.5rem;
}

.btn[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .decision-form-card {
    margin-bottom: 1rem;
  }

  .decision-options {
    padding: 1rem;
  }

  .form-check {
    margin-bottom: 1rem;
  }
}
</style>
