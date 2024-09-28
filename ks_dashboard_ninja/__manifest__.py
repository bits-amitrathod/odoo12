# -*- coding: utf-8 -*-
{
	'name': 'Dashboard Ninja with AI',

	'summary': """
Ksolves Dashboard Ninja gives you a wide-angle view of your business that you might have missed. Get smart visual data with interactive and engaging dashboards for your Odoo ERP.  Odoo Dashboard, CRM Dashboard, Inventory Dashboard, Sales Dashboard, Account Dashboard, Invoice Dashboard, Revamp Dashboard, Best Dashboard, Odoo Best Dashboard, Odoo Apps Dashboard, Best Ninja Dashboard, Analytic Dashboard, Pre-Configured Dashboard, Create Dashboard, Beautiful Dashboard, Customized Robust Dashboard, Predefined Dashboard, Multiple Dashboards, Advance Dashboard, Beautiful Powerful Dashboards, Chart Graphs Table View, All In One Dynamic Dashboard, Accounting Stock Dashboard, Pie Chart Dashboard, Modern Dashboard, Dashboard Studio, Dashboard Builder, Dashboard Designer, Odoo Studio.  Revamp your Odoo Dashboard like never before! It is one of the best dashboard odoo apps in the market.
""",

	'description': """
Dashboard Ninja v16.0,
        Odoo Dashboard,
        Dashboard,
        Dashboards,
        Odoo apps,
        Dashboard app,
        HR Dashboard,
        Sales Dashboard,
        inventory Dashboard,
        Lead Dashboard,
        Opportunity Dashboard,
        CRM Dashboard,
        POS,
        POS Dashboard,
        Connectors,
        Web Dynamic,
        Report Import/Export,
        Date Filter,
        HR,
        Sales,
        Theme,
        Tile Dashboard,
        Dashboard Widgets,
        Dashboard Manager,
        Debranding,
        Customize Dashboard,
        Graph Dashboard,
        Charts Dashboard,
        Invoice Dashboard,
        Project management,
        ksolves,
        ksolves apps,
        Ksolves India Ltd.
        Ksolves India  Limited,
        odoo dashboard apps
        odoo dashboard app
        odoo dashboard module
        odoo modules
        dashboards
        powerful dashboards
        beautiful odoo dashboard
        odoo dynamic dashboard
        all in one dashboard
        multiple dashboard menu
        odoo dashboard portal
        beautiful odoo dashboard
        odoo best dashboard
        dashboard for management
        Odoo custom dashboard
        odoo dashboard management
        odoo dashboard apps
        create odoo dashboard
        odoo dashboard extension
        odoo dashboard module
""",

	'author': 'Ksolves India Ltd.',

	'license': 'OPL-1',

	'currency': 'EUR',

	'price': '335.49',

	'website': 'https://store.ksolves.com/',

	'maintainer': 'Ksolves India Ltd.',

	'live_test_url': 'https://dashboardninja16.kappso.in/web/demo_login',

	'category': 'Services',
	'version': '16.0.1.7.7',


	'support': 'sales@ksolves.com',

	'images': ['static/description/On Dashboard Ninja & Dashboard Ninja Advance.gif'],

	'depends': ['base', 'web', 'base_setup', 'bus','base_geolocalize'],

	'data': [
		'security/ir.model.access.csv',
		'security/ks_security_groups.xml',
		'data/ks_default_data.xml',
		'data/ks_mail_cron.xml',
		'data/dn_data.xml',
		'data/sequence.xml',
		'views/res_settings.xml',
		'views/ks_dashboard_ninja_view.xml',
		'views/ks_dashboard_ninja_item_view.xml',
		'views/ks_dashboard_group_by.xml',
		'views/ks_dashboard_csv_group_by.xml',
		'views/ks_dashboard_action.xml',
		'views/ks_import_dashboard_view.xml',
		'wizard/ks_create_dashboard_wiz_view.xml',
		'wizard/ks_duplicate_dashboard_wiz_view.xml',
		'views/ks_ai_dashboard.xml',
		'views/ks_whole_ai_dashboard.xml',
		'views/ks_key_fetch.xml'
	],

	'demo': ['demo/ks_dashboard_ninja_demo.xml'],

	'assets': {'web.assets_backend':
				   ['https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap',
					'ks_dashboard_ninja/static/src/js/ks_funnel_chart.js',
					'ks_dashboard_ninja/static/src/css/ks_dashboard_ninja.scss',
					'ks_dashboard_ninja/static/src/css/ks_dashboard_ninja_item.css',
					'ks_dashboard_ninja/static/src/css/ks_icon_container_modal.css',
					'ks_dashboard_ninja/static/src/css/ks_dashboard_item_theme.css',
					'ks_dashboard_ninja/static/src/css/style.css',
					'ks_dashboard_ninja/static/src/css/ks_input_bar.css',
					'ks_dashboard_ninja/static/src/css/ks_ai_dash.css',
					'ks_dashboard_ninja/static/src/css/ks_dn_filter.css',
					'ks_dashboard_ninja/static/src/css/ks_toggle_icon.css',
					'ks_dashboard_ninja/static/src/css/ks_flower_view.css',
					'ks_dashboard_ninja/static/src/css/ks_map_view.css',
					'ks_dashboard_ninja/static/src/css/ks_funnel_view.css',
					'ks_dashboard_ninja/static/src/css/ks_dashboard_options.css',
					'ks_dashboard_ninja/static/lib/css/Chart.min.css',
					'ks_dashboard_ninja/static/lib/js/Chart.bundle.min.js',
					'ks_dashboard_ninja/static/lib/js/chartjs-plugin-datalabels.js',
					'ks_dashboard_ninja/static/lib/js/index.js',
					'ks_dashboard_ninja/static/lib/js/xy.js',
					'ks_dashboard_ninja/static/lib/js/radar.js',
					'ks_dashboard_ninja/static/lib/js/Animated.js',
					'ks_dashboard_ninja/static/lib/js/Dataviz.js',
					'ks_dashboard_ninja/static/lib/js/Material.js',
					'ks_dashboard_ninja/static/lib/js/map.js',
					'ks_dashboard_ninja/static/lib/js/worldLow.js',
					'ks_dashboard_ninja/static/lib/js/Moonrise.js',
					'ks_dashboard_ninja/static/lib/js/exporting.js',
					'ks_dashboard_ninja/static/lib/js/pdfmake.js',
					'ks_dashboard_ninja/static/lib/js/percent.js',
					'ks_dashboard_ninja/static/src/js/ks_flower_render.js',
					'ks_dashboard_ninja/static/src/js/ks_global_functions.js',
					'ks_dashboard_ninja/static/src/js/ks_dashboard_ninja.js',
					'ks_dashboard_ninja/static/src/js/ks_to_do_dashboard.js',
					'ks_dashboard_ninja/static/src/js/ks_filter_props.js',
					'ks_dashboard_ninja/static/src/js/ks_color_picker.js',
					'ks_dashboard_ninja/static/src/js/ks_dashboard_ninja_item_preview.js',
					'ks_dashboard_ninja/static/src/js/ks_image_basic_widget.js',
					'ks_dashboard_ninja/static/src/js/ks_dashboard_item_theme.js',
					'ks_dashboard_ninja/static/src/js/ks_widget_toggle.js',
					'ks_dashboard_ninja/static/src/js/ks_import_dashboard.js',
					'ks_dashboard_ninja/static/src/js/ks_domain_fix.js',
					'ks_dashboard_ninja/static/src/js/ks_owl_widget.js',
					'ks_dashboard_ninja/static/src/js/owl_image.js',
					'ks_dashboard_ninja/static/src/js/ks_quick_edit_view.js',
					'ks_dashboard_ninja/static/src/js/ks_dashboard_ninja_kpi_preview.js',
					'ks_dashboard_ninja/static/src/js/ks_date_picker.js',
					'ks_dashboard_ninja/static/lib/css/gridstack.min.css',
					'ks_dashboard_ninja/static/lib/js/gridstack-h5.js',
					'ks_dashboard_ninja/static/lib/js/Chart.bundle.min.js',
					'ks_dashboard_ninja/static/src/css/ks_dashboard_ninja_pro.css',
					'ks_dashboard_ninja/static/src/css/ks_to_do_item.css',
					'ks_dashboard_ninja/static/src/js/ks_dashboard_ninja_graph_preview.js',
					'ks_dashboard_ninja/static/src/js/ks_dashboard_ninja_list_view_preview.js',
					'ks_dashboard_ninja/static/src/js/ks_to_do_preview.js',
					'ks_dashboard_ninja/static/src/js/owl_image.js',
					'ks_dashboard_ninja/static/src/js/ks_item_theme.js',
					'ks_dashboard_ninja/static/src/js/ks_dashboard_item_theme_old.js',
					'ks_dashboard_ninja/static/src/xml/owl_template.xml',
					'ks_dashboard_ninja/static/src/xml/**/*',
					'ks_dashboard_ninja/static/src/js/ks_map_render_preview.js',
					'ks_dashboard_ninja/static/src/js/ks_bullet_chart.js',
					'ks_dashboard_ninja/static/src/css/ks_radial_chart.css',
					'ks_dashboard_ninja/static/src/js/ks_radial_graph_preview.js',
					'ks_dashboard_ninja/static/src/js/ks_ai_dash_action.js',
					'ks_dashboard_ninja/static/src/js/ks_keyword_selection.js',
					'ks_dashboard_ninja/static/src/js/ks_item_type_selection.js'

					],
			   },

	'external_dependencies': {
    	'python': ['pandas','xlrd']
    },

	'uninstall_hook': 'uninstall_hook',
}
