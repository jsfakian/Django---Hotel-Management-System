import React, { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  TableSortLabel,
} from '@mui/material'
import LoadingSpinner from './LoadingSpinner'

export default function DataTable({
  columns = [],
  rows = [],
  loading = false,
  onRowClick,
  rowsPerPageOptions = [10, 25, 50],
  defaultRowsPerPage = 10,
}) {
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(defaultRowsPerPage)

  const handleChangePage = (event, newPage) => setPage(newPage)
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  if (loading) return <LoadingSpinner />

  const paginatedRows = rows.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)

  return (
    <Paper variant="outlined" sx={{ width: '100%', overflow: 'hidden' }}>
      <TableContainer>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell
                  key={col.field}
                  style={{ width: col.width, fontWeight: 600 }}
                  sx={{ backgroundColor: 'background.paper' }}
                >
                  {col.headerName}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedRows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                  No records found.
                </TableCell>
              </TableRow>
            ) : (
              paginatedRows.map((row, rowIndex) => (
                <TableRow
                  key={row.id ?? rowIndex}
                  hover={!!onRowClick}
                  onClick={() => onRowClick && onRowClick(row)}
                  sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
                >
                  {columns.map((col) => (
                    <TableCell key={col.field}>
                      {col.renderCell
                        ? col.renderCell({ row, value: row[col.field] })
                        : row[col.field] ?? '—'}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={rowsPerPageOptions}
        component="div"
        count={rows.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Paper>
  )
}
