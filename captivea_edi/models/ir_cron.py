from odoo import fields, models, api


class IrCron(models.Model):
    _inherit = 'ir.cron'

    def ir_cron_edi_return_action(self):
        print('get')
        return {
            'name': 'Scheduler',
            # 'view_type': 'tree',
            'view_mode': 'tree,form',
            'res_model': 'ir.cron',
            'domain': [('id', 'in', [self.env.ref('captivea_edi.ir_cron_captivea_edi_process_schedule').id, self.env.ref('captivea_edi.cron_remove_logs').id])],
            'context': {'search_default_all': 1},
            'type': 'ir.actions.act_window',
        }
