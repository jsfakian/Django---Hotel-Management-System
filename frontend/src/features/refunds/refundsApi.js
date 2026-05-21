import { api } from '../../services/api'

export const refundsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getRefunds: builder.query({
      query: (params = {}) => ({ url: '/refund-requests/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'Payment', id: `refund-${id}` })), { type: 'Payment', id: 'REFUND_LIST' }]
          : [{ type: 'Payment', id: 'REFUND_LIST' }],
    }),
    getRefund: builder.query({
      query: (id) => ({ url: `/refund-requests/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Payment', id: `refund-${id}` }],
    }),
    createRefund: builder.mutation({
      query: (data) => ({ url: '/refund-requests/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Payment', id: 'REFUND_LIST' }],
    }),
    updateRefund: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/refund-requests/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Payment', id: `refund-${id}` }, { type: 'Payment', id: 'REFUND_LIST' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetRefundsQuery,
  useGetRefundQuery,
  useCreateRefundMutation,
  useUpdateRefundMutation,
} = refundsApi
