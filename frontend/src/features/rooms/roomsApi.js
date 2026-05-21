import { api } from '../../services/api'

export const roomsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getRooms: builder.query({
      query: (params = {}) => ({ url: '/rooms/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'Room', id })), { type: 'Room', id: 'LIST' }]
          : [{ type: 'Room', id: 'LIST' }],
    }),
    getRoom: builder.query({
      query: (id) => ({ url: `/rooms/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Room', id }],
    }),
    createRoom: builder.mutation({
      query: (data) => ({ url: '/rooms/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Room', id: 'LIST' }],
    }),
    updateRoom: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/rooms/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Room', id }, { type: 'Room', id: 'LIST' }],
    }),
    deleteRoom: builder.mutation({
      query: (id) => ({ url: `/rooms/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Room', id: 'LIST' }],
    }),
  }),
  overrideExisting: true,
})

export const {
  useGetRoomsQuery,
  useGetRoomQuery,
  useCreateRoomMutation,
  useUpdateRoomMutation,
  useDeleteRoomMutation,
} = roomsApi
