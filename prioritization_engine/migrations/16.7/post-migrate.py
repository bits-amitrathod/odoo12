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

    _logger.info(" ------- Post-Migration Ended -------" + "\n" * 20)
