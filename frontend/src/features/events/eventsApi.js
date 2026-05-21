import { api } from '../../services/api'

export const eventsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getEvents: builder.query({
      query: (params = {}) => ({ url: '/events/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'Booking', id: `event-${id}` })), { type: 'Booking', id: 'EVENT_LIST' }]
          : [{ type: 'Booking', id: 'EVENT_LIST' }],
    }),
    getEvent: builder.query({
      query: (id) => ({ url: `/events/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Booking', id: `event-${id}` }],
    }),
    createEvent: builder.mutation({
      query: (data) => ({ url: '/events/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Booking', id: 'EVENT_LIST' }],
    }),
    updateEvent: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/events/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Booking', id: `event-${id}` }, { type: 'Booking', id: 'EVENT_LIST' }],
    }),
    deleteEvent: builder.mutation({
      query: (id) => ({ url: `/events/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Booking', id: 'EVENT_LIST' }],
    }),
    attendEvent: builder.mutation({
      query: (id) => ({ url: `/events/${id}/attend/`, method: 'POST' }),
      invalidatesTags: (result, error, id) => [{ type: 'Booking', id: `event-${id}` }],
    }),
    cancelAttendance: builder.mutation({
      query: (id) => ({ url: `/events/${id}/cancel_attendance/`, method: 'POST' }),
      invalidatesTags: (result, error, id) => [{ type: 'Booking', id: `event-${id}` }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetEventsQuery,
  useGetEventQuery,
  useCreateEventMutation,
  useUpdateEventMutation,
  useDeleteEventMutation,
  useAttendEventMutation,
  useCancelAttendanceMutation,
} = eventsApi
