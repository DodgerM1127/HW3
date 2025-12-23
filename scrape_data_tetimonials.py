import json
import requests # Ensure requests is imported if not already in the scope
from bs4 import BeautifulSoup # Ensure BeautifulSoup is imported if not already in the scope

def scrape_all_testimonials():
    all_testimonials = []
    testimonials_url = 'https://web-scraping.dev/testimonials'

    # Initial request to get the first page's HTML content
    try:
        response = requests.get(testimonials_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        response.raise_for_status()
        current_page_source = response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching initial testimonials page: {e}")
        return []

    initial_testimonials_url = testimonials_url # The initial URL for the Referer header

    # Keep track of already scraped testimonials to avoid duplicates when appending
    scraped_texts = set()

    while True:
        current_soup = BeautifulSoup(current_page_source, 'html.parser')
        testimonial_elements_on_current_page = current_soup.find_all('div', class_='testimonial')

        next_page_url_trigger = None
        hx_headers_from_html = {}

        # Process testimonials from the current HTML snippet
        for testimonial_element in testimonial_elements_on_current_page:
            # Extract testimonial data for the current element
            text_tag = testimonial_element.find('p', class_='text')
            testimonial_text = text_tag.get_text(strip=True) if text_tag else 'N/A'

            # Only add if not already scraped
            if testimonial_text not in scraped_texts:
                author_tag = testimonial_element.find('identicon-svg')
                author_username = author_tag.get('username') if author_tag else 'Unknown Author'

                rating_span = testimonial_element.find('span', class_='rating')
                rating = len(rating_span.find_all('svg')) if rating_span else 0

                all_testimonials.append({
                    'author': author_username,
                    'rating': rating,
                    'text': testimonial_text
                })
                scraped_texts.add(testimonial_text)

            # Check if this is the pagination trigger (always the last one on the page usually)
            if testimonial_element.has_attr('hx-get'):
                next_page_url_trigger = testimonial_element['hx-get']
                hx_headers_str = testimonial_element.get('hx-headers', '{}')
                try:
                    hx_headers_from_html = json.loads(hx_headers_str.replace("'", '"'))
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse hx-headers for pagination: {hx_headers_str}")
                    hx_headers_from_html = {}

        # If no next page URL was found, we are done
        if not next_page_url_trigger:
            break

        # Prepare comprehensive headers for the next request
        hx_headers_to_send = {
            **hx_headers_from_html, # Includes x-secret-token if present
            'HX-Request': 'true',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': initial_testimonials_url, # The initial URL of the testimonials page
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Remove 'Accept' header as the response is HTML, not JSON
        if 'Accept' in hx_headers_to_send and hx_headers_to_send['Accept'] == 'application/json':
            del hx_headers_to_send['Accept']

        # Fetch the next page
        print(f"Fetching next page from: {next_page_url_trigger}")
        print(f"Using headers for pagination: {hx_headers_to_send}")
        try:
            response = requests.get(next_page_url_trigger, headers=hx_headers_to_send)
            response.raise_for_status() # Raise an exception for HTTP errors

            # The response is HTML, not JSON
            current_page_source = response.text # Update source for next iteration

        except requests.exceptions.RequestException as e:
            print(f"Request failed for {next_page_url_trigger}: {e}")
            print(f"Response content: {response.text}") # Print response text for debugging
            break
        except json.JSONDecodeError:
            # This block should ideally not be reached if response.text is used instead of response.json()
            print("Error: Tried to decode JSON but received non-JSON content. This indicates a logic error.")
            print(f"Response content: {response.text}") # Print response text for debugging
            break

    return all_testimonials

# Call the function to scrape all testimonials
scraped_testimonials_data = scrape_all_testimonials()

# Save the scraped testimonials to data.json
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(scraped_testimonials_data, f, ensure_ascii=False, indent=4)
print("Scraped testimonials successfully saved to data.json.")

print(f"\nTotal testimonials scraped: {len(scraped_testimonials_data)}")
print("First 5 scraped testimonials:")
for t in scraped_testimonials_data[:5]:
    print(t)
print("\nLast 5 scraped testimonials:")
for t in scraped_testimonials_data[-5:]: # Display last 5 to check pagination success
    print(t)
