# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    'name': "Activities Management-Advance",
    'author': 'Softhealer Technologies',
    'website': 'https://www.softhealer.com',
    "support": "support@softhealer.com",
    'category': 'Discuss',
    "license": "OPL-1",
    'version': '16.0.14',
    "summary": "Activity Management Activity Scheduler Manage Employee Activity Manage Supervisor Activity filter Activity Manage Multi Activities Schedule Mass Activities Dynamic Action For Multiple Activities Manage Activity Scheduler Employee Activity Supervisor Activity filter Activity Multi Activity Schedule Mass Activity Tag activity history Activity monitoring Activity multi users assign schedule activity schedule activities Multi Company Activity Mail Odoo Activity Management Activity Dashboard Activity Monitoring Activity Views User Activity Log, User Activity Audit,  Session Management, Record Log, Activity Traces, Login Notification, User Activity Record, Record History, Login History, Login location, Login IP Advance Schedule Activity multi users assign schedule activity to multi users Schedule Activity Dashboard for schedule activity history of schedule activity reports for schedule activity menu and view for schedule activities for Multi Company Activity Portal Activity At Portal Activities Portal odoo",
    "description": """Do you want to show the activities list beautifully? Do you want to show the well-organized structure of activities? Do you want to show completed, uncompleted activities easily to your employees? Do you want to show an activity dashboard to the employee? Do you want to manage activities nicely with odoo? Do you want to show the scheduled activity to the manager, supervisor & employee? This module helps the manager can see everyone's activity, the supervisor can see the assigned user and own activity, the user can see only own activity. Everyone can filter activity by the previous year, previous month, previous week, today, yesterday, tomorrow, weekly, monthly, yearly & custom date. You can see activities like all activities, planned activities, completed activities or overdue activities. Manager, Supervisor & Employee have their own dashboard, that provides a beautiful design on the dashboard. Hurray!""",
    'depends': [
        'bus',
        'sh_activity_base',
    ],
    'data': [
        'security/sh_activity_security_groups.xml',
        'security/ir.model.access.csv',
        'views/sh_menu.xml',
        'data/sh_data_sales_activity_notification.xml',
        'data/sh_sales_activity_email_template.xml',
        'views/sh_activity_alarm.xml',
        'views/activity_config_setting.xml',
        'wizard/sh_feedback.xml',
        'wizard/sh_mark_as_done.xml',
        'wizard/sh_mail_activity_popup.xml',
        'views/sh_dynamic_action_view.xml',
        'views/sh_activity_views.xml',
        'views/sh_activity_dashboard.xml',
        'data/sh_activity_reminder_mail_template.xml',
        'data/sh_activity_reminder_cron.xml',
        'views/sh_recurring_activities.xml',
    ],
    'images': ['static/description/background.png', ],
    "price": 100,
    "currency": "EUR",
    'uninstall_hook': 'uninstall_hook',
    'post_init_hook': '_sh_activity_post_init',
    'assets': {
        'web.assets_backend': [
            'sh_activities_management/static/src/scss/crm_dashboard.scss',
            'sh_activities_management/static/src/js/activity_dashboard.js',
            'sh_activities_management/static/src/xml/systray.xml',
            'sh_activities_management/static/src/xml/activity_dashboard.xml'
            ],
        'mail.assets_messaging': [
            'sh_activities_management/static/src/model/systray.js',
        ],
        }
}
