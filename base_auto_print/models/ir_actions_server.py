from odoo import models, fields, api


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    state = fields.Selection(selection_add=[('print', 'Print a Report')])
    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        domain="[('model_id', '=', model_id)]",
        ondelete='set null',
    )
    printer_id = fields.Many2one(
        comodel_name='printing.printer',
        string='Printer',
    )
    printer_tray_id = fields.Many2one(
        comodel_name='printing.tray',
        string='Paper Source',
        domain="[('printer_id', '=', printer_id)]",
    )

    @api.model
    def run_action_print(self, action, eval_context=None):
        if not action.report_id:
            return False
        description = 'Print %s' % action.report_id.name
        if eval_context.get('records'):
            record_ids = eval_context['records'].ids
            description = description + ' for ' + ','.join(
                [x[1] for x in eval_context['records'].name_get()])
        else:
            record_ids = None
        action.report_id.with_delay(description=description).print_document_auto(
            record_ids, behaviour=self.print_behaviour())
        return False

    @api.multi
    def print_behaviour(self):
        self.ensure_one()
        return {
            'action': 'server',
            'printer': self.printer_id,
            'tray': self.printer_tray_id.system_name
        }

    @api.onchange('state')
    def change_print_state(self):
        if self.state != 'print':
            self.printer_id = False
            self.report_id = False
            self.printer_tray_id = False
