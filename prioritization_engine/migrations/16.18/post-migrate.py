# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("\n" * 20 + " ------- Odoo Post-Migration Started -------")
    cr.execute("""
            update ir_ui_view set active = true where name = 'purchase.order.form' and id = 1953
        """)

    cr.execute("""update ir_ui_view set active = true where id in (4942,3239,2558);""")
    cr.execute("""update ir_ui_view set active = true where id in (4938,4936,4937);""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'sps_crm%' and name != 'mail.activity.view.form.popup.duplicate';""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'vendor_offer%' and name ='stock.picking.form.inherit.show.offer.price';""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'prioritization_engine%' and id != 1930;""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'account_pass%';""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'captivea_edi%';""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'appraisal_tracker%';""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'customer_credit_note%';""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'inventory_monitor%';""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'product_brand%';""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'product_expiry_extension%';""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'vendor_offer%';""")
    cr.execute("""update ir_ui_view set active = true where arch_fs ilike 'product_seo_backend%';""")

    # My Activity -> Filter view activate
    cr.execute("""update ir_ui_view set active = true where id in (5733);""")

    # Client don't want the this view (customer meeting info button)
    cr.execute("""update ir_ui_view set active = false where name = 'res_partner.view.form.calendar';""")

_logger.info(" ------- Post-Migration Ended -------" + "\n" * 20)
