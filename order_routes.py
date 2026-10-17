import uuid
from decimal import Decimal
from flask import Blueprint, request, jsonify
from models import db, User, Order, OrderItem, Payment, Cart, Product
from auth import jwt_required

order_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

# ----------------------------------------------------------------------------
# Order & Checkout Endpoints
# ----------------------------------------------------------------------------

@order_bp.route("/checkout", methods=["POST"])
@jwt_required
def checkout():
    """
    Creates an order from current cart items.
    Validates inventory, snapshots prices, deducts stock, and clears the cart.
    """
    user = request.current_user
    data = request.get_json() or {}
    shipping_address = data.get("shipping_address", "").strip()

    if not shipping_address:
        return jsonify({"error": "Field 'shipping_address' is required for checkout", "status": 400}), 400

    cart_items = Cart.query.filter_by(user_id=user.id).all()
    if not cart_items:
        return jsonify({"error": "Cannot checkout an empty cart", "status": 400}), 400

    # Stock and inventory verification pass
    for item in cart_items:
        if not item.product or item.product.stock < item.quantity:
            avail = item.product.stock if item.product else 0
            name = item.product.name if item.product else "Unknown"
            return jsonify({
                "error": f"Item '{name}' has insufficient stock (Requested: {item.quantity}, In Stock: {avail})",
                "status": 400
            }), 400

    try:
        total_amount = Decimal("0.00")
        order_items_to_create = []

        # Calculate totals and prepare line items
        for item in cart_items:
            unit_price = Decimal(str(item.product.price))
            line_total = unit_price * item.quantity
            total_amount += line_total

            # Deduct inventory stock
            item.product.stock -= item.quantity

            order_items_to_create.append(
                OrderItem(
                    product_id=item.product.id,
                    quantity=item.quantity,
                    price=unit_price
                )
            )

        # Create master order
        order = Order(
            user_id=user.id,
            total_amount=total_amount,
            status="Pending",
            shipping_address=shipping_address
        )
        db.session.add(order)
        db.session.flush()  # Flush to generate order.id

        # Associate order ID with line items
        for order_item in order_items_to_create:
            order_item.order_id = order.id
            db.session.add(order_item)

        # Clear active shopping cart
        Cart.query.filter_by(user_id=user.id).delete()

        db.session.commit()

        return jsonify({
            "message": "Order created successfully",
            "order": order.to_dict(include_items=True, include_payments=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to process checkout transaction", "details": str(e), "status": 500}), 500

@order_bp.route("", methods=["GET"])
@jwt_required
def get_user_orders():
    """Retrieve all past orders for the authenticated customer."""
    user = request.current_user
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return jsonify({
        "orders": [order.to_dict(include_items=True, include_payments=True) for order in orders]
    }), 200

@order_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required
def get_order_details(order_id):
    """Retrieve detailed information for a single order."""
    user = request.current_user
    order = Order.query.get(order_id)

    if not order:
        return jsonify({"error": "Order not found", "status": 404}), 404

    # Authorization check: user can only view their own orders unless admin
    if order.user_id != user.id and user.role != "admin":
        return jsonify({"error": "Forbidden: You do not have access to this order", "status": 403}), 403

    return jsonify({
        "order": order.to_dict(include_items=True, include_payments=True)
    }), 200

@order_bp.route("/<int:order_id>/pay", methods=["POST"])
@jwt_required
def process_payment(order_id):
    """
    Mock payment processing integration (e.g. Stripe, Razorpay).
    In production, this coordinates webhook confirmations or token charges.
    """
    user = request.current_user
    order = Order.query.get(order_id)

    if not order:
        return jsonify({"error": "Order not found", "status": 404}), 404

    if order.user_id != user.id and user.role != "admin":
        return jsonify({"error": "Forbidden: You do not own this order", "status": 403}), 403

    if order.status not in ["Pending"]:
        return jsonify({
            "error": f"Order cannot be paid. Current status is '{order.status}'",
            "status": 400
        }), 400

    data = request.get_json() or {}
    payment_gateway = data.get("payment_gateway", "Stripe").strip()
    simulate_status = data.get("simulate_status", "Success").strip().capitalize()

    if simulate_status not in ["Success", "Failed", "Pending"]:
        simulate_status = "Success"

    # Generate gateway mock transaction ID
    tx_prefix = "ch_" if payment_gateway.lower() == "stripe" else "pay_"
    transaction_id = f"{tx_prefix}{uuid.uuid4().hex[:16]}"

    payment = Payment(
        order_id=order.id,
        payment_gateway=payment_gateway,
        transaction_id=transaction_id,
        amount=order.total_amount,
        status=simulate_status
    )
    db.session.add(payment)

    if simulate_status == "Success":
        order.status = "Processing"

    db.session.commit()

    return jsonify({
        "message": f"Payment {simulate_status.lower()} via {payment_gateway}",
        "payment": payment.to_dict(),
        "order": order.to_dict(include_items=True, include_payments=True)
    }), 200
