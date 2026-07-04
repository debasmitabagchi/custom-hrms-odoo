from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrmsLeave(models.Model):
    _name = 'hrms.leave'
    _description = 'Employee Leave / Time Off Request'
    _order = 'start_date desc'

    employee_id = fields.Many2one('hrms.employee', string='Employee', required=True, ondelete='cascade')
    leave_type = fields.Selection([
        ('paid', 'Paid Time Off'),
        ('sick', 'Sick Leave'),
        ('unpaid', 'Unpaid Leave'),
    ], string='Time Off Type', required=True, default='paid')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    number_of_days = fields.Float(string='Days', compute='_compute_days', store=True)
    reason = fields.Text(string='Reason')
    attachment = fields.Binary(string='Attachment (Sick Certificate)')
    attachment_filename = fields.Char(string='Attachment Filename')
    state = fields.Selection([
        ('draft', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft')
    approved_by = fields.Many2one('hrms.employee', string='Approved/Rejected By', readonly=True)

    @api.depends('start_date', 'end_date')
    def _compute_days(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date >= rec.start_date:
                rec.number_of_days = (rec.end_date - rec.start_date).days + 1
            else:
                rec.number_of_days = 0.0

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.end_date < rec.start_date:
                raise ValidationError('End Date cannot be before Start Date.')

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            admin_employee = self.env['hrms.employee'].search(
                [('user_id', '=', self.env.uid)], limit=1)
            rec.approved_by = admin_employee.id if admin_employee else False

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
            admin_employee = self.env['hrms.employee'].search(
                [('user_id', '=', self.env.uid)], limit=1)
            rec.approved_by = admin_employee.id if admin_employee else False