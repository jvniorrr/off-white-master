# OFF-WHITE
- ARCHIVED REPOSITORY
- Off white script, autocheckout tool. 
- This was once working and was able to purchase a pair of Off White Jordan 4's. Super proud of this work, and that it was functioning for it having been my first program and was automation using requests library. Supported threading for multiple tasks to be automated. Here for research / learning purposes only now. If you would like to learn of requests and automation heres a rough idea. Again not the best code as I was a novice (still am >.<) and did not understand the principles of software engineering. This should give you a general idea of how to automate checkout processes using requests. 
* Has support for Paypal Checkout currently & multiple profiles. 
* Test for Off white Jordan 4

## Table of Contents
* [Installation](#Installation)
* [Setup](#Setup)
* [To Do](#TO-DO-List)


# INSTALLATION
1. Install Python 3: <https://www.python.org/downloads/windows/> or <https://www.python.org/downloads/mac-osx/>
2. Open a CMD Prmpt window or a Terminal Window and run `python3` to make sure it's installed. If it runs fine and shows Python 3.x.x Then just put in cmd `quit()` to exit. Else look up error google it.
3. Once Python 3 is installed. change your directory in the cmd prmpt or terminal to where the unzipped file is. 
Win: `C:\Users\userName\Downloads\off-white` or `C:<Path>`
Mac: `cd /Users/userName/downloads/off-white` or `cd <path>`
4. When in that directory, try to run `pip3 install -r requirements.txt` if it doesn't work run ``pip install -r requirements.txt`
5. If it installs all correctly, will take a while probably. Then run `python3 main.py`

# Setup
* After having done Installation Steps follow the steps here. 
* Setting up Profiles
```json 
    {
    "profiles":[
        {
    "profile":"Profile Name",
    "firstName":"First",
    "lastName":"Last",
    "phone":"1234567890",
    "email": "email@email.com",
    "addressLine1":"123 main str",
    "addressLine2":"",
    "addressLine3":"",
    "city":"los angeles",
    "state":"California",
    "country":"US",
    "zipCode":"90012",
    "card": {
        "name":"cardholder Name",
        "number": "4242424242424242",
        "expyear":2023,
        "expmonth": 6,
        "cvv":"123"
    },
    "proxies":null, 
    "paypal":false,
    "total":1
        }
    ],
    "webhook":"DiscordWebhook",
    "captcha": "APIkey"
}
```
Proxies value should be `null` to use local host, or a direct path of the proxies.txt file to use. Paypal should be `true` or `false`. Webhook should be a string (surrounded in quotes) and itll send successfull webhook / failure. Captcha is your 2 captcha API key. just pass in there as a string.
* "proxies": "C:\Users\userName\Downloads\off-white\proxies.txt"
* "paypal" : true
* "total": Integer Value with total tasks for that profile
* "webhook": "discordWebhook" 
* "captcha": "2captcha API key" 
* To add another profile, just copy the default one, and add 1 comma at the end (after "}") of the dictionary / profile you had just copied. Would end up being `},`


## TO-DO List
| **Done** | **News** |
| -------- | -------- |
| ✅| Add retries to request if any errors arise  |
| ✅| Find a way to add better handling specifically for site crashes (Fixed think)  |
| ✅| Add threading for multiple profile use |
| ✅| Add a simple terminal based UI / menu |
| ✅| Add support for proxy groups  |
| ✅| Add support for localhost |
| ❌| Add time outs to requests so sessions wont be hanging forever |
| ❌| Add multi-processing / or asynchronous code  |
| ❌| Add proxy handling: dead proxies |
| ❌| Fix CC support ASAP!!! |
