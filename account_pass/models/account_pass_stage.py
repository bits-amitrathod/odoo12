from odoo import api, fields, models


class Stage(models.Model):
    _name = "account.pass.stage"
    _description = "Account pass Stages"
    _rec_name = 'name'
    _order = "sequence, name, id"

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    is_won = fields.Boolean('Is Won Stage?')
    is_lost = fields.Boolean('Is Closed Stage?')
    requirements = fields.Text('Requirements',
                               help="Enter here the internal requirements for this stage (ex: Offer sent to customer). It will appear as a tooltip over the stage's name.")
    partner_id = fields.Many2one('res.partner', string='Customer', ondelete='set null',
                              help='Specific team that uses this stage. Other teams will not be able to see or use this stage.')
    fold = fields.Boolean('Folded in Pipeline',
                          help='This stage is folded in the kanban view when there are no records in that stage to display.')
