import { api } from '../../services/api'

export const gdprApi = api.injectEndpoints({
  endpoints: (builder) => ({
    requestDataExport: builder.mutation({
      query: () => ({ url: '/gdpr/request-export/', method: 'POST' }),
    }),
    downloadDataExport: builder.query({
      query: () => ({ url: '/gdpr/download-export/', method: 'GET' }),
    }),
    checkExportStatus: builder.query({
      query: (taskId) => ({ url: `/gdpr/export-status/${taskId}/`, method: 'GET' }),
    }),
    requestDataDeletion: builder.mutation({
      query: (data) => ({ url: '/gdpr/request-deletion/', method: 'POST', data }),
    }),
  }),
  overrideExisting: false,
})

export const {
  useRequestDataExportMutation,
  useDownloadDataExportQuery,
  useCheckExportStatusQuery,
  useRequestDataDeletionMutation,
} = gdprApi
