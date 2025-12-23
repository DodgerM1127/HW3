import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_products_improved():
    base_url = "https://web-scraping.dev/products"
    products_list = []
    current_page = 1
    total_pages = 1  # Initialize with 1, will be updated after first request

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    while current_page <= total_pages:
        url = f"{base_url}?page={current_page}"
        print(f"Scraping page: {url}")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Update total_pages after the first request
            if current_page == 1:
                paging_meta = soup.find('div', class_='paging-meta')
                if paging_meta:
                    match = re.search(r'total \d+ results in (\d+) pages', paging_meta.text)
                    if match:
                        total_pages = int(match.group(1))
                        print(f"Total pages identified: {total_pages}")
                else:
                    print("Paging meta not found, assuming single page.")

            products = soup.find_all('div', class_='product')

            for product in products:
                name_element = product.find('h3')
                name = name_element.text.strip() if name_element else "Neznano ime"

                price_element = product.find('div', class_='price')
                price = price_element.text.strip() if price_element else "Ni cene"

                desc_element = product.find('div', class_='short-description')
                description = desc_element.text.strip() if desc_element else "Brez opisa"

                products_list.append({
                    "ime": name,
                    "cena": price,
                    "opis": description
                })
            current_page += 1

        except requests.exceptions.RequestException as e:
            print(f"Prišlo je do napake pri zahtevi na strani {url}: {e}")
            break
        except Exception as e:
            print(f"Prišlo je do napake na strani {url}: {e}")
            break

    # Shranjevanje v data.json
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(products_list, f, ensure_ascii=False, indent=4)

    print(f"Uspešno smo postrgali {len(products_list)} izdelkov in jih shranili v data.json.")
    return products_list

if __name__ == "__main__":
    scraped_products = scrape_products_improved()
    # Verify the number of scraped products
    print(f"Number of products scraped: {len(scraped_products)}")
