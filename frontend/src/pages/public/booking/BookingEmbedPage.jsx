import React from 'react'
import { Box } from '@mui/material'
import BookingSearchPage from './BookingSearchPage'

/**
 * Embeddable booking engine surface for iframe / partner sites.
 * Same APIs as /book; stripped chrome for widget hosting.
 *
 * Partner snippet:
 *   <iframe src="https://HOST/book/embed?property_id=1" width="100%" height="720" style="border:0"></iframe>
 */
export default function BookingEmbedPage() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: '#f7f4ef',
        p: { xs: 1.5, sm: 2 },
      }}
    >
      <BookingSearchPage embedded />
    </Box>
  )
}
