#!/opt/anaconda3/envs/data_engineer_nd/bin/python

from bs4 import BeautifulSoup
import csv
import json
import logging
import re
import requests
import sys
import warnings


warnings.filterwarnings('ignore')


API_KEY = "c6df1900baa34395a8bfd0db327a09b1"

proxy_host = 'proxy.crawlera.com'
proxy_port = '8011'
proxy_auth = f'{API_KEY}:'


proxies = {"https": f"https://{proxy_auth}@{proxy_host}:{proxy_port}/",
           "http": f"http://{proxy_auth}@{proxy_host}:{proxy_port}/"}


in_file = sys.argv[1]  # CSV: EC number,  url
out_file = sys.argv[2]  # JSON
log_file = sys.argv[3]  # LOG
offset = int(sys.argv[4])  # line to start at


logging.basicConfig(filename=log_file, level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def extract_soup(ec_num, soup, line_num, json_file):
    try:
        about = soup.find('div', id=re.compile(r'AboutSubstance'))
        headers = about.find_all('a', href=re.compile(r'collapse'))
        content = about.find_all('div', id=re.compile(r'collapse'))
    except AttributeError as e:
        logging.debug(f'line {line_num}: AttributeError {e}')
    else:
        extract = {}
        for h, c in zip(headers, content):
            key = h.text.strip().lower()
            if 'precautionary' not in key:
                extract[key] = [p.text.strip() for p in c.find_all('p')]
        with open(json_file, 'a') as f:
            json.dump({ec_num: extract}, f, indent=2)


with open(in_file, 'r') as f:
    reader = csv.reader(f)
    for line_num, row in enumerate(reader):
        if line_num < offset:
            continue
        try:
            r = requests.get(row[1], proxies=proxies, verify=False)
        except requests.exceptions.HTTPError as e:
            logging.debug(f'line {line_num}: HTTPError {e}')
        else:
            soup = BeautifulSoup(r.content)
            try:
                fail = re.search(r'Your request failed', soup.div.text)
            except AttributeError as e:
                logging.debug(f'line {line_num}: AttributeError {e}')
            else:
                if fail:
                    logging.critical(f'line {line_num}: Website not responding')
                    break
                else:
                    extract_soup(row[0], soup, line_num, out_file)
