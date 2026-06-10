import os

os.makedirs("scraper_workspace", exist_ok=True)

config_code = """import os
import sys

def get_user_options():
    url = input("Enter the target URL to scrape: ").strip()
    
    print("\\nSelect data types / structural patterns to extract (separate multiple choices with commas):")
    print("1. Hyperlinks / Anchor Tags (href URLs)")
    print("2. Email Addresses")
    print("3. Tables / Structured Data Rows")
    print("4. Specific CSS Selectors / Class Names")
    choices = input("Enter choices (e.g., 1,2): ").strip().split(",")
    
    patterns = []
    if "1" in choices:
        patterns.append("links")
    if "2" in choices:
        patterns.append("emails")
    if "3" in choices:
        patterns.append("tables")
    if "4" in choices:
        patterns.append("custom")
        
    custom_selector = ""
    if "custom" in patterns:
        custom_selector = input("\\nEnter the specific CSS Selector or Class Name (e.g., .product-title): ").strip()
        
    try:
        delay = float(input("\\nEnter delay between actions in seconds (e.g., 30): "))
    except ValueError:
        delay = 0.0
        
    try:
        max_items = int(input("Enter how many pieces of data you want to extract per data type (e.g., 50): "))
    except ValueError:
        max_items = 999999
        
    output_dir = input("\\nEnter the file path location to save scraped data: ").strip()
    if not os.path.exists(output_dir):
        print(f"[ERROR] The specified path does not exist: {output_dir}")
        sys.exit(1)
        
    return {
        "url": url, 
        "patterns": patterns, 
        "custom_selector": custom_selector, 
        "delay": delay, 
        "max_items": max_items,
        "output_dir": output_dir
    }
"""

scraper_code = """import os
import time
import re
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

class ModularScraper:
    def __init__(self, config):
        self.config = config
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        self.driver = uc.Chrome(options=options)

    def execute(self):
        summary_report = {}
        try:
            self.driver.get(self.config["url"])
            time.sleep(max(5.0, self.config["delay"]))
            
            timestamp = int(time.time())
            limit = self.config["max_items"]
            
            if "links" in self.config["patterns"]:
                summary_report["links"] = self.extract_links(timestamp, limit)
                time.sleep(self.config["delay"])
                
            if "emails" in self.config["patterns"]:
                summary_report["emails"] = self.extract_emails(timestamp, limit)
                time.sleep(self.config["delay"])
                
            if "tables" in self.config["patterns"]:
                summary_report["tables"] = self.extract_tables(timestamp, limit)
                time.sleep(self.config["delay"])
                
            if "custom" in self.config["patterns"] and self.config["custom_selector"]:
                summary_report["custom"] = self.extract_custom(timestamp, limit)
                time.sleep(self.config["delay"])
                
        finally:
            self.driver.quit()
            
        print("\\n=== SCRAPING EXECUTION SUMMARY ===")
        for data_type, count in summary_report.items():
            if count > 0:
                print(f"[SUCCESS] Scraped data found! Extracted {count} items for '{data_type}'.")
            else:
                print(f"[WARNING] Data not found for '{data_type}'.")

    def extract_links(self, timestamp, limit):
        try:
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            links = list(set([el.get_attribute("href") for el in elements if el.get_attribute("href")]))[:limit]
            
            if not links:
                return 0
                
            file_path = os.path.join(self.config["output_dir"], f"links_{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(links, f, indent=4)
            return len(links)
        except Exception:
            return 0

    def extract_emails(self, timestamp, limit):
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}'
            emails = list(set(re.findall(email_pattern, body_text)))[:limit]
            
            if not emails:
                return 0
                
            file_path = os.path.join(self.config["output_dir"], f"emails_{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(emails, f, indent=4)
            return len(emails)
        except Exception:
            return 0

    def extract_tables(self, timestamp, limit):
        try:
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            extracted_tables = []
            item_count = 0
            
            for index, table in enumerate(tables):
                if item_count >= limit:
                    break
                table_data = []
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    if item_count >= limit:
                        break
                    cols = row.find_elements(By.XPATH, "./td | ./th")
                    row_text = [col.text.strip() for col in cols if col.text.strip()]
                    if row_text:
                        table_data.append(row_text)
                        item_count += 1
                if table_data:
                    extracted_tables.append({"table_index": index, "rows": table_data})
                    
            if not extracted_tables:
                return 0
                
            file_path = os.path.join(self.config["output_dir"], f"tables_{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(extracted_tables, f, indent=4)
            return item_count
        except Exception:
            return 0

    def extract_custom(self, timestamp, limit):
        try:
            selector = self.config["custom_selector"]
            if selector.startswith(".") or selector.startswith("#") or "[" in selector:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            else:
                elements = self.driver.find_elements(By.CLASS_NAME, selector)
                if not elements:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
            results = [el.text.strip() for el in elements if el.text.strip()][:limit]
            
            if not results:
                return 0
                
            file_path = os.path.join(self.config["output_dir"], f"custom_{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)
            return len(results)
        except Exception:
            return 0
"""

main_code = """from config import get_user_options
from scraper import ModularScraper

def main():
    print("=== Modular Pattern-Based Anti-CAPTCHA Scraper ===")
    config = get_user_options()
    if not config["patterns"]:
        print("[ERROR] No structural patterns selected. Exiting.")
        return
        
    print("[INFO] Initializing stealth web browser...")
    scraper = ModularScraper(config)
    
    print("[INFO] Starting extraction sequence...")
    scraper.execute()

if __name__ == "__main__":
    main()
"""

with open(os.path.join("scraper_workspace", "config.py"), "w", encoding="utf-8") as f:
    f.write(config_code)

with open(os.path.join("scraper_workspace", "scraper.py"), "w", encoding="utf-8") as f:
    f.write(scraper_code)

with open(os.path.join("scraper_workspace", "main.py"), "w", encoding="utf-8") as f:
    f.write(main_code)

print("Directory 'scraper_workspace' rebuilt with runtime data capping and error-checked paths.")
