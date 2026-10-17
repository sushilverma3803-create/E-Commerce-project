import os
from decimal import Decimal
from app import create_app, db
from models import User, Category, Product, Order, OrderItem, Payment

app = create_app()

CATEGORIES = [
    {
        "id": 1,
        "name": "Timepieces",
        "slug": "timepieces",
        "description": "Haute Horlogerie, Tourbillons, and Perpetual Complications",
        "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=800&q=80",
    },
    {
        "id": 2,
        "name": "Jewelry",
        "slug": "jewelry",
        "description": "High Jewelry Crafted in Solid Platinum 950 and Rare Certified Gemstones",
        "image_url": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=800&q=80",
    },
    {
        "id": 3,
        "name": "Leather Goods",
        "slug": "leather-goods",
        "description": "Tuscan Vegetable-Tanned Full-Grain Leather Briefcases & Weekend Holdalls",
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=800&q=80",
    },
    {
        "id": 4,
        "name": "Fragrance",
        "slug": "fragrance",
        "description": "Rare Extraits de Parfum, Aged French Oak Cognac Essences, and Wild Ouds",
        "image_url": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=800&q=80",
    },
    {
        "id": 5,
        "name": "Apparel",
        "slug": "apparel",
        "description": "Grade-A Mongolian Cashmere Robes, Tailored Silks, and Bespoke Outerwear",
        "image_url": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?auto=format&fit=crop&w=800&q=80",
    },
    {
        "id": 6,
        "name": "Living",
        "slug": "living",
        "description": "Mouth-blown Murano Faceted Crystal and Hand-Chiseled Architectural Artifacts",
        "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80",
    },
]

