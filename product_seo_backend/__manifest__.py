{
  
  # App information
   
    'name': 'Manage Product & Category SEO',
    'version': '1.0',
    'category': 'website',
    'license': 'OPL-1',
    'summary': """Manage product and category SEO from product and category form in backend.

    Odoo product SEO, odoo SEO, product ranking, category ranking, category SEO, SEO fields, backend SEO, easy SEO
    SEO management odoo
    """,
    
   # Dependencies
   
   'depends': ['website_sale'],
   
    # Views
   
    'data': [
          'views/product_template.xml',
	        'views/product_public_category.xml',
	],
   
   # Odoo Store Specific
    
    'images': ['static/description/product_category_seo.png'],      
    
    # Author

    'author': 'Craftsync Technologies',
    'website': 'https://www.craftsync.com',
    'maintainer': 'Craftsync Technologies',
       
       
    # Technical 
    
    'installable': True,
    'currency': 'EUR',
    'price': 9.00,
    'auto_install': False,
    'application': True,
          
}
