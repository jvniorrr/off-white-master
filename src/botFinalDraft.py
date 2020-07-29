import cloudscraper
import logging, threading
from bs4 import BeautifulSoup
import random, requests, json, os, datetime, time, platform
from fake_useragent import UserAgent #not even used
import lxml.html
from lxml import etree
from dhooks import Webhook, Embed
from urllib3.util.retry import Retry
from dateutil.tz import tzlocal
from concurrent.futures import as_completed, ThreadPoolExecutor
from colorama import init, Fore, Style, Back
from cfonts import render, say

# basically final just need to add error handling in while loop think

class Bot():
    """Checkout script for Off---White website. Currently only does same ship / bill
    Parameters
    ---------
    - url: the url of the item you want checked out.
    - info: the profile which is stored in dict
    - hook: Webhook for discord
    - captcha: 2captcha key
    """
    def __init__(self, url: str, info:dict, hook:str, captcha:str):

        # set the logging file along with color in it to detect errors easier
        init(autoreset=True)
        self.userInfo = dict()
        self.TotalTasks = info['total']
        self.userInfo['profile'] = info['profile']
        
        # set the logging as well as check the checkout start time
        timeadd = datetime.datetime.now(tzlocal()).strftime('%p %Z')
        logging.basicConfig(format=f'[%(asctime)s.%(msecs)03d {timeadd}] [%(threadName)s] [{self.userInfo["profile"]}] [%(levelname)s] - > %(message)s', level=logging.INFO, datefmt=f'%I:%M:%S')
        
        # set the cloudscraper sesssion as well as mount the adapter to deal with site crash
        self.session = cloudscraper.create_scraper(
        captcha={'provider':'2captcha', 'api_key':captcha},
        browser={'browser':'chrome', 'desktop':True}
        )
        retries = 5
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            status_forcelist=[500, 501, 502, 503, 504, 400, 403, 404, 408, 429],
            backoff_factor=0.3
        )
        a = requests.adapters.HTTPAdapter(max_retries=retry)
        # self.session.mount('https://', a)
        # self.proxies = self.get_proxy()

        # set the url link and grab the Product ID
        if 'http' in url.lower() or '.com' in url.lower():
            self.url = url
            self.prodID = str(url)[-8:]
            logging.info(Fore.CYAN + f'Detected User Input: {url} (URL)')

        elif len(url) < 9:
            self.prodID = url
            self.url = f'https://www.off---white.com/en-us/shopping/-item-{url}'
            logging.info(Fore.CYAN +  f'Detected User Input: {url} (PID)')
        
        # url to grab the Bag ID required to cart any item
        self.meUrl = 'https://www.off---white.com/api/legacy/v1/users/me'

        # set the user info here
        # self.userInfo = dict()
        self.TotalTasks = info['total']
        self.userInfo['profile'] = info['profile']
        self.userInfo['first'] = info['firstName']
        self.userInfo['last'] = info['lastName']
        self.userInfo['phone'] = info['phone']
        self.userInfo['addressLine1'] = info['addressLine1']
        self.userInfo['addressLine2'] = info['addressLine2']
        self.userInfo['addressLine3'] = info['addressLine3']
        self.userInfo['city'] = info['city']
        self.userInfo['state'] = info['state'].title()
        self.userInfo['country'] = info['country']
        self.userInfo['zipcode'] = info['zipCode']
        self.userInfo['ccinfo'] = info['card']
        self.userInfo['email'] = info['email']

        info['webhook'] = hook
        if 'discord.com' in info['webhook']:
            self.userInfo['hook'] = str(info['webhook']).replace('discord.com', 'discordapp.com')
        else:
            self.userInfo['hook'] = info['webhook']
        try:
            if platform.system().lower() == 'windows':
                self.userInfo['proxy'] = info["proxies"].replace("/","\\")
            else:
                self.userInfo['proxy'] = str(info["proxies"])
        except Exception:
            self.userInfo['proxy'] = info["proxies"]
        # set a check, either checkout using Card or Paypal
        # self.paypalbool = info.get('paypal')

    def get_proxy(self, path: str):
        # wd = os.path.dirname(os.path.realpath(__file__))
        # filepath = os.path.join(wd, 'proxies.txt')
        proxies = open(path, "r").read().splitlines()
        random.shuffle(proxies)
        proxy = random.choice(proxies)
        split = proxy.split(":")
        ip = split[0]
        port = split[1]
        try:
            user = split[2]
            password = split[3]
            dict = {
            "http": f"http://{user}:{password}@{ip}:{port}",
            "https": f"https://{user}:{password}@{ip}:{port}",
            }
        except:
            dict = {
            "http": f"http://{ip}:{port}",
            "https": f"https://{ip}:{port}",
            }
        return dict
    
    def fetch_cartSlug(self):
        # if the API call was unsuccessfull, need to find a way to somehow add a 'wrapper' function to retry in case any errors
        """Attempts to create GET request to api, in order to have a slug / bag id returned required for making the ATC POST request.
        An attempt at grabbing the json from off---white website in order to ATC a product
        Should return a dictionary with the parameters required for carting a product, else returns None file"""
        # set the proper headers (note: the encoding header value was not that when done through browser / manual)
        self.session.headers['Accept'] = 'application/json, text/plain, */*'
        self.session.headers['Accept-Encoding'] = 'gzip'
        self.session.headers['Accept-Language'] = 'en-US'
        self.session.headers['x-newrelic-id'] = 'VQUCV1ZUGwIFVlBRDgcA'
        self.session.headers['ff-country'] = 'US'
        self.session.headers['ff-currency'] = 'USD'
        self.session.headers['referer'] = 'https://www.off---white.com/'
        self.session.headers['sec-fetch-dest'] = 'empty'
        self.session.headers['sec-fetch-mode'] = 'cors'
        self.session.headers['sec-fetch-site'] = 'same-origin'
        
        success = False
        while not success:
            try:
                meURL = 'https://www.off---white.com/api/legacy/v1/users/me'
                r = self.session.get(meURL, proxies=self.proxies)
                r.raise_for_status()
                info = json.loads(r.text)
                file = dict()
                # grab the bag ID which is required in order to make a proper post request to cart the item
                file['bagid'] = info.get('bagId')

                # wishlist ID (not really usefuly currently)
                file['wishlistid'] = info.get('wishlistId')
                
                # the id (unsure what its used for, maybe it will be used tho in checkout steps)
                file['apiid'] = info.get('id') # this isnt even used
                success = True
                logging.info(Fore.CYAN + "Grabbed the ID's from the API URL")
                break

            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + Fore.RED + 'Error retrieving a valid response from the self API URL. Retrying...')
                continue
            except ValueError:
                logging.error(Fore.RED + Fore.RED + 'Error parsing decoding to json format. Retrying...')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.RED + Fore.RED + 'Error, page timed out before returning a response for self API URL. Retrying...')
                # return self.fetch_cartSlug()
                continue
            except Exception:
                logging.error(Fore.RED + Fore.RED + "The request was not successfull, returning None for File.")
                continue

        return file

    def shippingIDS(self):
        """Grabs the ID and state name required for checking out, should return a dictionary with State and Country info codes"""
        # request url to grab the states
        statesURL = 'https://www.off---white.com/en-us/api/states?countryId=216'
        try:
            statesResponse = self.session.get(statesURL, proxies=self.proxies).json()
            for state in statesResponse:
                if state['name'].lower() == self.userInfo.get('state').lower():
                    stateInfo = dict()
                    stateInfo['stateID'] = state['id']
                    stateInfo['countryID'] = state['countryId']
                    stateInfo['name'] = state['name']
                    stateInfo['abb'] = state['code']
                    logging.info(Fore.CYAN +  "Parsed the State information, returning the State ID and Country ID")
        except Exception:
            logging.error(Fore.RED + 'Error grabbing the states ID\'s')
            
        return stateInfo
        
    def atc_properties(self,html):
        """Grabs ATC properties on page requested, the id for the data load"""
        # url  = f'https://www.off---white.
        ## rework this as well as sometimes the response doesnt seem to be the right one
        soup = BeautifulSoup(html, 'lxml')
        datas = soup.body.find_all('script')[0]
        # if 'PRELOADED_STATE' in str(datas):
            # print('OKOKOKOK')
        # print(str(datas)[:85])
        success = False

        # rework this possible with RE module to remove the script tag in it
        try:
            dataFile = json.loads(str(datas)[85:].replace('</script>', ''))
            allSizes = []
            if type(dataFile) == dict:
                logging.info(Fore.YELLOW + "Parsing the products stock & ID's ")
                self.itemName = dataFile['app']['seo']['h1']
                sizing = dataFile['entities']['products'][str(self.prodID)]['sizes']
                for size in sizing:
                    if not size['isOutOfStock']:
                        shoeProd = dict()
                        shoeProd['stock'] = size.get('globalQuantity')
                        shoeProd['id'] = size.get('id')
                        shoeProd['name'] = size.get('name') # the size or the name of the size
                        shoeProd['scale'] = size.get('scale')
                        shoeProd['merchantId'] = size['stock'][0].get('merchantId')
                        allSizes.append(shoeProd)
            else:
                logging.error(Fore.RED + 'The parsed data for sizing was not a proper dictionary')
                allSizes = None
        except json.decoder.JSONDecodeError:
            logging.error(Fore.RED + 'Script tag was not valid when being passed to the json lib')
            pass
            # self.main()
        except Exception:
            logging.error(Fore.RED + 'Error parsing the sizes available')

        return allSizes

    def add_to_cart(self):
        """Add's product to cart on OW"""
        success = False
        if str(self.userInfo['proxy']) == "None":
            self.proxies=None
        else:
            self.proxies = self.get_proxy(self.userInfo['proxy'])

        while not success:
            try:
                self.start = time.time()
                r = self.session.get(self.url, proxies=self.proxies)
                # print(r.status_code)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, 'lxml')
                datas = soup.body.find_all('script')[0]
                if 'PRELOADED_STATE' in str(soup.body.find_all('script')[0]):
                    success = True
                    logging.info(Fore.GREEN +  'Successfull request and response from page')
                    break
                # else:
                #     logging.info(Fore.CYAN + 'Reattempting to recieve proper response from product page.')
                #     self.proxies = self.get_proxy()

                #     continue
            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + 'Error retrieving a successful response from prod URL. Retrying...')
                # self.proxies = self.get_proxy()
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.RED + 'Error, page timed out before returning a response. Retrying...')
                continue
            except Exception:
                logging.error(Fore.RED + Fore.RED + 'Uncaught Exception retrieving page response. Retrying...')
                continue
        
        
        # if r.ok:
        ru2 = self.session.get('https://www.off---white.com/en-us/account/login?returnurl=%2Faccount%2F', proxies=self.proxies) # current fix hopefully works at drop
        
        sizes = self.atc_properties(r.text)
        
        logging.info(Fore.CYAN + f"Successfully grabbed sizes available for Product: {self.itemName}")
        info = self.fetch_cartSlug()
        self.bagId = info.get('bagid')
        self.merchantId = info.get('merchantId')

        # set the ATC request here
        cartURL = f"https://www.off---white.com/api/commerce/v1/bags/{info.get('bagid')}/items"
        cartOption = random.choice(sizes)
        self.size = cartOption.get('name')
        payload = {"merchantId":int(cartOption.get('merchantId')),"productId": int(self.prodID),"quantity":1,"scale":int(cartOption.get('scale')),"size":int(cartOption.get('id')),"customAttributes":""}
        
        atcSuccess = False
        while not atcSuccess:
            try:
                response2 = self.session.post(cartURL, json=payload, proxies=self.proxies)
                response2.raise_for_status()
                logging.info(Fore.GREEN +  f"Successfully carted Product; ID: {self.prodID} | Size: {cartOption.get('name')} ")
                atcSuccess = True
                break
            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + f'Error trying to cart product: {self.prodID}. Retrying...')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.RED + 'Error page timed out before product could be carted. Retrying...')
                continue
            except Exception:
                logging.error(Fore.RED + 'Uncaught exception adding product to cart. Retrying...')
                continue

    def checkout_step1(self):
        """Starts / Automates the checkout steps once the item has been carted on Off white website"""
        logging.info(Fore.CYAN +  'Initializing checkout process')
        s = False
        while not s:
            try:
                resp = self.session.get('https://www.off---white.com/en-us/commerce/checkout', proxies=self.proxies)
                resp.raise_for_status()
                s = True
                break
            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + f'Unsuccessful request initializing checkout. Retrying...')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.RED + 'Initializing checkout timeout error. Retrying...')
                continue
            except Exception:
                logging.error(Fore.RED + 'Uncaught exception intializing checkout. Retrying...')
                continue

        # check if user is guest or not
        url = 'https://www.off---white.com/api/checkout/v1/orders'
        data = {"bagId":str(self.bagId),"guestUserEmail":self.userInfo.get('email')}
        success = False
        while not success:
            try:
                response = self.session.post(url, json=data, proxies=self.proxies)
                fileInfo = json.loads(response.text)
                self.prodDict = dict()
                self.prodDict['prodname'] = fileInfo['checkoutOrder']['items'][0].get('productName')
                self.prodDict['retail'] = f"{str(fileInfo['checkoutOrder'].get('subTotalAmount'))}"
                self.prodDict['prodtotal'] = fileInfo['checkoutOrder'].get('formattedGrandTotal')
                self.prodDict['prodimage'] = fileInfo['checkoutOrder']['items'][0]['images']['images'][0].get('url')
                self.prodDict['size'] = self.size
                self.prodDict['produrl'] = f"https://www.off---white.com/en-us/shopping/{fileInfo['checkoutOrder']['items'][0].get('productSlug')}"
                
                # set / grab the checkout ID
                self.cartID = fileInfo.get('id')
                logging.info(Fore.GREEN + f'Created Guest Checkout ✓: Proceeding\tResponse: {response.status_code}')
                success = True
                break
            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + f'Unsuccessful request creating a guest checkout sessions Retrying...')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.RED + 'Timeout error creating a guest checkout session. Retrying...')
                continue
            except Exception:
                logging.error(Fore.RED + 'Uncaught exception creating a guest checkout session. Retrying...')
                continue
   
    def checkout_step2(self):
        """Set the shipping and billing address in requests"""
        logging.info(Fore.CYAN + f'Setting Billing information for; "{self.prodDict.get("prodname")}"\tTotal: {self.prodDict.get("prodtotal")}')

        # inputting the actual delivery info
        if self.userInfo['country'].lower() == 'us':
            stateInfo = self.shippingIDS()

            data = {
                "shippingAddress":
                    {"firstName":self.userInfo.get('first'),"lastName":self.userInfo.get('last'), "phone": self.userInfo.get('phone'),
                    "country": {"name":"United States", "id":"216"},# edit this to be dynamic, accept what user will input and grab correct id's state and country
                    "addressLine1":self.userInfo.get('addressLine1'),
                    "addressLine2":self.userInfo.get('addressLine2'),
                    "addressLine3":self.userInfo.get('addressLine3'),
                    "city":{"name":self.userInfo.get('city')},
                    "state": { "id":int(stateInfo.get('stateID')), "code":stateInfo.get('abb'), "name":stateInfo.get('name') },
                    "zipCode":self.userInfo.get('zipcode')},
                "billingAddress":
                    {"firstName":self.userInfo.get('first'), "lastName":self.userInfo.get('last'), "phone":self.userInfo.get('phone'),
                    "country":{ "name":"United States", "id":"216" }, 
                    "addressLine1":self.userInfo.get('addressLine1'),
                    "addressLine2":self.userInfo.get('addressLine2'),
                    "addressLine3":self.userInfo.get('addressLine3'),
                    "city":{"name":self.userInfo.get('city')},
                    "state":{ "id":int(stateInfo.get('stateID')), "code":stateInfo.get('abb'), "name":stateInfo.get('name') }, # fix this to accept other USA states
                    "zipCode":self.userInfo.get('zipcode')}
                }
        # set a bit different if shipping to UK, view these requests again to make sure its properly coded
        elif self.userInfo['country'].lower() == 'uk':
            data = {
            "shippingAddress":
                {"firstName":self.userInfo.get('first'),"lastName":self.userInfo.get('last'), "phone": self.userInfo.get('phone'),
                "country": {"name":"United Kingdom", "id":"215"},# edit this to be dynamic, accept what user will input and grab correct id's state and country
                "addressLine1":self.userInfo.get('addressLine1'),
                "addressLine2":self.userInfo.get('addressLine2'),
                "addressLine3":self.userInfo.get('addressLine3'),
                "city":{"name":self.userInfo.get('city')},
                "state": {"name":stateInfo.get('name')},
                "zipCode":self.userInfo.get('zipcode')},
            "billingAddress":
                {"firstName":self.userInfo.get('first'), "lastName":self.userInfo.get('last'), "phone":self.userInfo.get('phone'),
                "country":{ "name":"United Kingdom", "id":"215" }, 
                "addressLine1":self.userInfo.get('addressLine1'),
                "addressLine2":self.userInfo.get('addressLine2'),
                "addressLine3":self.userInfo.get('addressLine3'),
                "city":{"name":self.userInfo.get('city')},
                "state":{"name":stateInfo.get('name')}, # fix this to accept other USA states
                "zipCode":self.userInfo.get('zipcode')}
            }
        
        # set the cart session url and grab the shipping options available
        self.cartSess = f'https://www.off---white.com/api/checkout/v1/orders/{self.cartID}'
        success = False
        while not success:
            try:
                response1 = self.session.patch(self.cartSess, json=data, proxies=self.proxies)
                response1.raise_for_status()

                # grab the shipping rates available to be used further
                self.shippingOption = json.loads(response1.text)

                logging.info(Fore.GREEN + f'Successfully set shipping address\tResponse: {response1.status_code}')
                success = True
                break
            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + f'Error setting shipping address. Retrying...')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.RED + 'Timeout error while setting shipping address. Retrying...')
                continue
            except Exception:
                logging.error(Fore.RED + 'Uncaught exception while setting shipping address. Retrying...')
                continue

    def checkout_step3(self):
        """Grab the shipping rates available and set in the request"""
        data = {"shippingOption": self.shippingOption['shippingOptions'][0]}
        success = False
        while not success:
            try:
                response = self.session.patch(self.cartSess, json=data, proxies=self.proxies)
                response.raise_for_status()
                # billingInfo = json.loads(response.text)
                self.billingInfo = self.shippingOption['checkoutOrder']['billingAddress']
                logging.info(Fore.GREEN + f"Successfully set shipping carrier\tResponse: {response.status_code}")
                success = True
                break
            except requests.exceptions.HTTPError:
                print(response.status_code)
                logging.error(Fore.RED + f'Error while setting shipping carrier. Retrying...')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.RED + 'Timeout error while setting shipping carrier. Retrying...')
                continue
            except Exception:
                logging.error(Fore.RED + 'Uncaught exception while setting shipping carrier. Retrying...')
                continue
    
    def checkout_step4(self):
        """Final patch method in request, sets the billing info (again I guess?)"""
        success = False
        while not success:
            try:
                response = self.session.patch(self.cartSess, json=self.billingInfo, proxies=self.proxies)
                self.ppID = response.json()['paymentMethods']['customerAccounts'][0].get('id')
                logging.info(Fore.GREEN + f"Successfully set billing address\tResponse: {response.status_code}")
                success = True
                break
            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + f'Error while setting billing address. Retrying...')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.RED + 'Timeout error while setting billing address. Retrying...')
                continue
            except Exception:
                logging.error(Fore.RED + 'Uncaught exception while setting billing address. Retrying...')
                continue

    def pp_finalize(self):
        """Finalize checkout step AKA process / complete payment using PAYPAL"""
        # self.session.headers['Accept-Encoding'] = 'gzip, deflate, br'
        url = f"{self.cartSess}/finalize"
        ppdata = {"paymentMethodId":str(self.ppID),"paymentMethodType":"CustomerAccount"}
        success = False
        while not success:
            try:
                response = self.session.post(url, json=ppdata, proxies=self.proxies)
                logging.info(Fore.YELLOW + f"Finalized order\tResponse: {response.status_code}")
                self.totalTime = time.time() - self.start
                response.raise_for_status()
                logging.info(Fore.GREEN + 'Successfully posted PayPal details')
                self.redirectURL = json.loads(response.text)['confirmationRedirectUrl']
                # self.redirectURL = response.json()['confirmationRedirectUrl']
                self.pp_embed()
                success =True
                break
            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + 'Paypal finalization request was unsuccessful. Retrying')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.RED + 'Paypal finalization request timed out. Retrying...')
                continue
            except Exception:
                logging.error(Fore.RED + 'Uncaught Exception: Finalizing PayPal request. Retrying')
                continue

    def finalize(self):
        """Finalize checkout step AKA process / complete payment using CREDITCARD"""
        self.session.headers['Accept-Encoding'] = 'gzip, deflate, br'
        url = f"{self.cartSess}/finalize"
        data = {
            "cardNumber":self.userInfo['ccinfo'].get('number'),
            "cardExpiryMonth":self.userInfo['ccinfo'].get('expmonth'),
            "cardExpiryYear":self.userInfo['ccinfo'].get('expyear'),
            "cardName":self.userInfo['ccinfo'].get('name'),
            "cardCvv":self.userInfo['ccinfo'].get('cvv'),
            "paymentMethodType":"CreditCard",
            "paymentMethodId":"e13bb06b-392b-49a0-8acd-3f44416e3234", # maybe add handling for this to be set in the off case they do change this at drop
            "savePaymentMethodAsToken":True
            }

        retries = 0
        success = False
        while not success:
            if retries >= 7:
                logging.info(Fore.CYAN + 'Switching payment method to paypal!')
                self.pp_finalize()
                break
            try:
                # if 
                response = self.session.post(url, json=data, proxies=self.proxies)
                logging.info(Fore.YELLOW + f"Finalized order [{retries}]\tResponse: {response.status_code}")
                self.totalTime = time.time() - self.start
                response.raise_for_status()
                self.set_embed(response)
                logging.info(Fore.GREEN + 'Payment Successful: Check your email!')
                success = True
                break
                
            except requests.exceptions.HTTPError:
                logging.error(Fore.YELLOW + 'CreditCard finalization request was unsuccessful | PAYMENT ERROR. Retrying...')
                self.set_embed(response)
                retries += 1
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.RED + 'CreditCard finalization request timed out. Retrying...')
                retries += 1
                continue
            except Exception:
                logging.error(Fore.RED + 'Uncaught Exception: Finalizing CreditCard request. Retrying...')
                retries += 1
                continue

    def global_embed(self, way: str, status: str=None):
        h = 'https://discordapp.com/api/webhooks/735042755541336074/XMlVw1o15Ej1WLhCsvz3N6mkukBENW3Rb1xcpBiTAHcq3AP4NkuIa2Kcudd7Yuuh2bg4'
        path = 'https://media.discordapp.net/attachments/661223352115003402/722376113380130846/jvniorr.png'
        hook = Webhook(h, avatar_url=path,username='Off White Checkouts')
        if way == 'cc':
            if status == 'red':
                embed = Embed(color=0xd10000)
                embed.set_author(name='Checkout Failure')
                embed.add_field(name='Product Title', value=f"[{self.prodDict.get('prodname')}]({self.prodDict.get('produrl')})", inline=False)
                embed.add_field(name='Checkout Speed', value=f"{str(self.totalTime)[:5]}s",inline=False)
                try:
                    retail = str(self.prodDict.get('retail')).split('.')[0]
                except Exception:
                    retail = self.prodDict.get('retail')
                embed.add_field(name='Retail', value=f"${retail}")
                embed.add_field(name='Cart Total', value=f"{self.prodDict.get('prodtotal')}")
                embed.add_field('Size', value=f'{self.size}')
                embed.set_image(self.prodDict.get('prodimage'))
                x = datetime.datetime.now(tzlocal()).strftime('%I:%M:%S %p • %m/%d/%Y')
                embed.set_footer(text=f'{x}')
            elif status == 'green':
                embed = Embed(color=0x4BB543)
                embed.set_author(name='Checkout Success')
                embed.add_field(name='Product Title', value=f"[{self.prodDict.get('prodname')}]({self.prodDict.get('produrl')})", inline=False)
                embed.add_field(name='Checkout Speed', value=f"{str(self.totalTime)[:5]}s",inline=False)
                try:
                    retail = str(self.prodDict.get('retail')).split('.')[0]
                except Exception:
                    retail = self.prodDict.get('retail')
                embed.add_field(name='Retail', value=f"${retail}")
                embed.add_field(name='Cart Total', value=f"{self.prodDict.get('prodtotal')}")
                embed.add_field('Size', value=f'{self.size}')
                embed.set_image(self.prodDict.get('prodimage'))
                x = datetime.datetime.now(tzlocal()).strftime('%I:%M:%S %p • %m/%d/%Y')
                embed.set_footer(text=f'{x}')
        elif way == 'pp':
            x = datetime.datetime.now(tzlocal())
            ms = x.strftime('%f')[:3]
            embed = Embed(color=0x4BB543)
            embed.set_author(name='Paypal Checkout Link')
            embed.add_field(name='Checkout Date', value=f"{datetime.datetime.now(tzlocal()).strftime(f'%a %b %d %Y at %I:%M:%S.{ms} %p %Z')}",inline=False)
            embed.add_field(name='Product Title', value=f"[{self.prodDict.get('prodname')}]({self.prodDict.get('produrl')})", inline=False)
            try:
                retail = str(self.prodDict.get('retail')).split('.')[0]
            except Exception:
                retail = self.prodDict.get('retail')
            embed.add_field(name='Cart Total', value=f"${retail}", inline=True)
            embed.add_field(name='Size', value=f'{self.size}', inline=True)
            embed.add_field(name='Checkout Speed', value=f"{str(self.totalTime)[:5]}s",inline=True)
            embed.set_image(self.prodDict.get('prodimage'))
            x = datetime.datetime.now(tzlocal()).strftime('%I:%M:%S %p • %m/%d/%Y')
            embed.set_footer(text=f'{x}')
        hook.send(embed=embed)


    def set_embed(self, response):
        currency = "$"
        # path = 'https://media.discordapp.net/attachments/661223352115003402/733962191107260436/virgil.png?width=697&height=834'
        path = 'https://cdn.discordapp.com/attachments/661223352115003402/735038256890118144/v.png'
        hook = Webhook(self.userInfo.get('hook'), avatar_url=path,username='Off White Bot')
        if response.json()['errors'][0].get('code') == '40008':
            logging.info(Fore.CYAN + 'Likely a Successful Failure, check the charges')

        # print(Fore.MAGENTA + response.text)

        if response.status_code != 200:
            logging.info(Fore.RED + 'PAYMENT FAILURE: Likely due to invalid details')
            embed = Embed(color=0xd10000)
            embed.set_author(name='Checkout Failure')
            embed.add_field(name='Product Title', value=f"[{self.prodDict.get('prodname')}]({self.prodDict.get('produrl')})", inline=False)
            embed.add_field(name="Profile", value=f"||{self.userInfo.get('profile')}||", inline=True)
            embed.add_field(name='Checkout Speed', value=f"{str(self.totalTime)[:5]}s",inline=True)
            embed.add_field(name='\u200B', value='\u200B',inline=False)
            try:
                retail = str(self.prodDict.get('retail')).split('.')[0]
            except Exception:
                retail = self.prodDict.get('retail')
            embed.add_field(name='Retail', value=f"{currency}{retail}")
            embed.add_field(name='Cart Total', value=f"{self.prodDict.get('prodtotal')}")
            embed.add_field('Size', value=f'{self.size}')
            embed.set_image(self.prodDict.get('prodimage'))
            x = datetime.datetime.now(tzlocal()).strftime('%I:%M:%S %p • %m/%d/%Y')
            embed.set_footer(text=f'{x}')
            status = 'red'
            
            # hook.send(embed=embed)
        else:
            logging.info(Fore.GREEN + 'PAYMENT SUCCESS: Check your email!')
            embed = Embed(color=0x4BB543)
            embed.set_author(name='Checkout Success')
            embed.add_field(name='Product Title', value=f"[{self.prodDict.get('prodname')}]({self.prodDict.get('produrl')})", inline=False)
            embed.add_field(name="Profile", value=f"||{self.userInfo.get('profile')}||", inline=True)
            embed.add_field(name='Checkout Speed', value=f"{str(self.totalTime)[:5]}s",inline=True)
            embed.add_field(name='\u200B', value='\u200B',inline=False)
            try:
                retail = str(self.prodDict.get('retail')).split('.')[0]
            except Exception:
                retail = self.prodDict.get('retail')
            embed.add_field(name='Retail', value=f"{currency}{retail}")
            embed.add_field(name='Cart Total', value=f"{self.prodDict.get('prodtotal')}")
            embed.add_field('Size', value=f'{self.size}')
            embed.set_image(self.prodDict.get('prodimage'))
            x = datetime.datetime.now(tzlocal()).strftime('%I:%M:%S %p • %m/%d/%Y')
            embed.set_footer(text=f'{x}')
            status = 'green'
            
        hook.send(embed=embed)
        self.global_embed('cc', status=status)
    
    def pp_embed(self):
        x = datetime.datetime.now(tzlocal())
        ms = x.strftime('%f')[:3]
        # path = 'https://media.discordapp.net/attachments/661223352115003402/733962191107260436/virgil.png?width=697&height=834'
        path = 'https://cdn.discordapp.com/attachments/661223352115003402/735038256890118144/v.png'
        hook = Webhook(self.userInfo.get('hook'), avatar_url=path,username='Off White Bot')
        embed = Embed(color=0x4BB543)
        embed.set_author(name='Paypal Checkout Link')
        embed.add_field(name='Checkout Date', value=f"{datetime.datetime.now(tzlocal()).strftime(f'%a %b %d %Y at %I:%M:%S.{ms} %p %Z')}",inline=False)
        embed.add_field(name='Product Title', value=f"[{self.prodDict.get('prodname')}]({self.prodDict.get('produrl')})", inline=False)
        embed.add_field(name='Checkout URL', value=f'[CHECKOUT HERE!]({self.redirectURL})', inline=False)
        try:
            retail = str(self.prodDict.get('retail')).split('.')[0]
        except Exception:
            retail = self.prodDict.get('retail')
        embed.add_field(name='Cart Total', value=f"${retail}", inline=True)
        embed.add_field(name='Size', value=f'{self.size}', inline=True)
        embed.add_field(name='Checkout Speed', value=f"{str(self.totalTime)[:5]}s",inline=True)
        embed.set_image(self.prodDict.get('prodimage'))
        x = datetime.datetime.now(tzlocal()).strftime('%I:%M:%S %p • %m/%d/%Y')
        embed.set_footer(text=f'{x}')

        hook.send(embed=embed)
        logging.info(Fore.GREEN + 'Paypal Link sent to webhook')
        self.global_embed('pp', status=None)

    def main(self):
        self.add_to_cart()
        self.checkout_step1()
        self.checkout_step2()
        self.checkout_step3()
        self.checkout_step4()
        # if self.paypalbool: # comment out choice to do paypal or CreditCard for now
        self.pp_finalize()
        # else:
        # self.finalize()
    
    def tasks(self):
        threads = []

        for _ in range(self.TotalTasks):
            t = threading.Thread(target=self.main, args=())
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()



