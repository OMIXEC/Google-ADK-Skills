# FunctionTool Examples

Complete, working examples of FunctionTool creation patterns.

## Example 1: Weather API Tool

```python
from google.adk.tools import FunctionTool
from google.adk.agents import LlmAgent
import requests
from typing import Optional

def get_weather(
    city: str,
    country_code: Optional[str] = None,
    units: str = "metric",
) -> dict:
    """Get current weather for a city.

    Fetches real-time weather data including temperature, conditions,
    humidity, and wind speed.

    Args:
        city: City name (e.g., "London", "New York").
        country_code: Optional ISO 3166 country code (e.g., "US", "GB").
        units: Temperature units - "metric" (Celsius) or "imperial" (Fahrenheit).

    Returns:
        Weather data including temperature, conditions, and metadata.
    """
    # Build location query
    location = f"{city},{country_code}" if country_code else city

    # Call weather API
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": location,
                "units": units,
                "appid": "YOUR_API_KEY",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "condition": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "units": "°C" if units == "metric" else "°F",
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "error": f"City '{city}' not found",
                "error_code": "CITY_NOT_FOUND",
            }
        else:
            return {
                "success": False,
                "error": f"API error: {e.response.status_code}",
                "error_code": "API_ERROR",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch weather: {str(e)}",
            "error_code": "UNKNOWN_ERROR",
        }

# Create tool
weather_tool = FunctionTool(get_weather)

# Create agent with tool
weather_agent = LlmAgent(
    name="weather_assistant",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool],
    system_instruction="""You are a helpful weather assistant.
    When asked about weather, use the get_weather tool.
    Always specify the city clearly and mention the temperature units.""",
)

# Test the agent
if __name__ == "__main__":
    response = weather_agent.send_message("What's the weather in Tokyo?")
    print(response.text)
```

## Example 2: Database Query Tool

```python
from google.adk.tools import FunctionTool
from typing import List, Dict, Any, Optional
import sqlite3
import json

class DatabaseTool:
    """Stateful database tool with connection pooling."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row  # Return dict-like rows

    def search_customers(
        self,
        country: Optional[str] = None,
        min_orders: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> dict:
        """Search customer database with filters.

        Args:
            country: Filter by country code (e.g., "US", "UK").
            min_orders: Minimum number of orders placed.
            status: Customer status ("active", "inactive", "suspended").
            limit: Maximum number of results to return (default: 10, max: 100).

        Returns:
            List of matching customers with their details.
        """
        # Validation
        if limit > 100:
            return {
                "success": False,
                "error": "Limit cannot exceed 100",
            }

        # Build safe parameterized query
        query = "SELECT * FROM customers WHERE 1=1"
        params = []

        if country:
            query += " AND country = ?"
            params.append(country)

        if min_orders is not None:
            query += " AND order_count >= ?"
            params.append(min_orders)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        try:
            cursor = self.connection.execute(query, params)
            rows = cursor.fetchall()

            customers = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "email": row["email"],
                    "country": row["country"],
                    "status": row["status"],
                    "order_count": row["order_count"],
                }
                for row in rows
            ]

            return {
                "success": True,
                "count": len(customers),
                "customers": customers,
                "filters_applied": {
                    "country": country,
                    "min_orders": min_orders,
                    "status": status,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Database query failed: {str(e)}",
                "error_code": "DB_ERROR",
            }

    def get_customer_orders(self, customer_id: int) -> dict:
        """Get all orders for a specific customer.

        Args:
            customer_id: The unique customer ID.

        Returns:
            Customer information and their order history.
        """
        try:
            # Get customer
            customer_row = self.connection.execute(
                "SELECT * FROM customers WHERE id = ?",
                (customer_id,)
            ).fetchone()

            if not customer_row:
                return {
                    "success": False,
                    "error": f"Customer {customer_id} not found",
                    "error_code": "NOT_FOUND",
                }

            # Get orders
            order_rows = self.connection.execute(
                "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC",
                (customer_id,)
            ).fetchall()

            return {
                "success": True,
                "customer": dict(customer_row),
                "order_count": len(order_rows),
                "orders": [dict(row) for row in order_rows],
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch orders: {str(e)}",
                "error_code": "DB_ERROR",
            }

# Create database tool instance
db = DatabaseTool("customers.db")

# Create FunctionTools
search_tool = FunctionTool(db.search_customers)
orders_tool = FunctionTool(db.get_customer_orders)

# Create agent with database tools
db_agent = LlmAgent(
    name="customer_support",
    model="gemini-2.0-flash-exp",
    tools=[search_tool, orders_tool],
    system_instruction="""You are a customer support assistant.
    You can search customers and view their order history.
    Always verify customer identity before sharing information.""",
)
```

## Example 3: Multi-Step Calculation Tool

