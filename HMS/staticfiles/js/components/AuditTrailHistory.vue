<template>
  <div class="audit-trail-card card">
    <div class="card-header bg-info text-white">
      <h5 class="mb-0">Audit Trail & Change History</h5>
      <small>Last 10 Pricing Changes</small>
    </div>
    <div class="card-body">
      <div v-if="loading" class="text-center py-4">
        <div class="spinner-border text-info" role="status">
          <span class="sr-only">Loading history...</span>
        </div>
      </div>

      <div v-else-if="changes && changes.length > 0" class="timeline">
        <div v-for="(change, index) in changes" :key="change.id || index" class="timeline-item">
          <!-- Timeline Marker -->
          <div class="timeline-marker" :class="markerClass(change)">
            <i :class="markerIcon(change)"></i>
          </div>

          <!-- Timeline Content -->
          <div class="timeline-content">
            <div class="change-header">
              <div>
                <strong>{{ formatDate(change.date) }}</strong>
                <span class="badge ml-2" :class="badgeClass(change)">
                  {{ change.change_type || 'Manual' }}
                </span>
              </div>
              <div class="change-time">{{ formatTime(change.date) }}</div>
            </div>

            <div class="change-details">
              <div class="row">
                <div class="col-md-3">
                  <small class="text-muted">From Price</small>
                  <p class="price-old">${{ formatPrice(change.previous_price) }}</p>
                </div>
                <div class="col-md-3">
                  <small class="text-muted">To Price</small>
                  <p :class="['price-new', priceChangeClass(change)]">
                    ${{ formatPrice(change.new_price) }}
                    <span class="price-change">
                      {{ change.new_price > change.previous_price ? '+' : ''}}${{ formatPrice(change.new_price - change.previous_price) }}
                    </span>
                  </p>
                </div>
                <div class="col-md-3">
                  <small class="text-muted">Changed By</small>
                  <p>{{ change.changed_by || 'System' }}</p>
                </div>
                <div class="col-md-3">
                  <small class="text-muted">Model</small>
                  <p v-if="change.model_version">{{ change.model_version }}</p>
                  <p v-else class="text-muted">Manual</p>
                </div>
              </div>

              <!-- Reason Display -->
              <div v-if="change.reason" class="mt-2 p-2 bg-light rounded">
                <small><strong>Reason:</strong> {{ change.reason }}</small>
              </div>

              <!-- Notes Display -->
              <div v-if="change.notes" class="mt-2 p-2 bg-light rounded">
                <small><strong>Notes:</strong> {{ change.notes }}</small>
              </div>
            </div>

            <!-- Confidence/Accuracy if AI change -->
            <div v-if="change.model_version" class="mt-2 confidence-badge">
              <small>
                <i class="fas fa-chart-bar"></i>
                Model Accuracy: <strong>{{ change.model_accuracy || 92 }}%</strong>
              </small>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center text-muted py-4">
        <i class="fas fa-history"></i>
        <p>No pricing changes recorded yet</p>
      </div>

      <!-- Summary Statistics -->
      <div v-if="changes && changes.length > 0" class="mt-4 pt-3 border-top">
        <h6>Summary</h6>
        <div class="row">
          <div class="col-md-3">
            <div class="stat-summary">
              <small class="text-muted">Total Changes</small>
              <p class="stat-value">{{ changes.length }}</p>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-summary">
              <small class="text-muted">AI-Driven</small>
              <p class="stat-value">{{ aiChanges }}</p>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-summary">
              <small class="text-muted">Manual Overrides</small>
              <p class="stat-value">{{ manualChanges }}</p>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-summary">
              <small class="text-muted">Avg Price Change</small>
              <p class="stat-value" :class="avgChangeClass">
                {{ avgPriceChange > 0 ? '+' : ''}}${{ formatPrice(Math.abs(avgPriceChange)) }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Model Performance -->
      <div v-if="aiChanges > 0" class="mt-3 pt-3 border-top">
        <h6>AI Model Performance</h6>
        <small class="text-muted">
          Average accuracy of AI recommendations:
          <strong>{{ avgModelAccuracy }}%</strong>
        </small>
        <div class="progress mt-2" style="height: 8px;">
          <div 
            class="progress-bar bg-success" 
            :style="{ width: avgModelAccuracy + '%' }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AuditTrailHistory',
  props: {
    changes: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    aiChanges() {
      return (this.changes || []).filter(c => c.model_version).length;
    },
    manualChanges() {
      return (this.changes || []).filter(c => !c.model_version).length;
    },
    avgPriceChange() {
      if (!this.changes || this.changes.length === 0) return 0;
      const total = this.changes.reduce((sum, c) => sum + (c.new_price - c.previous_price), 0);
      return total / this.changes.length;
    },
    avgChangeClass() {
      return this.avgPriceChange >= 0 ? 'text-success' : 'text-danger';
    },
    avgModelAccuracy() {
      const aiChanges = this.changes.filter(c => c.model_version);
      if (aiChanges.length === 0) return 0;
      const total = aiChanges.reduce((sum, c) => sum + (c.model_accuracy || 92), 0);
      return Math.round(total / aiChanges.length);
    }
  },
  methods: {
    formatDate(dateStr) {
      try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric',
          year: 'numeric'
        });
      } catch {
        return dateStr;
      }
    },
    formatTime(dateStr) {
      try {
        const date = new Date(dateStr);
        return date.toLocaleTimeString('en-US', { 
          hour: '2-digit',
          minute: '2-digit'
        });
      } catch {
        return '';
      }
    },
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2);
    },
    markerClass(change) {
      if (change.model_version) return 'ai-change';
      return 'manual-change';
    },
    markerIcon(change) {
      if (change.model_version) return 'fas fa-robot';
      return 'fas fa-user-edit';
    },
    badgeClass(change) {
      if (change.model_version) return 'badge-success';
      return 'badge-warning';
    },
    priceChangeClass(change) {
      const diff = change.new_price - change.previous_price;
      if (diff > 0) return 'text-success';
      if (diff < 0) return 'text-danger';
      return 'text-muted';
    }
  }
};
</script>

