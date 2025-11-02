"""
Boilerplate Code Generator
Generates ready-to-use Lambda handlers and Frontend code
WITHOUT modifying existing modules
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def generate_boilerplate(
    services: List[Dict],
    classification: Dict,
    estimated_users: int
) -> Dict[str, Any]:
    """
    Generate boilerplate code for Lambda backend and Frontend
    
    Args:
        services: List of recommended services
        classification: Project classification
        estimated_users: Estimated user count
    
    Returns:
        Dict with backend and frontend code files
    """
    project_type = classification.get("primary", "application")
    
    logger.info(f"Generating boilerplate for {project_type}")
    
    backend_code = generate_lambda_handler(services, project_type, estimated_users)
    frontend_code = generate_frontend_code(services, project_type)
    
    return {
        "format": "boilerplate",
        "backend": backend_code,
        "frontend": frontend_code,
        "instructions": [
            "1. Download backend files and deploy to Lambda",
            "2. Update API_URL in frontend files",
            "3. Deploy frontend to S3 or any static hosting",
            "4. Test the endpoints"
        ]
    }


def generate_lambda_handler(services: List[Dict], project_type: str, users: int) -> Dict[str, str]:
    """Generate Lambda handler code"""
    
    # Check which services are used
    has_dynamodb = any('dynamodb' in s['name'].lower() for s in services)
    has_cognito = any('cognito' in s['name'].lower() for s in services)
    has_s3 = any('s3' in s['name'].lower() for s in services)
    
    # Generate handler based on project type
    if project_type == "ecommerce":
        return generate_ecommerce_handler(has_dynamodb, has_s3)
    elif project_type == "api":
        return generate_api_handler(has_dynamodb)
    elif project_type == "social":
        return generate_social_handler(has_dynamodb, has_s3)
    else:
        return generate_generic_handler(has_dynamodb)


def generate_ecommerce_handler(has_db: bool, has_s3: bool) -> Dict[str, str]:
    """Generate ecommerce Lambda handler"""
    
    handler_py = """import json
import boto3
import os
from decimal import Decimal
from datetime import datetime

# AWS clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'Products'))

def lambda_handler(event, context):
    \"\"\"Main Lambda handler for ecommerce API\"\"\"
    
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    
    # Route requests
    if path == '/products':
        if http_method == 'GET':
            return get_products(event)
        elif http_method == 'POST':
            return create_product(event)
    elif path.startswith('/products/'):
        product_id = path.split('/')[-1]
        if http_method == 'GET':
            return get_product(product_id)
        elif http_method == 'PUT':
            return update_product(product_id, event)
        elif http_method == 'DELETE':
            return delete_product(product_id)
    
    return response(404, {'error': 'Not found'})


def get_products(event):
    \"\"\"Get all products\"\"\"
    try:
        result = table.scan(Limit=50)
        items = result.get('Items', [])
        
        return response(200, {
            'products': items,
            'count': len(items)
        })
    except Exception as e:
        return response(500, {'error': str(e)})


def get_product(product_id):
    \"\"\"Get single product\"\"\"
    try:
        result = table.get_item(Key={'id': product_id})
        
        if 'Item' not in result:
            return response(404, {'error': 'Product not found'})
        
        return response(200, result['Item'])
    except Exception as e:
        return response(500, {'error': str(e)})


def create_product(event):
    \"\"\"Create new product\"\"\"
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if not body.get('name') or not body.get('price'):
            return response(400, {'error': 'Missing required fields'})
        
        product = {
            'id': f"prod_{int(datetime.now().timestamp())}",
            'name': body['name'],
            'price': Decimal(str(body['price'])),
            'description': body.get('description', ''),
            'stock': body.get('stock', 0),
            'created_at': datetime.now().isoformat()
        }
        
        table.put_item(Item=product)
        
        return response(201, product)
    except Exception as e:
        return response(500, {'error': str(e)})


