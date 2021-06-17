# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools


class PickingOperationReportExtension(models.Model):
    _name = "picking.operation.report.extension"
    _auto = False
    _description = "Picking Operation Report Extension"

    def init(self):
        '''Create the view'''
        tools.drop_view_if_exists(self._cr, self._table)
        # This Code For only console error resolve purposr
        self.env.cr.execute('''
                         CREATE OR REPLACE VIEW %s AS (
                         SELECT  so.id AS id,
                                 so.name AS name
                         FROM sale_order so
                         )''' % (self._table)
                            )