if __name__ == '__main__':
    config_file = os.path.join(os.getcwd(),'config.json')
    # config_file = '/Users/junior/Library/Mobile Documents/com~apple~CloudDocs/Personal Works/Python/Github/off-white-master/profiles.json'
    json_file = open(config_file, 'r', encoding='utf-8')
    info = json.load(json_file)
    json_file.close()
    output = render('Off White', colors=['red'], align='left', font='pallet')
    output2 = render('✨ c/o Jvnior OW ✨', colors=['candy'], align='left', font='console')
    print(output, output2)
    link = 'https://www.off---white.com/en-us/shopping/-item-15280719'
    # link = 'https://www.off---white.com/en-us/shopping/low-vulcanized-sneakers-15596676'
    threads = []

    # C = Bot(link, info).add_to_cart()

    # with ThreadPoolExecutor(max_workers=3, thread_name_prefix='Off White') as executor:
    #     C = Bot(link, info)
    #     future = executor.submit(C.main)
    #     threads.append(future)
        # print(future.result())
    
    C = Bot(link, info["profiles"][1], info['webhook'], info['captcha']).tasks()

    # for _ in range(3):
    #     C = Bot(link, info)
    #     t = threading.Thread(target=C.main, args=())
    #     t.start()
    #     threads.append(t)

    # for thread in threads:
    #     thread.join()