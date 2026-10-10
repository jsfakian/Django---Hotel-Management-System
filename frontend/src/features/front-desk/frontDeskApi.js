import { api } from '../../services/api'

export const frontDeskApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getTapeChart: builder.query({
      query: (params = {}) => ({
        url: '/front-desk/tape-chart/',
        method: 'GET',
        params,
      }),
      providesTags: [{ type: 'Booking', id: 'TAPE_CHART' }],
    }),
    getHousekeeping: builder.query({
      query: (params = {}) => ({
        url: '/front-desk/housekeeping/',
        method: 'GET',
        params,
      }),
      providesTags: [{ type: 'Room', id: 'HOUSEKEEPING' }],
    }),
    updateHousekeeping: builder.mutation({
      query: (data) => ({
        url: '/front-desk/housekeeping/',
        method: 'PATCH',
        data,
      }),
      invalidatesTags: [{ type: 'Room', id: 'HOUSEKEEPING' }, { type: 'Room', id: 'LIST' }],
    }),
    assignRoom: builder.mutation({
      query: ({ bookingId, room_id }) => ({
        url: `/bookings/${bookingId}/assign-room/`,
        method: 'POST',
        data: { room_id },
      }),
      invalidatesTags: [
        { type: 'Booking', id: 'TAPE_CHART' },
        { type: 'Booking', id: 'LIST' },
        { type: 'Room', id: 'HOUSEKEEPING' },
      ],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetTapeChartQuery,
  useGetHousekeepingQuery,
  useUpdateHousekeepingMutation,
  useAssignRoomMutation,
} = frontDeskApi
