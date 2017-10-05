from odoo import models, fields, api
from odoo.addons.queue_job.job import job
from odoo.tools.safe_eval import safe_eval


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    state = fields.Selection(selection_add=[('print', 'Print a Report')])
    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        domain=lambda s: 'model' == s.model_id.model,
        ondelete='set null'
    )

    @api.model
    def run_action_print(self, action, eval_context=None):
        if not action.report_id or not self._context.get('active_id'):
            return False
        action.report_id.with_context(automatic=True).with_delay.print_document(
            [self.context['active_id']])
        return False

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    automatic_print_action_ids = fields.One2many(
        comodel_name='printing.report.xml.action.auto',
        inverse_name='report_id',
        string='Automated Printing Action Domain Rules',
    )

    @job
    @api.multi
    def print_document(self, record_ids, data=None):
        """Decorator Hook"""
        return super(IrActionsReport, self).print_document(
            record_ids, data=data)

    @api.multi
    def behaviour(self):
        self.ensure_one()
        res = super(self.behaviour())[self]
        record_id = self._context.get('active_id')
        if self._context.get('automatic') and record_id:
            model = self.env['ir.model']._get(self.model)
            record_domain = [('id', '=', record_id)]
            for action in self.automatic_print_action_ids:
                if model.search(record_domain +
                                safe_eval(action.filter_domain)):
                    auto_action = action.behaviour()
                    return {self: {'action': 'printer',


        result = {}
        printer_obj = self.env['printing.printer']
        printing_act_obj = self.env['printing.report.xml.action']
        # Set hardcoded default action
        default_action = 'client'
        # Retrieve system wide printer
        default_printer = printer_obj.get_default()


    @job
    @api.model
    def _print_document_automatically(self, report_name, records):
        report = self.sudo()._get_report_from_name(report_name)
        for record in records:
            record_domain = [('id', '=', record.id)]
            matched = False
            for action in report.domain_rule_ids:
                if record.search(record_domain +
                                 safe_eval(action.filter_domain)):
                    matched = action
                    break
            sudo_uid = matched.user_id.id if matched else self._uid
            self.sudo(sudo_uid).print_document([record.id], report_name)
        return True



class PrintingReportXmlAction(models.Model):
    _name = 'printing.report.xml.action.auto'
    _order = 'report_id, sequence asc'

    sequence = fields.Integer(default=5)
    filter_domain = fields.Char(
        string='Apply on',
        default='[]',
        required=True,
        help="If present, this condition must be satisfied before "
             "executing the action rule.")

    report_id = fields.Many2one(comodel_name='ir.actions.report',
                                string='Report',
                                required=True,
                                ondelete='cascade')
    user_id = fields.Many2one(comodel_name='res.users',
                              string='User',
                              required=True,
                              ondelete='cascade')
    action = fields.Selection(
        selection=lambda s: s.env['printing.action']._available_action_types(),
        required=True,
    )
    printer_id = fields.Many2one(comodel_name='printing.printer',
                                 string='Printer')

    @api.multi
    def behaviour(self):
        self.ensure_one()
        return {
            'action': 'printer',
            'printer': self.printer_id,
            'tray': self.printer_tray.system_name
        }