# Domain-Driven Agent Architecture Example

## Overview

This example demonstrates domain-driven design (DDD) applied to multi-agent systems, with agents organized by bounded contexts.

## E-commerce Platform Domains

```
Platform
├── Customer Domain
│   ├── Customer Profile Context
│   ├── Customer Support Context
│   └── Customer Loyalty Context
├── Order Domain
│   ├── Shopping Cart Context
│   ├── Checkout Context
│   └── Order Fulfillment Context
├── Product Domain
│   ├── Catalog Context
│   ├── Inventory Context
│   └── Pricing Context
└── Payment Domain
    ├── Payment Processing Context
    ├── Billing Context
    └── Refunds Context
```

## Implementation

### Domain Structure

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from typing import Dict, List, Set
from dataclasses import dataclass

# ============================================================================
# DOMAIN MODEL
# ============================================================================

@dataclass
class BoundedContext:
    """Represents a bounded context in DDD."""
    name: str
    domain: str
    agents: List[LlmAgent]
    events: Set[str]  # Domain events this context publishes
    commands: Set[str]  # Commands this context handles

@dataclass
class Domain:
    """Represents a business domain."""
    name: str
    contexts: List[BoundedContext]
    coordinator: LlmAgent

# ============================================================================
# CUSTOMER DOMAIN
# ============================================================================

# Customer Profile Context
customer_profile_coordinator = LlmAgent(
    name="customer_profile_coordinator",
    model="gemini-2.5-flash",
    description="Manages customer profile operations",
)

profile_creator = LlmAgent(
    name="profile_creator",
    model="gemini-2.5-flash",
    description="Creates new customer profiles",
    instruction="Create customer profiles with required fields: name, email, phone, address.",
)

profile_updater = LlmAgent(
    name="profile_updater",
    model="gemini-2.5-flash",
    description="Updates existing customer profiles",
    instruction="Update customer profile fields. Validate email format and phone numbers.",
)

preference_manager = LlmAgent(
    name="preference_manager",
    model="gemini-2.5-flash",
    description="Manages customer preferences and settings",
    instruction="Handle customer preferences: communication channels, notification settings, privacy preferences.",
)

customer_profile_coordinator.tools = [
    AgentTool(agent=profile_creator),
    AgentTool(agent=profile_updater),
    AgentTool(agent=preference_manager),
]

# Customer Support Context
customer_support_coordinator = LlmAgent(
    name="customer_support_coordinator",
    model="gemini-2.5-flash",
    description="Manages customer support operations",
)

ticket_creator = LlmAgent(
    name="ticket_creator",
    model="gemini-2.5-flash",
    description="Creates support tickets",
)

ticket_resolver = LlmAgent(
    name="ticket_resolver",
    model="gemini-2.5-flash",
    description="Resolves support tickets",
)

customer_support_coordinator.tools = [
    AgentTool(agent=ticket_creator),
    AgentTool(agent=ticket_resolver),
]

# Customer Domain Coordinator
customer_domain_coordinator = LlmAgent(
    name="customer_domain_coordinator",
    model="gemini-2.5-flash",
    description="Coordinates customer domain contexts",
    instruction="""
    You coordinate the customer domain with these bounded contexts:
    1. Customer Profile - customer data and preferences
    2. Customer Support - tickets and issue resolution
    3. Customer Loyalty - rewards and engagement

    Route requests to appropriate context coordinators.
    Coordinate cross-context workflows (e.g., create profile then enroll in loyalty).
    """,
)

customer_domain_coordinator.tools = [
    AgentTool(agent=customer_profile_coordinator),
    AgentTool(agent=customer_support_coordinator),
]

# ============================================================================
# ORDER DOMAIN
# ============================================================================

# Shopping Cart Context
cart_coordinator = LlmAgent(
    name="cart_coordinator",
    model="gemini-2.5-flash",
    description="Manages shopping cart operations",
)

cart_manager = LlmAgent(
    name="cart_manager",
    model="gemini-2.5-flash",
    description="Manages cart items (add, remove, update quantities)",
)

cart_calculator = LlmAgent(
    name="cart_calculator",
    model="gemini-2.5-flash",
    description="Calculates cart totals, taxes, and discounts",
)

cart_coordinator.tools = [
    AgentTool(agent=cart_manager),
    AgentTool(agent=cart_calculator),
]

