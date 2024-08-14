import redis
from odoo import models, api
from . import product_pb2  # Import generated Protobuf module
import datetime
import base64
import logging

_logger = logging.getLogger(__name__)

DOMAIN = [('sale_ok', '=', True), ('available_in_pos', '=', True)]
FIELD_LIST = ['display_name', 'lst_price', 'standard_price', 'categ_id', 'pos_categ_id', 'taxes_id', 'barcode', 'default_code', 'to_weight', 'uom_id', 'description_sale', 'description', 'product_tmpl_id', 'tracking', 'available_in_pos', 'attribute_line_ids', 'active', '__last_update', 'image_128', 'id']



def dict_to_protobuf(product_dict, product_pb):
    """Converts a Python dictionary to a Protobuf message."""
    for key, value in product_dict.items():
        if key in ['categ_id', 'pos_categ_id', 'uom_id', 'product_tmpl_id']:
            if value:
                nested_msg = getattr(product_pb, key)
                nested_msg.id = value[0]
                nested_msg.name = value[1]
            else:
                nested_msg = getattr(product_pb, key)
                nested_msg.ClearField('id')
                nested_msg.ClearField('name')
        elif key in ['taxes_id', 'attribute_line_ids']:
            getattr(product_pb, key).extend(value)
        elif key in ['barcode', 'description', 'description_sale','default_code']:
            if value is False:
                setattr(product_pb, key, "")
            else:
                setattr(product_pb, key, str(value))
        elif key == '__last_update':
            # Convert datetime to string
            if isinstance(value, datetime.datetime):
                value = value.isoformat()
            setattr(product_pb, key, str(value))
        # elif key == 'image_128' and value:
        #     product_pb.image_128 = value.encode('utf-8')
        elif key == 'image_128':
            if value:  # Check if value is not empty (False)
                if isinstance(value, str):
                    # Handle base64 encoded string as discussed previously
                    decoded_data = base64.b64decode(value)
                    product_pb.image_128 = decoded_data
                else:
                    product_pb.image_128 = value
        elif hasattr(product_pb, key):

            setattr(product_pb, key, value)
        else:
            # Handle unknown fields or nested structures
            pass
    return product_pb





class PosRedis(models.Model):
    _name = 'pos.redis'
    _description = 'Point of Sale Cache'

    def _get_redis_client(self):
        """Initialize RedisJSON client."""
        return redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=False)

    def get_products_from_database(self, limit=1000, offset=0):
        """Fetch products from database in batches for efficiency."""
        Product = self.env['product.product']
        products = Product.with_user(self.env.ref('base.user_admin').id).with_context(display_default_code=False)
        return products.search_read(DOMAIN, FIELD_LIST, limit=limit, offset=offset, order='sequence,default_code,name')

    @api.model
    def load_all_products_to_redis(self):
        """Load all products into Redis, serialized with Protobuf."""
        redis_client = self._get_redis_client()
        pipeline = redis_client.pipeline()

        offset = 0
        while True:
            products = self.get_products_from_database(limit=1000, offset=offset)
            if not products:
                break

            for product_data in products:
                product = product_pb2.Product()
                product = dict_to_protobuf(product_data, product)
                serialized_product = product.SerializeToString()
                pipeline.set(f"products:{product_data['id']}", serialized_product)

            pipeline.execute()  # Execute the pipeline to save the batch
            offset += 1000
            _logger.info('--------------------------------*****************************************************************************************************process products %s ', str(offset))

    @api.model
    def get_limited_products_from_redis(self,limit=1000,offset=0):
        """Retrieve all products from Redis."""
        redis_client = self._get_redis_client()

        # Fetch product IDs from the database
        Product = self.env['product.product']
        product_ids = Product.search(DOMAIN,limit=limit,offset=offset).ids

        # Construct Redis keys based on product IDs
        keys = [f"products:{product_id}" for product_id in product_ids]

        # Use pipeline for efficient retrieval
        pipeline = redis_client.pipeline()
        for key in keys:
            pipeline.get(key)
        serialized_products = pipeline.execute()

        products = []
        for serialized_product in serialized_products:
            if serialized_product:
                product = product_pb2.Product()
                product.ParseFromString(serialized_product)
                product_dict = self.protobuf_to_dict(product)
                products.append(product_dict)
                _logger.info(
                    '--------------------------------*****************************************************************************************************process product dict %s ',
                    product_dict)
        return products

    @api.model
    def get_products_from_redis(self):
        """Retrieve all products from Redis."""
        redis_client = self._get_redis_client()

        # Fetch product IDs from the database
        Product = self.env['product.product']
        product_ids = Product.search(DOMAIN).ids

        # Construct Redis keys based on product IDs
        keys = [f"products:{product_id}" for product_id in product_ids]

        # Use pipeline for efficient retrieval
        pipeline = redis_client.pipeline()
        for key in keys:
            pipeline.get(key)
        serialized_products = pipeline.execute()

        products = []
        for serialized_product in serialized_products:
            if serialized_product:
                product = product_pb2.Product()
                product.ParseFromString(serialized_product)
                product_dict = self.protobuf_to_dict(product)
                products.append(product_dict)
                _logger.info(
                    '--------------------------------*****************************************************************************************************process product dict %s ',product_dict)
        return products



    def protobuf_to_dict(self, product_pb):
        """Convert Protobuf object to dictionary."""
        product_dict = {}
        for field in product_pb.DESCRIPTOR.fields:
            value = getattr(product_pb, field.name)
            if isinstance(value, product_pb2.Product.Tuple):
                product_dict[field.name] = [value.id, value.name]
            elif field.name == 'image_128':
                product_dict[field.name] = value.decode('utf-8')
            elif field.name in ('taxes_id', 'attribute_line_ids'):
                product_dict[field.name] = list(value)
            else:
                product_dict[field.name] = value
        return product_dict

