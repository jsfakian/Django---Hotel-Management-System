import { api } from '../../services/api'

export const contractsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getContracts: builder.query({
      query: (params = {}) => ({ url: '/contracts/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'Property', id: `contract-${id}` })), { type: 'Property', id: 'CONTRACT_LIST' }]
          : [{ type: 'Property', id: 'CONTRACT_LIST' }],
    }),
    getContract: builder.query({
      query: (id) => ({ url: `/contracts/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Property', id: `contract-${id}` }],
    }),
    createContract: builder.mutation({
      query: (data) => ({ url: '/contracts/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Property', id: 'CONTRACT_LIST' }],
    }),
    updateContract: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/contracts/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Property', id: `contract-${id}` }],
    }),
    signContract: builder.mutation({
      query: (id) => ({ url: `/contracts/${id}/sign/`, method: 'POST' }),
      invalidatesTags: (result, error, id) => [{ type: 'Property', id: `contract-${id}` }, { type: 'Property', id: 'CONTRACT_LIST' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetContractsQuery,
  useGetContractQuery,
  useCreateContractMutation,
  useUpdateContractMutation,
  useSignContractMutation,
} = contractsApi
