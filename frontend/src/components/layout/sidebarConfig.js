/**
 * Ops sidebar navigation.
 * Items may include `group` for section headings: Front desk | Revenue | Property | System
 */
export const SIDEBAR_ITEMS = {
  admin: [
    { label: 'Dashboard', path: '/admin/dashboard', icon: 'Dashboard', group: 'Front desk' },
    { label: 'Bookings', path: '/admin/bookings', icon: 'EventNote', group: 'Front desk' },
    { label: 'Guests', path: '/admin/guests', icon: 'PersonOutline', group: 'Front desk' },
    { label: 'Rooms', path: '/admin/rooms', icon: 'MeetingRoom', group: 'Front desk' },
    { label: 'Tape Chart', path: '/receptionist/tape-chart', icon: 'ViewTimeline', group: 'Front desk' },
    { label: 'Housekeeping', path: '/receptionist/housekeeping', icon: 'CleaningServices', group: 'Front desk' },
    { label: 'Tasks', path: '/admin/tasks', icon: 'Assignment', group: 'Front desk' },
    { label: 'Room Services', path: '/admin/room-services', icon: 'RoomService', group: 'Front desk' },
    { label: 'Events', path: '/admin/events', icon: 'Event', group: 'Front desk' },
    { label: 'Announcements', path: '/admin/announcements', icon: 'Campaign', group: 'Front desk' },

    { label: 'Payments', path: '/admin/payments', icon: 'Payment', group: 'Revenue' },
    { label: 'Invoices', path: '/admin/invoices', icon: 'Receipt', group: 'Revenue' },
    { label: 'Refunds', path: '/admin/refunds', icon: 'MoneyOff', group: 'Revenue' },
    { label: 'Dynamic Pricing', path: '/admin/pricing', icon: 'TrendingUp', group: 'Revenue' },
    { label: 'Contracts', path: '/admin/contracts', icon: 'Description', group: 'Revenue' },
    { label: 'Analytics', path: '/analytics', icon: 'BarChart', group: 'Revenue' },

    { label: 'Properties', path: '/admin/properties', icon: 'Business', group: 'Property' },
    { label: 'Travel Agencies', path: '/admin/travel-agencies', icon: 'DirectionsBus', group: 'Property' },
    { label: 'Room Types', path: '/admin/room-types', icon: 'Category', group: 'Property' },
    { label: 'Rate Plans', path: '/admin/rate-plans', icon: 'LocalOffer', group: 'Property' },
    { label: 'Availability', path: '/admin/availability-calendar', icon: 'CalendarMonth', group: 'Property' },
    { label: 'Inventory', path: '/admin/inventory', icon: 'GridView', group: 'Property' },
    { label: 'OTA Channels', path: '/admin/channels', icon: 'CloudSync', group: 'Property' },
    { label: 'Storage', path: '/admin/storage', icon: 'Inventory', group: 'Property' },
    { label: 'Employees', path: '/admin/employees', icon: 'BadgeOutlined', group: 'Property' },

    { label: 'Users', path: '/admin/users', icon: 'People', group: 'System' },
    { label: 'Notifications', path: '/admin/notifications', icon: 'Notifications', group: 'System' },
  ],

  manager: [
    { label: 'Dashboard', path: '/manager/dashboard', icon: 'Dashboard', group: 'Front desk' },
    { label: 'Bookings', path: '/manager/bookings', icon: 'EventNote', group: 'Front desk' },
    { label: 'Rooms', path: '/manager/rooms', icon: 'MeetingRoom', group: 'Front desk' },
    { label: 'Tasks', path: '/manager/tasks', icon: 'Assignment', group: 'Front desk' },
    { label: 'Events', path: '/manager/events', icon: 'Event', group: 'Front desk' },
    { label: 'Announcements', path: '/manager/announcements', icon: 'Campaign', group: 'Front desk' },
    { label: 'Payments', path: '/manager/payments', icon: 'Payment', group: 'Revenue' },
    { label: 'Contracts', path: '/manager/contracts', icon: 'Description', group: 'Revenue' },
    { label: 'Analytics', path: '/manager/analytics', icon: 'BarChart', group: 'Revenue' },
  ],

  receptionist: [
    { label: 'Dashboard', path: '/receptionist/dashboard', icon: 'Dashboard', group: 'Front desk' },
    { label: 'Bookings', path: '/receptionist/bookings', icon: 'EventNote', group: 'Front desk' },
    { label: 'Check-In / Out', path: '/receptionist/check-in', icon: 'HotelOutlined', group: 'Front desk' },
    { label: 'Tape Chart', path: '/receptionist/tape-chart', icon: 'ViewTimeline', group: 'Front desk' },
    { label: 'Housekeeping', path: '/receptionist/housekeeping', icon: 'CleaningServices', group: 'Front desk' },
    { label: 'Rooms', path: '/receptionist/rooms', icon: 'MeetingRoom', group: 'Front desk' },
    { label: 'Guests', path: '/receptionist/guests', icon: 'People', group: 'Front desk' },
    { label: 'Payments', path: '/receptionist/payments', icon: 'Payment', group: 'Revenue' },
  ],

  staff: [
    { label: 'Dashboard', path: '/staff/dashboard', icon: 'Dashboard', group: 'Front desk' },
    { label: 'Tasks', path: '/staff/tasks', icon: 'Assignment', group: 'Front desk' },
  ],

  // Guests use GuestLayout; keep config for fallback
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
