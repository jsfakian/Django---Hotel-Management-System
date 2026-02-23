<template>
  <div class="trend-chart-card card">
    <div class="card-header bg-secondary text-white">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <h5 class="mb-0">Historical Pricing Trend</h5>
          <small>Last 30 Days</small>
        </div>
        <div class="chart-controls">
          <button 
            @click="toggleBaseDynamic"
            class="btn btn-sm btn-light"
            :title="showDynamic ? 'Hide Dynamic Price' : 'Show Dynamic Price'"
          >
            <i :class="['fas', showDynamic ? 'fa-eye' : 'fa-eye-slash']"></i>
          </button>
        </div>
      </div>
    </div>
    <div class="card-body">
      <!-- Chart Container -->
      <div class="chart-container">
        <canvas ref="trendChart"></canvas>
      </div>

      <!-- Statistics Summary -->
      <div class="row mt-4">
        <div class="col-md-3">
          <div class="stat-box">
            <small class="stat-label">Minimum Price</small>
            <p class="stat-value">${{ formatPrice(statistics.min_price) }}</p>
            <small class="text-muted">{{ statistics.min_date }}</small>
          </div>
        </div>
        <div class="col-md-3">
          <div class="stat-box">
            <small class="stat-label">Maximum Price</small>
            <p class="stat-value">${{ formatPrice(statistics.max_price) }}</p>
            <small class="text-muted">{{ statistics.max_date }}</small>
          </div>
        </div>
        <div class="col-md-3">
          <div class="stat-box">
            <small class="stat-label">Average Price</small>
            <p class="stat-value">${{ formatPrice(statistics.avg_price) }}</p>
          </div>
        </div>
        <div class="col-md-3">
          <div class="stat-box">
            <small class="stat-label">Price Volatility</small>
            <p class="stat-value">${{ formatPrice(statistics.std_dev) }}</p>
            <small class="text-muted">Standard Deviation</small>
          </div>
        </div>
      </div>

      <!-- Trend Analysis -->
      <div class="mt-3 p-3 bg-light rounded">
        <h6>Trend Analysis</h6>
        <div class="row">
          <div class="col-md-6">
            <small><strong>Recent Trend:</strong></small>
            <p class="trend-indicator" :class="trendDirection">
              <i :class="['fas', trendIcon]"></i>
              {{ trendDescription }}
            </p>
          </div>
          <div class="col-md-6">
            <small><strong>Price Stability:</strong></small>
            <p class="text-muted small">
              {{ volatilityInterpretation }}
            </p>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div class="mt-3 pt-3 border-top small text-muted">
        <span class="legend-item">
          <span class="legend-color" style="background-color: #007bff;"></span> Base Price
        </span>
        <span v-show="showDynamic" class="legend-item ml-3">
          <span class="legend-color" style="background-color: #28a745;"></span> Dynamic Price
        </span>
        <span class="legend-item ml-3">
          <span class="legend-color" style="background-color: #ffc107;"></span> Market Average
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import Chart from 'chart.js/auto';

