import { api } from '../../services/api'

export const guestsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getGuests: builder.query({
      query: (params = {}) => ({
        url: '/guests/',
        method: 'GET',
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...((result.results || result).map
                ? (result.results || result).map(({ id }) => ({
                    type: 'Guest',
                    id,
                  }))
                : []),
              { type: 'Guest', id: 'LIST' },
            ]
          : [{ type: 'Guest', id: 'LIST' }],
    }),
    getGuest: builder.query({
      query: (id) => ({
        url: `/guests/${id}/`,
        method: 'GET',
      }),
      providesTags: (result, error, id) => [{ type: 'Guest', id }],
    }),
    createGuest: builder.mutation({
      query: (data) => ({
        url: '/guests/',
        method: 'POST',
        data,
      }),
      invalidatesTags: [{ type: 'Guest', id: 'LIST' }],
    }),
    updateGuest: builder.mutation({
      query: ({ id, ...data }) => ({
        url: `/guests/${id}/`,
        method: 'PATCH',
        data,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Guest', id }],
    }),
    deleteGuest: builder.mutation({
      query: (id) => ({ url: `/guests/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Guest', id: 'LIST' }],
    }),
  }),
  overrideExisting: true,
})

export const {
  useGetGuestsQuery,
  useGetGuestQuery,
  useCreateGuestMutation,
  useUpdateGuestMutation,
  useDeleteGuestMutation,
} = guestsApi
