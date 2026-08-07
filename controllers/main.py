import urllib.parse
import requests
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class MitIDWebsiteSale(WebsiteSale):

    def _cart_contains_alcohol(self):
        # Safe fetch for order across Odoo 17 and Odoo 19
        website = request.website
        order = None

        if hasattr(request, 'cart'):
            order = request.cart
        elif hasattr(website, '_get_checkout_order'):
            order = website._get_checkout_order()
        elif hasattr(website, 'sale_get_order'):
            order = website.sale_get_order()

        if not order or not order.order_line:
            return False

        # Check if any line product belongs to an Alcohol public category
        for line in order.order_line:
            public_categories = line.product_id.public_categ_ids.mapped('name')
            if any('alcohol' in (cat or '').lower() for cat in public_categories):
                return True

        return False

    @http.route('/shop/mitid/verify', type='http', auth='public', website=True)
    def mitid_verify_redirect(self, **kw):
        """ Directs customer to MitID Broker Authorization URL """
        params = request.env['ir.config_parameter'].sudo()
        client_id = params.get_param('mitid.client_id', '')
        broker_domain = params.get_param('mitid.broker_domain', '').rstrip('/')

        redirect_uri = request.website.get_base_url() + "/shop/mitid/callback"

        query_params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'openid age_verify:18',
            'acr_values': 'urn:grn:authn:dk:mitid:substantial'
        }
        
        # Constructs external authorization URL
        auth_url = f"{broker_domain}/authorize?" + urllib.parse.urlencode(query_params)
        
        # local=False is required to allow Odoo to redirect externally to Signicat
        return request.redirect(auth_url, local=False)

    @http.route('/shop/mitid/callback', type='http', auth='public', website=True)
    def mitid_callback(self, code=None, error=None, **kw):
        """ Handles return handshake from MitID Broker """
        if error or not code:
            return request.redirect('/shop/cart?error=mitid_failed')

        params = request.env['ir.config_parameter'].sudo()
        client_id = params.get_param('mitid.client_id', '')
        client_secret = params.get_param('mitid.client_secret', '')
        broker_domain = params.get_param('mitid.broker_domain', '').rstrip('/')
        redirect_uri = request.website.get_base_url() + "/shop/mitid/callback"

        token_endpoint = f"{broker_domain}/token"
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }

        try:
            res = requests.post(token_endpoint, data=payload, timeout=10)
            token_data = res.json()

            userinfo_endpoint = f"{broker_domain}/userinfo"
            headers = {'Authorization': f"Bearer {token_data.get('access_token')}"}
            user_info = requests.get(userinfo_endpoint, headers=headers, timeout=10).json()

            is_adult = user_info.get('age_above_18') or user_info.get('idbrokerdk_age_verified', False)

            if is_adult:
                request.session['mitid_age_verified'] = True
                return request.redirect('/shop/payment')
            else:
                return request.redirect('/shop/cart?error=underage')
        except Exception:
            return request.redirect('/shop/cart?error=mitid_exception')

    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment(self, **post):
        requires_mitid = self._cart_contains_alcohol()
        is_verified = request.session.get('mitid_age_verified', False)

        response = super(MitIDWebsiteSale, self).shop_payment(**post)
        if hasattr(response, 'qcontext'):
            response.qcontext['requires_mitid'] = requires_mitid
            response.qcontext['mitid_verified'] = is_verified
        return response