def update_product(product_id, event):
    \"\"\"Update existing product\"\"\"
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Build update expression
        update_expr = 'SET '
        expr_values = {}
        
        if 'name' in body:
            update_expr += 'name = :name, '
            expr_values[':name'] = body['name']
        
        if 'price' in body:
            update_expr += 'price = :price, '
            expr_values[':price'] = Decimal(str(body['price']))
        
        if 'stock' in body:
            update_expr += 'stock = :stock, '
            expr_values[':stock'] = body['stock']
        
        update_expr = update_expr.rstrip(', ')
        
        table.update_item(
            Key={'id': product_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        return response(200, {'message': 'Product updated'})
    except Exception as e:
        return response(500, {'error': str(e)})


def delete_product(product_id):
    \"\"\"Delete product\"\"\"
    try:
        table.delete_item(Key={'id': product_id})
        return response(200, {'message': 'Product deleted'})
    except Exception as e:
        return response(500, {'error': str(e)})


def response(status_code, body):
    \"\"\"Format API response\"\"\"
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, default=str)
    }
"""

    requirements_txt = """boto3>=1.26.0
python-dateutil>=2.8.0
"""

    readme = """# Ecommerce Lambda Handler

## Setup

1. Install dependencies:
```bash
   pip install -r requirements.txt -t .
```

2. Create deployment package:
```bash
   zip -r function.zip .
```

3. Deploy to Lambda:
```bash
   aws lambda update-function-code \\
     --function-name your-function-name \\
     --zip-file fileb://function.zip
```

4. Set environment variables:
   - TABLE_NAME: Your DynamoDB table name

## API Endpoints

- `GET /products` - List all products
- `GET /products/{id}` - Get single product
- `POST /products` - Create product
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product

## Testing
```bash
# List products
curl https://your-api-url/products

# Create product
curl -X POST https://your-api-url/products \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Test Product","price":29.99,"stock":100}'
```
"""

    return {
        "handler.py": handler_py,
        "requirements.txt": requirements_txt,
        "README.md": readme
    }


def generate_api_handler(has_db: bool) -> Dict[str, str]:
    """Generate generic API Lambda handler"""
    
    handler_py = """import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'ApiData'))

def lambda_handler(event, context):
    \"\"\"Generic API handler\"\"\"
    
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    
    if http_method == 'GET':
        return handle_get(event)
    elif http_method == 'POST':
        return handle_post(event)
    else:
        return response(405, {'error': 'Method not allowed'})


def handle_get(event):
    \"\"\"Handle GET requests\"\"\"
    try:
        result = table.scan(Limit=100)
        return response(200, {'items': result.get('Items', [])})
    except Exception as e:
        return response(500, {'error': str(e)})


def handle_post(event):
    \"\"\"Handle POST requests\"\"\"
    try:
        body = json.loads(event.get('body', '{}'))
        
        item = {
            'id': f"item_{int(datetime.now().timestamp())}",
            'data': body,
            'timestamp': datetime.now().isoformat()
        }
        
        table.put_item(Item=item)
        
        return response(201, item)
    except Exception as e:
        return response(500, {'error': str(e)})


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, default=str)
    }
"""

    requirements_txt = "boto3>=1.26.0"
    
    readme = """# API Lambda Handler

Simple API handler with DynamoDB integration.

