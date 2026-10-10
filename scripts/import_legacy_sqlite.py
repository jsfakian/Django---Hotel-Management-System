import argparse
import sqlite3
from datetime import datetime


DIRECT_TABLES = [
    'auth_user',
    'auth_group',
    'auth_group_permissions',
    'auth_user_groups',
    'auth_user_user_permissions',
    'django_content_type',
    'auth_permission',
    'properties_property',
    'properties_propertyamenity',
    'properties_propertypolicy',
    'bookings_pricinghistory',
    'bookings_demandforecast',
    'bookings_competitorprice',
    'contracts_contract',
    'hotel_announcement',
    'hotel_bills',
    'hotel_event',
    'hotel_eventattendees',
    'hotel_foodmenu',
    'hotel_report',
    'hotel_storage',
    'notifications_notificationtype',
    'notifications_notificationpreference',
    'notifications_notification',
    'notifications_notificationlog',
    'notifications_emailnotification',
    'notifications_smsnotification',
]


def get_columns(conn, table_name):
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [row[1] for row in rows]


def table_exists(conn, table_name):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return bool(row)


def copy_intersection(src_conn, dst_conn, table_name):
    if not table_exists(src_conn, table_name) or not table_exists(dst_conn, table_name):
        return 0

    src_cols = set(get_columns(src_conn, table_name))
    dst_cols = [col for col in get_columns(dst_conn, table_name) if col in src_cols]
    if not dst_cols:
        return 0

    select_sql = f"SELECT {', '.join(dst_cols)} FROM {table_name}"
    rows = src_conn.execute(select_sql).fetchall()
    if not rows:
        return 0

    placeholders = ', '.join(['?'] * len(dst_cols))
    insert_sql = (
        f"INSERT OR IGNORE INTO {table_name} ({', '.join(dst_cols)}) "
        f"VALUES ({placeholders})"
    )
    dst_conn.executemany(insert_sql, rows)
    return len(rows)


def import_accounts(src_conn, dst_conn):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    imported_guests = 0
    if table_exists(src_conn, 'accounts_guest') and table_exists(dst_conn, 'accounts_guest'):
        legacy_rows = src_conn.execute(
            'SELECT id, phoneNumber, user_id FROM accounts_guest'
        ).fetchall()

        for guest_id, phone_number, user_id in legacy_rows:
            user_row = src_conn.execute(
                'SELECT email, first_name, last_name FROM auth_user WHERE id=?',
                (user_id,),
            ).fetchone()

            email = (user_row[0] if user_row and user_row[0] else f'guest-{guest_id}@imported.local').lower()
            first_name = user_row[1] if user_row and user_row[1] else 'Guest'
            last_name = user_row[2] if user_row and user_row[2] else str(guest_id)

            dst_conn.execute(
                '''
                INSERT OR IGNORE INTO accounts_guest (
                    id, user_id, email, first_name, last_name, phone_number,
                    address, city, country, postal_code, preferences,
                    number_of_bookings, total_nights_stayed, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, '', '', '', '', '{}', 0, 0, ?, ?)
                ''',
                (
                    guest_id,
                    user_id,
                    email,
                    first_name,
                    last_name,
                    phone_number or '',
                    now,
                    now,
                ),
            )
            imported_guests += 1

    imported_employees = 0
    if table_exists(src_conn, 'accounts_employee') and table_exists(dst_conn, 'accounts_employee'):
        legacy_rows = src_conn.execute(
            'SELECT id, phoneNumber, salary, user_id FROM accounts_employee'
        ).fetchall()

        for employee_id, phone_number, salary, user_id in legacy_rows:
            dst_conn.execute(
                '''
                INSERT OR IGNORE INTO accounts_employee (
                    id, user_id, phone_number, salary, position, department,
                    hire_date, status, property_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, '', '', NULL, 'active', NULL, ?, ?)
                ''',
                (employee_id, user_id, phone_number or '', salary or 0, now, now),
            )
            imported_employees += 1

    imported_tasks = 0
    if table_exists(src_conn, 'accounts_task') and table_exists(dst_conn, 'accounts_task'):
        legacy_rows = src_conn.execute(
            'SELECT id, startTime, endTime, description, employee_id FROM accounts_task'
        ).fetchall()

        for task_id, start_time, end_time, description, employee_id in legacy_rows:
            title = (description or 'Imported task')[:255]
            dst_conn.execute(
                '''
                INSERT OR IGNORE INTO accounts_task (
                    id, employee_id, title, description, start_time, end_time,
                    status, priority, booking_id, property_id, created_at, updated_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'pending', 'medium', NULL, NULL, ?, ?, NULL)
                ''',
                (task_id, employee_id, title, description or '', start_time, end_time, now, now),
            )
            imported_tasks += 1

    return imported_guests, imported_employees, imported_tasks


