# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("\n" * 20 + " ------- Pri-Migration Started -------")
    # cr.execute("""
    #         delete from ir_ui_view
    #         where id =(
    #         select id from ir_ui_view
    #         where id in (1930)
    #         and name = 'report_invoice_document_extended' limit 1)
    #     """)

    cr.execute("""
        update ir_ui_view set active = false where id =(
        select id from ir_ui_view
        where id in (1930)
        and name = 'report_invoice_document_extended' limit 1)
    """)
    cr.execute("""update ir_ui_view set active = true where name = 'purchase.order.form' and id = 1953""")
    cr.execute("""DELETE FROM ir_ui_view where inherit_id in (6176, 5895, 5698, 5697, 1953, 5696,4216,7559);""")
    cr.execute("""DELETE FROM ir_ui_view where id in (5742,5696,4216,4901);""")
    cr.execute("""DELETE FROM ir_cron where ir_actions_server_id in (2064, 1902);""")
    cr.execute("""ALTER TABLE payment_transaction DROP CONSTRAINT IF EXISTS payment_transaction_acquirer_id_fkey;""")
    cr.execute("""DELETE FROM ir_asset where id=94;""")

    cr.execute("""DELETE FROM ir_asset where name ilike 'sps_theme%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'website_quote_ext%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'website_sales%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'payment_aquirer_cstm%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'product_expiry_extension%';""")

    cr.execute("""DELETE FROM mail_template WHERE id in (13, 14, 134);""")
    cr.execute("""DELETE FROM ir_model_data WHERE name in ('email_template_edi_purchase', 'email_template_edi_purchase_done', 'email_template_edi_purchase_reminder')""")
    cr.execute("""DELETE FROM ir_ui_view WHERE key ilike 'sps_theme%' and type = 'qweb' and id not in (5508);""")
    cr.execute("""DELETE FROM ir_ui_view WHERE key ilike 'website_sales%' and type = 'qweb';""")
    cr.execute("""DELETE FROM ir_ui_view WHERE key ilike 'website_quote_ext%' and type = 'qweb';""")

    _logger.info(" ------- Pri-Migration Ended -------" + "\n" * 20)
