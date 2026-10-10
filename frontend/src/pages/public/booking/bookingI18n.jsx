import React, { useCallback, useMemo, useState } from 'react'
import {
  BookingLangContext,
  LANG_KEY,
  STRINGS,
  readStoredLang,
} from './bookingLang'

export function BookingLangProvider({ children }) {
  const [lang, setLang] = useState(readStoredLang)

  const toggleLang = useCallback(() => {
    setLang((prev) => {
      const next = prev === 'el' ? 'en' : 'el'
      try {
        localStorage.setItem(LANG_KEY, next)
      } catch {
        /* ignore */
      }
      return next
    })
  }, [])

  const t = useCallback(
    (key) => STRINGS[lang]?.[key] || STRINGS.en[key] || key,
    [lang],
  )

  const value = useMemo(() => ({ lang, t, toggleLang }), [lang, t, toggleLang])
  return <BookingLangContext.Provider value={value}>{children}</BookingLangContext.Provider>
}
