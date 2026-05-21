import { api } from '../../services/api'

export const roomServicesApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getRoomServices: builder.query({
      query: (params = {}) => ({ url: '/room-services/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'Booking', id: `rs-${id}` })), { type: 'Booking', id: 'RS_LIST' }]
          : [{ type: 'Booking', id: 'RS_LIST' }],
    }),
    getRoomService: builder.query({
      query: (id) => ({ url: `/room-services/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Booking', id: `rs-${id}` }],
    }),
    getCurrentRoomServices: builder.query({
      query: (params = {}) => ({
        url: '/room-services/',
        method: 'GET',
        params: { current: true, ...params },
      }),
      providesTags: () => [{ type: 'Booking', id: 'RS_CURRENT' }],
    }),
    getActiveRoomServices: builder.query({
      query: (params = {}) => ({
        url: '/room-services/',
        method: 'GET',
        params: { status: 'in_progress', ...params },
      }),
      providesTags: () => [{ type: 'Booking', id: 'RS_ACTIVE' }],
    }),
    createRoomService: builder.mutation({
      query: (data) => ({ url: '/room-services/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Booking', id: 'RS_LIST' }],
    }),
    updateRoomService: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/room-services/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Booking', id: `rs-${id}` }, { type: 'Booking', id: 'RS_LIST' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetRoomServicesQuery,
  useGetRoomServiceQuery,
  useGetCurrentRoomServicesQuery,
  useGetActiveRoomServicesQuery,
  useCreateRoomServiceMutation,
  useUpdateRoomServiceMutation,
} = roomServicesApi
