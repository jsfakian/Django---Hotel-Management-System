/**
 * Ops sidebar — simplified IA (Phases 1–4).
 * Primary nav stays short; setup lives under Settings hubs.
 *
 * Groups: Operations | Revenue | Distribution | Account
 */

/** Nested links shown on /admin/settings (and role variants). */
export const SETTINGS_SECTIONS = {
  admin: [
    {
      name: 'Property',
      description: 'Hotels, agencies, and staff',
      items: [
        { label: 'Properties', path: '/admin/properties', icon: 'Business' },
        { label: 'Travel agencies', path: '/admin/travel-agencies', icon: 'DirectionsBus' },
        { label: 'Employees', path: '/admin/employees', icon: 'BadgeOutlined' },
        { label: 'Rooms', path: '/admin/rooms', icon: 'MeetingRoom' },
      ],
    },
    {
      name: 'Billing & pricing',
      description: 'Contracts and dynamic pricing',
      items: [
        { label: 'Contracts', path: '/admin/contracts', icon: 'Description' },
        { label: 'Dynamic pricing', path: '/admin/pricing', icon: 'TrendingUp' },
      ],
    },
    {
      name: 'Operations',
      description: 'Tasks, services, and hotel ops',
      items: [
        { label: 'Tasks', path: '/admin/tasks', icon: 'Assignment' },
        { label: 'Room services', path: '/admin/room-services', icon: 'RoomService' },
        { label: 'Events', path: '/admin/events', icon: 'Event' },
        { label: 'Announcements', path: '/admin/announcements', icon: 'Campaign' },
        { label: 'Storage', path: '/admin/storage', icon: 'Inventory' },
      ],
    },
    {
      name: 'System',
      description: 'Access and notifications',
      items: [
        { label: 'Users', path: '/admin/users', icon: 'People' },
        { label: 'Notifications', path: '/admin/notifications', icon: 'Notifications' },
      ],
    },
  ],
  manager: [
    {
      name: 'Operations',
      description: 'Day-to-day property tools',
      items: [
        { label: 'Tasks', path: '/manager/tasks', icon: 'Assignment' },
        { label: 'Events', path: '/manager/events', icon: 'Event' },
        { label: 'Announcements', path: '/manager/announcements', icon: 'Campaign' },
        { label: 'Contracts', path: '/manager/contracts', icon: 'Description' },
      ],
    },
  ],
}

export const SIDEBAR_ITEMS = {
  admin: [
    { label: 'Dashboard', path: '/admin/dashboard', icon: 'Dashboard', group: 'Operations' },
    { label: 'Calendar', path: '/receptionist/tape-chart', icon: 'ViewTimeline', group: 'Operations' },
    { label: 'Reservations', path: '/admin/bookings', icon: 'EventNote', group: 'Operations' },
    { label: 'Guests', path: '/admin/guests', icon: 'PersonOutline', group: 'Operations' },
    { label: 'Housekeeping', path: '/receptionist/housekeeping', icon: 'CleaningServices', group: 'Operations' },

    { label: 'Rates & availability', path: '/admin/rates', icon: 'LocalOffer', group: 'Revenue' },
    { label: 'Payments', path: '/admin/payments', icon: 'Payment', group: 'Revenue' },
    { label: 'Reports', path: '/analytics', icon: 'BarChart', group: 'Revenue' },

    { label: 'Channels', path: '/admin/channels', icon: 'CloudSync', group: 'Distribution' },

    { label: 'Settings', path: '/admin/settings', icon: 'Settings', group: 'Account' },
  ],

  manager: [
    { label: 'Dashboard', path: '/manager/dashboard', icon: 'Dashboard', group: 'Operations' },
    { label: 'Calendar', path: '/receptionist/tape-chart', icon: 'ViewTimeline', group: 'Operations' },
    { label: 'Reservations', path: '/manager/bookings', icon: 'EventNote', group: 'Operations' },
    { label: 'Rooms', path: '/manager/rooms', icon: 'MeetingRoom', group: 'Operations' },
    { label: 'Payments', path: '/admin/payments', icon: 'Payment', group: 'Revenue' },
    { label: 'Reports', path: '/manager/analytics', icon: 'BarChart', group: 'Revenue' },
    { label: 'Settings', path: '/manager/settings', icon: 'Settings', group: 'Account' },
  ],

  receptionist: [
    { label: 'Dashboard', path: '/receptionist/dashboard', icon: 'Dashboard', group: 'Operations' },
    { label: 'Calendar', path: '/receptionist/tape-chart', icon: 'ViewTimeline', group: 'Operations' },
    { label: 'Reservations', path: '/receptionist/bookings', icon: 'EventNote', group: 'Operations' },
    { label: 'Check-in / out', path: '/receptionist/check-in', icon: 'HotelOutlined', group: 'Operations' },
    { label: 'Guests', path: '/receptionist/guests', icon: 'People', group: 'Operations' },
    { label: 'Housekeeping', path: '/receptionist/housekeeping', icon: 'CleaningServices', group: 'Operations' },
  ],

  staff: [
    { label: 'Dashboard', path: '/staff/dashboard', icon: 'Dashboard', group: 'Operations' },
    { label: 'Tasks', path: '/staff/tasks', icon: 'Assignment', group: 'Operations' },
  ],

  guest: [
    { label: 'Dashboard', path: '/guest/dashboard', icon: 'Dashboard' },
    { label: 'My Bookings', path: '/guest/bookings', icon: 'EventNote' },
    { label: 'Invoices', path: '/guest/invoices', icon: 'Receipt' },
    { label: 'Refunds', path: '/guest/refunds', icon: 'MoneyOff' },
    { label: 'Events', path: '/guest/events', icon: 'Event' },
    { label: 'Room Services', path: '/guest/room-services', icon: 'RoomService' },
    { label: 'Notifications', path: '/guest/notifications', icon: 'Notifications' },
    { label: 'Profile', path: '/guest/profile', icon: 'AccountCircle' },
    { label: 'Privacy & Data', path: '/guest/privacy', icon: 'Shield' },
  ],
}

export function groupSidebarItems(items) {
  const groups = []
  const map = new Map()
  for (const item of items) {
    const key = item.group || 'Menu'
    if (!map.has(key)) {
      const g = { name: key, items: [] }
      map.set(key, g)
      groups.push(g)
    }
    map.get(key).items.push(item)
  }
  return groups
}
