import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime


def collect_data(url):
    retry_strategy = Retry(
        total=30,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    k = 1
    ua = UserAgent()
    r = http.get(url, headers={'user-agent': f'{ua.random}'})
    soup = BeautifulSoup(r.text, 'lxml')
    categories = soup.find_all('div', class_='col-xs-12 col-md-6 col-lg-3')
    s = {i.find('h3').text.strip(): [b.text.strip() for b in i.find_all('li')] for i in categories}
    yml_catalog_date = ET.Element('yml_catalog')
    shop_data = ET.SubElement(yml_catalog_date, 'shop')
    categories_data = ET.SubElement(shop_data, 'categories')
    check_data = []
    z = 1
    for i in s:
        category_data = ET.SubElement(categories_data, 'category')
        c = z
        check_data.append(i)
        category_data.set('id', str(c))
        z += 1
        category_data.text = i
        for m in s.get(i):
            subcategory_data = ET.SubElement(categories_data, 'category')
            subcategory_data.set('id', str(z))
            subcategory_data.set('parentId', str(c))
            subcategory_data.text = m
            check_data.append(m)
            z += 1
    offers = ET.SubElement(shop_data, 'offers')
    categories = ['https://nir-vanna.ru' + i.find('a').get('href') for i in categories]
    for main_url in categories:
        r = http.get(main_url, headers={'user-agent': f'{ua.random}'})
        soup = BeautifulSoup(r.text, 'lxml')
        try:
            pages = int(soup.find('ul', class_='pagination line').find_all('li')[-2].text)
        except AttributeError:
            pages = 1
        for page in range(1, pages + 1):
            print(str(page) + ' / ' + str(pages))
            url = main_url + f'?PAGEN_1={page}'
            r = http.get(url, headers={'user-agent': f'{ua.random}'})
            soup = BeautifulSoup(r.text, 'lxml')
            items = soup.find_all('a', class_='p__i p__i__s')
            for item in items:
                url = 'https://nir-vanna.ru' + item.get('href')
                r = http.get(url, headers={'user-agent': f'{ua.random}'})
                soup = BeautifulSoup(r.text, 'lxml')
                try:
                    price_before = soup.find('div', class_='old-price').text[:-2].strip()
                    price_after = soup.find('div', class_='new-price').text[:-2].strip()
                except AttributeError:
                    price_before = ''
                    try:
                        price_after = soup.find('div', class_='new-price').text[:-2].strip()
                    except AttributeError:
                        price_after = ''
                images = soup.find_all('div', class_='item-card-slider-preview-one')
                image_urls = []
                for image in images:
                    try:
                        image_urls.append('https://nir-vanna.ru' + image.find('img').get('data-lazy'))
                    except TypeError:
                        break
                breadcrumbs = soup.find('ul', class_='bread-crumbs').find_all('li')
                name = breadcrumbs[-1].text
                category = breadcrumbs[-2].text
                kit = soup.find('div', id=f'tab2').find('div', class_='tab-pane-set-block-top').find_all('div', class_='set-block-top-item static')
                kit = [i.find('div', class_='item-right-title').text.strip() for i in kit]
                extra = soup.find('div', id=f'tab2').find_all('div', class_='set-block-bottom-section')
                extra = {i.find('div', class_='set-block-bottom-section-title').text: [article.find('span').text for article in i.find_all('div', class_='article')] for i in extra}
                params = soup.find('div', id=f'tab3').find('div', class_='tab-pane-product-parameters-block').find_all('li', class_='tab-pane-product-parameter-item')
                params = {param.find('div', class_='parameter-name').text.strip().split()[0]: param.find('div', class_='parameter-value').text.strip() for param in params}
                try:
                    description = soup.find('div', id=f'tab4').find('div', class_='detail-block-left text').text.replace('\n', '').strip()
                except AttributeError:
                    description = ''
                for i in check_data:
                    if i == category:
                        id = check_data.index(i) + 1
                offer = ET.SubElement(offers, 'offer')
                offer.set('id', str(k))
                url_data = ET.SubElement(offer, 'url')
                url_data.text = url
                price_data = ET.SubElement(offer, 'price')
                price_data.text = price_after
                old_price_data = ET.SubElement(offer, 'oldprice')
                old_price_data.text = price_before
                cur_data = ET.SubElement(offer, 'currencyId')
                cur_data.text = 'RUB'
                category_data = ET.SubElement(offer, 'categoryId')
                category_data.text = str(id)
                for i in image_urls:
                    picture_data = ET.SubElement(offer, 'picture')
                    picture_data.text = i
                kit_total_data = ET.SubElement(offer, 'kit_info')
                kit_data = ET.SubElement(kit_total_data, 'kit_include')
                for i in kit:
                    kit_data_element = ET.SubElement(kit_data, 'kit_elem')
                    kit_data_element.text = i
                extra_data = ET.SubElement(kit_total_data, 'kit_extra')
                for i in extra:
                    extra_data_main = ET.SubElement(extra_data, 'kit_extra_elem')
                    extra_data_main.set('name', i)
                    for m in extra.get(i):
                        extra_data_elem = ET.SubElement(extra_data_main, 'kit_extra_elem_article')
                        extra_data_elem.text = m
                description_data = ET.SubElement(offer, 'description')
                description_data.text = description
                for i in params:
                    param_data = ET.SubElement(offer, 'param')
                    param_data.set('name', i)
                    param_data.text = params.get(i)
                name_data = ET.SubElement(offer, 'name')
                name_data.text = name
                k += 1
    yml_catalog_date.set('date', str(datetime.today().strftime("%Y-%m-%d %H:%M")))
    tree = ET.ElementTree(yml_catalog_date)
    tree.write("/var/www/www-root/data/www/qeeb.ru/wa-data/yml/sample.xml", encoding="UTF-8", xml_declaration=True)


def main():
    while True:
        collect_data('https://nir-vanna.ru/catalog/')
        print('FILE HAS CREATED!')


if __name__ == '__main__':
    main()
