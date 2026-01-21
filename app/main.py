from fastapi import FastAPI, Request, Form, Depends, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.config import SEO_CONFIG, GUMROAD_PRODUCT_URL
from app.database import get_current_user, ensure_user_subscription, supabase
from app.services import auth_service, license_service, audit_service

# Initialize FastAPI
app = FastAPI(title="OccupancyOS - Airbnb Listing Optimizer")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ==================== AUTH DEPENDENCY ====================
async def get_user_from_cookie(access_token: str = Cookie(None)):
    """Get current user from cookie"""
    return get_current_user(access_token)


# ==================== PAGE ROUTES ====================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_user_from_cookie)):
    """Landing page"""
    return templates.TemplateResponse("home.html", {
        "request": request,
        "seo": SEO_CONFIG["home"],
        "user": user,
        "current_year": datetime.now().year
    })


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page"""
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "seo": SEO_CONFIG["signup"],
        "current_year": datetime.now().year
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "seo": SEO_CONFIG["login"],
        "current_year": datetime.now().year
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_user_from_cookie)):
    """User dashboard with subscription guarantee"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    subscription_data = None
    audits_data = []
    
    if supabase:
        # Ensure subscription exists
        subscription_data = ensure_user_subscription(user.id, user.email)
        
        # Fetch audit history
        try:
            audits = supabase.table("audit_history")\
                .select("*")\
                .eq("user_id", user.id)\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()
            audits_data = audits.data if audits.data else []
        except Exception as e:
            print(f"Failed to fetch audits: {e}")
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "seo": SEO_CONFIG["dashboard"],
        "user": user,
        "subscription": subscription_data,
        "audits": audits_data,
        "gumroad_url": GUMROAD_PRODUCT_URL,
        "current_year": datetime.now().year
    })


@app.get("/audit", response_class=HTMLResponse)
async def audit_page(request: Request, user=Depends(get_user_from_cookie)):
    """Audit tool page"""
    audits_remaining = None
    plan = "free"
    
    if user and supabase:
        # Ensure subscription exists
        subscription = ensure_user_subscription(user.id, user.email)
        if subscription:
            audits_remaining = subscription.get("audits_remaining")
            plan = subscription.get("plan", "free")
    
    return templates.TemplateResponse("audit.html", {
        "request": request,
        "seo": SEO_CONFIG["audit"],
        "user": user,
        "audits_remaining": audits_remaining,
        "plan": plan,
        "gumroad_url": GUMROAD_PRODUCT_URL,
        "current_year": datetime.now().year
    })


@app.get("/tos", response_class=HTMLResponse)
async def tos_page(request: Request):
    """Terms of Service page"""
    return templates.TemplateResponse("tos.html", {
        "request": request,
        "seo": {
            "title": "Terms of Service - OccupancyOS",
            "description": "OccupancyOS Terms of Service. Review our service agreement before creating an account.",
            "keywords": "terms of service, legal agreement, user terms",
            "og_image": "https://occupancyos.com/static/og-image.jpg"
        },
        "current_year": datetime.now().year
    })


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """Privacy Policy page"""
    return templates.TemplateResponse("privacy.html", {
        "request": request,
        "seo": {
            "title": "Privacy Policy - OccupancyOS",
            "description": "OccupancyOS Privacy Policy. Learn how we collect, use, and protect your data.",
            "keywords": "privacy policy, data protection, privacy",
            "og_image": "https://occupancyos.com/static/og-image.jpg"
        },
        "current_year": datetime.now().year
    })


# ==================== API ROUTES ====================
@app.post("/api/signup")
async def signup(
    request: Request,
    email: str = Form(...), 
    password: str = Form(...),
    tos_accepted: str = Form(None)
):
    """Sign up new user with TOS acceptance and IP tracking"""
    try:
        # Validate TOS acceptance
        tos_bool = tos_accepted == "on" or tos_accepted == "true"
        
        if not tos_bool:
            return JSONResponse({
                "success": False, 
                "error": "You must accept the Terms of Service and Privacy Policy to create an account."
            }, status_code=400)
        
        # Get client IP address
        client_ip = request.client.host if request.client else None
        
        # Fallback to X-Forwarded-For header (for proxies/load balancers)
        if not client_ip or client_ip == "127.0.0.1":
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()
        
        print(f"📍 Signup IP: {client_ip}")
        
        result = await auth_service.signup_user(email, password, tos_bool, client_ip)
        return JSONResponse(result)
    except Exception as e:
        error_message = str(e)
        
        if "already registered" in error_message.lower() or "duplicate" in error_message.lower():
            error_message = "This email is already registered. Try logging in instead."
        elif "password" in error_message.lower() and "weak" in error_message.lower():
            error_message = "Password is too weak. Use at least 8 characters."
        elif "invalid" in error_message.lower() and "email" in error_message.lower():
            error_message = "Please enter a valid email address."
        elif "Terms of Service" in error_message:
            error_message = error_message  # Keep TOS error as-is
        elif len(error_message) > 200:
            error_message = "Signup failed. Please try again."
        
        return JSONResponse({"success": False, "error": error_message}, status_code=400)


