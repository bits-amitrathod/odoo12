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
    cr.execute("""
            update ir_ui_view set active = true where name = 'purchase.order.form' and id = 1953
        """)

    _logger.info(" ------- Pri-Migration Ended -------" + "\n" * 20)