def import_custom_reports(src_conn, dst_conn):
    if not table_exists(src_conn, 'custom_report') or not table_exists(dst_conn, 'custom_reports'):
        return 0

    rows = src_conn.execute(
        '''
        SELECT
            id, name, description, report_type, from_date, to_date,
            include_charts, include_summary, include_detailed_data,
            export_format, file_path, status, generated_at,
            created_at, updated_at, created_by_id, property_id
        FROM custom_report
        '''
    ).fetchall()

    inserted = 0
    for row in rows:
        dst_conn.execute(
            '''
            INSERT OR IGNORE INTO custom_reports (
                id, name, description, report_type, from_date, to_date,
                include_charts, include_summary, include_detailed_data,
                export_format, file_path, status, generated_at,
                created_at, updated_at, created_by_id, property_id, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '')
            ''',
            row,
        )
        inserted += 1

    return inserted


def import_dashboard_metrics(src_conn, dst_conn):
    inserted = 0

    if table_exists(src_conn, 'dashboard_executive_metrics') and table_exists(dst_conn, 'dashboard_executive_metrics'):
        inserted += copy_intersection(src_conn, dst_conn, 'dashboard_executive_metrics')

    if table_exists(src_conn, 'dashboard_revenue_metrics') and table_exists(dst_conn, 'dashboard_revenue_metrics'):
        inserted += copy_intersection(src_conn, dst_conn, 'dashboard_revenue_metrics')

    if table_exists(src_conn, 'dashboard_guest_analytics') and table_exists(dst_conn, 'dashboard_guest_analytics'):
        inserted += copy_intersection(src_conn, dst_conn, 'dashboard_guest_analytics')

    if table_exists(src_conn, 'dashboard_operational_status') and table_exists(dst_conn, 'dashboard_operational_status'):
        legacy_cols = set(get_columns(src_conn, 'dashboard_operational_status'))
        if {'status_time', 'available_rooms', 'occupied_rooms', 'cleaning_rooms', 'maintenance_rooms', 'pending_checkins', 'pending_checkouts', 'property_id', 'created_at'}.issubset(legacy_cols):
            rows = src_conn.execute(
                '''
                SELECT
                    id,
                    date(status_time) AS status_date,
                    status_time,
                    occupied_rooms,
                    available_rooms,
                    cleaning_rooms,
                    maintenance_rooms,
                    0 AS blocked_count,
                    pending_checkouts,
                    pending_checkins,
                    0 AS housekeeping_tasks_pending,
                    0 AS housekeeping_tasks_in_progress,
                    0 AS maintenance_tickets_pending,
                    0 AS active_guests_count,
                    0 AS guests_with_special_requests,
                    created_at,
                    property_id
                FROM dashboard_operational_status
                '''
            ).fetchall()

            for row in rows:
                dst_conn.execute(
                    '''
                    INSERT OR IGNORE INTO dashboard_operational_status (
                        id, status_date, status_time,
                        occupied_count, vacant_count, cleaning_count, maintenance_count, blocked_count,
                        checkouts_scheduled, checkins_scheduled,
                        housekeeping_tasks_pending, housekeeping_tasks_in_progress,
                        maintenance_tickets_pending, active_guests_count, guests_with_special_requests,
                        created_at, property_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    row,
                )
                inserted += 1

    return inserted


def main():
    parser = argparse.ArgumentParser(description='Import legacy SQLite data into migrated DB.')
    parser.add_argument('--legacy-db', required=True)
    parser.add_argument('--target-db', required=True)
    args = parser.parse_args()

    src_conn = sqlite3.connect(args.legacy_db)
    dst_conn = sqlite3.connect(args.target_db)

    dst_conn.execute('PRAGMA foreign_keys = OFF;')
    copied_counts = {}

    for table_name in DIRECT_TABLES:
        copied_counts[table_name] = copy_intersection(src_conn, dst_conn, table_name)

    guest_count, employee_count, task_count = import_accounts(src_conn, dst_conn)
    custom_reports = import_custom_reports(src_conn, dst_conn)
    dashboard_rows = import_dashboard_metrics(src_conn, dst_conn)

    dst_conn.commit()
    dst_conn.execute('PRAGMA foreign_keys = ON;')

    print('Legacy import completed.')
    print('Direct copies:')
    for table_name, count in copied_counts.items():
        if count:
            print(f'  - {table_name}: {count}')
    print(f'Accounts import: guests={guest_count}, employees={employee_count}, tasks={task_count}')
    print(f'Custom reports imported: {custom_reports}')
    print(f'Dashboard rows imported: {dashboard_rows}')


if __name__ == '__main__':
    main()
