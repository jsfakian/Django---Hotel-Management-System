import { api } from '../../services/api'

export const authApi = api.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation({
      query: (credentials) => ({
        url: '/auth/login/',
        method: 'POST',
        data: credentials,
      }),
    }),
    refreshToken: builder.mutation({
      query: (data) => ({
        url: '/auth/refresh/',
        method: 'POST',
        data,
      }),
    }),
    forgotPassword: builder.mutation({
      query: (data) => ({
        url: '/auth/forgot-password/',
        method: 'POST',
        data,
      }),
    }),
    logout: builder.mutation({
      query: (data) => ({
        url: '/auth/logout/',
        method: 'POST',
        data,
      }),
    }),
  }),
  overrideExisting: false,
})

export const {
  useLoginMutation,
  useRefreshTokenMutation,
  useForgotPasswordMutation,
  useLogoutMutation,
} = authApi
