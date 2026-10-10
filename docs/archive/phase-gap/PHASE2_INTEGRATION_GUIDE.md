# Phase 2 Frontend Integration Guide
## How to Use the Pricing Analysis Components

**Date:** February 20, 2026  
**Status:** Ready for Integration  
**Components:** 9 Vue components + 1 API service module  

---

## Quick Start

### 1. Include Vue.js & Chart.js in Your Template

Add these to your `HMS/templates/base.html` or module template:

```html
<!-- Vue.js 3.x -->
<script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>

<!-- Chart.js for trend visualization -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>

<!-- OR use Chart.js 2.x if Vue 2.x -->
<!-- <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script> -->
```

### 2. Create the Pricing Analysis Template

Create `HMS/templates/manager/pricing-analysis.html`:

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Dynamic Pricing Analysis{% endblock %}

{% block content %}
<div id="pricing-analysis-app"></div>

<script type="module">
  import PricingAnalysis from '{% static "js/components/PricingAnalysis.vue" %}';
  
  const { createApp } = Vue;
  
  createApp({
    components: {
      PricingAnalysis
    },
    template: `
      <pricing-analysis 
        :room-id="roomId" 
        :room-name="roomName" 
        :selected-date="selectedDate"
      />
    `,
    data() {
      return {
        roomId: {{ room.id }},
        roomName: '{{ room.name }}',
        selectedDate: '{{ selected_date | date:"Y-m-d" }}'
      };
    }
  }).mount('#pricing-analysis-app');
</script>
{% endblock %}
```

### 3. Add Route in Django

Update `HMS/urls.py`:

```python
urlpatterns = [
    # ... existing patterns
    path('pricing/<int:room_id>/<str:date>/', 
         views.pricing_analysis_view, 
         name='pricing-analysis'),
]
```

### 4. Create View

Add to `HMS/views.py`:

```python
from django.shortcuts import render
from room.models import Room

def pricing_analysis_view(request, room_id, date):
    """Display pricing analysis interface for a room on a specific date."""
    room = get_object_or_404(Room, id=room_id)
    
    context = {
        'room': room,
        'selected_date': date,
        'page_title': f'Pricing Analysis - {room.name} ({date})'
    }
    return render(request, 'manager/pricing-analysis.html', context)
```

---

## Component Usage Examples

### Standalone Usage (Not Recommended)

If you need to use individual components, here's how:

```javascript
// Import single component
import PricingStatusCard from '/static/js/components/PricingStatusCard.vue';

// Create Vue app with component
const app = Vue.createApp({
  components: { PricingStatusCard },
  template: `
    <pricing-status-card 
      :base-price="100"
      :ai-recommendation="125.50"
      :competitor-price="120"
      :confidence="0.92"
    />
  `
});

app.mount('#app');
```

### Data Structure for Manual Testing

If you need to mock the API responses:

```javascript
// Pricing prediction response
{
  "ensemble_prediction": 185.50,
  "confidence": 0.92,
  "all_predictions": {
    "ensemble": 185.50,
    "gradient_boosting": 187.00,
    "neural_network": 182.30,
    "linear_regression": 180.00,
    "seasonal": 188.00
  },
  "factors": {
    "base_price": 150.00,
    "occupancy_rate": 75,
    "occupancy_impact_dollars": 15.50,
    "occupancy_impact_percent": 5.2,
    "season": "high",
    "seasonal_impact_dollars": 25.00,
    "seasonal_impact_percent": 8.3,
    "demand_score": "high",
    "demand_impact_dollars": 10.00,
    "demand_impact_percent": 3.3,
    "competitor_impact_dollars": -5.00,
    "competitor_impact_percent": -1.7
  },
  "competitor_price": 180.00,
  "market_range": {
    "min": 140.00,
    "max": 220.00,
    "average": 180.00,
    "stddev": 15.50
  }
}

// Pricing history response
{
  "room_id": 1,
  "date_range": {
    "from": "2026-01-21",
    "to": "2026-02-20"
  },
  "history": [
    {
      "date": "2026-02-20",
      "base_price": 150.00,
      "dynamic_price": 185.50,
      "competitor_price": 180.00,
      "occupancy_rate": 75
    },
    // ... 29 more days
  ],
  "statistics": {
    "min_price": 140.00,
    "max_price": 195.00,
    "avg_price": 172.50,
    "std_dev": 12.30,
    "min_date": "2026-01-25",
    "max_date": "2026-02-14"
  }
}

// Scenario analysis response
{
  "scenario_price": 195.00,
  "current_price": 185.50,
  "price_change": 9.50,
  "price_change_percent": 5.12,
  "revenue_impact_per_night": 9.50,
  "revenue_impact_per_3night_stay": 28.50
}
```

---

## Accessing Components in Templates

### Standard Module CRUD Integration

If you're using the generic `module-crud.html` template, add a conditional:

```html
{% if module_key == 'inventory' %}
  <!-- Show pricing analysis instead of generic form -->
  {% include 'manager/pricing-analysis.html' %}
{% else %}
  <!-- Standard CRUD form -->
  <form method="post" class="module-form">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit" class="btn btn-primary">Save</button>
  </form>
{% endif %}
```

### Navigation Link

Add to your admin navigation:

```html
<a href="{% url 'pricing-analysis' room.id '2026-02-20' %}" class="nav-link">
  <i class="fas fa-chart-line"></i> Pricing Analysis
