# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-JANUARY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: PRASANNA KUMARA B (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
from datetime import datetime, timedelta
from odoo import fields, models, _
from odoo.exceptions import UserError


class StockMovesReportWizard(models.TransientModel):
    _name = 'product.batch.report'
    _description = 'Product Batch Report Wizard'

    tracking_wise = fields.Selection([
        ('tracking_wise', 'Por Lot/Serie'),
        ('product_wise', 'Por Producto'), ],
        string='Seguimiento por', default="tracking_wise", required=True)
    product_ids = fields.Many2many('product.product', string='Producto')
    expiry_days = fields.Integer('Dentro de')
    expiry_type = fields.Selection([
        ('expired', 'Caducado'),
        ('expire', 'Por Caducar'), ],
        string='Tipo de Rastreo', required=True)

    def generate_pdf_report(self):
        """
        This Function generates the values required to print the
        PDF report. This function takes below arguments and
        return a data dictionary to the report template.

        :param self: object pointer.
        :return data_dict: Returns filtered data of stock lot and serial data to the report template.
        """
        # expiration_config = self.env['res.config.settings'].search([], order='id desc', limit=1).mapped('module_product_expiry')
        # if expiration_config:
        #     if not expiration_config[0]:
        #         raise UserError(_('Please enable Expiration Settings to get the Report.'))
        # else:
        #     raise UserError(_('Please enable Expiration Settings to get the Report.'))
        if self.expiry_days:
            if self.expiry_days < 0:
                raise UserError('Ingresar número mayor ó igual a Cero')
        today = datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')
        batch_data = self.env['stock.lot']
        if self.product_ids:
            for product in self.product_ids:
                batch_data += batch_data.search(
                    [('product_id', '=', product.id), ('product_id.qty_available', '>', 0)])
        else:
            batch_data = batch_data.search([('product_id.qty_available', '>', 0)])
        if self.expiry_type == 'expired':
            batch_data = batch_data.filtered(lambda l: str(l.expiration_date) <= today)
        else:
            batch_data = batch_data.filtered(lambda l: str(l.expiration_date) >= today)
        values = []
        heading = []
        date_within = ''
        if self.expiry_days:
            if self.expiry_type == 'expired':
                date_within = datetime.strftime((datetime.today() - timedelta(days=int(self.expiry_days))),
                                                '%Y-%m-%d %H:%M:%S')
                batch_data = batch_data.filtered(lambda l: str(date_within) <= str(l.expiration_date) <= str(today))

            else:
                date_within = datetime.strftime((datetime.today() + timedelta(days=int(self.expiry_days))),
                                                '%Y-%m-%d %H:%M:%S')
                batch_data = batch_data.filtered(lambda l: str(date_within) >= str(l.expiration_date) >= str(today))
        batch_data = batch_data.filtered(lambda l: l.expiration_date)
        for line in batch_data:
            expiry_days = line.expiration_date - datetime.today()
            values.append({
                'lot_name': line.name,
                'product': line.product_id.name,
                'expiry_date': line.expiration_date,
                'expiry_days': str(expiry_days.days).replace('-', '')+' Dias'
                # 'expiry_days': str(
                #     (datetime.strptime(str(line.expiration_date), "%Y-%m-%d %H:%M:%S") - datetime.strptime(
                #         today, "%Y-%m-%d %H:%M:%S")).days).replace("-", "") + " Days"
            })
            if self.tracking_wise == 'tracking_wise':
                heading.append({
                    'name': line.id
                })
            else:
                heading.append({
                    'name': line.product_id.name
                })
        # To get product names
        heading = [i for n, i in enumerate(heading) if i not in heading[n + 1:]]  # duplicate check
        view_type = self.tracking_wise
        data_dict = {
            'values': values,
            'heading': heading,
            'view_type': view_type,
            'expiry_type': self.expiry_type,
            'today': today.split(' ')[0],
            'date_within': str(date_within).split(' ')[0],
            'expiry_days': self.expiry_days,
        }
        return self.env.ref('product_batch_report.product_batch_report_action_report').report_action(self,
                                                                                                     data=data_dict)