export default {
  name: 'HistoricalTrendChart',
  props: {
    historyData: {
      type: Array,
      required: true
    },
    statistics: {
      type: Object,
      default: () => ({
        min_price: 0,
        max_price: 0,
        avg_price: 0,
        std_dev: 0,
        min_date: '',
        max_date: ''
      })
    },
    competitorPrice: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      chartInstance: null,
      showDynamic: true
    };
  },
  computed: {
    trendDirection() {
      if (!this.historyData || this.historyData.length < 2) return 'text-secondary';
      const recent = this.historyData.slice(-7);
      const older = this.historyData.slice(-14, -7);
      const recentAvg = recent.reduce((sum, d) => sum + (d.dynamic_price || 0), 0) / recent.length;
      const olderAvg = older.reduce((sum, d) => sum + (d.dynamic_price || 0), 0) / older.length;
      
      if (recentAvg > olderAvg) return 'text-success';
      if (recentAvg < olderAvg) return 'text-danger';
      return 'text-secondary';
    },
    trendIcon() {
      if (this.trendDirection === 'text-success') return 'fa-arrow-up';
      if (this.trendDirection === 'text-danger') return 'fa-arrow-down';
      return 'fa-minus';
    },
    trendDescription() {
      if (this.trendDirection === 'text-success') return 'Prices rising - strong demand';
      if (this.trendDirection === 'text-danger') return 'Prices falling - weak demand';
      return 'Prices stable - steady demand';
    },
    volatilityInterpretation() {
      const stdDev = this.statistics.std_dev || 0;
      const avg = this.statistics.avg_price || 1;
      const cv = (stdDev / avg) * 100; // Coefficient of variation
      
      if (cv < 5) return '🟢 Very stable pricing - consistent pattern';
      if (cv < 10) return '🟡 Moderate volatility - typical seasonal variation';
      if (cv < 20) return '🟠 High volatility - consider stabilizing strategy';
      return '🔴 Very high volatility - significant price swings';
    }
  },
  watch: {
    historyData: {
      handler() {
        this.$nextTick(() => {
          this.initChart();
        });
      },
      deep: true
    }
  },
  mounted() {
    this.initChart();
  },
  beforeDestroy() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }
  },
  methods: {
    initChart() {
      if (!this.$refs.trendChart) return;

      // Prepare chart data
      const labels = (this.historyData || []).map(d => this.formatDate(d.date));
      const basePrices = (this.historyData || []).map(d => d.base_price || 0);
      const dynamicPrices = (this.historyData || []).map(d => d.dynamic_price || 0);
      const marketAverages = (this.historyData || []).map(() => this.competitorPrice);

      // Destroy old chart if exists
      if (this.chartInstance) {
        this.chartInstance.destroy();
      }

      // Create new chart
      const ctx = this.$refs.trendChart.getContext('2d');
      this.chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Base Price',
              data: basePrices,
              borderColor: '#007bff',
              backgroundColor: 'rgba(0, 123, 255, 0.05)',
              borderWidth: 2,
              tension: 0.1,
              fill: true,
              pointRadius: 3,
              pointBackgroundColor: '#007bff',
              pointBorderColor: '#fff',
              pointBorderWidth: 2
            },
            {
              label: 'Dynamic Price',
              data: this.showDynamic ? dynamicPrices : [],
              borderColor: '#28a745',
              backgroundColor: 'rgba(40, 167, 69, 0.05)',
              borderWidth: 2,
              tension: 0.1,
              fill: true,
              pointRadius: 3,
              pointBackgroundColor: '#28a745',
              pointBorderColor: '#fff',
              pointBorderWidth: 2,
              hidden: !this.showDynamic
            },
            {
              label: 'Market Average',
              data: marketAverages,
              borderColor: '#ffc107',
              backgroundColor: 'transparent',
              borderWidth: 2,
              borderDash: [5, 5],
              tension: 0.1,
              fill: false,
              pointRadius: 0,
              pointBackgroundColor: '#ffc107'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          interaction: {
            mode: 'index',
            intersect: false
          },
          plugins: {
            legend: {
              position: 'top',
              labels: {
                padding: 15,
                usePointStyle: true,
                font: {
                  size: 12
                }
              }
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              padding: 12,
              titleFont: { size: 13 },
              bodyFont: { size: 12 },
              callbacks: {
                afterLabel: (context) => {
                  if (context.datasetIndex === 1) {
                    const basePrice = context.chart.data.datasets[0].data[context.dataIndex];
                    const dynamicPrice = context.parsed.y;
                    const diff = dynamicPrice - basePrice;
                    return `Adjustment: ${diff > 0 ? '+' : ''}$${diff.toFixed(2)}`;
                  }
                  return '';
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: false,
              ticks: {
                callback: (value) => '$' + value.toFixed(0)
              },
              title: {
                display: true,
                text: 'Price ($)'
              }
            },
            x: {
              title: {
                display: true,
                text: 'Date'
              }
            }
          }
        }
      });
    },
    formatDate(dateStr) {
      try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      } catch {
        return dateStr;
      }
    },
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2);
    },
    toggleBaseDynamic() {
      this.showDynamic = !this.showDynamic;
      if (this.chartInstance) {
        this.chartInstance.data.datasets[1].hidden = !this.showDynamic;
        this.chartInstance.update();
      }
    }
  }
};
</script>

<style scoped>
.trend-chart-card {
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-container {
  position: relative;
  height: 300px;
  margin-bottom: 1.5rem;
}

.chart-controls {
  display: flex;
  gap: 0.5rem;
}

.stat-box {
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 1rem;
  text-align: center;
}

.stat-label {
  display: block;
  color: #6c757d;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  margin: 0.5rem 0;
  color: #333;
}

.trend-indicator {
  margin: 0.5rem 0;
  font-size: 1rem;
  font-weight: 500;
}

.trend-indicator.text-success {
  color: #28a745;
}

.trend-indicator.text-danger {
  color: #dc3545;
}

.trend-indicator.text-secondary {
  color: #6c757d;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-color {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

@media (max-width: 768px) {
  .chart-container {
    height: 200px;
  }

  .stat-box {
    padding: 1rem;
    margin-bottom: 0.5rem;
  }

  .stat-value {
    font-size: 1.25rem;
  }
}
</style>