```python
from google.adk.tools import FunctionTool
from typing import List, Literal
import statistics
import math

def analyze_data(
    numbers: List[float],
    operations: List[Literal["mean", "median", "stdev", "min", "max", "sum"]],
) -> dict:
    """Perform statistical analysis on numeric data.

    Args:
        numbers: List of numbers to analyze.
        operations: List of operations to perform. Available:
            - mean: Calculate average
            - median: Calculate median value
            - stdev: Calculate standard deviation
            - min: Find minimum value
            - max: Find maximum value
            - sum: Calculate sum

    Returns:
        Results for each requested operation.
    """
    # Validation
    if not numbers:
        return {
            "success": False,
            "error": "Cannot analyze empty list",
        }

    if not operations:
        return {
            "success": False,
            "error": "At least one operation required",
        }

    # Perform operations
    results = {}

    try:
        for op in operations:
            if op == "mean":
                results["mean"] = statistics.mean(numbers)
            elif op == "median":
                results["median"] = statistics.median(numbers)
            elif op == "stdev":
                if len(numbers) < 2:
                    results["stdev"] = None
                    results["stdev_error"] = "Need at least 2 values"
                else:
                    results["stdev"] = statistics.stdev(numbers)
            elif op == "min":
                results["min"] = min(numbers)
            elif op == "max":
                results["max"] = max(numbers)
            elif op == "sum":
                results["sum"] = sum(numbers)

        return {
            "success": True,
            "count": len(numbers),
            "results": results,
            "operations_performed": operations,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}",
        }

analyze_tool = FunctionTool(analyze_data)

# Example usage
if __name__ == "__main__":
    result = analyze_tool.invoke({
        "numbers": [10, 20, 30, 40, 50],
        "operations": ["mean", "median", "stdev", "min", "max"],
    })
    print(json.dumps(result, indent=2))
```

## Example 4: File Processing Tool

```python
from google.adk.tools import FunctionTool
from pathlib import Path
from typing import Literal, Optional
import json
import csv

def process_file(
    file_path: str,
    operation: Literal["read", "count_lines", "parse_json", "parse_csv", "get_info"],
    encoding: str = "utf-8",
) -> dict:
    """Process text and data files.

    Args:
        file_path: Path to the file to process.
        operation: Operation to perform:
            - read: Read entire file content
            - count_lines: Count lines in file
            - parse_json: Parse JSON file
            - parse_csv: Parse CSV file (returns first 10 rows)
            - get_info: Get file metadata
        encoding: Character encoding (default: utf-8).

    Returns:
        Processing results based on operation type.
    """
    path = Path(file_path)

    # Security checks
    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "error_code": "NOT_FOUND",
        }

    if not path.is_file():
        return {
            "success": False,
            "error": f"Path is not a file: {file_path}",
            "error_code": "NOT_A_FILE",
        }

    # Size limit: 10MB
    file_size = path.stat().st_size
    if file_size > 10 * 1024 * 1024:
        return {
            "success": False,
            "error": "File too large (max 10MB)",
            "error_code": "FILE_TOO_LARGE",
        }

    try:
        if operation == "read":
            content = path.read_text(encoding=encoding)
            return {
                "success": True,
                "content": content,
                "size_bytes": len(content.encode(encoding)),
                "line_count": content.count('\n') + 1,
            }

        elif operation == "count_lines":
            with open(path, 'r', encoding=encoding) as f:
                line_count = sum(1 for _ in f)
            return {
                "success": True,
                "line_count": line_count,
                "file_size": file_size,
            }

        elif operation == "parse_json":
            with open(path, 'r', encoding=encoding) as f:
                data = json.load(f)
            return {
                "success": True,
                "data": data,
                "type": type(data).__name__,
            }

        elif operation == "parse_csv":
            with open(path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)[:10]  # First 10 rows
                total_rows = sum(1 for _ in csv.reader(open(path, 'r', encoding=encoding)))

            return {
                "success": True,
                "columns": list(rows[0].keys()) if rows else [],
                "sample_rows": rows,
                "total_rows": total_rows - 1,  # Exclude header
            }

        elif operation == "get_info":
            stat = path.stat()
            return {
                "success": True,
                "info": {
                    "name": path.name,
                    "extension": path.suffix,
                    "size_bytes": stat.st_size,
                    "modified_timestamp": stat.st_mtime,
                    "is_readable": path.is_file() and path.exists(),
                },
            }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {str(e)}",
            "error_code": "INVALID_JSON",
        }

    except UnicodeDecodeError as e:
        return {
            "success": False,
            "error": f"Encoding error: {str(e)}. Try different encoding.",
            "error_code": "ENCODING_ERROR",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Processing failed: {str(e)}",
            "error_code": "PROCESSING_ERROR",
        }

file_tool = FunctionTool(process_file)
```

## Example 5: REST API Client Tool

