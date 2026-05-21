import { api } from '../../services/api'

export const announcementsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getAnnouncements: builder.query({
      query: (params = {}) => ({ url: '/announcements/', method: 'GET', params }),
      providesTags: () => [{ type: 'Property', id: 'ANNOUNCEMENT_LIST' }],
    }),
    createAnnouncement: builder.mutation({
      query: (data) => ({ url: '/announcements/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Property', id: 'ANNOUNCEMENT_LIST' }],
    }),
    deleteAnnouncement: builder.mutation({
      query: (id) => ({ url: `/announcements/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Property', id: 'ANNOUNCEMENT_LIST' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetAnnouncementsQuery,
  useCreateAnnouncementMutation,
  useDeleteAnnouncementMutation,
} = announcementsApi
