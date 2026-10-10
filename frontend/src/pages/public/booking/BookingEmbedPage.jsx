import React, { useEffect } from 'react'
import { Box } from '@mui/material'
import BookingSearchPage from './BookingSearchPage'

/**
 * Embeddable booking engine surface for iframe / partner sites.
 *
 * Preferred partner snippet (see /nephele-book-embed.js):
 *   <div id="nephele-book" data-property-id="1"></div>
 *   <script src="https://HOST/nephele-book-embed.js" async></script>
 *
 * Raw iframe fallback:
 *   <iframe src="https://HOST/book/embed?property_id=1" width="100%" height="720" style="border:0"></iframe>
 */
export default function BookingEmbedPage() {
  useEffect(() => {
    const postHeight = () => {
      if (window.parent === window) return
      const height = Math.ceil(document.documentElement.scrollHeight)
      window.parent.postMessage({ source: 'nephele-book', type: 'resize', height }, '*')
    }
    postHeight()
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(postHeight) : null
    if (ro) ro.observe(document.body)
    window.addEventListener('load', postHeight)
    return () => {
      if (ro) ro.disconnect()
      window.removeEventListener('load', postHeight)
    }
  }, [])

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
