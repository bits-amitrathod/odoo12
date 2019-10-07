

{
    'name': 'po_lot_upgrade',
    'summary':"upgrade po lot",
    'category': 'Report',
    'version': '11.0.0.1',
     'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base', 'stock','sale','purchase'],
    'data': [
          'views/styles_template.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
