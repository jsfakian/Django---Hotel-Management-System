import { api } from '../../services/api'
import { createCrudEndpoints } from '../../services/createCrudApi'

export const guestsApi = api.injectEndpoints({
  endpoints: (builder) =>
    createCrudEndpoints({
      resourcePath: '/guests',
      tagType: 'Guest',
      names: {
        list: 'getGuests',
        detail: 'getGuest',
        create: 'createGuest',
        update: 'updateGuest',
        remove: 'deleteGuest',
      },
    })(builder),
  overrideExisting: true,
})

export const {
  useGetGuestsQuery,
  useGetGuestQuery,
  useCreateGuestMutation,
  useUpdateGuestMutation,
  useDeleteGuestMutation,
} = guestsApi
