import { createSlice } from '@reduxjs/toolkit'
import { jwtDecode } from 'jwt-decode'

const decodeToken = (token) => {
  try {
    return jwtDecode(token)
  } catch {
    return null
  }
}

const loadInitialState = () => {
  const accessToken = localStorage.getItem('access_token')
  const refreshToken = localStorage.getItem('refresh_token')

  if (accessToken) {
    const decoded = decodeToken(accessToken)
    if (decoded) {
      // Check if token is expired
      const now = Date.now() / 1000
      if (decoded.exp && decoded.exp < now) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        return {
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }
      }
      return {
        user: {
          id: decoded.user_id,
          username: decoded.username,
          email: decoded.email,
          role: decoded.role,
        },
        accessToken,
        refreshToken,
        isAuthenticated: true,
      }
    }
  }

  return {
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
  }
}

const authSlice = createSlice({
  name: 'auth',
  initialState: loadInitialState(),
  reducers: {
    setCredentials: (state, action) => {
      const { access, refresh } = action.payload
      const decoded = decodeToken(access)

      state.accessToken = access
      state.refreshToken = refresh
      state.isAuthenticated = true
      state.user = decoded
        ? {
            id: decoded.user_id,
            username: decoded.username,
            email: decoded.email,
            role: decoded.role,
          }
        : null

      localStorage.setItem('access_token', access)
      if (refresh) {
        localStorage.setItem('refresh_token', refresh)
      }
    },
    clearCredentials: (state) => {
      state.user = null
      state.accessToken = null
      state.refreshToken = null
      state.isAuthenticated = false

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },
  },
})

export const { setCredentials, clearCredentials } = authSlice.actions

export const selectCurrentUser = (state) => state.auth.user
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated
export const selectUserRole = (state) => state.auth.user?.role

export default authSlice.reducer
