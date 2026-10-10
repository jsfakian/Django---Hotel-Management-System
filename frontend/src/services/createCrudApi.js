/**
 * Factory for standard RTK Query CRUD endpoint sets.
 * Matches axiosBaseQuery ({ url, method, data, params }).
 */
export function createCrudEndpoints({ resourcePath, tagType, names }) {
  const path = resourcePath.replace(/\/$/, '')
  const {
    list = 'getList',
    detail = 'getDetail',
    create = 'create',
    update = 'update',
    remove = 'remove',
  } = names || {}

  return (build) => ({
    [list]: build.query({
      query: (params = {}) => ({ url: `${path}/`, method: 'GET', params }),
      providesTags: (result) => {
        const rows = result?.results || result || []
        return Array.isArray(rows)
          ? [...rows.map(({ id }) => ({ type: tagType, id })), { type: tagType, id: 'LIST' }]
          : [{ type: tagType, id: 'LIST' }]
      },
    }),
    [detail]: build.query({
      query: (id) => ({ url: `${path}/${id}/`, method: 'GET' }),
      providesTags: (_r, _e, id) => [{ type: tagType, id }],
    }),
    [create]: build.mutation({
      query: (data) => ({ url: `${path}/`, method: 'POST', data }),
      invalidatesTags: [{ type: tagType, id: 'LIST' }],
    }),
    [update]: build.mutation({
      query: ({ id, ...data }) => ({
        url: `${path}/${id}/`,
        method: 'PATCH',
        data,
      }),
      invalidatesTags: (_r, _e, { id }) => [
        { type: tagType, id },
        { type: tagType, id: 'LIST' },
      ],
    }),
    [remove]: build.mutation({
      query: (id) => ({ url: `${path}/${id}/`, method: 'DELETE' }),
      invalidatesTags: [{ type: tagType, id: 'LIST' }],
    }),
  })
}
