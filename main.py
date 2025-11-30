import argparse
import time
import re
import pandas as pd
import os
from playwright.sync_api import sync_playwright

def load_existing_results(filename):
    """Load existing results to avoid duplicates"""
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            return set(df['NAME'].tolist())
        except:
            return set()
    return set()

def scrape_google_maps(search_term, total_needed, existing_names=None):
    """Scrape Google Maps for a single search term"""
    if existing_names is None:
        existing_names = set()
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print(f"\n{'='*60}")
        print(f"Searching for: {search_term}")
        print(f"Target: {total_needed} results")
        print(f"Already scraped: {len(existing_names)} items")
        print(f"{'='*60}\n")
        
        try:
            page.goto("https://www.google.com/maps", timeout=60000)
            
            # Wait for input and type search term
            page.wait_for_selector("input#searchboxinput")
            page.fill("input#searchboxinput", search_term)
            page.keyboard.press("Enter")
            
            # Wait for results to load
            page.wait_for_selector('div[role="feed"]', timeout=10000)
            
            previously_counted = 0
            scroll_attempts = 0
            max_scroll_attempts = 50  # Prevent infinite scrolling
            
            while len(results) < total_needed and scroll_attempts < max_scroll_attempts:
                # Scroll the feed
                page.hover('div[role="feed"]')
                page.mouse.wheel(0, 5000)
                time.sleep(2)  # Wait for load
                
                # Extract elements
                listings = page.locator('div[role="article"]').all()
                
                # Process new listings
                for listing in listings:
                    if len(results) >= total_needed:
                        break
                        
                    try:
                        # Extract name
                        aria_label = listing.get_attribute("aria-label")
                        if not aria_label:
                            continue
                            
                        # Skip if already scraped (in current session or previous runs)
                        if aria_label in existing_names or any(r['NAME'] == aria_label for r in results):
                            continue
                        
                        print(f"Processing: {aria_label}")
                        
                        # Click to get details
                        listing.click()
                        time.sleep(2) # Wait for details panel to load
                        
                        # Extract details
                        contact_no = "N/A"
                        website = "No"
                        gmail = "N/A"
                        location = "N/A"
                        whatsapp = "N/A"
                        
                        # 1. Contact No
                        try:
                            phone_btn = page.locator('button[data-item-id^="phone:"]')
                            if phone_btn.count() > 0:
                                raw_phone = phone_btn.first.get_attribute("aria-label")
                                contact_no = "".join(c for c in raw_phone if c.isdigit() or c in "+- ")
                                contact_no = contact_no.strip()
                        except:
                            pass

                        # 2. Website
                        try:
                            website_btn = page.locator('a[data-item-id="authority"]')
                            if website_btn.count() > 0:
                                website = "Yes"
                        except:
                            pass
                            
                        # 3. Location (Address)
                        try:
                            address_btn = page.locator('button[data-item-id="address"]')
                            if address_btn.count() > 0:
                                raw_location = address_btn.first.get_attribute("aria-label")
                                # Remove "Address: " or localized equivalents
                                location = re.sub(r'^[^:]+:\s*', '', raw_location).strip()
                                # Ensure proper UTF-8 encoding
                                location = location.encode('utf-8', errors='ignore').decode('utf-8')
                        except:
                            pass
                            
                        # 4. Gmail
                        try:
                            details_text = page.locator('div[role="main"]').inner_text()
                            
                            # Gmail
                            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', details_text)
                            if email_match:
                                gmail = email_match.group(0)
                                
                            # WhatsApp - check if mentioned in text
                            if "whatsapp" in details_text.lower():
                                whatsapp = "Yes (Found in text)"
                                     
                        except:
                            pass
                        
                        # 5. WhatsApp detection from phone number
                        if contact_no != "N/A" and whatsapp == "N/A":
                            clean_number = contact_no.replace(" ", "").replace("-", "")
                            if (clean_number.startswith("98") or clean_number.startswith("97") or 
                                clean_number.startswith("+97798") or clean_number.startswith("+97797")):
                                whatsapp = contact_no
                            
                        data = {
                            "NAME": aria_label,
                            "CONTACT NO": contact_no,
                            "GMAIL": gmail,
                            "WEBSITE": website,
                            "LOCATION": location,
                            "WHATSAPP": whatsapp
                        }
                        results.append(data)
                        existing_names.add(aria_label)  # Add to existing to avoid duplicates
                        print(f"✓ Collected: {aria_label} ({len(results)}/{total_needed})")
                        
                    except Exception as e:
                        print(f"✗ Error processing: {e}")
                        continue
                
                if len(results) == previously_counted:
                    scroll_attempts += 1
                    print(f"No new results after scroll (attempt {scroll_attempts}/{max_scroll_attempts})")
                else:
                    scroll_attempts = 0  # Reset if we found new results
                
                previously_counted = len(results)
        
        except Exception as e:
            print(f"Error searching for '{search_term}': {e}")
        
        finally:
            browser.close()
        
        return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Google Maps")
    parser.add_argument("-s", "--search", required=True, type=str, help="Comma-separated search terms (e.g. 'cafe, gym')")
    parser.add_argument("-t", "--total", required=True, type=int, help="Total results needed PER KEYWORD")
    
    args = parser.parse_args()
    
    search_terms = [s.strip() for s in args.search.split(',')]
    
    print(f"\n{'#'*60}")
    print(f"# Google Maps Scraper")
    print(f"# Keywords: {len(search_terms)}")
    print(f"# Target per keyword: {args.total}")
    print(f"{'#'*60}\n")
    
    for search_term in search_terms:
        # Create filename for this keyword
        safe_name = re.sub(r'[^\w\s-]', '', search_term).strip().replace(' ', '_')
        filename = f"results_{safe_name}.csv"
        
        # Load existing results
        existing_names = load_existing_results(filename)
        
        # Scrape
        data = scrape_google_maps(search_term, args.total, existing_names)
        
        # Save or append
        if data:
            if os.path.exists(filename):
                # Append to existing file
                existing_df = pd.read_csv(filename)
                new_df = pd.DataFrame(data)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"\n✓ Appended {len(data)} new results to {filename}")
                print(f"✓ Total results in file: {len(combined_df)}")
            else:
                # Create new file
                pd.DataFrame(data).to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"\n✓ Saved {len(data)} results to {filename}")
        else:
            print(f"\n✗ No new data found for '{search_term}'")
    
    print(f"\n{'#'*60}")
    print(f"# Scraping Complete!")
    print(f"{'#'*60}\n")
