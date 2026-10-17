from flask import Blueprint, request, jsonify
# pyrefly: ignore [missing-import]
from sqlalchemy import or_
from models import db, Product, Category

product_bp = Blueprint("products", __name__, url_prefix="/api")

# ----------------------------------------------------------------------------
# Categories Public Endpoints
# ----------------------------------------------------------------------------

@product_bp.route("/categories", methods=["GET"])
def list_categories():
    """Retrieve all available product categories."""
    categories = Category.query.order_by(Category.name.asc()).all()
    return jsonify({
        "categories": [c.to_dict(include_products_count=True) for c in categories]
    }), 200

@product_bp.route("/categories/<identifier>", methods=["GET"])
def get_category_details(identifier):
    """Retrieve category details and products by category ID or slug."""
    if identifier.isdigit():
        category = Category.query.get(int(identifier))
    else:
        category = Category.query.filter_by(slug=identifier).first()

    if not category:
        return jsonify({"error": "Category not found", "status": 404}), 404

    products = Product.query.filter_by(category_id=category.id).order_by(Product.id.desc()).all()

    return jsonify({
        "category": category.to_dict(),
        "products": [p.to_dict() for p in products]
    }), 200

# ----------------------------------------------------------------------------
# Products Public Endpoints
# ----------------------------------------------------------------------------

@product_bp.route("/products", methods=["GET"])
def list_products():
    """
    Public catalog query endpoint.
    Supports filtering by category, text keyword search, price range, sorting, and pagination.
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 48, type=int), 100)
    category_id = request.args.get("category_id", type=int)
    category_slug = request.args.get("category", type=str)
    search = request.args.get("search", request.args.get("q", "")).strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort_by = request.args.get("sort", "newest").strip().lower()

    query = Product.query

    # Category filter
    if category_id:
        query = query.filter(Product.category_id == category_id)
    elif category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)

    # Keyword search (name or description)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern)
            )
        )

    # Price range filters
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort_by == "name":
        query = query.order_by(Product.name.asc())
    else:  # 'newest' default
        query = query.order_by(Product.created_at.desc(), Product.id.desc())

    # Pagination
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "products": [p.to_dict() for p in paginated.items],
        "pagination": {
            "page": paginated.page,
            "per_page": paginated.per_page,
            "total_items": paginated.total,
            "total_pages": paginated.pages,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev
        }
    }), 200

@product_bp.route("/products/<identifier>", methods=["GET"])
def get_product(identifier):
    """Retrieve detailed product information by either ID or slug."""
    if identifier.isdigit():
        product = Product.query.get(int(identifier))
    else:
        product = Product.query.filter_by(slug=identifier).first()

    if not product:
        return jsonify({"error": "Product not found", "status": 404}), 404

    return jsonify({
        "product": product.to_dict()
    }), 200
