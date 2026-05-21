import { api } from '../../services/api'

export const bookingsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getBookings: builder.query({
      query: (params = {}) => ({
        url: '/bookings/',
        method: 'GET',
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...((result.results || result).map
                ? (result.results || result).map(({ id }) => ({
                    type: 'Booking',
                    id,
                  }))
                : []),
              { type: 'Booking', id: 'LIST' },
            ]
          : [{ type: 'Booking', id: 'LIST' }],
    }),
    getBooking: builder.query({
      query: (id) => ({
        url: `/bookings/${id}/`,
        method: 'GET',
      }),
      providesTags: (result, error, id) => [{ type: 'Booking', id }],
    }),
    createBooking: builder.mutation({
      query: (data) => ({
        url: '/bookings/',
        method: 'POST',
        data,
      }),
      invalidatesTags: [{ type: 'Booking', id: 'LIST' }],
    }),
    updateBooking: builder.mutation({
      query: ({ id, ...data }) => ({
        url: `/bookings/${id}/`,
        method: 'PATCH',
        data,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Booking', id }],
    }),
    cancelBooking: builder.mutation({
      query: (id) => ({
        url: `/bookings/${id}/cancel/`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Booking', id },
        { type: 'Booking', id: 'LIST' },
      ],
    }),
    checkIn: builder.mutation({
      query: (id) => ({
        url: `/bookings/${id}/check_in/`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Booking', id },
        { type: 'Booking', id: 'LIST' },
        { type: 'Dashboard' },
      ],
    }),
    checkOut: builder.mutation({
      query: (id) => ({
        url: `/bookings/${id}/check_out/`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Booking', id },
        { type: 'Booking', id: 'LIST' },
        { type: 'Dashboard' },
      ],
    }),
    getRoomRecommendations: builder.query({
      query: ({ guestId, ...params }) => ({
        url: `/bookings/recommendations/${guestId}/`,
        method: 'GET',
        params,
      }),
      providesTags: () => [{ type: 'Booking', id: 'RECOMMENDATIONS' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetBookingsQuery,
  useGetBookingQuery,
  useCreateBookingMutation,
  useUpdateBookingMutation,
  useCancelBookingMutation,
  useCheckInMutation,
  useCheckOutMutation,
  useGetRoomRecommendationsQuery,
} = bookingsApi
