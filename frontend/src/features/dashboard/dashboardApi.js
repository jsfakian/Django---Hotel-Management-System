import { api } from '../../services/api'

export const dashboardApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getDashboardStats: builder.query({
      query: () => ({
        url: '/dashboard/stats/',
        method: 'GET',
      }),
      providesTags: ['Dashboard'],
    }),
  }),
  overrideExisting: false,
})

export const { useGetDashboardStatsQuery } = dashboardApi
