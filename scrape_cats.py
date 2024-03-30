import pickle
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import gmtime, strftime

DESC_PATH = './desc.pkl' # path to iterable containing product names 
CAT_PATH = './categories.pkl' # path to output file
FIREFOX_WEBDRIVER_PATH = './geckodriver' # selenium webdriver executable
SITE = 'www.carrefour.es'
MAX_WAIT = 10 # max wait for pages/elements to laod

with open(DESC_PATH, 'rb') as f:
    products = pickle.load(f)

opts = webdriver.FirefoxOptions()
opts.headless = True

def get_driver(executable_path, options):
    return webdriver.Firefox(executable_path=FIREFOX_WEBDRIVER_PATH, options=opts)

driver = get_driver(FIREFOX_WEBDRIVER_PATH, opts)

categories = dict()
for i, product in enumerate(products):
    if (i + 1) % 100 == 0:
        driver.quit()
        driver = get_driver(FIREFOX_WEBDRIVER_PATH, opts)
    query = f'https://www.bing.com/search?q=site%3A{SITE}+{product.replace(" ", "+")}'
    driver.get(query)
    try:
        urls = WebDriverWait(driver, MAX_WAIT).until(
            EC.presence_of_element_located((By.ID, 'b_results'))
        ).find_elements_by_xpath("./*")
        if urls[0].get_attribute('class') == 'b_algo':
            try:
                urls = list(map(lambda x: x.find_element_by_xpath('.//h2/a').get_attribute('href'), filter(lambda x: x.get_attribute('class') == 'b_algo', urls)))
                print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tFound {len(urls)} URLs for product {i}, '{product}'.")
            except:
                print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tEncountered unexpected page structure.")
                continue
        else:
            print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tCouldn't find anything for product {i}, '{product}', at {query}.")
            continue
    except TimeoutException:
        print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tMAX_WAIT exceeded for product {i}, '{product}', at {query}.")
        continue 
    urls = list(filter(lambda x: (x != 'https://www.carrefour.es/') and ('www.bing.com/aclick' not in x) and ('www.microsofttranslator.com' not in x), urls))
    if len(urls) > 0:
        url = urls[0]
        try:
            assert url[0:len('http')] == 'http'
            assert 'carrefour.es' in url
        except AssertionError:
            print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tThe top link for product {i}, '{product}', is not a carrefour.es link.")
            continue
        try:
            driver.get(url)
        except WebDriverException:
            print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tReached error page for product {i}, '{product}', at {url}.")
            continue
        except TimeoutException:
            print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tMAX_WAIT exceeded for product {i}, '{product}', at {url}.")
            continue
        try:
            elem = WebDriverWait(driver, MAX_WAIT).until(
                EC.presence_of_all_elements_located((By.XPATH, "//script[contains(., 'dataLayer')]"))
            )
        except TimeoutException:
            print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tMAX_WAIT exceeded for loading dataLayer script for product {i}, '{product}', at {url}.")
            continue
        datalayer = driver.execute_script('return dataLayer')
        try:
            cats = datalayer[0]['pageCategoryTree'].replace('/nn', '').replace('nn', '').split('/')
            if cats == ['']:
                continue
            print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tFound {len(cats)} categories for product {i}, '{product}'.")
        except KeyError:
            print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tEncountered unexpected page structure.")
            continue
        categories[product] = cats
driver.quit()

with open(CAT_PATH, 'wb') as f:
    pickle.dump(search_results, f)