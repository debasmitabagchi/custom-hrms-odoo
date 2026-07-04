{
    'name': 'Custom HRMS',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Custom Human Resource Management System',
    'description': """
        Custom-built HRMS module from scratch.
        Includes Employees, Attendance, Time Off, Skills and Certifications.
    """,
    'author': 'Deb',
    'depends': ['base', 'mail'],
    'data': [
        'security/hrms_security.xml',
        'security/ir.model.access.csv',
        'views/hrms_employee_views.xml',
        'views/hrms_attendance_views.xml',
        'views/hrms_leave_views.xml',
        'views/hrms_config_views.xml',
        'views/hrms_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}