```python
from google.adk.tools import FunctionTool
import requests
from typing import Optional, Dict, Any, Literal

class APIClient:
    """REST API client tool."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'

    def call_api(
        self,
        endpoint: str,
        method: Literal["GET", "POST", "PUT", "DELETE"] = "GET",
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Call REST API endpoint.

        Args:
            endpoint: API endpoint path (e.g., "/users", "/products/123").
            method: HTTP method to use.
            params: URL query parameters for GET requests.
            body: JSON request body for POST/PUT requests.

        Returns:
            API response data and metadata.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=body if method in ["POST", "PUT"] else None,
                timeout=30,
            )

            # Try to parse JSON response
            try:
                data = response.json()
            except:
                data = response.text

            # Return based on status
            if response.status_code >= 200 and response.status_code < 300:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": data,
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": data if isinstance(data, str) else data.get("error", "Unknown error"),
                    "error_code": "HTTP_ERROR",
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timeout (30s exceeded)",
                "error_code": "TIMEOUT",
            }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Failed to connect to {self.base_url}",
                "error_code": "CONNECTION_ERROR",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "error_code": "REQUEST_ERROR",
            }

# Create API client and tool
api_client = APIClient(
    base_url="https://api.example.com/v1",
    api_key="your-api-key-here",
)

api_tool = FunctionTool(api_client.call_api)

# Use with agent
api_agent = LlmAgent(
    name="api_assistant",
    model="gemini-2.0-flash-exp",
    tools=[api_tool],
    system_instruction="""You can interact with the API using call_api tool.
    Always check the 'success' field in responses.
    If success=False, explain the error to the user.""",
)
```

## Example 6: Data Validation Tool

```python
from google.adk.tools import FunctionTool
from typing import Any, Dict, List, Literal
import re

def validate_data(
    data: Dict[str, Any],
    schema: Dict[str, str],
) -> dict:
    """Validate data against a schema.

    Args:
        data: The data to validate (key-value pairs).
        schema: Validation schema. Keys are field names, values are types:
            - "string": Must be string
            - "number": Must be int or float
            - "email": Must be valid email
            - "url": Must be valid URL
            - "required": Field must exist

    Returns:
        Validation results with errors for invalid fields.
    """
    errors = []
    warnings = []

    # Check required fields
    for field, rule in schema.items():
        if "required" in rule.split(','):
            if field not in data:
                errors.append({
                    "field": field,
                    "error": "Required field missing",
                })
                continue

        # Skip validation if field not present and not required
        if field not in data:
            continue

        value = data[field]

        # Validate type
        if "string" in rule:
            if not isinstance(value, str):
                errors.append({
                    "field": field,
                    "error": f"Expected string, got {type(value).__name__}",
                    "value": value,
                })

        elif "number" in rule:
            if not isinstance(value, (int, float)):
                errors.append({
                    "field": field,
                    "error": f"Expected number, got {type(value).__name__}",
                    "value": value,
                })

        elif "email" in rule:
            if not isinstance(value, str) or not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
                errors.append({
                    "field": field,
                    "error": "Invalid email format",
                    "value": value,
                })

        elif "url" in rule:
            if not isinstance(value, str) or not value.startswith(('http://', 'https://')):
                errors.append({
                    "field": field,
                    "error": "Invalid URL format",
                    "value": value,
                })

    # Return validation results
    is_valid = len(errors) == 0

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "fields_validated": len(schema),
        "fields_passed": len(schema) - len(errors),
    }

validate_tool = FunctionTool(validate_data)

# Example usage
if __name__ == "__main__":
    result = validate_tool.invoke({
        "data": {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "website": "https://example.com",
        },
        "schema": {
            "name": "string,required",
            "email": "email,required",
            "age": "number",
            "website": "url",
        },
    })
    print(json.dumps(result, indent=2))
```

## Running the Examples

```bash
# Install dependencies
pip install google-adk requests

# Set API keys
export GOOGLE_API_KEY="your-gemini-api-key"
export OPENWEATHER_API_KEY="your-weather-api-key"  # For weather example

# Run an example
python function_tools_weather.py

# Test with ADK CLI
adk run --input "What's the weather in Paris?"
```

## Testing Function Tools

```python
import pytest
from my_tools import get_weather, search_customers, analyze_data

def test_weather_tool_valid_city():
    """Test weather tool with valid city."""
    result = get_weather("London")

    assert result["success"] == True
    assert "temperature" in result
    assert "condition" in result

def test_weather_tool_invalid_city():
    """Test weather tool with invalid city."""
    result = get_weather("InvalidCity123")

    assert result["success"] == False
    assert "error" in result

def test_analyze_data_mean():
    """Test data analysis tool."""
    result = analyze_data([10, 20, 30], ["mean", "sum"])

    assert result["success"] == True
    assert result["results"]["mean"] == 20.0
    assert result["results"]["sum"] == 60

@pytest.mark.asyncio
async def test_tool_with_agent():
    """Test tool integrated with agent."""
    from google.adk.agents import LlmAgent

    agent = LlmAgent(
        name="test_agent",
        model="gemini-2.0-flash-exp",
        tools=[weather_tool],
    )

    response = await agent.send_message("What's the weather in Tokyo?")
    assert "temperature" in response.text.lower() or "weather" in response.text.lower()
```
