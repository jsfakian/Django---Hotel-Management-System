import { api } from '../../services/api'

export const inventoryApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getPropertyAvailability: builder.query({
      query: (propertyId) => ({ url: `/inventory/availability/${propertyId}/`, method: 'GET' }),
      providesTags: (result, error, propertyId) => [{ type: 'Room', id: `avail-${propertyId}` }],
    }),
    updateRoomAvailability: builder.mutation({
      query: ({ roomId, ...data }) => ({ url: `/inventory/rooms/${roomId}/availability/`, method: 'PUT', data }),
      invalidatesTags: [{ type: 'Room', id: 'LIST' }],
    }),
    overbook: builder.mutation({
      query: (data) => ({ url: '/inventory/overbook/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Room', id: 'LIST' }],
    }),
    getSyncLog: builder.query({
      query: (propertyId) => ({ url: `/inventory/sync-log/${propertyId}/`, method: 'GET' }),
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetPropertyAvailabilityQuery,
  useUpdateRoomAvailabilityMutation,
  useOverbookMutation,
  useGetSyncLogQuery,
} = inventoryApi
