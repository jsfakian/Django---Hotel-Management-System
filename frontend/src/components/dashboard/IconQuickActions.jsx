import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, IconButton, Tooltip, Typography } from '@mui/material'

/**
 * Cloudbeds/Mews-style icon toolbar — label via tooltip + caption under icon.
 * @param {{ actions: Array<{ label: string, icon: React.ElementType, path: string, color?: string }> }} props
 */
export default function IconQuickActions({ actions = [], title = 'Quick actions' }) {
  const navigate = useNavigate()

  if (!actions.length) return null

  return (
    <Box>
      {title ? (
        <Typography
          variant="overline"
          color="text.secondary"
          sx={{ letterSpacing: 0.8, display: 'block', mb: 1 }}
        >
          {title}
        </Typography>
      ) : null}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
        {actions.map(({ label, icon: Icon, path, color = 'primary' }) => (
          <Tooltip key={label} title={label} arrow>
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                width: 72,
              }}
            >
              <IconButton
                aria-label={label}
                onClick={() => navigate(path)}
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: 2,
                  border: '1px solid',
                  borderColor: 'divider',
                  bgcolor: 'background.paper',
                  color: `${color}.main`,
                  '&:hover': {
                    bgcolor: `${color}.main`,
                    color: 'common.white',
                    borderColor: `${color}.main`,
                  },
                }}
              >
                <Icon />
              </IconButton>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  mt: 0.5,
                  textAlign: 'center',
                  lineHeight: 1.2,
                  maxWidth: 72,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {label}
              </Typography>
            </Box>
          </Tooltip>
        ))}
      </Box>
    </Box>
  )
}
