import os
from dotenv import load_dotenv

load_dotenv()

# ==================== ENVIRONMENT VARIABLES ====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Changed from GEMINI
GUMROAD_ACCESS_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN", "")
GUMROAD_PRODUCT_ID = os.getenv("GUMROAD_PRODUCT_ID", "")
GUMROAD_PRODUCT_URL = os.getenv("GUMROAD_PRODUCT_URL", "https://gumroad.com")

# ==================== GROQ MODELS ====================
# Remove deprecated models, use only working ones
GROQ_MODELS = [
    "llama-3.3-70b-versatile",  # Newest, most reliable
    "llama-3.1-8b-instant",     # Fast fallback
    "gemma2-9b-it",             # Alternative fallback
]

# ==================== SEO CONFIGURATION ====================
SEO_CONFIG = {
    "home": {
        "title": "OccupancyOS - Airbnb SEO Tool | Increase Occupancy Rates",
        "description": "Professional Airbnb listing optimizer & SEO tool for hosts. AI-powered title generator, description rewriter, and amenity gap analysis.",
        "keywords": "airbnb seo tool, airbnb listing optimizer, occupancy rate calculator, airbnb title generator, host tools",
        "og_image": "https://occupancyos.com/static/og-image.jpg"
    },
    "audit": {
        "title": "Free Airbnb Listing Audit Tool | OccupancyOS SEO Analyzer",
        "description": "Analyze your Airbnb listing with our free AI-powered audit tool. Get SEO-optimized titles instantly.",
        "keywords": "airbnb listing audit, free airbnb seo tool, listing analyzer",
        "og_image": "https://occupancyos.com/static/og-audit.jpg"
    },
    "pricing": {
        "title": "Pricing Plans - OccupancyOS Airbnb Optimization Tool",
        "description": "Affordable pricing for Airbnb hosts. Free audits available. Pro plans start at $4.99.",
        "keywords": "airbnb tool pricing, host software pricing",
        "og_image": "https://occupancyos.com/static/og-pricing.jpg"
    },
    "dashboard": {
        "title": "Dashboard - OccupancyOS | Your Airbnb Listings",
        "description": "Manage your Airbnb listing audits and view optimization insights.",
        "keywords": "airbnb dashboard, listing management",
        "og_image": "https://occupancyos.com/static/og-image.jpg"
    },
    "signup": {
        "title": "Sign Up - OccupancyOS | Free Airbnb Listing Optimizer",
        "description": "Create your free OccupancyOS account. Get instant access to AI-powered Airbnb listing optimization.",
        "keywords": "airbnb signup, free account, listing optimizer",
        "og_image": "https://occupancyos.com/static/og-image.jpg"
    },
    "login": {
        "title": "Log In - OccupancyOS | Airbnb Listing Optimizer",
        "description": "Log in to your OccupancyOS account to access your audit history and optimized listings.",
        "keywords": "airbnb login, account access",
        "og_image": "https://occupancyos.com/static/og-image.jpg"
    }
}