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


class OffWhite():
    """Checkout script for Off---White website EU based. Currently only does same ship / bill
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

        # User Configuration 
        self.profile(info=info)
        self.webhook = hook
        if 'discord.com' in self.webhook:
            self.webhook = str(self.webhook).replace('discord.com', 'discordapp.com')
        
        # set the logging as well as check the checkout start time
        timeadd = datetime.datetime.now(tzlocal()).strftime('%p %Z')
        logging.basicConfig(format=f'[%(asctime)s.%(msecs)03d {timeadd}] [%(threadName)s] [{self.userInfo["profile"]}] [%(levelname)s] - > %(message)s', level=logging.INFO, datefmt=f'%I:%M:%S')
        
        # set the cloudscraper sesssion as well as mount the adapter to deal with site crash
        self.session = cloudscraper.create_scraper(
            captcha={'provider':'2captcha', 'api_key':captcha},
            browser={'browser':'chrome', 'desktop':True, 'platform':'windows'},
            interpreter='nodejs'
        )

        # set the url link and grab the Product ID (fix this to make it more dynamic for user)
        if 'http' in url.lower() or '.com' in url.lower():
            self.url = url
            self.prodID = str(url)[-8:]
            logging.info(Fore.CYAN + f'Detected User Input: {url} (URL)')

        elif len(url) < 9: # if user input something less than 9 its likely a pid
            self.prodID = url
            self.url = f'https://www.off---white.com/en-gb/shopping/-item-{url}'
            logging.info(Fore.CYAN +  f'Detected User Input: {url} (PID)')
    
    def profile(self, info):
        '''Formats user's profile for use in checking out.
        Formats Total Tasks for that profile as well as billing / shipping address. 
        Also properly grabs and returns a proxy to the Instance.'''
        # perhaps add try / except blocks here in case user doesnt specify all info
        self.userInfo = dict()
        self.TotalTasks = info['total']
        self.userInfo['profile'] = info['profile'] # profile name
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

        # importing in proxies | Check if windows or not as paths from Windows needs adjustment
        if platform.system().lower() == 'windows':
            self.proxies = self.get_proxy(info['proxies'].replace("/","\\"))
        else:
            self.proxies = self.get_proxy(info['proxies'])

    def get_proxy(self, path: str):
        '''Returns a proxy to user if one is specified in json file
        Parameters
        ----------
        - Path: Directory path where the proxies are located, should be a .txt file'''
        try:
            if path != None:
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
            else:
                dict = None
        except Exception:
            dict = None
            logging.info(Fore.CYAN + 'Using localhost as proxy')

        return dict

    def getAPI(self):
        '''Makes a get request to the Off White API which returns id's / slugs neccesary for carting products'''
        # set the proper headers to make a successful request
        self.session.headers['Accept'] = 'application/json, text/plain, */*'
        self.session.headers['Accept-Encoding'] = 'gzip'
        self.session.headers['Accept-Language'] = 'en-GB'
        self.session.headers['x-newrelic-id'] = 'VQUCV1ZUGwIFVlBRDgcA'
        self.session.headers['ff-country'] = 'GB'
        self.session.headers['ff-currency'] = 'GBP'
        self.session.headers['sec-fetch-dest'] = 'empty'
        self.session.headers['sec-fetch-mode'] = 'cors'
        self.session.headers['sec-fetch-site'] = 'same-origin'

        # Repeated request if unsuccessful
        success = False
        while not success:
            try:
                meURL = 'https://www.off---white.com/api/legacy/v1/users/me'
                slugs = self.session.get(meURL, proxies=self.proxies)
                slugs.raise_for_status()
                self.bagid = slugs.json().get('bagId')
                success = True
                logging.info(Fore.CYAN + f"Grabbed the ID's from the API URL. Response: {slugs.status_code}")
                break
            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + f'Error: Request was unsuccesfull {slugs.status_code} Retrying...')

                # check if that proxy / session is banned.
                # if slugs.status_code == 403:
                #     logging.info(Fore.RED + 'Task is banned. Retrying soon') # fix this to restart the whole process
                #     break
                continue
            except ValueError:
                logging.error(Fore.RED + 'Error: Invalid JSON response. Retrying...')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.LIGHTRED_EX + 'Error: Request timeout. Retrying')
                continue
            except Exception as e:
                logging.error(Fore.RED + 'Fatal Error: Uncaught Exception')
                logging.error(Fore.RED + f'{e}')
        
    def createSession(self):
        '''Creates a valid session for Off White. Grabs requests to Product Page & makes API call neccessary for Adding to Cart'''
        # Add the proper request headers so requests are successful
        logging.info(Fore.CYAN + 'Creating session')
        self.session.headers['Accept-Language'] = 'en-US,en;q=0.9'
        self.session.headers['Accept-Encoding'] = 'gzip'
        self.session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        self.session.headers['sec-fetch-dest'] = 'document'
        self.session.headers['sec-fetch-mode'] = 'navigate'
        self.session.headers['sec-fetch-site'] = 'none'
        self.session.headers['sec-fetch-user'] = '?1'
        self.session.headers['upgrade-insecure-requests'] = '1'
        self.session.headers['authority'] = 'www.off---white.com'
        self.session.headers['cache-control'] = 'max-age=0'
        # self.session.headers['cookie'] = 'ss=a; _cfruid=a'
        cookieDict = {'ss':'a', '_cfruid':'a'}
        # self.session.headers['Connection'] = 'keep-alive'
        # print(self.session.headers)
        # time.sleep(30)

        # self.session.get(self.url, proxies=self.proxies)

        # grab the product page
        success = False
        while not success:
            try:
                self.start = time.time()
                prodPage = self.session.get(self.url, proxies=self.proxies)
                print(prodPage)
                print(prodPage.headers, '\n')
                print(prodPage.request.headers)
                time.sleep(30)
                prodPage.raise_for_status()
                success = True
                break
            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + f'Error: ProdPage Request was unsuccesfull {prodPage.status_code} Retrying...')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.LIGHTRED_EX + 'Error: ProdPage Request timeout. Retrying')
            except Exception as e:
                logging.error(Fore.RED + 'Fatal Error: Uncaught Exception')
                logging.error(Fore.RED + f'{e}')

        # make a request to login URL. Currently what is holding script together, perhaps look for alternative methods
        guest = False
        while not guest:
            try:
                self.start = time.time()
                guestCheckout = self.session.get('https://www.off---white.com/en-gb/account/login?returnurl=%2Faccount%2F', proxies=self.proxies)
                guestCheckout.raise_for_status()
                guest = True
                break
            except requests.exceptions.HTTPError:
                logging.error(Fore.RED + f'Error: Guest Checkout request was unsuccesfull {guestCheckout.status_code} Retrying...')
                continue
            except requests.exceptions.Timeout:
                logging.error(Fore.LIGHTRED_EX + 'Error: Request timeout. Retrying...')
            except Exception as e:
                logging.error(Fore.RED + 'Fatal Error: Uncaught Exception')
                logging.error(Fore.RED + f'{e}')

        # make API call & have the badID returned
        self.getAPI()
        print(self.bagid)
        logging.info(Fore.GREEN + 'Session Created. Fetching Prod Info.')



    def main(self):
        # create the session
        pass


if __name__ == "__main__":
    config_file = '/Users/junior/Library/Mobile Documents/com~apple~CloudDocs/Personal Works/Python/Github/off-white-master/config.json'
    json_file = open(config_file, 'r', encoding='utf-8')
    info = json.load(json_file)
    json_file.close()
    link = 'https://www.off---white.com/en-gb/shopping/-item-15280719'
    task = OffWhite(url=link, info=info['profiles'][1], hook=info['webhook'], captcha=info['captcha'])
    task.createSession()