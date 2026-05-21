import { api } from '../../services/api'

export const usersApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getUsers: builder.query({
      query: (params = {}) => ({ url: '/users/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'User', id })), { type: 'User', id: 'LIST' }]
          : [{ type: 'User', id: 'LIST' }],
    }),
    getUser: builder.query({
      query: (id) => ({ url: `/users/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'User', id }],
    }),
    updateUser: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/users/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'User', id }, { type: 'User', id: 'LIST' }],
    }),
    deleteUser: builder.mutation({
      query: (id) => ({ url: `/users/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'User', id: 'LIST' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetUsersQuery,
  useGetUserQuery,
  useUpdateUserMutation,
  useDeleteUserMutation,
} = usersApi
