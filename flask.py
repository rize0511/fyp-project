from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from bs4 import BeautifulSoup
import requests
import random
import logging
from fuzzywuzzy import process

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'your_secret_key'
Session(app)


limelight_base_url = 'https://www.limelight.pk'
limelight_urls = [
                  '/collections/daily-wear',
                  # '/collections/formal-wear',
                  '/collections/western',
                  # '/collections/unstitched'
                ]

khaadi_base_urls = [
    "https://pk.khaadi.com/gifts-for-her/",
    "https://pk.khaadi.com/ready-to-wear/smart-casuals/maxi-dress/",
    # "https://pk.khaadi.com/ready-to-wear/smart-casuals/sweater/",
    "https://pk.khaadi.com/ready-to-wear/casuals/jeans/",
    # "https://pk.khaadi.com/ready-to-wear/signature/pants/",
    # "https://pk.khaadi.com/ready-to-wear/signature/shawl/",
    # "https://pk.khaadi.com/ready-to-wear/signature/dupatta/",
    # "https://pk.khaadi.com/ready-to-wear/signature/shalwar/",
]

bareeze_urls = [
    "https://www.bareeze.com/pk/casuals/by-category/printed.html?p=1",
    "https://www.bareeze.com/pk/casuals/by-category/printed.html?p=2",
    # "https://www.bareeze.com/pk/casuals/by-category/printed.html?p=3",
    # "https://www.bareeze.com/pk/casuals/by-category/printed.html?p=4",
    # "https://www.bareeze.com/pk/casuals/by-category/printed.html?p=5",
]

def scrape_limelight_products():
    all_products = []
    for relative_url in limelight_urls:
        try:
            response = requests.get(limelight_base_url + relative_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            products = soup.select('.card-wrapper')
            for product in products:
                title = product.select_one('.card-information__text').get_text().strip()
                image_url = product.select_one('.media img')['src']
                product_url = limelight_base_url + product.find('a', class_='full-unstyled-link')['href']

                # Fetch the price
                price_tag = product.select_one('.price-item--sale .money')
                price = price_tag.get_text().strip() if price_tag else product.select_one('.price-item .money').get_text().strip()

                all_products.append({
                    'title': title,
                    'imageUrl': image_url,
                    'price': price,
                    'productUrl': product_url,
                    'brand': "Limelight"
                })

        except Exception as e:
            logging.error(f"Error scraping Limelight URL {relative_url}: {e}")

    return all_products


def scrape_khaadi_products():
    all_products = []
    for base_url in khaadi_base_urls:
        try:
            response = requests.get(base_url)
            response.raise_for_status()  # Check for HTTP errors
            soup = BeautifulSoup(response.content, 'html.parser')

            titles = [title.text.strip() for title in soup.find_all("h2", "pdp-link-heading")]
            prices = [price.text.strip() if price else 'Not available' for price in soup.find_all("span", "value cc-price")]
            image_urls = [img["src"] for img in soup.find_all("img", "tile-image")]
            product_urls = [base_url + link["href"] for link in soup.find_all("a", "plp-tap-mobile plpRedirectPdp")]

            for i in range(len(titles)):
                all_products.append({
                    'title': titles[i],
                    'imageUrl': image_urls[i],
                    'price': prices[i],
                    'productUrl': product_urls[i],
                    'brand': "Khaadi"
                })

        except Exception as e:
            logging.error(f"Error scraping Khaadi URL {base_url}: {e}")

    return all_products

def scrape_bareeze_products():
    all_products = []
    for url in bareeze_urls:
        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            titles = [link.text.strip() for link in soup.find_all('a', 'product-item-link')]
            images = [img['src'] for img in soup.find_all('img', 'product-image-photo')]
            product_urls = [link.get('href') for link in soup.find_all('a', 'product-item-link')]

            # Fetch prices, defaulting to "Not available" if missing
            prices = [price.get('data-price-amount', 'Not available') for price in soup.find_all('span', attrs={'data-price-amount': True})]

            for i in range(len(titles)):
                all_products.append({
                    'title': titles[i],
                    'imageUrl': images[i],
                    'price': prices[i],
                    'productUrl': product_urls[i],
                    'brand': "Bareeze"
                })

        except Exception as e:
            logging.error(f"Error scraping Bareeze URL {url}: {e}")

    return all_products
def scrape_baroque_products():
    all_products = []
    baroque_base_url = 'https://baroque.pk'  # Base URL for Baroque

    baroque_urls = [
        'https://baroque.pk/collections/swiss',
        # 'https://baroque.pk/collections/chantelle',
        # 'https://baroque.pk/collections/pret',
    ]

    for url in baroque_urls:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Ensure successful HTTP response

            soup = BeautifulSoup(response.text, 'html.parser')

            products = soup.select('.product-card')
            for product in products:
                title = product.select_one('.product-title').get_text().strip()
                image_url = product.select_one('.product-card__media img')['src']
                product_url = f"{baroque_base_url}{product.select_one('.product-card__media')['href']}"

                price_tag = product.select_one('.price-list')
                regular_price = 'Not available'
                if price_tag:
                    regular_price_element = price_tag.select_one('.money')
                    if regular_price_element:
                        regular_price = regular_price_element.get_text().strip()

                all_products.append({
                    'title': title,
                    'imageUrl': image_url,
                    'price': regular_price,
                    'productUrl': product_url,
                    'brand': 'Baroque',  # Consistent naming with other brands
                })

        except Exception as e:
            logging.error(f'Error fetching and scraping products from {url}: {e}')  # Use logging for errors

    return all_products

mohagni_urls = [
    'https://mohagni.com/collections/lawn-collection',
    # 'https://mohagni.com/collections/winter-collection',
    # 'https://mohagni.com/collections/chiffon'
]

def scrape_mohagni_products():
    all_products = []

    for url in mohagni_urls:
        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            product_elements = soup.select('.card-wrapper.product-card-wrapper')

            for product in product_elements:
                title = product.select_one('.card__heading a').text.strip()
                image_url = product.select_one('.card__media img')['src']
                price = product.select_one('.price-item--sale .money').text.strip()
                product_url = 'https://mohagni.com' + product.select_one('.card__heading a')['href']

                all_products.append({
                    'title': title,
                    'imageUrl': image_url,
                    'price': price,
                    'productUrl': product_url,
                    'brand': 'Mohagni'
                })

        except Exception as e:
            logging.error(f"Error fetching and scraping products from {url}: {e}")

    return all_products

def scrape_all_products():
    limelight_products = scrape_limelight_products()
    khaadi_products = scrape_khaadi_products()
    bareeze_products = scrape_bareeze_products()
    baroque_products = scrape_baroque_products()
    mohagni_products = scrape_mohagni_products()  # Scrape Mohagni products

    all_products = (
        limelight_products +
        khaadi_products +
        bareeze_products +
        baroque_products +
        mohagni_products  # Combine all products
    )
    random.shuffle(all_products)

    return all_products

@app.route('/')
def landing_page():
    return render_template('landingpage.html')
# Route to render template.html
@app.route('/shop')
def shop_now():
    return render_template('template.html')

# Route to display products by brand
# @app.route('/')
# def index():
#     cart_count = len(session.get("cart", []))  # Current cart count
#     return render_template('template.html', cart_count=cart_count)

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '').strip().lower()  # Get the search query

    all_products = scrape_all_products()  # Retrieve all products
    random.shuffle(all_products)  # Shuffle for variety

    matching_products = []
    query_words = query.split()  # Split the query into words

    for product in all_products:
        title = product['title'].lower()
        if any(process.extractOne(word, [title])[1] >= 70 for word in query_words):
            matching_products.append(product)

    return jsonify(matching_products)  # Return matching products as JSON

