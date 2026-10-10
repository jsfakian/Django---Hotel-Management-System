import { api } from '../../services/api'

export const catalogApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getRoomTypes: builder.query({
      query: (params = {}) => ({ url: '/room-types/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [
              ...(result.results || result).map(({ id }) => ({ type: 'Room', id: `rt-${id}` })),
              { type: 'Room', id: 'ROOM_TYPE_LIST' },
            ]
          : [{ type: 'Room', id: 'ROOM_TYPE_LIST' }],
    }),
    getRoomType: builder.query({
      query: (id) => ({ url: `/room-types/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Room', id: `rt-${id}` }],
    }),
    createRoomType: builder.mutation({
      query: (data) => ({ url: '/room-types/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Room', id: 'ROOM_TYPE_LIST' }],
    }),
    updateRoomType: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/room-types/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Room', id: `rt-${id}` },
        { type: 'Room', id: 'ROOM_TYPE_LIST' },
      ],
    }),
    deleteRoomType: builder.mutation({
      query: (id) => ({ url: `/room-types/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Room', id: 'ROOM_TYPE_LIST' }],
    }),
    patchRoomTypeAvailability: builder.mutation({
      query: ({ id, ...data }) => ({
        url: `/room-types/${id}/availability/`,
        method: 'PATCH',
        data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Room', id: `rt-${id}` },
        { type: 'Room', id: 'AVAIL_CALENDAR' },
      ],
    }),
    getRatePlans: builder.query({
      query: (params = {}) => ({ url: '/rate-plans/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [
              ...(result.results || result).map(({ id }) => ({ type: 'Room', id: `rp-${id}` })),
              { type: 'Room', id: 'RATE_PLAN_LIST' },
            ]
          : [{ type: 'Room', id: 'RATE_PLAN_LIST' }],
    }),
    getRatePlan: builder.query({
      query: (id) => ({ url: `/rate-plans/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Room', id: `rp-${id}` }],
    }),
    createRatePlan: builder.mutation({
      query: (data) => ({ url: '/rate-plans/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Room', id: 'RATE_PLAN_LIST' }],
    }),
    updateRatePlan: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/rate-plans/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Room', id: `rp-${id}` },
        { type: 'Room', id: 'RATE_PLAN_LIST' },
      ],
    }),
    deleteRatePlan: builder.mutation({
      query: (id) => ({ url: `/rate-plans/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Room', id: 'RATE_PLAN_LIST' }],
    }),
    quoteAvailability: builder.mutation({
      query: (data) => ({ url: '/availability/quote/', method: 'POST', data }),
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetRoomTypesQuery,
  useGetRoomTypeQuery,
  useCreateRoomTypeMutation,
  useUpdateRoomTypeMutation,
  useDeleteRoomTypeMutation,
  usePatchRoomTypeAvailabilityMutation,
  useGetRatePlansQuery,
  useGetRatePlanQuery,
  useCreateRatePlanMutation,
  useUpdateRatePlanMutation,
  useDeleteRatePlanMutation,
  useQuoteAvailabilityMutation,
} = catalogApi
