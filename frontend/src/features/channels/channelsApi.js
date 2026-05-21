import { api } from '../../services/api'

export const channelsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getChannels: builder.query({
      query: (params = {}) => ({ url: '/channels/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'Property', id: `channel-${id}` })), { type: 'Property', id: 'CHANNEL_LIST' }]
          : [{ type: 'Property', id: 'CHANNEL_LIST' }],
    }),
    getChannel: builder.query({
      query: (id) => ({ url: `/channels/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'Property', id: `channel-${id}` }],
    }),
    createChannel: builder.mutation({
      query: (data) => ({ url: '/channels/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Property', id: 'CHANNEL_LIST' }],
    }),
    updateChannel: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/channels/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Property', id: `channel-${id}` }, { type: 'Property', id: 'CHANNEL_LIST' }],
    }),
    deleteChannel: builder.mutation({
      query: (id) => ({ url: `/channels/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Property', id: 'CHANNEL_LIST' }],
    }),
    syncChannelAvailability: builder.mutation({
      query: (id) => ({ url: `/channels/${id}/sync_availability/`, method: 'POST' }),
      invalidatesTags: (result, error, id) => [{ type: 'Property', id: `channel-${id}` }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetChannelsQuery,
  useGetChannelQuery,
  useCreateChannelMutation,
  useUpdateChannelMutation,
  useDeleteChannelMutation,
  useSyncChannelAvailabilityMutation,
} = channelsApi
