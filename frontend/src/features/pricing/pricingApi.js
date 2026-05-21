import { api } from '../../services/api'

export const pricingApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getPricingAnalysis: builder.query({
      query: (params = {}) => ({ url: '/bookings/pricing/predict/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getPricingHistory: builder.query({
      query: (params = {}) => ({ url: '/bookings/pricing/history/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    analyzePricingScenario: builder.mutation({
      query: (data) => ({ url: '/bookings/pricing/scenario/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Dashboard' }],
    }),
    getPricingModels: builder.query({
      query: () => ({ url: '/bookings/pricing/models/', method: 'GET' }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getPricingRecommendations: builder.query({
      query: (params = {}) => ({ url: '/bookings/pricing-recommendations/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetPricingAnalysisQuery,
  useGetPricingHistoryQuery,
  useAnalyzePricingScenarioMutation,
  useGetPricingModelsQuery,
  useGetPricingRecommendationsQuery,
} = pricingApi
