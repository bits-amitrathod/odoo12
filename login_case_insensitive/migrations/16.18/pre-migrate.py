# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("\n" * 20 + " ------- Pri-Migration Started -------")

    # Sh_Activities_management module related views and assets removing
    # at the time of upgrade all views will generate again
    cr.execute("""DELETE FROM ir_asset where path ilike '/sh_activiti%';""")
    cr.execute("""DELETE FROM ir_ui_view where arch_fs ilike 'sh_activit%' and id not in(5675,5678,6176);""")

    _logger.info(" ------- Pri-Migration Ended -------" + "\n" * 20)
