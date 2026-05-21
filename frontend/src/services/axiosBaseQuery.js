import axiosInstance from './axiosInstance'

const axiosBaseQuery =
  ({ baseUrl } = { baseUrl: '' }) =>
  async ({ url, method = 'GET', data, params, headers }) => {
    try {
      const result = await axiosInstance({
        url: baseUrl ? `${baseUrl}${url}` : url,
        method,
        data,
        params,
        headers,
      })
      return { data: result.data }
    } catch (axiosError) {
      const err = axiosError
      return {
        error: {
          status: err.response?.status,
          data: err.response?.data || err.message,
        },
      }
    }
  }

export default axiosBaseQuery