<style scoped>
.audit-trail-card {
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.timeline {
  position: relative;
  padding: 2rem 0;
}

.timeline-item {
  position: relative;
  padding-left: 60px;
  margin-bottom: 2rem;
}

.timeline-item:last-child {
  margin-bottom: 0;
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: 16px;
  top: 40px;
  bottom: -60px;
  width: 2px;
  background-color: #dee2e6;
}

.timeline-item:last-child::before {
  display: none;
}

.timeline-marker {
  position: absolute;
  left: -10px;
  top: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1rem;
  z-index: 1;
}

.timeline-marker.ai-change {
  background-color: #28a745;
  border: 3px solid white;
  box-shadow: 0 0 0 3px #28a745;
}

.timeline-marker.manual-change {
  background-color: #ffc107;
  border: 3px solid white;
  box-shadow: 0 0 0 3px #ffc107;
  color: #333;
}

.timeline-content {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #dee2e6;
}

.timeline-item .timeline-marker.ai-change ~ .timeline-content {
  border-left-color: #28a745;
}

.timeline-item .timeline-marker.manual-change ~ .timeline-content {
  border-left-color: #ffc107;
}

.change-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  font-weight: 500;
}

.change-time {
  font-size: 0.85rem;
  color: #6c757d;
}

.badge {
  font-size: 0.75rem;
  font-weight: bold;
  padding: 0.35rem 0.6rem;
}

.change-details {
  margin-bottom: 0.5rem;
}

.price-old {
  margin: 0.5rem 0 0 0;
  color: #6c757d;
  font-size: 1.1rem;
}

.price-new {
  margin: 0.5rem 0 0 0;
  font-size: 1.1rem;
  font-weight: bold;
}

.price-change {
  display: block;
  font-size: 0.85rem;
  font-weight: normal;
}

.stat-summary {
  text-align: center;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  margin: 0.5rem 0 0 0;
  color: #333;
}

.confidence-badge {
  padding: 0.5rem 1rem;
  background-color: #e8f4f8;
  border-left: 3px solid #17a2b8;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #055160;
}

@media (max-width: 768px) {
  .timeline-item {
    padding-left: 40px;
  }

  .timeline-marker {
    width: 30px;
    height: 30px;
    font-size: 0.75rem;
    left: -5px;
  }

  .timeline-content {
    padding: 1rem;
  }

  .change-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .change-time {
    margin-top: 0.5rem;
  }
}
</style>
