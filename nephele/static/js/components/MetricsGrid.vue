<template>
  <div class="metrics-grid">
    <div class="metric-card" v-for="metric in metrics" :key="metric.id">
      <div class="metric-card-header">
        <h6 class="metric-label">{{ metric.label }}</h6>
        <span v-if="metric.trend" :class="['trend-badge', metric.trend > 0 ? 'trend-up' : 'trend-down']">
          <i :class="['fas', metric.trend > 0 ? 'fa-arrow-up' : 'fa-arrow-down']"></i>
          {{ Math.abs(metric.trend) }}%
        </span>
      </div>
      <div class="metric-value">
        {{ formatValue(metric.value, metric.type) }}
      </div>
      <div class="metric-footer">
        <small class="text-muted">{{ metric.comparison }}</small>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MetricsGrid',
  props: {
    metrics: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    formatValue(value, type) {
      if (value === null || value === undefined) return '—';
      
      switch (type) {
        case 'currency':
          return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0
          }).format(value);
        case 'percentage':
          return (value).toFixed(1) + '%';
        case 'number':
          return new Intl.NumberFormat('en-US').format(Math.round(value));
        case 'decimal':
          return (value).toFixed(2);
        default:
          return value;
      }
    }
  }
};
</script>

<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 1.5rem;
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  transition: box-shadow 0.2s ease;
}

.metric-card:hover {
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.metric-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.metric-label {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.trend-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-weight: 600;
}

.trend-up {
  background-color: #d4edda;
  color: #155724;
}

.trend-down {
  background-color: #f8d7da;
  color: #721c24;
}

.trend-badge i {
  margin-right: 0.25rem;
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #212529;
  margin-bottom: 0.5rem;
}

.metric-footer {
  border-top: 1px solid #e9ecef;
  padding-top: 0.75rem;
}
</style>
