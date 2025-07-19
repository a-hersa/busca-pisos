# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class PropertyItem(scrapy.Item):
    p_id = scrapy.Field()
    nombre = scrapy.Field()
    fecha_new = scrapy.Field()
    fecha_updated = scrapy.Field()
    precio = scrapy.Field()
    metros = scrapy.Field()
    habitaciones = scrapy.Field()
    planta = scrapy.Field()
    ascensor = scrapy.Field()
    poblacion = scrapy.Field()
    url = scrapy.Field()
    descripcion = scrapy.Field()
    estatus = scrapy.Field()

class UrlItem(scrapy.Item):
    url = scrapy.Field()