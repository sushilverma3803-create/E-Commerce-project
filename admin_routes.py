import re
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import db, Product, Category, Order, OrderItem, User
from auth import admin_required


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Generate a clean URL slug from a string."""
    text = str(text).lower().strip()

    # Remove special characters
    text = re.sub(r"[^\w\s-]", "", text)

    # Replace spaces/underscores/multiple hyphens with one hyphen
    text = re.sub(r"[\s_-]+", "-", text)

    return text.strip("-")


def get_json_data():
    """Safely get JSON request body."""
    return request.get_json(silent=True) or {}


def commit_changes():
    """Commit DB changes safely."""
    try:
        db.session.commit()
        return None
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Database constraint error. Please check the submitted data.",
            "status": 409
        }), 409
    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "An unexpected database error occurred.",
            "status": 500
        }), 500


def validate_price(value):
    """Convert and validate price."""
    try:
        price = Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        return None, "Price must be a valid numeric value."

    if not price.is_finite():
        return None, "Price must be a finite number."

    if price < Decimal("0.00"):
        return None, "Price must be greater than or equal to 0."

    return price, None


def validate_stock(value):
    """Convert and validate stock."""
    try:
        stock = int(value)
    except (ValueError, TypeError):
        return None, "Stock must be an integer."

    if stock < 0:
        return None, "Stock cannot be negative."

    return stock, None


# ----------------------------------------------------------------------------
# 1. Analytics & Sales Dashboard
# ----------------------------------------------------------------------------

@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def get_dashboard_metrics():
    """
    Return dashboard analytics:
    revenue, orders, customers, products,
    low-stock products and recent orders.
    """

    # Total revenue from all non-cancelled orders
    revenue_res = (
        db.session.query(
            func.coalesce(func.sum(Order.total_amount), 0)
        )
        .filter(Order.status != "Cancelled")
        .scalar()
    )

    total_revenue = float(revenue_res or 0)

    # Counts
    total_orders = (
        db.session.query(func.count(Order.id)).scalar() or 0
    )

    total_customers = (
        db.session.query(func.count(User.id))
        .filter(User.role == "customer")
        .scalar()
        or 0
    )

    total_products = (
        db.session.query(func.count(Product.id)).scalar() or 0
    )

    # Actual low-stock count
    low_stock_count = (
        db.session.query(func.count(Product.id))
        .filter(Product.stock <= 5)
        .scalar()
        or 0
    )

    # Orders grouped by status
    status_counts_raw = (
        db.session.query(
            Order.status,
            func.count(Order.id)
        )
        .group_by(Order.status)
        .all()
    )

    orders_by_status = {
        status: count
        for status, count in status_counts_raw
    }

    # Show only 10 low-stock products
    low_stock_items = (
        Product.query
        .filter(Product.stock <= 5)
        .order_by(Product.stock.asc())
        .limit(10)
        .all()
    )

    # Recent 5 orders
    recent_orders = (
        Order.query
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    return jsonify({
        "metrics": {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "total_customers": total_customers,
            "total_products": total_products,
            "low_stock_count": low_stock_count
        },

        "orders_by_status": orders_by_status,

        "low_stock_products": [
            p.to_dict()
            for p in low_stock_items
        ],

        "recent_orders": [
            order.to_dict(
                include_items=False,
                include_payments=False
            )
            for order in recent_orders
        ]
    }), 200


# ----------------------------------------------------------------------------
# 2. Product Management
# ----------------------------------------------------------------------------

@admin_bp.route("/products", methods=["POST"])
@admin_required
def create_product():
    """Create a new product."""

    data = get_json_data()

    # -------------------------
    # Name
    # -------------------------
    name = data.get("name")

    if not isinstance(name, str):
        return jsonify({
            "error": "Field 'name' must be a string.",
            "status": 400
        }), 400

    name = name.strip()

    if not name:
        return jsonify({
            "error": "Field 'name' is required.",
            "status": 400
        }), 400

    # -------------------------
    # Category
    # -------------------------
    category_id = data.get("category_id")

    if category_id is None:
        return jsonify({
            "error": "Field 'category_id' is required.",
            "status": 400
        }), 400

    try:
        category_id = int(category_id)
    except (ValueError, TypeError):
        return jsonify({
            "error": "'category_id' must be an integer.",
            "status": 400
        }), 400

    category = db.session.get(Category, category_id)

    if not category:
        return jsonify({
            "error": "Specified category_id does not exist.",
            "status": 404
        }), 404

    # -------------------------
    # Price
    # -------------------------
    if "price" not in data:
        return jsonify({
            "error": "Field 'price' is required.",
            "status": 400
        }), 400

    price, price_error = validate_price(data.get("price"))

    if price_error:
        return jsonify({
            "error": price_error,
            "status": 400
        }), 400

    # -------------------------
    # Stock
    # -------------------------
    stock, stock_error = validate_stock(
        data.get("stock", 0)
    )

    if stock_error:
        return jsonify({
            "error": stock_error,
            "status": 400
        }), 400

    # -------------------------
    # Optional fields
    # -------------------------
    description = data.get("description")

    if description is not None:
        if not isinstance(description, str):
            return jsonify({
                "error": "'description' must be a string.",
                "status": 400
            }), 400

        description = description.strip() or None

    image_url = data.get("image_url")

    if image_url is not None:
        if not isinstance(image_url, str):
            return jsonify({
                "error": "'image_url' must be a string.",
                "status": 400
            }), 400

        image_url = image_url.strip() or None

    custom_slug = data.get("slug", "")

    if custom_slug and not isinstance(custom_slug, str):
        return jsonify({
            "error": "'slug' must be a string.",
            "status": 400
        }), 400

    # -------------------------
    # Generate slug
    # -------------------------
    slug_source = custom_slug.strip() if custom_slug else name

    slug = slugify(slug_source)

    if not slug:
        return jsonify({
            "error": "Could not generate a valid slug.",
            "status": 400
        }), 400

    # Ensure unique slug
    base_slug = slug
    counter = 1

    while db.session.query(
        Product.id
    ).filter(
        Product.slug == slug
    ).first():

        slug = f"{base_slug}-{counter}"
        counter += 1

    # -------------------------
    # Create product
    # -------------------------
    product = Product(
        name=name,
        slug=slug,
        category_id=category.id,
        price=price,
        stock=stock,
        description=description,
        image_url=image_url
    )

    db.session.add(product)

    error_response = commit_changes()

    if error_response:
        return error_response

    return jsonify({
        "message": "Product created successfully",
        "product": product.to_dict()
    }), 201


@admin_bp.route("/products/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):
    """Update an existing product."""

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({
            "error": "Product not found.",
            "status": 404
        }), 404

    data = get_json_data()

    # -------------------------
    # Name
    # -------------------------
    if "name" in data:
        if not isinstance(data["name"], str):
            return jsonify({
                "error": "'name' must be a string.",
                "status": 400
            }), 400

        new_name = data["name"].strip()

        if not new_name:
            return jsonify({
                "error": "Product name cannot be empty.",
                "status": 400
            }), 400

        product.name = new_name

    # -------------------------
    # Category
    # -------------------------
    if "category_id" in data:
        try:
            category_id = int(data["category_id"])
        except (ValueError, TypeError):
            return jsonify({
                "error": "'category_id' must be an integer.",
                "status": 400
            }), 400

        category = db.session.get(Category, category_id)

        if not category:
            return jsonify({
                "error": "Specified category_id does not exist.",
                "status": 404
            }), 404

        product.category_id = category.id

    # -------------------------
    # Price
    # -------------------------
    if "price" in data:
        price, price_error = validate_price(
            data["price"]
        )

        if price_error:
            return jsonify({
                "error": price_error,
                "status": 400
            }), 400

        product.price = price

    # -------------------------
    # Stock
    # -------------------------
    if "stock" in data:
        stock, stock_error = validate_stock(
            data["stock"]
        )

        if stock_error:
            return jsonify({
                "error": stock_error,
                "status": 400
            }), 400

        product.stock = stock

    # -------------------------
    # Description
    # -------------------------
    if "description" in data:
        if data["description"] is not None and not isinstance(
            data["description"],
            str
        ):
            return jsonify({
                "error": "'description' must be a string.",
                "status": 400
            }), 400

        product.description = (
            data["description"].strip()
            if isinstance(data["description"], str)
            else None
        )

    # -------------------------
    # Image URL
    # -------------------------
    if "image_url" in data:
        if data["image_url"] is not None and not isinstance(
            data["image_url"],
            str
        ):
            return jsonify({
                "error": "'image_url' must be a string.",
                "status": 400
            }), 400

        product.image_url = (
            data["image_url"].strip()
            if isinstance(data["image_url"], str)
            else None
        )

    # -------------------------
    # Slug
    # -------------------------
    if "slug" in data:
        if not isinstance(data["slug"], str):
            return jsonify({
                "error": "'slug' must be a string.",
                "status": 400
            }), 400

        new_slug = slugify(data["slug"])

        if not new_slug:
            return jsonify({
                "error": "Slug cannot be empty.",
                "status": 400
            }), 400

        existing = (
            Product.query
            .filter(
                Product.slug == new_slug,
                Product.id != product.id
            )
            .first()
        )

        if existing:
            return jsonify({
                "error": "A product with this slug already exists.",
                "status": 409
            }), 409

        product.slug = new_slug

    error_response = commit_changes()

    if error_response:
        return error_response

    return jsonify({
        "message": "Product updated successfully",
        "product": product.to_dict()
    }), 200


@admin_bp.route("/products/<int:product_id>/stock", methods=["PATCH"])
@admin_required
def update_product_stock(product_id):
    """Directly set or adjust product stock."""

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({
            "error": "Product not found.",
            "status": 404
        }), 404

    data = get_json_data()

    stock = data.get("stock")
    delta = data.get("delta")

    # Both supplied
    if stock is not None and delta is not None:
        return jsonify({
            "error": "Provide either 'stock' or 'delta', not both.",
            "status": 400
        }), 400

    # Set stock directly
    if stock is not None:

        new_stock, stock_error = validate_stock(stock)

        if stock_error:
            return jsonify({
                "error": stock_error,
                "status": 400
            }), 400

        product.stock = new_stock

    # Adjust stock
    elif delta is not None:

        try:
            delta = int(delta)
        except (ValueError, TypeError):
            return jsonify({
                "error": "Delta must be an integer.",
                "status": 400
            }), 400

        new_stock = product.stock + delta

        if new_stock < 0:
            return jsonify({
                "error": (
                    f"Adjustment would result in negative stock "
                    f"({new_stock})."
                ),
                "status": 400
            }), 400

        product.stock = new_stock

    else:
        return jsonify({
            "error": "Provide either 'stock' or 'delta'.",
            "status": 400
        }), 400

    error_response = commit_changes()

    if error_response:
        return error_response

    return jsonify({
        "message": "Product stock updated successfully",
        "product": product.to_dict()
    }), 200


@admin_bp.route("/products/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):
    """
    Delete a product only if it has never been used in an order.
    Otherwise, set stock to 0 instead of deleting it.
    """

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({
            "error": "Product not found.",
            "status": 404
        }), 404

    has_orders = (
        OrderItem.query
        .filter_by(product_id=product.id)
        .first()
    )

    if has_orders:
        return jsonify({
            "error": (
                "Cannot delete product because it is referenced "
                "in past customer orders. Set stock to 0 instead."
            ),
            "status": 400
        }), 400

    product_name = product.name

    db.session.delete(product)

    error_response = commit_changes()

    if error_response:
        return error_response

    return jsonify({
        "message": f"Product '{product_name}' deleted successfully."
    }), 200


# ----------------------------------------------------------------------------
# 3. Order Management
# ----------------------------------------------------------------------------

@admin_bp.route("/orders", methods=["GET"])
@admin_required
def list_all_orders():
    """Retrieve all orders with optional filtering and pagination."""

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status", type=str)

    # Safe pagination values
    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 20

    per_page = min(per_page, 100)

    query = Order.query

    if status:
        status = status.strip()

        allowed_statuses = [
            "Pending",
            "Processing",
            "Shipped",
            "Delivered",
            "Cancelled"
        ]

        if status not in allowed_statuses:
            return jsonify({
                "error": (
                    "Invalid status. Must be one of "
                    f"{allowed_statuses}"
                ),
                "status": 400
            }), 400

        query = query.filter(
            Order.status == status
        )

    paginated = (
        query
        .order_by(Order.created_at.desc())
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    )

    return jsonify({
        "orders": [
            order.to_dict(
                include_items=True,
                include_payments=True
            )
            for order in paginated.items
        ],

        "pagination": {
            "page": paginated.page,
            "per_page": paginated.per_page,
            "total_items": paginated.total,
            "total_pages": paginated.pages
        }
    }), 200


@admin_bp.route("/orders/<int:order_id>/status", methods=["PATCH"])
@admin_required
def update_order_status(order_id):
    """
    Update order status safely.

    Important:
    - Cancellation restocks inventory only once.
    - A cancelled order cannot be moved back to an active state.
    - Delivered orders cannot be cancelled through this endpoint.
    """

    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({
            "error": "Order not found.",
            "status": 404
        }), 404

    data = get_json_data()

    new_status = data.get("status")

    allowed_statuses = [
        "Pending",
        "Processing",
        "Shipped",
        "Delivered",
        "Cancelled"
    ]

    if new_status not in allowed_statuses:
        return jsonify({
            "error": (
                f"Invalid status. Must be one of {allowed_statuses}"
            ),
            "status": 400
        }), 400

    current_status = order.status

    # No change
    if current_status == new_status:
        return jsonify({
            "message": "Order status is already set to this value.",
            "order": order.to_dict(
                include_items=True,
                include_payments=True
            )
        }), 200

    # ---------------------------------------------------------
    # Prevent invalid state changes
    # ---------------------------------------------------------

    if current_status == "Cancelled":
        return jsonify({
            "error": (
                "Cancelled orders cannot be moved back "
                "to another status."
            ),
            "status": 400
        }), 400

    if current_status == "Delivered" and new_status == "Cancelled":
        return jsonify({
            "error": "Delivered orders cannot be cancelled.",
            "status": 400
        }), 400

    # For this simple system, only Pending/Processing
    # orders can be cancelled and restocked automatically.
    if new_status == "Cancelled":
        if current_status not in ["Pending", "Processing"]:
            return jsonify({
                "error": (
                    f"Order cannot be cancelled from "
                    f"'{current_status}' status."
                ),
                "status": 400
            }), 400

        # Restock exactly once
        for item in order.items:
            if item.product:
                item.product.stock += item.quantity

    order.status = new_status

    error_response = commit_changes()

    if error_response:
        return error_response

    return jsonify({
        "message": (
            f"Order status updated from "
            f"'{current_status}' to '{new_status}'."
        ),
        "order": order.to_dict(
            include_items=True,
            include_payments=True
        )
    }), 200


# ----------------------------------------------------------------------------
# 4. Customer Directory & Metrics
# ----------------------------------------------------------------------------

@admin_bp.route("/customers", methods=["GET"])
@admin_required
def list_customers():
    """Return customer accounts with order statistics."""

    customers = (
        User.query
        .filter_by(role="customer")
        .order_by(User.created_at.desc())
        .all()
    )

    results = []

    for customer in customers:

        # Count all orders
        order_count = len(customer.orders)

        # Total spent from non-cancelled orders
        total_spent = sum(
            float(order.total_amount or 0)
            for order in customer.orders
            if order.status != "Cancelled"
        )

        customer_data = customer.to_dict()

        customer_data["order_count"] = order_count
        customer_data["total_spent"] = round(
            total_spent,
            2
        )

        results.append(customer_data)

    return jsonify({
        "customers": results
    }), 200