</a>
```

---

## API Service Usage

The `pricingApiService.js` singleton is auto-loaded by `PricingAnalysis.vue`, but you can use it directly if needed:

```javascript
import pricingApi from '/static/js/services/pricingApiService.js';

// Get pricing prediction
const prediction = await pricingApi.getPricingPrediction(
  roomId,      // number
  '2026-02-20' // date string YYYY-MM-DD
);

// Get pricing history
const history = await pricingApi.getPricingHistory(
  roomId,    // number
  30         // days (optional, default 30)
);

// Analyze scenario (what-if)
const scenario = await pricingApi.analyzeScenario(
  roomId,
  '2026-02-20',
  {
    occupancy_rate: 80,
    season: 'peak',
    competitor_price: 175.00
  }
);

// Get available models
const models = await pricingApi.getAvailableModels();
```

---

## Customization Options

### Change Color Scheme

Edit component `<style scoped>` sections:

```vue
<style scoped>
/* Change primary color from blue to purple */
.btn-primary {
  background-color: #6f42c1; /* was #007bff */
}
</style>
```

### Disable Specific Sections

Comment out components in `PricingAnalysis.vue`:

```vue
<!-- Section to hide -->
<!-- <ScenarioAnalyzer ... /> -->
```

### Customize Breakpoints

Edit responsive design breakpoints in individual components:

```vue
@media (max-width: 768px) {
  /* Change to your breakpoint */
}
```

### Add Additional Factors

Extend `PricingFactorsBreakdown.vue` to include custom factors:

```vue
<!-- Add new factor section -->
<div class="factor-item custom-factor">
  <div class="factor-header">
    <span>Custom Factor</span>
    <span class="factor-value">$X.XX</span>
  </div>
</div>
```

---

## Troubleshooting

### "Cannot find module" errors

Make sure all imports use correct relative paths:

```javascript
// ✓ Correct
import pricingApi from '../services/pricingApiService.js';

// ✗ Wrong (missing .js extension)
import pricingApi from '../services/pricingApiService';
```

### Chart not rendering

Ensure Chart.js library is loaded before the component:

```html
<!-- Must be BEFORE Vue app script -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>

<!-- THEN your Vue app -->
<script type="module" src="/static/js/app.js"></script>
```

### CSRF token missing errors

The service auto-injects CSRF tokens, but ensure:

```html
<!-- In your Django template -->
{% csrf_token %}
<!-- OR in a meta tag -->
<meta name="csrf-token" content="{{ csrf_token }}">
```

### API endpoint 404 errors

Verify Phase 1 backend is built and endpoints exist:

```bash
# Check endpoints are registered
python manage.py show_urls | grep pricing

# Should show:
# /api/v1/bookings/pricing/predict/
# /api/v1/bookings/pricing/history/
# /api/v1/bookings/pricing/scenario/
# /api/v1/bookings/pricing/models/
```

---

## Performance Optimization

### Lazy Load Chart.js

Only load Chart.js for HistoricalTrendChart:

```vue
<!-- In HistoricalTrendChart.vue -->
<script>
// Dynamic import only when needed
import { defineAsyncComponent } from 'vue';

const Chart = defineAsyncComponent(() => 
  import('chart.js/auto')
);
</script>
```

### Cache API Responses

Add to `pricingApiService.js`:

```javascript
const cache = new Map();

async _apiCall(endpoint, options = {}) {
  // Check cache (optional TTL)
  if (cache.has(endpoint)) {
    return cache.get(endpoint).data;
  }
  
  const response = await fetch(...);
  
  // Cache for 5 minutes
  cache.set(endpoint, {
    data: response,
    timestamp: Date.now()
  });
  
  return response;
}
```

---

## Browser Testing

Test on all supported browsers:

```bash
# Chrome
open -a "Google Chrome" http://localhost:8000/pricing/1/2026-02-20/

# Firefox
open -a Firefox http://localhost:8000/pricing/1/2026-02-20/

# Safari
open -a Safari http://localhost:8000/pricing/1/2026-02-20/
```

### Mobile Testing

Use responsive design mode:

```bash
# Chrome DevTools
Cmd+Shift+M (Mac) or Ctrl+Shift+M (Windows/Linux)

# Test widths: 375px (mobile), 768px (tablet), 1024px (desktop)
```

---

## Next Steps: Phase 3

After Phase 2 is integrated:

1. **Celery Tasks** - Background pricing updates
2. **Admin Features** - Bulk pricing, alerts, templates
3. **Database Optimization** - Indexing, caching
4. **Analytics** - Track AI recommendation accuracy
5. **Email Notifications** - Alert managers of price changes
6. **API Documentation** - OpenAPI/Swagger for frontend

---

## Support & Questions

Refer to detailed documentation:
- [PHASE2_IMPLEMENTATION_SUMMARY.md](PHASE2_IMPLEMENTATION_SUMMARY.md) - Component specs
- [PRICING_MODULE_FE_REDESIGN_PLAN.md](PRICING_MODULE_FE_REDESIGN_PLAN.md) - Design requirements
- [PHASE1_COMPLETION_SUMMARY.md](PHASE1_COMPLETION_SUMMARY.md) - Backend API details

Components are production-ready and fully integrated with Phase 1 backend APIs.

