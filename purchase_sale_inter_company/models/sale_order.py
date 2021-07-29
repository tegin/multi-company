# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    auto_purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Source Purchase Order',
        readonly=True,
        copy=False,
    )

    def assert_intercompany_prices_equal(self):
        """Check if the prices of both orders are the same"""
        unequal_line = []
        for so in self:
            for line in so.sudo().order_line:
                if not line.auto_purchase_line_id:
                    continue
                if not so.currency_id.compare_amounts(
                   line.price_unit, line.auto_purchase_line_id.price_unit):
                    continue
                po_line_prod = (
                    line.product_id.default_code or line.product_id.name)
                so_line_prod = (
                    line.auto_purchase_line_id.product_id.default_code
                    or line.auto_purchase_line_id.product_id.name)
                unequal_line.append(
                    _("PO line %s with price %s is not equal to SO "
                      "line %s with price %s \n"
                      ) % (po_line_prod,
                           line.auto_purchase_line_id.price_unit,
                           so_line_prod,
                           line.price_unit))

        if unequal_line:
            raise UserError(
                _('Error. The following lines do not match on'
                  ' the remote order: %s') % "\n".join(unequal_line))

    @api.multi
    def action_confirm(self):
        for order in self.filtered('auto_purchase_order_id'):
            po_company = order.sudo().auto_purchase_order_id.company_id
            if not po_company.intercompany_overwrite_purchase_price:
                order.assert_intercompany_prices_equal()
            else:
                for line in order.order_line.sudo():
                    if line.auto_purchase_line_id:
                        line.auto_purchase_line_id.price_unit = line.price_unit
        return super(SaleOrder, self).action_confirm()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Source Purchase Order Line',
        readonly=True,
        copy=False,
    )
