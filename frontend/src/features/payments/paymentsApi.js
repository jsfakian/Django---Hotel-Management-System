import { api } from '../../services/api'

export const paymentsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getPayments: builder.query({
      query: (params = {}) => ({
        url: '/payments/',
        method: 'GET',
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...((result.results || result).map
                ? (result.results || result).map(({ id }) => ({
                    type: 'Payment',
                    id,
                  }))
                : []),
              { type: 'Payment', id: 'LIST' },
            ]
          : [{ type: 'Payment', id: 'LIST' }],
    }),
    getInvoices: builder.query({
      query: (params = {}) => ({
        url: '/invoices/',
        method: 'GET',
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...((result.results || result).map
                ? (result.results || result).map(({ id }) => ({
                    type: 'Invoice',
                    id,
                  }))
                : []),
              { type: 'Invoice', id: 'LIST' },
            ]
          : [{ type: 'Invoice', id: 'LIST' }],
    }),
    getPayment: builder.query({
      query: (id) => ({ url: `/payments/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Payment', id }],
    }),
    createPayment: builder.mutation({
      query: (data) => ({ url: '/payments/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Payment', id: 'LIST' }, { type: 'Invoice', id: 'LIST' }],
    }),
    updatePayment: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/payments/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Payment', id }],
    }),
    verifyPayment: builder.mutation({
      query: ({ id, verification_code }) => ({
        url: `/payments/${id}/verify/`,
        method: 'POST',
        data: { verification_code },
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Payment', id }, { type: 'Payment', id: 'LIST' }],
    }),
    getInvoice: builder.query({
      query: (id) => ({ url: `/invoices/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Invoice', id }],
    }),
    transmitInvoiceToMydata: builder.mutation({
      query: (id) => ({ url: `/payments/invoices/${id}/mydata/transmit/`, method: 'POST' }),
      invalidatesTags: (result, error, id) => [{ type: 'Invoice', id }],
    }),
    getMyDataStatus: builder.query({
      query: (id) => ({ url: `/payments/invoices/${id}/mydata/status/`, method: 'GET' }),
    }),
    bulkTransmitMydata: builder.mutation({
      query: (data) => ({ url: '/payments/invoices/mydata/bulk-transmit/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Invoice', id: 'LIST' }],
    }),
  }),
  overrideExisting: true,
})

export const {
  useGetPaymentsQuery,
  useGetPaymentQuery,
  useCreatePaymentMutation,
  useUpdatePaymentMutation,
  useVerifyPaymentMutation,
  useGetInvoicesQuery,
  useGetInvoiceQuery,
  useTransmitInvoiceToMydataMutation,
  useGetMyDataStatusQuery,
  useBulkTransmitMydataMutation,
} = paymentsApi
