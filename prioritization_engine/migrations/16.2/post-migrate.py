# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("\n" * 20 + " ------- Odoo Post-Migration Started -------")
    cr.execute("""
            update ir_ui_view set active = true where name = 'purchase.order.form' and id = 1953
        """)

    _logger.info(" ------- Post-Migration Ended -------" + "\n" * 20)
