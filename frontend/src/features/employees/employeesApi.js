import { api } from '../../services/api'

export const employeesApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getEmployees: builder.query({
      query: (params = {}) => ({ url: '/employees/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'User', id: `emp-${id}` })), { type: 'User', id: 'EMP_LIST' }]
          : [{ type: 'User', id: 'EMP_LIST' }],
    }),
    getEmployee: builder.query({
      query: (id) => ({ url: `/employees/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'User', id: `emp-${id}` }],
    }),
    createEmployee: builder.mutation({
      query: (data) => ({ url: '/employees/', method: 'POST', data }),
      invalidatesTags: [{ type: 'User', id: 'EMP_LIST' }],
    }),
    updateEmployee: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/employees/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'User', id: `emp-${id}` }, { type: 'User', id: 'EMP_LIST' }],
    }),
    deleteEmployee: builder.mutation({
      query: (id) => ({ url: `/employees/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: 'User', id: 'EMP_LIST' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetEmployeesQuery,
  useGetEmployeeQuery,
  useCreateEmployeeMutation,
  useUpdateEmployeeMutation,
  useDeleteEmployeeMutation,
} = employeesApi
