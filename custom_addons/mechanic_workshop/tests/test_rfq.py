from __future__ import annotations

import re
from odoo import Command
from odoo.tests import TransactionCase, HttpCase, tagged
from odoo.exceptions import AccessError, UserError, ValidationError


@tagged('post_install', '-at_install')
class TestRfq(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({'name': 'RFQ test product'})
        self.rfq = self.env['sre.rfq'].create({
            'contact_name': 'Test', 'company_name': 'Test company', 'email': 'test@example.invalid',
            'line_ids': [Command.create({'product_id': self.product.id, 'quantity': 3.5})],
        })

    def test_quotation_requires_verified_customer_and_preserves_lines(self):
        with self.assertRaises(UserError):
            self.rfq.action_create_quotation()
        self.rfq.partner_id = self.env['res.partner'].create({'name': 'Verified test company'})
        self.rfq.action_create_quotation()
        order = self.rfq.order_id
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.order_line.product_id, self.product)
        self.assertEqual(order.order_line.product_uom_qty, 3.5)
        self.assertEqual(order.order_line.product_uom_id, self.product.uom_id)
        self.assertEqual(order.opportunity_id, self.rfq.lead_id)
        self.rfq.action_create_quotation()
        self.assertEqual(self.rfq.order_id, order)

    def test_quantity_validation(self):
        for qty in (0, -1, float('nan'), float('inf'), 1000001):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.rfq.line_ids.write({'quantity': qty})

    def test_public_cannot_read_or_create(self):
        public = self.env.ref('base.public_user')
        with self.assertRaises(AccessError):
            self.rfq.with_user(public).read(['contact_name'])
        with self.assertRaises(AccessError):
            self.env['sre.rfq'].with_user(public).create({
                'contact_name': 'Bad', 'company_name': 'Bad', 'email': 'x@example.invalid',
            })


@tagged('post_install', '-at_install')
class TestRfqWebsite(HttpCase):
    def setUp(self):
        super().setUp()
        self.products = self.env['product.product'].create([
            {'name': 'RFQ browser test %s' % n, 'is_published': True, 'sale_ok': True}
            for n in range(3)
        ])

    def token(self, response, name='csrf_token'):
        return re.search(r'name="%s"[^>]*value="([^"]+)"' % name, response.text).group(1)

    def test_guest_basket_submit_and_replay(self):
        page = self.url_open('/rfq')
        self.assertEqual(page.status_code, 200)
        # Empty basket has no form; get CSRF from product form.
        detail = self.url_open(self.products[0].product_tmpl_id.website_url)
        self.assertEqual(detail.status_code, 200)
        csrf = self.token(detail)
        for product in self.products:
            page = self.url_open('/rfq/add', data={'csrf_token': csrf, 'product_id': product.id, 'quantity': '2'})
            self.assertEqual(page.status_code, 200)
        csrf = self.token(page)
        page = self.url_open('/rfq/update', data={'csrf_token': csrf, 'product_id': self.products[0].id, 'quantity': '4'})
        page = self.url_open('/rfq/update', data={'csrf_token': csrf, 'product_id': self.products[2].id, 'remove': '1'})
        self.assertNotIn(self.products[2].name, page.text)
        page = self.url_open('/rfq/add', data={'csrf_token': csrf, 'product_id': self.products[2].id, 'quantity': '3'})
        self.url_open('/shop')
        page = self.url_open('/rfq')
        payload = {'csrf_token': self.token(page), 'submission_key': self.token(page, 'submission_key'),
                   'contact_name': 'Guest RFQ test', 'company_name': 'Browser test', 'email': 'rfq-test@example.invalid'}
        for unused in range(2):
            response = self.url_open('/rfq/submit', data=payload)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Your RFQ has been received', response.text)
        rfq = self.env['sre.rfq'].sudo().search([('submission_key', '=', payload['submission_key'])])
        self.assertEqual(len(rfq), 1)
        self.assertEqual(len(rfq.line_ids), 3)
        self.assertEqual(sorted(rfq.line_ids.mapped('quantity')), [2, 3, 4])
        self.assertTrue(rfq.lead_id)
        self.assertFalse(rfq.partner_id)
        self.assertFalse(rfq.order_id)

    def test_reject_invalid_products_quantity_and_csrf(self):
        detail = self.url_open(self.products[0].product_tmpl_id.website_url)
        csrf = self.token(detail)
        product = self.products[0]
        response = self.url_open('/rfq/add', data={'product_id': product.id, 'quantity': 1})
        self.assertEqual(response.status_code, 400)
        for value in ('0', '-2', 'nan', 'inf', 'garbage', '0.0000001'):
            response = self.url_open('/rfq/add', data={'csrf_token': csrf, 'product_id': product.id, 'quantity': value})
            self.assertEqual(response.status_code, 400)
        product.is_published = False
        response = self.url_open('/rfq/add', data={'csrf_token': csrf, 'product_id': product.id, 'quantity': 1})
        self.assertEqual(response.status_code, 400)

    def test_company_scope_and_empty_submit(self):
        detail = self.url_open(self.products[0].product_tmpl_id.website_url)
        csrf = self.token(detail)
        other_company = self.env['res.company'].create({'name': 'RFQ other company'})
        self.products[0].company_id = other_company
        response = self.url_open('/rfq/add', data={'csrf_token': csrf, 'product_id': self.products[0].id, 'quantity': 1})
        self.assertEqual(response.status_code, 400)
        page = self.url_open('/rfq/add', data={'csrf_token': csrf, 'product_id': self.products[1].id, 'quantity': 1})
        token = self.token(page, 'submission_key')
        self.url_open('/rfq/update', data={'csrf_token': csrf, 'product_id': self.products[1].id, 'remove': '1'})
        response = self.url_open('/rfq/submit', data={'csrf_token': csrf, 'submission_key': token,
            'contact_name': 'Test', 'company_name': 'Test', 'email': 'test@example.invalid'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.env['sre.rfq'].sudo().search([('submission_key', '=', token)]))