# Checkout Context
checkout_coordinator = LlmAgent(
    name="checkout_coordinator",
    model="gemini-2.5-flash",
    description="Manages checkout process",
)

address_validator = LlmAgent(
    name="address_validator",
    model="gemini-2.5-flash",
    description="Validates shipping addresses",
)

shipping_calculator = LlmAgent(
    name="shipping_calculator",
    model="gemini-2.5-flash",
    description="Calculates shipping costs and delivery dates",
)

order_placer = LlmAgent(
    name="order_placer",
    model="gemini-2.5-flash",
    description="Places final order and creates order record",
)

checkout_coordinator.tools = [
    AgentTool(agent=address_validator),
    AgentTool(agent=shipping_calculator),
    AgentTool(agent=order_placer),
]

# Order Domain Coordinator
order_domain_coordinator = LlmAgent(
    name="order_domain_coordinator",
    model="gemini-2.5-flash",
    description="Coordinates order domain contexts",
    instruction="""
    You coordinate the order domain with these bounded contexts:
    1. Shopping Cart - cart management and calculations
    2. Checkout - address validation, shipping, order placement
    3. Order Fulfillment - order processing and tracking

    Route requests to appropriate context coordinators.
    Coordinate order lifecycle from cart to fulfillment.
    """,
)

order_domain_coordinator.tools = [
    AgentTool(agent=cart_coordinator),
    AgentTool(agent=checkout_coordinator),
]

# ============================================================================
# PRODUCT DOMAIN
# ============================================================================

# Catalog Context
catalog_coordinator = LlmAgent(
    name="catalog_coordinator",
    model="gemini-2.5-flash",
    description="Manages product catalog operations",
)

product_search = LlmAgent(
    name="product_search",
    model="gemini-2.5-flash",
    description="Searches products by various criteria",
)

product_details = LlmAgent(
    name="product_details",
    model="gemini-2.5-flash",
    description="Retrieves detailed product information",
)

catalog_coordinator.tools = [
    AgentTool(agent=product_search),
    AgentTool(agent=product_details),
]

# Inventory Context
inventory_coordinator = LlmAgent(
    name="inventory_coordinator",
    model="gemini-2.5-flash",
    description="Manages inventory operations",
)

stock_checker = LlmAgent(
    name="stock_checker",
    model="gemini-2.5-flash",
    description="Checks product stock availability",
)

inventory_reservor = LlmAgent(
    name="inventory_reservor",
    model="gemini-2.5-flash",
    description="Reserves inventory for orders",
)

inventory_coordinator.tools = [
    AgentTool(agent=stock_checker),
    AgentTool(agent=inventory_reservor),
]

# Pricing Context
pricing_coordinator = LlmAgent(
    name="pricing_coordinator",
    model="gemini-2.5-flash",
    description="Manages pricing operations",
)

price_calculator = LlmAgent(
    name="price_calculator",
    model="gemini-2.5-flash",
    description="Calculates product prices with discounts",
)

promotion_applier = LlmAgent(
    name="promotion_applier",
    model="gemini-2.5-flash",
    description="Applies promotional codes and offers",
)

pricing_coordinator.tools = [
    AgentTool(agent=price_calculator),
    AgentTool(agent=promotion_applier),
]

# Product Domain Coordinator
product_domain_coordinator = LlmAgent(
    name="product_domain_coordinator",
    model="gemini-2.5-flash",
    description="Coordinates product domain contexts",
    instruction="""
    You coordinate the product domain with these bounded contexts:
    1. Catalog - product search and details
    2. Inventory - stock availability and reservation
    3. Pricing - price calculation and promotions

    Route requests to appropriate context coordinators.
    Coordinate product operations across contexts.
    """,
)

product_domain_coordinator.tools = [
    AgentTool(agent=catalog_coordinator),
    AgentTool(agent=inventory_coordinator),
    AgentTool(agent=pricing_coordinator),
]

# ============================================================================
# PAYMENT DOMAIN
# ============================================================================

# Payment Processing Context
payment_coordinator = LlmAgent(
    name="payment_coordinator",
    model="gemini-2.5-flash",
    description="Manages payment processing",
)

payment_validator = LlmAgent(
    name="payment_validator",
    model="gemini-2.5-flash",
    description="Validates payment information",
)

payment_processor = LlmAgent(
    name="payment_processor",
    model="gemini-2.5-flash",
    description="Processes payments through payment gateway",
)