@app.post("/api/login")
async def login(email: str = Form(...), password: str = Form(...)):
    """Login user"""
    try:
        token = await auth_service.login_user(email, password)
        response = JSONResponse({"success": True, "redirect": "/dashboard"})
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=3600 * 24 * 7
        )
        return response
    except Exception as e:
        error_str = str(e).lower()
        
        if "email not confirmed" in error_str:
            error_message = "Please check your email and click the confirmation link before logging in."
        else:
            error_message = "Invalid email or password"
        
        return JSONResponse({"success": False, "error": error_message}, status_code=401)


@app.get("/logout")
async def logout():
    """Logout user"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response


@app.post("/api/redeem-license")
async def redeem_license(
    license_key: str = Form(...),
    user=Depends(get_user_from_cookie)
):
    """Redeem license key"""
    if not user:
        return JSONResponse({
            "error": "Please log in to redeem a license key",
            "login_required": True
        }, status_code=401)
    
    try:
        result = await license_service.redeem_license(license_key, user.id, user.email)
        return JSONResponse({
            "success": True,
            "message": f"Successfully added {result['credits_added']} credits to your account!",
            **result
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)


@app.post("/api/audit")
async def audit(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    property_type: str = Form(...),
    target_audience: str = Form("All Audiences"),
    amenities: str = Form(""),
    user=Depends(get_user_from_cookie)
):
    """AI-powered listing analysis - FREE preview for guests, full access for users"""
    
    # NON-LOGGED IN USERS: Give preview (scores only, no solutions)
    if not user:
        try:
            result = await audit_service.analyze_listing(
                title, description, property_type, 
                target_audience, amenities, user_id=None  # Pass None for guests
            )
            
            # Mark as preview (frontend will blur solutions)
            result["is_preview"] = True
            result["requires_signup"] = True
            
            return JSONResponse(result)
        
        except audit_service.ValidationError as e:
            return JSONResponse({
                "error": str(e),
                "validation_error": True
            }, status_code=400)
        
        except Exception as e:
            error_message = str(e)
            print(f"❌ Audit error: {error_message}")
            return JSONResponse({
                "error": error_message if len(error_message) < 200 else "Analysis failed. Please try again."
            }, status_code=500)
    
    # LOGGED IN USERS: Full access with credit check
    try:
        result = await audit_service.analyze_listing(
            title, description, property_type, 
            target_audience, amenities, user.id
        )
        
        # GUARANTEE credits_remaining exists
        if "credits_remaining" not in result:
            print(f"⚠️ WARNING: credits_remaining missing, fetching manually")
            if supabase:
                try:
                    subscription = ensure_user_subscription(user.id, user.email)
                    result["credits_remaining"] = subscription.get("audits_remaining", 0) if subscription else 0
                except Exception as e:
                    print(f"❌ Failed to fetch credits: {e}")
                    result["credits_remaining"] = 0
            else:
                result["credits_remaining"] = 0
        
        result["is_preview"] = False
        
        print(f"✅ Audit response includes credits_remaining: {result.get('credits_remaining')}")
        return JSONResponse(result)
    
    except audit_service.ValidationError as e:
        return JSONResponse({
            "error": str(e),
            "validation_error": True
        }, status_code=400)
    
    except audit_service.InsufficientCreditsError as e:
        return JSONResponse({
            "error": str(e),
            "upgrade_required": True,
            "gumroad_url": GUMROAD_PRODUCT_URL
        }, status_code=403)
    
    except Exception as e:
        error_message = str(e)
        print(f"❌ Audit error: {error_message}")
        return JSONResponse({
            "error": error_message if len(error_message) < 200 else "Analysis failed. Please try again."
        }, status_code=500)


# ==================== SEO ROUTES ====================
@app.get("/sitemap.xml", response_class=Response)
async def sitemap():
    """Dynamic XML sitemap for SEO"""
    base_url = "https://occupancyos.com"
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{current_date}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base_url}/audit</loc>
    <lastmod>{current_date}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/signup</loc>
    <lastmod>{current_date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/login</loc>
    <lastmod>{current_date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>{base_url}/tos</loc>
    <lastmod>{current_date}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>{base_url}/privacy</loc>
    <lastmod>{current_date}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>"""
    
    return Response(content=xml_content, media_type="application/xml")


@app.get("/robots.txt", response_class=Response)
async def robots():
    """Robots.txt for crawler directives"""
    content = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /dashboard

Sitemap: https://occupancyos.com/sitemap.xml"""
    return Response(content=content, media_type="text/plain")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "supabase": "connected" if supabase else "not configured",
        "groq": "configured" if audit_service.groq_client else "not configured",
        "gumroad": "configured" if (license_service.GUMROAD_ACCESS_TOKEN and license_service.GUMROAD_PRODUCT_ID) else "not configured"
    }