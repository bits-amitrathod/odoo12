# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" : "Merge Sale Orders",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "info@softhealer.com",    
    "category": "Sales",
    "summary": """
Merge Sale Orders
This module useful to Merge Sale Orders. Sometime required to make single quote from multi quotation. This module help user to merge quotation as well many more options. easy and quick solition to make new quotation or replace existing quotation. 

Easy to merge quotation or sale orders.

Various options provided in merge order popup. 

1. customer (customer option useful if multi customers quotation selected than you can chose in popup. we have not restrict similar customer in this module. you can select any mutli quotations and merge for any single customer.)

2. sale order (sale order option useful if you want merge selected quotation in any specific quotation than you can choose that sale order also in wizard. so this feature is very useful if you want to merge multi quotation in any existing quotation. if you leave blank than it will consider as new quotation)

3. merge type (merge type option useful to give action for selected quotation weather you want to cancel, remove or keep as it is.)

merge quotation
merge sale order
combine quotation
combine sale order

                    """,
    "description": """
Merge Sale Orders
This module useful to Merge Sale Orders. Sometime required to make single quote from multi quotation. This module help user to merge quotation as well many more options. easy and quick solition to make new quotation or replace existing quotation. 

Easy to merge quotation or sale orders.

Various options provided in merge order popup. 

1. customer (customer option useful if multi customers quotation selected than you can chose in popup. we have not restrict similar customer in this module. you can select any mutli quotations and merge for any single customer.)

2. sale order (sale order option useful if you want merge selected quotation in any specific quotation than you can choose that sale order also in wizard. so this feature is very useful if you want to merge multi quotation in any existing quotation. if you leave blank than it will consider as new quotation)

3. merge type (merge type option useful to give action for selected quotation weather you want to cancel, remove or keep as it is.)

merge quotation
merge sale order
combine quotation
combine sale order

                    """,    
    "version":"12.0.1",
    "depends" : [
                
                "base",
                "sale_management",
            ],
    "application" : True,
    "data" : [
        
            "wizard/merge_sale_order.xml",
            
            ],            
    "images": ["static/description/background.png",],              
    "auto_install":False,
    "installable" : True,
    "price": 25,
    "currency": "EUR"   
}
