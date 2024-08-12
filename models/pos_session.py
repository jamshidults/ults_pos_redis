# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def get_products_from_cache(self):
        cache = self.env['pos.redis']
        products = cache.get_products_from_redis()
        return products



    def _get_pos_ui_product_product(self, params):
        """
        If limited_products_loading is active, prefer the native way of loading products.
        Otherwise, replace the way products are loaded.
            First, we only load the first 100000 products.
            Then, the UI will make further requests of the remaining products.
        """
        if self.config_id.limited_products_loading:
            return super()._get_pos_ui_product_product(params)
        records = self.get_products_from_cache()
        self._process_pos_ui_product_product(records)
        return records[:100000]

    def get_cached_products(self, start, end):
        records = self.get_products_from_cache()
        self._process_pos_ui_product_product(records)
        return records[start:end]

    def get_total_products_count(self):
        records = self.get_products_from_cache()
        return len(records)
