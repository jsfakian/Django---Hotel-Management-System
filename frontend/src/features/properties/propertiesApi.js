import { api } from '../../services/api'

export const propertiesApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getProperties: builder.query({
      query: (params = {}) => ({ url: '/properties/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'Property', id })), { type: 'Property', id: 'LIST' }]
          : [{ type: 'Property', id: 'LIST' }],
    }),
    getProperty: builder.query({
      query: (id) => ({ url: `/properties/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Property', id }],
    }),
    createProperty: builder.mutation({
      query: (data) => ({ url: '/properties/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Property', id: 'LIST' }],
    }),
    updateProperty: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/properties/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Property', id }, { type: 'Property', id: 'LIST' }],
    }),
    deleteProperty: builder.mutation({
      query: (id) => ({ url: `/properties/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Property', id: 'LIST' }],
    }),
    getTravelAgencies: builder.query({
      query: (params = {}) => ({ url: '/travel-agencies/', method: 'GET', params }),
      providesTags: () => [{ type: 'Property', id: 'TRAVEL_AGENCIES' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetPropertiesQuery,
  useGetPropertyQuery,
  useCreatePropertyMutation,
  useUpdatePropertyMutation,
  useDeletePropertyMutation,
  useGetTravelAgenciesQuery,
} = propertiesApi
