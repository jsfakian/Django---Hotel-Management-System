import { api } from '../../services/api'

export const notificationsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getNotifications: builder.query({
      query: (params = {}) => ({ url: '/notifications/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'User', id: `notif-${id}` })), { type: 'User', id: 'NOTIF_LIST' }]
          : [{ type: 'User', id: 'NOTIF_LIST' }],
    }),
    markRead: builder.mutation({
      query: (id) => ({ url: `/notifications/${id}/`, method: 'PATCH', data: { is_read: true } }),
      invalidatesTags: (result, error, id) => [{ type: 'User', id: `notif-${id}` }, { type: 'User', id: 'NOTIF_LIST' }],
    }),
    markAllRead: builder.mutation({
      query: () => ({ url: '/notifications/mark_all_read/', method: 'POST' }),
      invalidatesTags: [{ type: 'User', id: 'NOTIF_LIST' }],
    }),
    getNotificationPreferences: builder.query({
      query: () => ({ url: '/notifications/preferences/', method: 'GET' }),
      providesTags: () => [{ type: 'User', id: 'NOTIF_PREFS' }],
    }),
    updateNotificationPreferences: builder.mutation({
      query: (data) => ({ url: '/notifications/preferences/', method: 'PATCH', data }),
      invalidatesTags: [{ type: 'User', id: 'NOTIF_PREFS' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetNotificationsQuery,
  useMarkReadMutation,
  useMarkAllReadMutation,
  useGetNotificationPreferencesQuery,
  useUpdateNotificationPreferencesMutation,
} = notificationsApi
