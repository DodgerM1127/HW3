import requests
import json

def scrape_all_reviews_graphql(graphql_api_url, graphql_query):
    all_reviews = []
    current_cursor = None
    has_next_page = True
    first_param = 20 # Number of reviews to fetch per request, as inferred from loadPage(20)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print("Starting to scrape reviews via GraphQL...")
    page_count = 0
    while has_next_page:
        page_count += 1
        print(f"Fetching page {page_count} (after cursor: {current_cursor})...")

        payload = {
            "query": graphql_query,
            "variables": {
                "first": first_param,
                "after": current_cursor
            }
        }

        try:
            graphql_response = requests.post(graphql_api_url, headers=headers, data=json.dumps(payload))
            graphql_response.raise_for_status() # Raise an exception for HTTP errors
            response_data = graphql_response.json()

            # Extract reviews and page info
            reviews_edges = response_data['data']['reviews']['edges']
            page_info = response_data['data']['reviews']['pageInfo']

            if not reviews_edges:
                print("No more reviews found on this page.")
                break # Exit if no reviews are returned

            for edge in reviews_edges:
                node = edge['node']
                review = {
                    'rid': node['rid'],
                    'text': node['text'],
                    'rating': node['rating'],
                    'date': node['date']
                }
                all_reviews.append(review)

            current_cursor = page_info['endCursor']
            has_next_page = page_info['hasNextPage']
            print(f"  -> Fetched {len(reviews_edges)} reviews. Total so far: {len(all_reviews)}.")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching GraphQL data: {e}")
            break # Exit loop on error
        except KeyError as e:
            print(f"Error parsing GraphQL response. Missing key: {e}. Response: {response_data}")
            break

    print("Finished scraping reviews.")
    return all_reviews

# Define the GraphQL API endpoint and query for local execution
graphql_api_url = "https://web-scraping.dev/api/graphql"
graphql_query = """
query GetReviews($first: Int, $after: String) {
  reviews(first: $first, after: $after) {
    edges {
      node {
        rid
        text
        rating
        date
      }
      cursor
    }
    pageInfo {
      startCursor
      endCursor
      hasPreviousPage
      hasNextPage
    }
  }
}
"""

# Call the function with the identified GraphQL API URL and query
scraped_reviews = scrape_all_reviews_graphql(graphql_api_url, graphql_query)

# Save the scraped reviews to data.json
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(scraped_reviews, f, ensure_ascii=False, indent=4)
print("Scraped reviews successfully saved to data.json.")

print(f"\nTotal reviews scraped: {len(scraped_reviews)}")
print("\nFirst 5 scraped reviews:")
for i, review in enumerate(scraped_reviews[:5]):
    print(f"Review {i+1}: {review}")
