from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field, root_validator
from typing import Literal
from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.contrib.fastapi import register_tortoise

app = FastAPI()

# class Category(BaseModel):
#     id: int
#     # name: str

# class Product(BaseModel):
#     id: int
#     sku: str
#     name: str
#     price: float
#     category_id: int
#     category: Category

class Category(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    
class Product(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=255)
  sku = fields.FloatField(max_length=10)
  price = fields.JSONField()
  percentage_off = fields.FloatField(max_length=10)
  category = fields.ForeignKeyField('models.Category', related_name='products')
  date_added = fields.DateField(auto_now_add=True)
  
  
  
  def __str__(self):
        return self.name   

Product_pydantic = pydantic_model_creator(Product, name="product") 
ProductIn_pydantic = pydantic_model_creator(Product, name="productIn", exclude_readonly=True)


# class DiscountProduct(BaseModel):
#     id: int
#     percentage_off: float
#     product: Product
    
# class DiscountCategory(BaseModel):
#     id: int
#     percentage_off: float
#     category_id: int = Field(..., alias="category.category_id")
#     category: Category
    

class DiscountIn(BaseModel):
  category: str | None
  product_id: int | None
  category_id: int | None
  product_name: str | None
  category_name: str | None
  discount_type: Literal['product', 'category']
  percentage_off: float | None = None
  
  @root_validator
  def validate_discount_type(cls, values):
    discount_type = values.get('discount_type')
    if discount_type == 'product' and values.get('sku') is None:
      raise ValueError('discount_type is product but sku is not provided')
      
    if discount_type == 'category' and values.get('category') is None:
      raise ValueError('discount_type is category but category is not provided')
      
    return values

@app.post("/new_products")
async def create_product(
    sku: str,
    name: str ,
    price: float,
    category_id: int 
    
    ):
           
    new_product = await Product.create(sku=sku, name=name, price=price, category=category)
    return new_product

@app.put("/discounts/")
async def create_discount(discount: DiscountIn):
    discount_dict = discount.dict()    
    
    if discount.discount_type == 'product':
      
      if discount.product_id is not None:
        product = await Product.get(id=discount.product_id)
        category = await Category.get(name=discount.category_name)
        product.percentage_off = discount.percentage_off
      
      if product.percentage_off < category.percentage_off:
        product.percentage_off = category.percentage_off
        final_price = product.price - (product.price * product.percentage_off)
      return final_price
      
        
    if discount.discount_type == 'category':  
      if discount.category_id is not None:
        category = await Category.get(id=discount.category_id)
        category.percentage_off = discount.percentage_off
        

@app.get("/products/")
async def read_products(category: int = Query(None, title="Filter by category"), price_less_than: float = Query(None, title="Filter by price less than")):
    products = await Product.all().limit(10).order_by('id').execute()
    if category:
        products = products.filter(category=category)
    if price_less_than:
        products = products.filter(price__lte=price_less_than)
    return products
  
    discounted_products = []
    for product in products:
      if product.percenatge_off:
        price = {"original": product.price, "final": product.price - (product.price * product.percentage_off)}
        discount = product.percentage_off * 100
        discount_percentage = f"{discount}%"
      else:
        price = {"original": product.price, "final": product.price}
        discount_percentage = None

      discounted_products.append(Products(sku=product.sku,name=product.name,price=price, discount_percentage=discount_percentage, currency="usd"))
      
        

    
      
      

# @app.get("/products/")
# async def read_products(
#     category: str = Query(None, max_length=50), 
#     price_less_than: float = Query(None),
#     db: Session = Depends(get_db)
# ):
#     query = db.query(Product).filter(Product.price <= price_less_than)
#     if category:
#         query = query.join(Product.category).filter(Category.name == category)
#     products = query.limit(10).all()
#     for product in products:
#         product.discount_percentage = None
#         product.price_final = product.price
#         if product.discount_product:
#             product.discount_percentage = f"{product.discount_product.percentage_off*100}%"
#             product.price_final = product.price - (product.price * product.discount_product.percentage_off)
#     return products


register_tortoise(
  app,
  db_url='sqlite://db.sqlite3',
  modules={'models': ['main']},
  generate_schemas= True,
  add_exception_handlers=True
)

      

  