## Deploy
```bash
pip install -r requirements.txt -t .
zip -r function.zip .
aws lambda update-function-code --function-name your-function --zip-file fileb://function.zip
```
"""

    return {
        "handler.py": handler_py,
        "requirements.txt": requirements_txt,
        "README.md": readme
    }


def generate_social_handler(has_db: bool, has_s3: bool) -> Dict[str, str]:
    """Generate social media Lambda handler"""
    return generate_generic_handler(has_db)


def generate_generic_handler(has_db: bool) -> Dict[str, str]:
    """Generate generic Lambda handler"""
    return generate_api_handler(has_db)


def generate_frontend_code(services: List[Dict], project_type: str) -> Dict[str, str]:
    """Generate frontend code"""
    
    if project_type == "ecommerce":
        return generate_ecommerce_frontend()
    else:
        return generate_generic_frontend()


def generate_ecommerce_frontend() -> Dict[str, str]:
    """Generate ecommerce frontend"""
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ecommerce Store</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🛍️ My Store</h1>
            <div id="cart-count">Cart: 0</div>
        </header>
        
        <main>
            <div id="products" class="products-grid"></div>
        </main>
    </div>
    
    <script src="app.js"></script>
</body>
</html>
"""

    css = """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: white;
    border-radius: 8px;
    margin-bottom: 30px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 20px;
}

.product-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s;
}

.product-card:hover {
    transform: translateY(-5px);
}

.product-card h3 {
    margin-bottom: 10px;
}

.product-price {
    font-size: 24px;
    color: #e74c3c;
    font-weight: bold;
    margin: 10px 0;
}

.btn {
    background: #3498db;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    width: 100%;
    font-size: 16px;
}

.btn:hover {
    background: #2980b9;
}
"""

    js = """// UPDATE THIS with your API endpoint
const API_URL = 'https://YOUR-API-URL.execute-api.REGION.amazonaws.com/prod';

let cart = [];

// Load products on page load
document.addEventListener('DOMContentLoaded', loadProducts);

async function loadProducts() {
    try {
        const response = await fetch(`${API_URL}/products`);
        const data = await response.json();
        
        displayProducts(data.products || []);
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

function displayProducts(products) {
    const container = document.getElementById('products');
    
    if (products.length === 0) {
        container.innerHTML = '<p>No products available</p>';
        return;
    }
    
    container.innerHTML = products.map(product => `
        <div class="product-card">
            <h3>${product.name}</h3>
            <p>${product.description || ''}</p>
            <div class="product-price">$${product.price}</div>
            <p>Stock: ${product.stock || 0}</p>
            <button class="btn" onclick="addToCart('${product.id}')">
                Add to Cart
            </button>
        </div>
    `).join('');
}

function addToCart(productId) {
    cart.push(productId);
    updateCartCount();
    alert('Product added to cart!');
}

function updateCartCount() {
    document.getElementById('cart-count').textContent = `Cart: ${cart.length}`;
}

// Admin functions (add these to a separate admin page)
async function createProduct(productData) {
    try {
        const response = await fetch(`${API_URL}/products`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });
        
        const data = await response.json();
        console.log('Product created:', data);
        loadProducts(); // Reload products
    } catch (error) {
        console.error('Error creating product:', error);
    }
}
"""

    readme = """# Ecommerce Frontend

## Setup

1. Update `app.js`:
   - Replace `API_URL` with your actual API Gateway URL

2. Deploy to S3:
```bash
   aws s3 cp index.html s3://your-bucket/
   aws s3 cp styles.css s3://your-bucket/
   aws s3 cp app.js s3://your-bucket/
```

3. Or use any static hosting (Netlify, Vercel, etc.)

## Features
- Product listing
- Shopping cart
- Responsive design

## Adding Products

Use the browser console or create an admin page:
```javascript
createProduct({
    name: "Product Name",
    price: 29.99,
    description: "Product description",
    stock: 100
});
```
"""

    return {
        "index.html": html,
        "styles.css": css,
        "app.js": js,
        "README.md": readme
    }


def generate_generic_frontend() -> Dict[str, str]:
    """Generate generic frontend"""
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My App</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>My Application</h1>
        <div id="data"></div>
        <button onclick="loadData()">Load Data</button>
    </div>
    <script src="app.js"></script>
</body>
</html>
"""

    css = """body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background: #f5f5f5;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 30px;
    border-radius: 8px;
}

button {
    background: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
}
"""

    js = """const API_URL = 'https://YOUR-API-URL.execute-api.REGION.amazonaws.com/prod';

async function loadData() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();
        document.getElementById('data').innerHTML = JSON.stringify(data, null, 2);
    } catch (error) {
        console.error('Error:', error);
    }
}
"""

    readme = """# Application Frontend

Update API_URL in app.js with your actual endpoint.
"""

    return {
        "index.html": html,
        "styles.css": css,
        "app.js": js,
        "README.md": readme
    }
