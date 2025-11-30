import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# 1. Enhanced Proxy Rotator Class with File Checking
class ProxyRotator:
    def __init__(self, proxy_file_path):
        # Check if file exists
        if not os.path.exists(proxy_file_path):
            raise FileNotFoundError(f"Proxy file not found at: {os.path.abspath(proxy_file_path)}")
        
        with open(proxy_file_path, 'r') as f:
            self.proxies = [line.strip() for line in f if line.strip()]
            
        if not self.proxies:
            raise ValueError("No proxies found in the file")
            
        self.current_index = 0
    
    def get_proxy(self):
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

# 2. Configuration
PROXY_FILE_PATH = 'proxies.txt'  # Same folder as script
OUTPUT_FILE = 'scraped_results.csv'

# 3. Create Browser with Error Handling
def create_browser(proxy_rotator):
    try:
        proxy = proxy_rotator.get_proxy()
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
            print(f"Using proxy: {proxy}")
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Browser creation failed: {str(e)}")
        return None

# 4. Main Scraping Function
def scrape_data():
    try:
        proxy_rotator = ProxyRotator(PROXY_FILE_PATH)
    except Exception as e:
        print(f"Proxy initialization failed: {str(e)}")
        print("Please create a 'proxies.txt' file with your proxies.")
        print("Example content:")
        print("http://123.123.123.123:8080")
        print("http://user:pass@111.111.111.111:3128")
        return []
    
    results = []
    
    for attempt in range(3):  # Try 3 times
        driver = None
        try:
            driver = create_browser(proxy_rotator)
            if not driver:
                continue
                
            query = 'site:linkedin.com/in "Founder" "Austin"'
            url = f"https://www.google.com/search?q={query}"
            
            driver.get(url)
            time.sleep(random.uniform(3, 7))
            
            if "captcha" in driver.page_source.lower():
                print("CAPTCHA detected! Rotating proxy...")
                continue
                
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            new_results = []
            
            for result in soup.select(".tF2Cxc"):
                try:
                    title = result.find("h3").text
                    link = result.find("a")["href"]
                    new_results.append({
                        "Name": title.split("-")[0].strip(),
                        "Profile": link,
                        "Proxy": proxy_rotator.proxies[proxy_rotator.current_index]
                    })
                except:
                    continue
            
            if new_results:
                results.extend(new_results)
                break
                
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
        finally:
            if driver:
                driver.quit()
            time.sleep(random.uniform(5, 10))
    
    return results

# 5. Run with clear instructions
if __name__ == "__main__":
    print("Starting scraping process...")
    print(f"Looking for proxies in: {os.path.abspath(PROXY_FILE_PATH)}")
    
    data = scrape_data()
    
    if data:
        pd.DataFrame(data).to_csv(OUTPUT_FILE, index=False)
        print(f"\nSuccess! Saved {len(data)} results to {OUTPUT_FILE}")
        print("Sample results:")
        print(pd.DataFrame(data).head())
    else:
        print("\nScraping failed. Possible solutions:")
        print("1. Create a proxies.txt file in the same folder")
        print("2. Check your internet connection")
        print("3. Try again later (Google might be blocking you)")