PRODUCTS = [
    # --- TIMEPIECES (Category 1) ---
    {
        "name": "Chronographe Imperial Obsidian",
        "slug": "chronographe-imperial-obsidian",
        "category_id": 1,
        "price": Decimal("4850.00"),
        "stock": 8,
        "description": "Forged from brushed volcanic obsidian and 18K rose gold casing with an open-heart tourbillon movement.",
        "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Aeterna Skeleton Tourbillon",
        "slug": "aeterna-skeleton-tourbillon",
        "category_id": 1,
        "price": Decimal("7200.00"),
        "stock": 4,
        "description": "Ultra-thin manual caliber with open-worked bridges in titanium, sapphire crystal back, and hand-stitched alligator strap.",
        "image_url": "https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Nautilus Platinum Diver Complication",
        "slug": "nautilus-platinum-diver-complication",
        "category_id": 1,
        "price": Decimal("6400.00"),
        "stock": 12,
        "description": "Pressure-tested to 300 meters, solid platinum 950 case with ceramic unidirectional bezel and luminescent blue dial.",
        "image_url": "https://images.unsplash.com/photo-1533139502658-0198f920d8e8?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Royal Celestial Moonphase",
        "slug": "royal-celestial-moonphase",
        "category_id": 1,
        "price": Decimal("5900.00"),
        "stock": 6,
        "description": "Automatic chronometer with hand-engraved lapis lazuli dial, mother-of-pearl moon phase disc, and 18K yellow gold case.",
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Zenith Monopusher Heritage Chronograph",
        "slug": "zenith-monopusher-heritage-chronograph",
        "category_id": 1,
        "price": Decimal("4200.00"),
        "stock": 9,
        "description": "Vintage-inspired single-pusher chronograph with column wheel caliber, enamel dial, and hand-finished blued steel hands.",
        "image_url": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Monaco Grand Prix Carbon Edition",
        "slug": "monaco-grand-prix-carbon-edition",
        "category_id": 1,
        "price": Decimal("8100.00"),
        "stock": 3,
        "description": "Forged carbon fiber case with tachymeter scale, skeletonized oscillating weight, and perforated vulcanized rubber strap.",
        "image_url": "https://images.unsplash.com/photo-1542496658-e33a6d0d50f6?auto=format&fit=crop&w=800&q=80",
    },

    # --- JEWELRY (Category 2) ---
    {
        "name": "Astral Signet Ring in Solid Platinum",
        "slug": "astral-signet-ring-in-solid-platinum",
        "category_id": 2,
        "price": Decimal("3200.00"),
        "stock": 6,
        "description": "Platinum 950 setting holding a brilliant-cut natural Ceylon sapphire framed by pavé VVS diamonds.",
        "image_url": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Celeste Emerald Cut Diamond Collar",
        "slug": "celeste-emerald-cut-diamond-collar",
        "category_id": 2,
        "price": Decimal("8900.00"),
        "stock": 2,
        "description": "Graduated triple-row diamond necklace in 18K white gold featuring 14.5 carats of internally flawless diamonds.",
        "image_url": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Imperial Jadeite Cabochon Cufflinks",
        "slug": "imperial-jadeite-cabochon-cufflinks",
        "category_id": 2,
        "price": Decimal("2100.00"),
        "stock": 9,
        "description": "Translucent Burmese green imperial jadeite cabochons set in brushed 18K yellow gold with guilloché backing.",
        "image_url": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Solstice Rose Gold & Paraíba Pendant",
        "slug": "solstice-rose-gold-paraiba-pendant",
        "category_id": 2,
        "price": Decimal("4600.00"),
        "stock": 5,
        "description": "Vivid neon turquoise Brazilian Paraíba tourmaline set within 18K rose gold halo encrusted with micro-pavé diamonds.",
        "image_url": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Sovereign Serpenti Diamond Bangle",
        "slug": "sovereign-serpenti-diamond-bangle",
        "category_id": 2,
        "price": Decimal("5400.00"),
        "stock": 4,
        "description": "Coiled diamond-paved serpent bangle in 18K yellow gold with pear-cut ruby eyes and articulating geometric scales.",
        "image_url": "https://images.unsplash.com/photo-1611591475152-478311394c8b?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Lumina Tahitian Black Pearl Drop Earrings",
        "slug": "lumina-tahitian-black-pearl-drop-earrings",
        "category_id": 2,
        "price": Decimal("2750.00"),
        "stock": 7,
        "description": "Lustrous 14mm peacock Tahitian pearls suspended from platinum diamond-encrusted ear wires with French leverbacks.",
        "image_url": "https://images.unsplash.com/photo-1630019852942-f89202989a59?auto=format&fit=crop&w=800&q=80",
    },

    # --- LEATHER GOODS (Category 3) ---
    {
        "name": "L’Ombre Calfskin Briefcase",
        "slug": "lombre-calfskin-briefcase",
        "category_id": 3,
        "price": Decimal("2450.00"),
        "stock": 10,
        "description": "Vegetable-tanned Tuscan full-grain leather fitted with solid brass palladium hardware and suede microfiber lining.",
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Monte Carlo Weekender Holdall",
        "slug": "monte-carlo-weekender-holdall",
        "category_id": 3,
        "price": Decimal("2890.00"),
        "stock": 5,
        "description": "Hand-stitched saddle leather duffel featuring reinforced corner guards, Swiss RiRi zippers, and monogram luggage tag.",
        "image_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Sartorial Alligator Card Wallet",
        "slug": "sartorial-alligator-card-wallet",
        "category_id": 3,
        "price": Decimal("780.00"),
        "stock": 15,
        "description": "Matte Mississippiensis alligator skin in deep midnight noir with hand-painted beveled edges and eight card slots.",
        "image_url": "https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Vendôme Structured Satchel in Box Calf",
        "slug": "vendome-structured-satchel-in-box-calf",
        "category_id": 3,
        "price": Decimal("3100.00"),
        "stock": 8,
        "description": "Mirror-smooth French box calfskin with handcrafted saddle stitching, turn-lock palladium clasp, and removable shoulder strap.",
        "image_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Milano Woven Leather Backpack",
        "slug": "milano-woven-leather-backpack",
        "category_id": 3,
        "price": Decimal("2150.00"),
        "stock": 11,
        "description": "Intrecciato hand-woven nappa leather backpack featuring magnetic buckle closures, laptop sleeve, and breathable mesh back.",
        "image_url": "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "St. Tropez Grain Leather Passport Folio",
        "slug": "st-tropez-grain-leather-passport-folio",
        "category_id": 3,
        "price": Decimal("620.00"),
        "stock": 18,
        "description": "Grained Taurillon leather travel organizer with compartments for passport, boarding passes, currency, and six cards.",
        "image_url": "https://images.unsplash.com/photo-1563903530908-afdd155d057a?auto=format&fit=crop&w=800&q=80",
    },

    # --- FRAGRANCE (Category 4) ---
    {
        "name": "Nectar Botanique Extrait de Parfum",
        "slug": "nectar-botanique-extrait-de-parfum",
        "category_id": 4,
        "price": Decimal("640.00"),
        "stock": 14,
        "description": "Rare Bulgarian centifolia rose steeped in aged French oak cognac barrels with warm amber resin and smoky tobacco.",
        "image_url": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Oud Royale 1928 Pure Elixir",
        "slug": "oud-royale-1928-pure-elixir",
        "category_id": 4,
        "price": Decimal("980.00"),
        "stock": 3,
        "description": "Vintage wild Cambodian agarwood oil aged for four decades, blended with Tahitian vanilla bean and Mysore sandalwood.",
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Soleil d'Or Neroli Cologne Absolue",
        "slug": "soleil-dor-neroli-cologne-absolue",
        "category_id": 4,
        "price": Decimal("490.00"),
        "stock": 20,
        "description": "Sparkling Calabrian bergamot infused with hand-picked orange blossom blossoms and Florentine iris root.",
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Ambre Nocturne Eau de Parfum",
        "slug": "ambre-nocturne-eau-de-parfum",
        "category_id": 4,
        "price": Decimal("520.00"),
        "stock": 12,
        "description": "Sensual ambergris wrapped in Madagascar bourbon vanilla, Indonesian patchouli, and smoky labdanum resin.",
        "image_url": "https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Santal Éternel Pure Parfum",
        "slug": "santal-eternel-pure-parfum",
        "category_id": 4,
        "price": Decimal("750.00"),
        "stock": 8,
        "description": "Rare organic Mysore sandalwood aged with cardamom seed, Florentine orris butter, and violet leaf.",
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Fleur d'Hiver Extrait",
        "slug": "fleur-dhiver-extrait",
        "category_id": 4,
        "price": Decimal("680.00"),
        "stock": 9,
        "description": "Rare winter jasmine harvested at dawn, paired with chilled pink peppercorn, crisp white musk, and cedarwood.",
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=800&q=80",
    },

    # --- APPAREL (Category 5) ---
    {
        "name": "Sovereign Cashmere Robe",
        "slug": "sovereign-cashmere-robe",
        "category_id": 5,
        "price": Decimal("1290.00"),
        "stock": 7,
        "description": "Hand-woven grade-A Mongolian white cashmere with satin silk lapels and tailored monogram detailing.",
        "image_url": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Venetian Silk Jacquard Smoking Jacket",
        "slug": "venetian-silk-jacquard-smoking-jacket",
        "category_id": 5,
        "price": Decimal("1850.00"),
        "stock": 4,
        "description": "Woven on antique Jacquard looms in Como, Italy, with quilted silk velvet collar and braided frog closures.",
        "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Heirloom Vicuña Travelling Cape",
        "slug": "heirloom-vicuna-travelling-cape",
        "category_id": 5,
        "price": Decimal("5400.00"),
        "stock": 2,
        "description": "Harvested from wild Peruvian vicuña, the golden fleece of the Andes, un-dyed in its purest natural cinnamon hue.",
        "image_url": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Savile Row Double-Breasted Wool Trench",
        "slug": "savile-row-double-breasted-wool-trench",
        "category_id": 5,
        "price": Decimal("2600.00"),
        "stock": 5,
        "description": "Water-repellent English cavalry twill wool tailored with horn buttons, storm flaps, and silk twill lining.",
        "image_url": "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Como Silk Charmeuse Evening Gown",
        "slug": "como-silk-charmeuse-evening-gown",
        "category_id": 5,
        "price": Decimal("3400.00"),
        "stock": 3,
        "description": "Fluid emerald green heavy silk charmeuse with bias-cut silhouette, draped cowled back, and delicate train.",
        "image_url": "https://images.unsplash.com/photo-1518049362265-d5b2a6467637?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Alpaca & Silk Knit Oversized Cardigan",
        "slug": "alpaca-silk-knit-oversized-cardigan",
        "category_id": 5,
        "price": Decimal("1150.00"),
        "stock": 10,
        "description": "Ultra-soft royal baby alpaca spun with mulberry silk, featuring mother-of-pearl buttons and drop shoulders.",
        "image_url": "https://images.unsplash.com/photo-1485968579580-b6d095142e6e?auto=format&fit=crop&w=800&q=80",
    },

    # --- LIVING (Category 6) ---
    {
        "name": "Venetian Sculpted Glass Decanter",
        "slug": "venetian-sculpted-glass-decanter",
        "category_id": 6,
        "price": Decimal("880.00"),
        "stock": 6,
        "description": "Mouth-blown Murano crystalline glass with hand-chiseled geometric facets and 24K gold foil flakes.",
        "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Carrara Marble Sculptural Chess Set",
        "slug": "carrara-marble-sculptural-chess-set",
        "category_id": 6,
        "price": Decimal("3100.00"),
        "stock": 3,
        "description": "Solid Italian Bianco Carrara and Belgian Black marble, hand-carved minimalist pieces with velvet storage coffer.",
        "image_url": "https://images.unsplash.com/photo-1529699211952-734e80c4d42b?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Imperial Gilt Bronze Candelabra",
        "slug": "imperial-gilt-bronze-candelabra",
        "category_id": 6,
        "price": Decimal("1650.00"),
        "stock": 8,
        "description": "Neo-classical five-branch candelabra cast in heavy bronze and electroplated in 24K French ormolu gold.",
        "image_url": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Kyphi Scented Porcelain Diffuser Vessel",
        "slug": "kyphi-scented-porcelain-diffuser-vessel",
        "category_id": 6,
        "price": Decimal("420.00"),
        "stock": 14,
        "description": "Hand-cast Limoges porcelain vessel with 24K gold rim, accompanied by diffuser reeds and kyphi oil elixir.",
        "image_url": "https://images.unsplash.com/photo-1602928321679-560bb453f190?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Obsidian & Brass Architectural Hourglass",
        "slug": "obsidian-brass-architectural-hourglass",
        "category_id": 6,
        "price": Decimal("790.00"),
        "stock": 7,
        "description": "Hand-turned solid satin brass armature holding hand-blown borosilicate glass filled with black magnetite sand.",
        "image_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Bohemian Cut-Crystal Champagne Coupes (Set of 4)",
        "slug": "bohemian-cut-crystal-champagne-coupes-set-of-4",
        "category_id": 6,
        "price": Decimal("950.00"),
        "stock": 12,
        "description": "Hand-chiseled lead crystal coupes with vintage optic diamond facets, designed for vintage grand crus.",
        "image_url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=800&q=80",
    },
]