payment_coordinator.tools = [
    AgentTool(agent=payment_validator),
    AgentTool(agent=payment_processor),
]

# Payment Domain Coordinator
payment_domain_coordinator = LlmAgent(
    name="payment_domain_coordinator",
    model="gemini-2.5-flash",
    description="Coordinates payment domain contexts",
)

payment_domain_coordinator.tools = [
    AgentTool(agent=payment_coordinator),
]

# ============================================================================
# PLATFORM COORDINATOR (ROOT)
# ============================================================================

platform_coordinator = LlmAgent(
    name="platform_coordinator",
    model="gemini-2.5-pro",
    description="E-commerce platform coordinator",
    instruction="""
    You are the platform coordinator for the e-commerce system.

    Business Domains:
    1. Customer - customer profiles, support, loyalty
    2. Order - carts, checkout, fulfillment
    3. Product - catalog, inventory, pricing
    4. Payment - payment processing, billing, refunds

    Route requests to appropriate domain coordinators.
    Coordinate cross-domain workflows.
    Ensure domain boundaries are respected.
    """,
)

platform_coordinator.tools = [
    AgentTool(agent=customer_domain_coordinator),
    AgentTool(agent=order_domain_coordinator),
    AgentTool(agent=product_domain_coordinator),
    AgentTool(agent=payment_domain_coordinator),
]

# ============================================================================
# DOMAIN EVENT BUS
# ============================================================================

from typing import Callable, Dict, List

