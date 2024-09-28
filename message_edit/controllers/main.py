# -*- coding: utf-8 -*-

from odoo import http
from odoo.addons.web.controllers.main import Action, clean_action
from odoo.http import request


class Action(Action):
    """
    Re-write to add edit method controller used in js
    """
    @http.route('/web/action/load_edit_mode', type='json', auth="user")
    def load_edit_mode(self, action_id, do_not_eval=False, additional_context=None):
        """
        The controller used in js to load message edit wizard
        """
        Actions = request.env['ir.actions.actions']
        value = False
        try:
            action_id = int(action_id)
        except ValueError:
            try:
                action = request.env.ref(action_id)
                assert action._name.startswith('ir.actions.')
                action_id = action.id
            except Exception:
                action_id = 0   # force failed read

        base_action = Actions.browse([action_id]).read(['type'])
        if base_action:
            ctx = dict(request.context)
            action_type = base_action[0]['type']
            if action_type == 'ir.actions.report.xml':
                ctx.update({'bin_size': True})
            if additional_context:
                ctx.update(additional_context)
            action = request.env[action_type].browse([action_id]).read()
            if action:
                value = clean_action(action[0])
            value['flags'] = {
                'form': {'action_buttons': True, 'options': {'mode': 'edit'}}
            }
            value['context'] = {"message_edit": True}
        return value
