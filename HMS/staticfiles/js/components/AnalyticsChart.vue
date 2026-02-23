<template>
  <div class="analytics-chart-wrapper">
    <div class="card">
      <div class="card-header bg-light">
        <h5 class="mb-0">{{ title }}</h5>
        <p class="text-muted small mb-0" v-if="subtitle">{{ subtitle }}</p>
      </div>
      <div class="card-body">
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
        <div v-else-if="errorMessage" class="alert alert-danger">
          {{ errorMessage }}
        </div>
        <canvas v-else ref="chartCanvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalyticsChart',
  props: {
    title: String,
    subtitle: String,
    chartType: {
      type: String,
      default: 'line' // line, bar, doughnut, pie
    },
    labels: Array,
    datasets: Array,
    options: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      loading: false,
      errorMessage: null,
      chart: null
    };
  },
  watch: {
    datasets: {
      handler() {
        this.updateChart();
      },
      deep: true
    },
    labels() {
      this.updateChart();
    }
  },
  mounted() {
    this.initChart();
  },
  methods: {
    initChart() {
      const ctx = this.$refs.chartCanvas.getContext('2d');
      
      const defaultOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: false,
          }
        },
        scales: this.chartType === 'line' || this.chartType === 'bar' ? {
          y: {
            beginAtZero: true
          }
        } : {}
      };

      const chartOptions = { ...defaultOptions, ...this.options };

      if (this.chart) {
        this.chart.destroy();
      }

      this.chart = new Chart(ctx, {
        type: this.chartType,
        data: {
          labels: this.labels,
          datasets: this.datasets
        },
        options: chartOptions
      });
    },
    updateChart() {
      if (this.chart) {
        this.chart.data.labels = this.labels;
        this.chart.data.datasets = this.datasets;
        this.chart.update();
      }
    }
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.destroy();
    }
  }
};
</script>

<style scoped>
.analytics-chart-wrapper {
  margin-bottom: 1.5rem;
}

.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  border: 1px solid #dee2e6;
}

.card-header {
  border-bottom: 1px solid #dee2e6;
}

canvas {
  max-height: 400px;
}
</style>
