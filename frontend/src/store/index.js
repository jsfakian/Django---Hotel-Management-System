import { configureStore } from '@reduxjs/toolkit'
import { api } from '../services/api'
import authReducer from '../features/auth/authSlice'
// Ensure injectEndpoints side-effects run at store boot
import '../features/channels/channelsApi'
import '../features/catalog/catalogApi'
import '../features/front-desk/frontDeskApi'
import '../features/public/publicBookingApi'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    [api.reducerPath]: api.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware),
})
