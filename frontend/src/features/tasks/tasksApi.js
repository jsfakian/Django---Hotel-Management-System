import { api } from '../../services/api'

export const tasksApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getTasks: builder.query({
      query: (params = {}) => ({ url: '/tasks/', method: 'GET', params }),
      providesTags: (result) =>
        result
          ? [...(result.results || result).map(({ id }) => ({ type: 'User', id: `task-${id}` })), { type: 'User', id: 'TASK_LIST' }]
          : [{ type: 'User', id: 'TASK_LIST' }],
    }),
    getTask: builder.query({
      query: (id) => ({ url: `/tasks/${id}/`, method: 'GET' }),
      providesTags: (result, error, id) => [{ type: 'User', id: `task-${id}` }],
    }),
    createTask: builder.mutation({
      query: (data) => ({ url: '/tasks/', method: 'POST', data }),
      invalidatesTags: [{ type: 'User', id: 'TASK_LIST' }],
    }),
    updateTask: builder.mutation({
      query: ({ id, ...data }) => ({ url: `/tasks/${id}/`, method: 'PATCH', data }),
      invalidatesTags: (result, error, { id }) => [{ type: 'User', id: `task-${id}` }, { type: 'User', id: 'TASK_LIST' }],
    }),
    completeTask: builder.mutation({
      query: (id) => ({ url: `/tasks/${id}/`, method: 'PATCH', data: { status: 'completed' } }),
      invalidatesTags: (result, error, id) => [{ type: 'User', id: `task-${id}` }, { type: 'User', id: 'TASK_LIST' }],
    }),
  }),
  overrideExisting: false,
})

export const {
  useGetTasksQuery,
  useGetTaskQuery,
  useCreateTaskMutation,
  useUpdateTaskMutation,
  useCompleteTaskMutation,
} = tasksApi
