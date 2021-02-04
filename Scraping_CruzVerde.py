from scrapy.item import Item
from scrapy.item import Field
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy.loader.processors import MapCompose
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from bs4 import BeautifulSoup
import re

class Product(Item):
    # As we know, the value from the key in every json file, is retrieved inside a list. This is because we can have more than one value valid for every field.
    # Nevertheless, If we are just retrieving one, we can pass the param "output_processor" with a "lambda function" that allows us to retrieve the first item
    # from that list.
    product_name = Field(output_processor = lambda x: x[0])
    price = Field(output_processor = lambda x: x[0])
    
class CruzVerdeCrawlSpider(CrawlSpider):
    name = "CruzVerdeCrawlSpider"
    custom_settings = {
        "USER_AGENT":"Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/84.0.2",
        #"CLOSESPIDER_PAGECOUNT": 3,
        "CLOSESPIDER_ITEMCOUNT":3,
        "FEED_EXPORT_ENCODING": "utf-8",
        #"FEED_EXPORT-FIELDS": ["price", "product_name"], # This it's important whenever we are saving our data inside a ".csv" file.
        "CONCURRENT_REQUESTS": 16, # This stands for the number of request carried out at the same time. By default it's "16". Nevertheless, we can modify
        # this param to be, for example; 18. However, "16" protect us for being ban.
    }
    
    allowed_domains = ["cruzverde.cl"]
    start_urls = ["https://www.cruzverde.cl/medicamentos/?start=0&sz=18&maxsize=18"]
    download_delay = 1 # 1s. The time isn't always the same (that's logic, otherwise it would be detectable). Scrapy uses this value to create a range:
    # (0.5 - 1.5)*download_delay. Scrapy multiplies any value inside that range for the value we have passed to the variable.
    
    rules = (
    
        Rule( # Horizontal pagination. We will extract data from every medicine, without request its detail page.
            LinkExtractor( # NOTA: "LinkExtractor" FUNCIONA BUSCANDO ENTRE TODOS LOS TAGS <a></a> DEL ÁRBOL DE LA PÁG. AQUELLOS CUYOS "href" CUMPLEN CON LO 
                # ESTABLECIDO EN "allow".
                allow = r"cgid=medicamentos&start=\d*",
                tags = ('a', "button"), # SINCE "LinkExtractor" just looks for the "urls" at 'a' tags. So, in this website, the "urls" are inside the "button" 
                # tags. We can add ANY TYPE OF TAG WHERE THE URL WE ARE LOOKING FOR IS.
                attrs = ("href", "data-url",), # SINCE "LinkExtractor" LOOKS FOR THE "URLs" INSIDE "href" ATTR BY DEFAULT, WE NEED TO ADD THE ATTR WHERE OUR
                # URLs ARE.
            ), follow = True, callback = "parse_medicine"
        ),
        
    )
    
    """
    # PARA PARSEAR DIRECTAMENTE EN LA URL SEMILLA (DADO QUE LA URL SEMILLA, SIEMPRE ES EN DONDE SE INICIA). EL MÉTODO QUE DEBEMOS USAR ES:
    
    def parse_start_url(self, response): # ES FORZOSO QUE TENGA ESTE NOMBRE.
        pass
        # LÓGICA DE LA EXTRACCIÓN.
    
    # USAR ESTE MÉTODO CADA QUE SE REQUIERA SCRAPEAR DE LA URL SEMILLA, DE ESTA FORMA, EVITAREMOS ALGUNOS DOLORSITOS DE CABEZA. SIN EMBARGO, NOSOTROS NO LAS 
    HEMOS INGENIADO EN "allow" PARA PODER PARSEAR LA "URL SEMILLA" TAMBIÉN.
    """
    
    def parse_medicine(self, response):
        # Using BeautifulSoup:
        BS_object = BeautifulSoup(response.body, 'lxml')
        for obj in BS_object.find_all("div", {"class":re.compile(r"tile-body((?![w\-100]).)*$")}): # "div" should contain "tile-body" but not contain "w-100".
            medicine_name = obj.find('a',{"class":"link"}).text.replace('\n','').strip()
            medicine_price = obj.find("span",{"class":re.compile(r"value")}).text.replace("(Oferta)",'').replace('$','').strip()
            try:
                medicine_price = float(medicine_price)
            except:
                medicine_price = obj.find("div",{"class":re.compile(r"large-price w-100 d-flex mb-1")}).find("span").text.replace("(Oferta)",'')
                medicine_price = float(medicine_price.replace('$','').strip())
            item = ItemLoader(Product(), response)
            item.add_value("product_name", medicine_name)
            item.add_value("price", medicine_price)
            
            yield item.load_item()
        
        """
        # Using Selector with Xpath (didn't work as I expected):
        
        selector = Selector(response)
        containers = selector.xpath("//div[contains(@class, 'tile-body')][1]")
        for i,container in enumerate(containers, start=1):
            medicine_name = container.xpath(".//a[@class='link']/text()").get().replace('\n','').replace('\t','').strip()
            try:
                medicine_price = container.xpath(".//div[contains(@class, 'large-price')]/span[contains(@class, 'value')]/text()").get()
                medicine_price = medicine_price.replace('$','').replace('(Oferta)','').strip()
                medicine_price = float(medicine_price)
            except:
                print("Empty price, let's grab the next sibling.")
            else:
                medicine_price = container.xpath("string(.//div[contains(@class, 'large-price')]/span/@content)").get()
                medicine_price = medicine_price.replace('$','').replace('(Oferta)','').strip()
                medicine_price = float(medicine_price)
            
            item = ItemLoader(Product(), response)
            item.add_value("product_name", medicine_name)
            item.add_value("price", float(medicine_price))
            yield item.load_item()
        """