@app.route('/brand/<brand_name>')
def view_products_by_brand(brand_name):
    all_products = scrape_all_products()  # Retrieve all products

    # Filter products by the specified brand
    brand_products = [product for product in all_products if product['brand'].lower() == brand_name.lower()]

    return render_template('brand.html', products=brand_products, brand_name=brand_name)


@app.route('/cart')
def view_cart():
    cart_items = session.get("cart", [])  # Retrieve cart contents from the session

    return render_template("cart.html", cart_items=cart_items)  # Render cart template
def extract_price(price_str):
    # Remove non-numeric characters except for digits and the decimal point
    cleaned_price = ''.join(filter(lambda x: x.isdigit() or x == '.', price_str))
    return float(cleaned_price)  # Convert the cleaned string to a float


@app.route('/price-filter', methods=['POST'])
def price_filter():
    data = request.json  # Get data from the client
    min_price = data.get('minPrice', 0)  # Default to 0 if not specified
    max_price = data.get('maxPrice', float('inf'))  # Default to infinity if not specified

    # Ensure min and max prices are valid floats
    if min_price < 0 or max_price < min_price:
        return jsonify({"error": "Invalid price range"}), 400  # Return error if range is invalid

    all_products = scrape_all_products()  # Retrieve all products
    matching_products = []

    for product in all_products:
        try:
            price = extract_price(product['price'])  # Safely convert to float
            if min_price <= price <= max_price:  # Check if within range
                matching_products.append(product)
        except Exception as e:
            logging.error(f"Error extracting price from {product['title']}: {e}")

    return jsonify(matching_products)  # Return matching products as JSON

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    product = request.json  # Product data from the client

    if "cart" not in session:
        session["cart"] = []  # Initialize cart if needed

    session["cart"].append(product)  # Add product to cart

    return jsonify({"status": "Product added to cart"}), 200

# Debug check to run the app

if __name__ == '__main__':
    app.run(debug=True)

