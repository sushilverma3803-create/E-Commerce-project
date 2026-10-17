from flask import Blueprint, request, jsonify
from models import db, Cart, Product
from auth import jwt_required

cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")

def calculate_cart_summary(user_id: int):
    """Utility to calculate current user's cart item count and grand total."""
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    serialized_items = [item.to_dict() for item in cart_items]
    total_quantity = sum(item.quantity for item in cart_items)
    grand_total = round(sum(item["subtotal"] for item in serialized_items), 2)
    return serialized_items, total_quantity, grand_total

# ----------------------------------------------------------------------------
# Cart Protected Endpoints
# ----------------------------------------------------------------------------

@cart_bp.route("", methods=["GET"])
@jwt_required
def get_cart():
    """Retrieve all items in the authenticated user's shopping cart."""
    user = request.current_user
    items, total_quantity, grand_total = calculate_cart_summary(user.id)

    return jsonify({
        "items": items,
        "total_items": total_quantity,
        "grand_total": grand_total
    }), 200

@cart_bp.route("", methods=["POST"])
@jwt_required
def add_to_cart():
    """
    Add a product to the user's cart.
    If the product is already in the cart, updates the quantity.
    """
    user = request.current_user
    data = request.get_json() or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not product_id:
        return jsonify({"error": "Field 'product_id' is required", "status": 400}), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({"error": "Quantity must be greater than zero", "status": 400}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Quantity must be a valid integer", "status": 400}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found", "status": 404}), 404

    if product.stock < quantity:
        return jsonify({
            "error": f"Insufficient stock. Only {product.stock} units available",
            "available_stock": product.stock,
            "status": 400
        }), 400

    existing_item = Cart.query.filter_by(user_id=user.id, product_id=product_id).first()

    if existing_item:
        new_quantity = existing_item.quantity + quantity
        if new_quantity > product.stock:
            return jsonify({
                "error": f"Cannot add {quantity} more. Total requested ({new_quantity}) exceeds available stock ({product.stock})",
                "available_stock": product.stock,
                "status": 400
            }), 400
        existing_item.quantity = new_quantity
        message = "Cart item quantity updated"
    else:
        cart_item = Cart(user_id=user.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)
        message = "Product added to cart"

    db.session.commit()
    items, total_quantity, grand_total = calculate_cart_summary(user.id)

    return jsonify({
        "message": message,
        "items": items,
        "total_items": total_quantity,
        "grand_total": grand_total
    }), 200

@cart_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required
def update_cart_item(item_id):
    """Update item quantity or remove if quantity is set to 0."""
    user = request.current_user
    data = request.get_json() or {}
    quantity = data.get("quantity")

    if quantity is None:
        return jsonify({"error": "Field 'quantity' is required", "status": 400}), 400

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return jsonify({"error": "Quantity must be an integer", "status": 400}), 400

    cart_item = Cart.query.filter_by(id=item_id, user_id=user.id).first()
    if not cart_item:
        return jsonify({"error": "Cart item not found in your cart", "status": 404}), 404

    if quantity <= 0:
        db.session.delete(cart_item)
        db.session.commit()
        items, total_quantity, grand_total = calculate_cart_summary(user.id)
        return jsonify({
            "message": "Item removed from cart",
            "items": items,
            "total_items": total_quantity,
            "grand_total": grand_total
        }), 200

    if quantity > cart_item.product.stock:
        return jsonify({
            "error": f"Cannot set quantity to {quantity}. Only {cart_item.product.stock} units available",
            "available_stock": cart_item.product.stock,
            "status": 400
        }), 400

    cart_item.quantity = quantity
    db.session.commit()

    items, total_quantity, grand_total = calculate_cart_summary(user.id)
    return jsonify({
        "message": "Cart item updated successfully",
        "items": items,
        "total_items": total_quantity,
        "grand_total": grand_total
    }), 200

@cart_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required
def remove_from_cart(item_id):
    """Delete a single line item from the user's cart."""
    user = request.current_user
    cart_item = Cart.query.filter_by(id=item_id, user_id=user.id).first()

    if not cart_item:
        return jsonify({"error": "Cart item not found in your basket", "status": 404}), 404

    db.session.delete(cart_item)
    db.session.commit()

    items, total_quantity, grand_total = calculate_cart_summary(user.id)
    return jsonify({
        "message": "Item removed from cart",
        "items": items,
        "total_items": total_quantity,
        "grand_total": grand_total
    }), 200

@cart_bp.route("/clear", methods=["DELETE"])
@jwt_required
def clear_cart():
    """Empty all contents from the user's cart."""
    user = request.current_user
    Cart.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return jsonify({
        "message": "Shopping cart cleared successfully",
        "items": [],
        "total_items": 0,
        "grand_total": 0.0
    }), 200