def seed_database():
    with app.app_context():
        print("Recreating database tables...")
        db.create_all()

        # 1. Seed or update Categories
        print("Seeding Categories...")
        for cat_data in CATEGORIES:
            cat = Category.query.filter_by(slug=cat_data["slug"]).first()
            if not cat:
                cat = Category(**cat_data)
                db.session.add(cat)
            else:
                cat.name = cat_data["name"]
                cat.description = cat_data["description"]
                cat.image_url = cat_data["image_url"]
        db.session.commit()

        # 2. Seed or update Products
        print("Seeding Products...")
        for p_data in PRODUCTS:
            prod = Product.query.filter_by(slug=p_data["slug"]).first()
            if not prod:
                prod = Product(**p_data)
                db.session.add(prod)
            else:
                prod.price = p_data["price"]
                prod.stock = p_data["stock"]
                prod.description = p_data["description"]
                prod.image_url = p_data["image_url"]
                prod.category_id = p_data["category_id"]
        db.session.commit()

        # 3. Seed Admin and Customer Users
        print("Seeding Users...")
        admin = User.query.filter_by(email="admin@example.com").first()
        if not admin:
            admin = User(name="Maison Administrator", email="admin@example.com", role="admin", phone="+1 (555) 999-0001")
            admin.set_password("admin123")
            db.session.add(admin)

        customer = User.query.filter_by(email="test@example.com").first()
        if not customer:
            customer = User(name="Countess Vivienne", email="test@example.com", role="customer", phone="+1 (555) 234-5678")
            customer.set_password("password123")
            db.session.add(customer)

        db.session.commit()

        # 4. Seed sample past orders for the customer
        if customer and not customer.orders:
            print("Seeding Sample Orders...")
            sample_product = Product.query.first()
            if sample_product:
                ord1 = Order(
                    user_id=customer.id,
                    total_amount=sample_product.price,
                    status="Delivered",
                    shipping_address="740 Park Avenue, Apt 14B, New York, NY 10021"
                )
                db.session.add(ord1)
                db.session.flush()

                item1 = OrderItem(order_id=ord1.id, product_id=sample_product.id, quantity=1, price=sample_product.price)
                db.session.add(item1)

                pay1 = Payment(order_id=ord1.id, payment_gateway="Stripe", transaction_id="ch_3M8Zk82eZvKYlo2C", amount=sample_product.price, status="Success")
                db.session.add(pay1)

                db.session.commit()

        total_prods = Product.query.count()
        total_cats = Category.query.count()
        total_users = User.query.count()
        print(f"Database seeded successfully: {total_prods} products, {total_cats} categories, {total_users} users.")

if __name__ == "__main__":
    seed_database()