class DomainEventBus:
    """Event bus for cross-domain communication."""

    def __init__(self):
        self.subscriptions: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to domain event."""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(handler)

    async def publish(self, event_type: str, event_data: dict):
        """Publish domain event."""
        handlers = self.subscriptions.get(event_type, [])
        for handler in handlers:
            await handler(event_data)

# Create event bus
event_bus = DomainEventBus()

# Define domain events
class DomainEvents:
    # Customer Domain
    CUSTOMER_REGISTERED = "customer.registered"
    CUSTOMER_UPDATED = "customer.updated"

    # Order Domain
    CART_CREATED = "order.cart_created"
    ORDER_PLACED = "order.placed"
    ORDER_COMPLETED = "order.completed"

    # Product Domain
    PRODUCT_OUT_OF_STOCK = "product.out_of_stock"
    INVENTORY_RESERVED = "product.inventory_reserved"

    # Payment Domain
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"

# Set up cross-domain event handlers

async def on_customer_registered(event: dict):
    """When customer registers, create loyalty account."""
    customer_id = event["customer_id"]
    # Trigger loyalty context
    await loyalty_coordinator.invoke(f"Create loyalty account for {customer_id}")

async def on_order_placed(event: dict):
    """When order placed, reserve inventory."""
    order_id = event["order_id"]
    items = event["items"]
    # Trigger inventory reservation
    await inventory_coordinator.invoke(f"Reserve inventory for order {order_id}")

async def on_payment_completed(event: dict):
    """When payment completes, mark order as paid."""
    order_id = event["order_id"]
    # Trigger order fulfillment
    await fulfillment_coordinator.invoke(f"Process order {order_id}")

# Subscribe to events
event_bus.subscribe(DomainEvents.CUSTOMER_REGISTERED, on_customer_registered)
event_bus.subscribe(DomainEvents.ORDER_PLACED, on_order_placed)
event_bus.subscribe(DomainEvents.PAYMENT_COMPLETED, on_payment_completed)

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_purchase_flow():
    """Complete purchase flow across multiple domains."""

    # 1. Customer searches for product (Product Domain)
    search_result = await platform_coordinator.invoke(
        "Search for wireless headphones under $200"
    )
    # Routes: platform → product_domain → catalog_coordinator → product_search

    # 2. Add to cart (Order Domain)
    cart_result = await platform_coordinator.invoke(
        "Add product SKU-12345 to cart"
    )
    # Routes: platform → order_domain → cart_coordinator → cart_manager
    # Publishes: order.cart_created event

    # 3. Check inventory (Product Domain)
    inventory_result = await platform_coordinator.invoke(
        "Check stock for SKU-12345"
    )
    # Routes: platform → product_domain → inventory_coordinator → stock_checker

    # 4. Proceed to checkout (Order Domain)
    checkout_result = await platform_coordinator.invoke(
        "Checkout cart with shipping address: 123 Main St, San Francisco, CA"
    )
    # Routes: platform → order_domain → checkout_coordinator → address_validator
    # Then: shipping_calculator → order_placer
    # Publishes: order.placed event

    # 5. Process payment (Payment Domain)
    payment_result = await platform_coordinator.invoke(
        "Process payment for order ORD-12345 with card ending 4242"
    )
    # Routes: platform → payment_domain → payment_coordinator → payment_processor
    # Publishes: payment.completed event (triggers inventory reservation + fulfillment)

async def example_customer_support():
    """Customer support flow across domains."""

    # Customer has payment issue
    support_result = await platform_coordinator.invoke(
        "Customer reports failed payment for order ORD-12345"
    )
    # Routes: platform → customer_domain → customer_support → ticket_creator

    # Support needs to check order details (cross-domain)
    order_details = await platform_coordinator.invoke(
        "Get order details for ORD-12345"
    )
    # Routes: platform → order_domain

    # Support needs to retry payment (cross-domain)
    retry_payment = await platform_coordinator.invoke(
        "Retry payment for order ORD-12345"
    )
    # Routes: platform → payment_domain

# ============================================================================
# DOMAIN BOUNDARIES
# ============================================================================

class DomainBoundaryValidator:
    """Enforce domain boundaries and anti-corruption layers."""

    def __init__(self):
        self.domain_ownership = {
            "customer": ["customer_id", "customer_profile", "customer_preferences"],
            "order": ["order_id", "cart_id", "order_items"],
            "product": ["product_id", "sku", "inventory"],
            "payment": ["payment_id", "transaction_id", "payment_method"],
        }

    def validate_cross_domain_access(
        self,
        source_domain: str,
        target_domain: str,
        accessed_fields: List[str],
    ) -> bool:
        """Validate cross-domain data access."""
        if source_domain == target_domain:
            return True

        # Check if accessing fields owned by target domain
        target_owned = self.domain_ownership.get(target_domain, [])
        for field in accessed_fields:
            if field not in target_owned:
                raise ValueError(
                    f"Domain {source_domain} cannot access {field} from {target_domain}"
                )

        return True

# Usage
validator = DomainBoundaryValidator()

# Valid: Order domain accessing product data
validator.validate_cross_domain_access(
    source_domain="order",
    target_domain="product",
    accessed_fields=["product_id", "sku"],
)

# Invalid: Order domain accessing customer preferences
# validator.validate_cross_domain_access(
#     source_domain="order",
#     target_domain="customer",
#     accessed_fields=["customer_preferences"],  # Raises ValueError
# )
```

## Benefits of Domain-Driven Agent Architecture

### 1. Clear Ownership

Each domain has clear ownership of data and business logic:
- **Customer Domain** owns customer data and relationships
- **Order Domain** owns order lifecycle
- **Product Domain** owns product catalog and inventory
- **Payment Domain** owns payment processing

### 2. Loose Coupling

Domains communicate through:
- Domain events (asynchronous)
- Anti-corruption layers (validation)
- Well-defined interfaces (coordinator agents)

### 3. Independent Scaling

Scale domains independently based on load:
- High product search traffic → scale Product domain agents
- High order volume → scale Order domain agents

### 4. Team Alignment

Agent teams align to organizational structure:
- Customer team → Customer domain agents
- Product team → Product domain agents
- Payments team → Payment domain agents

## Testing Domain Boundaries

```python
import pytest

@pytest.mark.asyncio
async def test_order_placement_flow():
    """Test complete order placement across domains."""

    # Given: Customer, product, and inventory exist
    customer_id = "CUST-123"
    product_id = "PROD-456"

    # When: Place order
    result = await platform_coordinator.invoke(
        f"Place order for customer {customer_id}, product {product_id}"
    )

    # Then: Should coordinate across domains
    assert "order.placed" in result.events_published
    assert "inventory.reserved" in result.events_published
    assert result.order_id is not None

@pytest.mark.asyncio
async def test_domain_boundary_enforcement():
    """Test that domain boundaries are enforced."""

    validator = DomainBoundaryValidator()

    # Should raise error when accessing private domain data
    with pytest.raises(ValueError):
        validator.validate_cross_domain_access(
            source_domain="order",
            target_domain="customer",
            accessed_fields=["customer_password_hash"],  # Private field
        )
```
