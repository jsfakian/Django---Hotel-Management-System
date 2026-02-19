<template>
  <div class="model-comparison-card card">
    <div class="card-header bg-info text-white">
      <h5 class="mb-0">Model Predictions Comparison</h5>
      <small>5 Trained Models Ranked by Confidence</small>
    </div>
    <div class="card-body">
      <div v-if="loading" class="text-center py-4">
        <div class="spinner-border text-info" role="status">
          <span class="sr-only">Loading models...</span>
        </div>
      </div>

      <div v-else class="models-list">
        <!-- Header Row -->
        <div class="model-header">
          <div class="col rank">Rank</div>
          <div class="col model-name">Model</div>
          <div class="col prediction">Price</div>
          <div class="col accuracy">Accuracy</div>
          <div class="col action">Action</div>
        </div>

        <!-- Model Rows -->
        <div v-for="(model, index) in sortedModels" :key="model.name" class="model-row">
          <div class="col rank">
            <span class="badge badge-primary">{{ index + 1 }}</span>
          </div>
          <div class="col model-name">
            <div class="model-info">
              <strong>{{ model.display_name }}</strong>
              <small class="text-muted d-block">{{ model.description }}</small>
            </div>
          </div>
          <div class="col prediction">
            <span class="model-price">{{ formatPrice(model.prediction) }}</span>
          </div>
          <div class="col accuracy">
            <div class="accuracy-badge" :class="accuracyClass(model.accuracy)">
              {{ (model.accuracy * 100).toFixed(0) }}%
            </div>
            <small class="text-muted d-block">RMSE: {{ model.rmse || 'N/A' }}</small>
          </div>
          <div class="col action">
            <button 
              class="btn btn-sm btn-outline-primary"
              @click="selectModel(model)"
              :disabled="loading"
            >
              Use This
            </button>
          </div>
        </div>
      </div>

      <!-- Model Info Section -->
      <div v-if="selectedModel" class="mt-4 p-3 bg-light rounded">
        <h6>{{ selectedModel.display_name }} Details</h6>
        <div class="row">
          <div class="col-md-4">
            <p class="small"><strong>Type:</strong> {{ selectedModel.type }}</p>
            <p class="small"><strong>Accuracy:</strong> {{ (selectedModel.accuracy * 100).toFixed(1) }}%</p>
          </div>
          <div class="col-md-4">
            <p class="small"><strong>RMSE:</strong> ${{ selectedModel.rmse || 'N/A' }}</p>
            <p class="small"><strong>MAE:</strong> ${{ selectedModel.mae || 'N/A' }}</p>
          </div>
          <div class="col-md-4">
            <p class="small"><strong>Prediction:</strong> <span class="text-success font-weight-bold">${{ formatPrice(selectedModel.prediction) }}</span></p>
          </div>
        </div>
        <p class="text-muted small mt-2">{{ selectedModel.details }}</p>
      </div>

      <!-- Model Descriptions Legend -->
      <div class="mt-3 pt-3 border-top">
        <small class="text-muted">
          <strong>Model Types:</strong>
          Ensemble = Voting from all models | 
          Gradient Boosting = Superior non-linear patterns | 
          Neural Network = Complex feature interactions | 
          Linear = Baseline/interpretable | 
          Seasonal = Time-series aware
        </small>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ModelComparisonCard',
  props: {
    models: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      selectedModel: null
    };
  },
  computed: {
    sortedModels() {
      // Sort by accuracy descending (highest confidence first)
      return [...this.models].sort((a, b) => (b.accuracy || 0) - (a.accuracy || 0));
    }
  },
  watch: {
    models(newModels) {
      if (newModels.length > 0 && !this.selectedModel) {
        this.selectedModel = newModels[0];
      }
    }
  },
  methods: {
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2);
    },
    accuracyClass(accuracy) {
      if (accuracy >= 0.90) return 'badge-success';
      if (accuracy >= 0.80) return 'badge-info';
      if (accuracy >= 0.70) return 'badge-warning';
      return 'badge-danger';
    },
    selectModel(model) {
      this.selectedModel = model;
      this.$emit('select-model', model);
    }
  }
};
</script>

<style scoped>
.model-comparison-card {
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.models-list {
  display: flex;
  flex-direction: column;
}

.model-header,
.model-row {
  display: grid;
  grid-template-columns: 60px 1fr 100px 100px 120px;
  gap: 1rem;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #e9ecef;
}

.model-header {
  font-weight: bold;
  background-color: #f8f9fa;
  padding: 0.75rem 0;
  font-size: 0.9rem;
  color: #6c757d;
}

.model-row {
  transition: background-color 0.2s;
}

.model-row:hover {
  background-color: #f8f9fa;
}

.model-row:last-child {
  border-bottom: none;
}

.col {
  overflow: hidden;
}

.col.rank {
  text-align: center;
}

.col.prediction {
  font-weight: bold;
}

.model-info strong {
  display: block;
  margin-bottom: 0.25rem;
}

.model-price {
  font-size: 1.25rem;
  font-weight: bold;
  color: #28a745;
}

.accuracy-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: bold;
  color: white;
}

.accuracy-badge.badge-success {
  background-color: #28a745;
}

.accuracy-badge.badge-info {
  background-color: #17a2b8;
}

.accuracy-badge.badge-warning {
  background-color: #ffc107;
  color: #333;
}

.accuracy-badge.badge-danger {
  background-color: #dc3545;
}

@media (max-width: 768px) {
  .model-header,
  .model-row {
    grid-template-columns: 45px 1fr 80px 80px;
    gap: 0.5rem;
  }
  
  .col.action {
    display: none;
  }
}
</style>
