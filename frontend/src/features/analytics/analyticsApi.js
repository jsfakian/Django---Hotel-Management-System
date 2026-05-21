import { api } from '../../services/api'

export const analyticsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    // Dashboards
    getExecutiveDashboard: builder.query({
      query: (params = {}) => ({ url: '/analytics/executive-dashboard/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getOperationalDashboard: builder.query({
      query: (params = {}) => ({ url: '/analytics/operational-dashboard/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getRevenueAnalytics: builder.query({
      query: (params = {}) => ({ url: '/analytics/revenue-analytics/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getGuestAnalytics: builder.query({
      query: (params = {}) => ({ url: '/analytics/guest-analytics/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),

    // Forecasting
    getOccupancyForecasts: builder.query({
      query: (params = {}) => ({ url: '/analytics/occupancy-forecasts/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getOccupancyForecastNext30: builder.query({
      query: () => ({ url: '/analytics/occupancy-forecasts/next-30-days/', method: 'GET' }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getRevenueForecasts: builder.query({
      query: (params = {}) => ({ url: '/analytics/revenue-forecasts/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getRevenueForecastNext30: builder.query({
      query: () => ({ url: '/analytics/revenue-forecasts/next-30-days/', method: 'GET' }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getForecastMetrics: builder.query({
      query: () => ({ url: '/analytics/forecast-metrics/', method: 'GET' }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getForecastHealthCheck: builder.query({
      query: () => ({ url: '/analytics/forecast-metrics/health-check/', method: 'GET' }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),

    // Predictions
    getCancellationPredictions: builder.query({
      query: (params = {}) => ({ url: '/analytics/cancellation-predictions/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getHighRiskCancellations: builder.query({
      query: () => ({ url: '/analytics/cancellation-predictions/high-risk/', method: 'GET' }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getCancellationsByProperty: builder.query({
      query: (property_id) => ({
        url: '/analytics/cancellation-predictions/by_property/',
        method: 'GET',
        params: { property_id },
      }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getNoShowPredictions: builder.query({
      query: (params = {}) => ({ url: '/analytics/noshow-predictions/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getHighRiskNoShows: builder.query({
      query: () => ({ url: '/analytics/noshow-predictions/high_risk/', method: 'GET' }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),
    getOverbookingRecommendations: builder.query({
      query: () => ({ url: '/analytics/noshow-predictions/overbooking-recommendations/', method: 'GET' }),
      providesTags: () => [{ type: 'Dashboard' }],
    }),

    // Custom Reports
    getCustomReports: builder.query({
      query: (params = {}) => ({ url: '/analytics/custom-reports/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'Dashboard', id: `report-${id}` })), { type: 'Dashboard', id: 'REPORT_LIST' }]
          : [{ type: 'Dashboard', id: 'REPORT_LIST' }],
    }),
    createCustomReport: builder.mutation({
      query: (data) => ({ url: '/analytics/custom-reports/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Dashboard', id: 'REPORT_LIST' }],
    }),
    deleteCustomReport: builder.mutation({
      query: (id) => ({ url: `/analytics/custom-reports/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Dashboard', id: 'REPORT_LIST' }],
    }),

    // Scheduled Reports
    getScheduledReports: builder.query({
      query: (params = {}) => ({ url: '/analytics/scheduled-reports/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'Dashboard', id: `sched-${id}` })), { type: 'Dashboard', id: 'SCHED_LIST' }]
          : [{ type: 'Dashboard', id: 'SCHED_LIST' }],
    }),
    createScheduledReport: builder.mutation({
      query: (data) => ({ url: '/analytics/scheduled-reports/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Dashboard', id: 'SCHED_LIST' }],
    }),
    triggerScheduledReport: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/analytics/scheduled-reports/${id}/trigger/`, method: 'POST', data }),
      invalidatesTags: [{ type: 'Dashboard', id: 'EXEC_LIST' }],
    }),
    testScheduledReport: builder.mutation({
      query: (id) => ({ url: `/analytics/scheduled-reports/${id}/test/`, method: 'POST' }),
      invalidatesTags: [{ type: 'Dashboard', id: 'EXEC_LIST' }],
    }),
    updateScheduledReport: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/analytics/scheduled-reports/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Dashboard', id: `sched-${id}` }],
    }),
    deleteScheduledReport: builder.mutation({
      query: (id) => ({ url: `/analytics/scheduled-reports/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Dashboard', id: 'SCHED_LIST' }],
    }),

    // Report Executions
    getReportExecutions: builder.query({
      query: (params = {}) => ({ url: '/analytics/report-executions/', method: 'GET', params }),
      providesTags: () => [{ type: 'Dashboard', id: 'EXEC_LIST' }],
    }),
    getExecutionDeliveryTracking: builder.query({
      query: (id) => ({ url: `/analytics/report-executions/${id}/delivery_status/`, method: 'GET' }),
      providesTags: () => [{ type: 'Dashboard', id: 'EXEC_LIST' }],
    }),
    resendReportExecution: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/analytics/report-executions/${id}/resend/`, method: 'POST', data }),
      invalidatesTags: [{ type: 'Dashboard', id: 'EXEC_LIST' }],
    }),
  }),
  overrideExisting: true,
})

export const {
  useGetExecutiveDashboardQuery,
  useGetOperationalDashboardQuery,
  useGetRevenueAnalyticsQuery,
  useGetGuestAnalyticsQuery,
  useGetOccupancyForecastsQuery,
  useGetOccupancyForecastNext30Query,
  useGetRevenueForecastsQuery,
  useGetRevenueForecastNext30Query,
  useGetForecastMetricsQuery,
  useGetForecastHealthCheckQuery,
  useGetCancellationPredictionsQuery,
  useGetHighRiskCancellationsQuery,
  useGetCancellationsByPropertyQuery,
  useGetNoShowPredictionsQuery,
  useGetHighRiskNoShowsQuery,
  useGetOverbookingRecommendationsQuery,
  useGetCustomReportsQuery,
  useCreateCustomReportMutation,
  useDeleteCustomReportMutation,
  useGetScheduledReportsQuery,
  useCreateScheduledReportMutation,
  useTriggerScheduledReportMutation,
  useTestScheduledReportMutation,
  useUpdateScheduledReportMutation,
  useDeleteScheduledReportMutation,
  useGetReportExecutionsQuery,
  useGetExecutionDeliveryTrackingQuery,
  useResendReportExecutionMutation,
} = analyticsApi
