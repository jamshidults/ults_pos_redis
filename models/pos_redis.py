# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import json
from ast import literal_eval

from odoo import models, fields, api
from odoo.tools import date_utils

import json
from datetime import datetime

import redis
from redis.exceptions import DataError

DOMAIN = [('sale_ok', '=', True), ('available_in_pos', '=', True)]


class pos_redis(models.Model):
    _name = 'pos.redis'
    _description = 'Point of Sale Cache'

    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)



    def get_all_products_from_database(self):
        product = self.env['product.product'].with_user(self.env.ref('base.user_admin').id)
        product_data = product.with_context(display_default_code=False).search_read(DOMAIN,
                                                                                    order='sequence,default_code,name')
        return product_data

    @api.model
    def load_all_products_to_redis(self):

        products = self.get_all_products_from_database()

        try:
            products_json = json.dumps(products)
            self.redis_client.set('pos_cache_products', products_json)

        except DataError as e:
            print(f"DataError occurred: {e}")



    @api.model
    def get_products_from_redis(self):
        """
        Retrieve all products from Redis.
        """
        products = self.redis_client.get('pos_cache_products')
        products = json.loads(products)
        if not products:
            # If products not found in Redis, fetch from DB and update Redis
            self.load_all_products_to_redis()
            products = self.get_products_from_redis()
        return products








