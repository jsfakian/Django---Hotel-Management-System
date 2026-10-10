# Nephele Hotel Management System - Admin Manual

## Overview

Welcome to the **Nephele Admin Manual**. This guide is intended for system administrators responsible for managing the entire hotel management system, including user accounts, properties, employees, system configuration, and overall system health.

As an admin, you have the highest level of access and control over all system features and data.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Logging In](#logging-in)
3. [Admin Dashboard](#admin-dashboard)
4. [User Management](#user-management)
5. [Employee Management](#employee-management)
6. [Property Configuration](#property-configuration)
7. [System Settings](#system-settings)
8. [Reporting & Analytics](#reporting--analytics)
9. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Getting Started

### Prerequisites
- You have been assigned admin credentials by the system owner
- You have access to the Nephele system via a web browser
- Your account has "System Administrator" role enabled

### System Access
- **URL**: Access Nephele via your hotel's designated system URL
- **Browser Compatibility**: Chrome, Firefox, Safari, or Edge (latest versions recommended)
- **Internet Connection**: Stable internet connection required

---

## Logging In

### Initial Login Steps

1. Navigate to the Nephele login page
2. Enter your **username** (admin credentials provided by system owner)
3. Enter your **password**
4. Click the **"Sign In"** button

**Screenshot Reference**: See `sign_in_up.jpg` in the Screenshots folder

### First-Time Setup

After your first login, you will:
1. Be prompted to verify your email address
2. Receive a verification code via email
3. Enter the verification code in the system
4. Complete your admin profile setup
5. Configure your preferred system settings

### Forgotten Password/Access Issues

If you cannot log in:
1. Click **"Forgot Password?"** on the login page
2. Enter your registered email address
3. Check your email for a password reset link
4. Follow the link to create a new password
5. Log in with your new credentials

---

## Admin Dashboard

### Dashboard Overview

Upon logging in, you'll see the **Admin Dashboard** containing:

- **Quick Statistics**: Overview of key metrics (total guests, bookings, revenue, etc.)
- **Recent Activities**: Latest system actions and user activities
- **System Health Status**: Status of critical system components
- **Alerts & Notifications**: Important system messages requiring attention
- **Navigation Menu**: Quick access to all admin functions

### Key Dashboard Metrics

| Metric | Description |
|--------|-------------|
| **Total Users** | Count of all system users (admin, managers, staff, agents, guests) |
| **Active Bookings** | Number of current/ongoing reservations |
| **Monthly Revenue** | Aggregated booking payments for the current month |
| **Property Count** | Number of configured hotel properties |
| **Employee Count** | Total active and inactive employees |
| **System Status** | Operational status of all system modules |

---

## User Management

### Understanding User Roles

Nephele supports the following user roles:

1. **System Administrator (Admin)**
   - Full system access
   - System configuration and settings
   - User account management
   - Financial and reporting functions

2. **Hotel Manager (Property Manager)**
   - Manage one or more properties
   - View property-specific data
   - Configure property settings
   - Manage staff and operations for their properties

3. **Receptionist**
   - Guest check-in/check-out
   - Room assignments
   - Guest inquiries and requests
   - Basic booking modifications

4. **Travel Agent**
   - Create and manage bookings
   - Process reservations
   - Manage commission structures
   - Access to travel agency dashboard

5. **Guest**
   - View own bookings and reservations
   - Manage room service requests
   - View invoices and bills
   - Browse available events and announcements

6. **Employee (Staff)**
   - View assigned tasks and schedules
   - Submit availability and leave requests
   - Housekeeping and maintenance tasks
   - Time tracking

### Adding a New Employee Account

**Prerequisites**: You have employee information (name, email, position, department)

**Step-by-Step Guide**:

1. From the admin sidebar, select **"Employee Management"** → **"Add New Employee"**
2. Fill in the employee information:
   - **First Name**: Employee's first name
   - **Last Name**: Employee's last name
   - **Email**: Valid workplace email address
   - **Phone Number**: Contact number (optional but recommended)
   - **Position**: Job title (e.g., Manager, Housekeeper, Chef)
   - **Department**: Department name (e.g., Operations, Housekeeping, Restaurant)
   - **Hire Date**: Start date of employment
   - **Property Assignment**: Select which property they belong to
   - **Initial Salary**: Annual salary (leave as 0 if to be configured later)

3. Select the appropriate **Role**: (Receptionist, Travel Agent, Employee, etc.)
4. Set initial login credentials:
   - The system can auto-generate a temporary password
   - Employee will be prompted to change password on first login
   - Or you can manually set an initial password
5. Click **"Create Employee Account"**

**Screenshot Reference**: See `add_new_employee.jpg` for reference on the employee form

**Notification**: The new employee will receive an email with login instructions

### Managing Existing Users

#### View User List
1. Navigate to **"User Management"** → **"All Users"**
2. View table of all users with their:
   - Name and email
   - Role
   - Status (Active/Inactive)
   - Last login date
   - Account creation date

**Screenshot Reference**: See `employee_list.jpg`, `guest_list.jpg`

#### Edit User Details
1. Click on a user's name in the user list
2. Modify their information as needed:
   - Contact details
   - Role assignments
   - Account status
3. Click **"Save Changes"**

#### Disable/Deactivate User Account
1. Find the user in the user list
2. Click **"Edit"** or the user row
3. Change **Status** to **"Inactive"**
4. Optionally add a **"Deactivation Reason"**
5. Click **"Save Changes"**

**Note**: Deactivated users cannot log into the system but their historical data is preserved

#### Reset User Password
If a user forgets their password while you're working:
1. Go to **"User Management"**
2. Find the user and click **"Reset Password"**
3. A temporary password will be sent to their email
4. The user must change this password on next login

---

## Employee Management

### Employee Dashboard Overview

The **Employee Management** section allows you to:
- View all current and past employees
- Manage employment records
- Track employee status and assignments
- Monitor payroll and benefits
- Review employee performance data

### Viewing Employees
1. Navigate to **"Employee Management"** → **"All Employees"**
2. View the employee list with:
   - Name and contact info
   - Position and department
   - Assigned property
   - Employment status
   - Hire date and salary

3. **Filter options**:
   - By Status (Active, On Leave, Terminated)
   - By Department
   - By Property
   - By Hire Date

### Employee Status Management

Employee statuses include:

| Status | Description |
|--------|-------------|
| **Active** | Currently employed and working |
| **Inactive** | Employee account disabled (not terminated) |
| **On Leave** | Employee on approved leave/vacation |
| **Terminated** | Former employee (record kept for history) |

### Updating Employee Status

1. Go to **"Employee Management"** → **"All Employees"**
2. Click on the employee name
3. In the **Status** field, select new status
4. Optionally add **notes** explaining status change
5. Click **"Save Changes"**

### Managing Employee Assignments

#### Assign Employee to Property
1. Open employee record
2. Scroll to **"Property Assignment"** section
3. Select property from dropdown
4. Click **"Save"**

#### Assign Department
1. Open employee record
2. Scroll to **"Department"** section
3. Select or enter department
4. Click **"Save"**

---

## Property Configuration

### Property Management Overview

Properties are individual hotel locations managed within Nephele. Each property can have its own:
- Rooms and room types
- Pricing and rates
- Staff and employees
- Events and announcements
- Financial records

### Viewing Properties

1. Navigate to **"Property Management"** → **"All Properties"**
2. See list of all configured properties with:
   - Property name and location
   - Number of rooms
   - Active managers
   - Current status
   - Contact information

### Adding a New Property

**When you need this**: Setting up a new hotel location or branch

**Step-by-Step**:

1. Go to **"Property Management"** → **"Add New Property"**
2. Fill in property details:
   - **Property Name**: Official name of the hotel
   - **Address**: Full address
   - **City/Town**: City location
   - **Country**: Country location
   - **Postal Code**: Postal/ZIP code
   - **Phone Number**: Main property phone
   - **Email Address**: Property email for bookings/inquiries
   - **Website**: Property website (if applicable)

3. Configure basic property settings:
   - **Total Rooms**: How many rooms in this property
   - **Opening Date**: When property opened/being opened
   - **Currency**: Local currency for this property
   - **Time Zone**: Timezone for booking calculations

4. Add property manager:
   - Select or create a Hotel Manager account
   - This person will oversee all operations at this property
   - Can override most property-level settings

5. Upload property information (optional):
   - Property logo/image
   - Description
   - Amenities list

6. Click **"Create Property"**

### Managing Room Inventory

Each property requires room setup in Nephele:

1. Go to **"Property Management"** → select property → **"Rooms"**
2. View all rooms with:
   - Room number/ID
   - Room type
   - Capacity
   - Price
   - Current status (Available, Occupied, Maintenance)

3. **Add New Room**:
   - Click **"Add Room"**
   - Enter room number
   - Select room type (Single, Double, Suite, etc.)
   - Set room capacity
   - Set base price
   - Click **"Create Room"**

4. **Edit Room Details**:
   - Click room in list
   - Modify details (price, capacity, amenities)
   - Click **"Save"**

### Viewing Room List

**Screenshot Reference**: See `room_list.jpg` for room management interface

---

## System Settings

### Accessing System Settings

1. Navigate to **"Settings"** or **"System Configuration"** (typically in admin menu)
2. Available settings categories:
   - Email Configuration
   - Payment Processing
   - Booking Rules
   - System-wide Announcements
   - Backup and Recovery

### Email Configuration

Nephele can send automated emails for:
- Booking confirmations
- Payment verification codes
- Refund notifications
- Employee notifications
- Guest announcements

**Configuring Email Settings**:

1. Go to **"Settings"** → **"Email Configuration"**
2. Configure:
   - **SMTP Server**: Email provider's SMTP server
   - **SMTP Port**: Usually 587 (TLS) or 465 (SSL)
   - **From Email**: System's email address
   - **From Name**: Display name for emails
   - **Email Username**: SMTP login username
   - **Email Password**: SMTP login password (use app passwords for Gmail/Outlook)

3. Click **"Test Email Configuration"** to verify settings work
4. Click **"Save Settings"**

**Example**: For Gmail:
- SMTP Server: smtp.gmail.com
- Port: 587
- Use Gmail "App Password" (not your regular password)

### Payment Processing Settings

1. Go to **"Settings"** → **"Payment Configuration"**
2. View or configure:
   - **Active Payment Methods**: Which methods are enabled (Card, Cash, Bank Transfer)
   - **Currency**: Default payment currency
   - **Verification Requirements**: Which payment methods need verification

### Booking Configuration

1. Go to **"Settings"** → **"Booking Rules"**
2. Configure:
   - **Minimum Stay**: Minimum nights for a booking
   - **Maximum Stay**: Maximum nights per booking
   - **Advance Booking**: How many days ahead can guests book
   - **Cancellation Policy**: Terms for cancellations
   - **Check-in/Check-out Times**: Default times

### System Announcements

**Making Property-Wide Announcements**:

1. Go to **"Hotel"** → **"Announcements"**
2. Click **"Create New Announcement"**
3. Enter announcement content
4. Select which properties this applies to
5. Set visibility (all guests, members only, staff only)
6. Set duration (when it displays)
7. Click **"Publish"**

---

## Reporting & Analytics

### Accessing Reports & Analytics

1. Navigate to **"Reports"** or **"Analytics"** from admin menu
2. Available report categories:
   - Booking & Occupancy Reports
   - Financial & Revenue Reports
   - User & Guest Reports
   - Employee & Payroll Reports
   - System Activity Reports

### Booking Reports

View booking statistics:
1. Go to **"Reports"** → **"Booking Reports"**
2. Select report type:
   - **Bookings by Date**: Bookings created in a date range
   - **Occupancy Rate**: Occupancy percentage by property/date
   - **Booking Status**: Filter by status (Pending, Confirmed, Cancelled)

3. Select date range and properties
4. Click **"Generate Report"**
5. View summary statistics and detailed table
6. Export to CSV or PDF if needed

### Financial Reports

**Revenue Overview**:
1. Go to **"Reports"** → **"Financial Reports"**
2. View total revenue by:
   - Property
   - Date range
   - Payment method
   - Guest type

3. See breakdown of:
   - Total bookings and revenue
   - Cancellations and refunds
   - Payment processing costs
   - Net revenue

### Guest Reports

Track guest information and trends:
1. Go to **"Reports"** → **"Guest Reports"**
2. View:
   - Total guest count
   - New guests this period
   - Guest retention rate
   - Guest by nationality
   - Guest preferences

### Employee Reports

Monitor employee activity:
1. Go to **"Reports"** → **"Employee Reports"**
2. View:
   - Employee roster by property
   - Hours worked (if time tracking enabled)
   - Department staffing levels
   - Payroll summaries

### Exporting Reports

Most reports can be exported:
1. After generating a report
2. Look for **"Export"** or **"Download"** button
3. Choose format:
   - **CSV**: For use in spreadsheet applications
   - **PDF**: For printing or sharing
   - **Excel**: For advanced spreadsheet analysis

---

## FAQ & Troubleshooting

### Q: How do I reset the password for an admin account?
**A**: Only the system owner or database administrator can reset admin passwords directly. Other admins can reset user passwords through User Management.

### Q: Can I delete a user account?
**A**: For data integrity, user accounts are deactivated rather than deleted. Deactivated users cannot log in, but their historical data is preserved. Go to the user record and change Status to "Inactive".

### Q: What happens when I change a user's role?
**A**: The user's permissions immediately change to match the new role. They may need to log out and back in to see updated features.

### Q: How can I back up system data?
**A**: Contact your system administrator or database administrator. Backups are typically handled at the server level, not through the admin interface.

### Q: Why am I not seeing all users/properties in the system?
**A**: Check if there are active filters. Some views can be filtered by status, property, or date. Clear any filters to see the full list.

### Q: Can I schedule user deactivation for a future date?
**A**: This feature is not currently available. You can manually deactivate accounts when needed, or request a system administrator to set up automated scheduling.

### Q: How frequently should I review system logs for security?
**A**: Review system logs at least weekly, or more frequently if your property is large or has high transaction volume.

### Q: What happens if an employee changes their phone number?
**A**: You (or they) can edit the phone number in the employee record at any time. The change takes effect immediately.

### Q: Can I temporarily disable a user without deactivating them?
**A**: Users can only be Active or Inactive. You can change them back to Active at any time if needed.

### Q: How do I add multiple employees at once?
**A**: Currently, employees must be added individually. For bulk operations, contact your system administrator about batch import features if available.

### Q: What should I do if I see suspicious activity in the system logs?
**A**: 
1. Document the suspicious activity (user, action, timestamp)
2. Review the Employee/User status
3. If warranted, deactivate the user account
4. Investigate the activity further
5. Contact system support if needed

### Q: How can I archive old data?
**A**: Archive functionality depends on your system configuration. Contact system support for information about data archival and retention policies.

---

## Best Practices

1. **Regular Security Reviews**: Review user accounts and access levels monthly
2. **Password Management**: Encourage users to change passwords regularly
3. **Activity Monitoring**: Check system logs weekly for unusual activity
4. **Backup Strategy**: Ensure regular backups are happening (work with server admin)
5. **User Deactivation**: Deactivate accounts immediately when employees leave
6. **Role Assignments**: Ensure users have minimum necessary permissions (principle of least privilege)
7. **Update Audits**: Keep property and employee information current

---

## Support & Contact

For technical support, system issues, or advanced configuration needs:
- Contact your system administrator
- Refer to system documentation
- Submit technical support tickets through your support portal

---

**Manual Version**: 1.0  
**Last Updated**: February 2026  
**System**: Nephele Hotel Management System
