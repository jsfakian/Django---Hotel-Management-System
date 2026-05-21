import { createApi } from '@reduxjs/toolkit/query/react'
import axiosBaseQuery from './axiosBaseQuery'

export const api = createApi({
  reducerPath: 'api',
  baseQuery: axiosBaseQuery(),
  tagTypes: [
    'Booking',
    'Room',
    'Guest',
    'Payment',
    'Invoice',
    'User',
    'Property',
    'Dashboard',
  ],
  endpoints: () => ({}),
})
