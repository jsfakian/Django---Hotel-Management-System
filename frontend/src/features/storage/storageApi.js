import { api } from '../../services/api'

export const storageApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getStorageItems: builder.query({
      query: (params = {}) => ({ url: '/storage/', method: 'GET', params }),
      providesTags: () => [{ type: 'Property', id: 'STORAGE_LIST' }],
    }),
    createStorageItem: builder.mutation({
      query: (data) => ({ url: '/storage/', method: 'POST', data }),
      invalidatesTags: [{ type: 'Property', id: 'STORAGE_LIST' }],
    }),
    updateStorageItem: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/storage/${id}/`, method: 'PATCH', data }),
      invalidatesTags: [{ type: 'Property', id: 'STORAGE_LIST' }],
    }),
    deleteStorageItem: builder.mutation({
      query: (id) => ({ url: `/storage/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'Property', id: 'STORAGE_LIST' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetStorageItemsQuery,
  useCreateStorageItemMutation,
  useUpdateStorageItemMutation,
  useDeleteStorageItemMutation,
} = storageApi
