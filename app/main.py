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

BASE_URL = "https://occupancy-os.vercel.app"


# ==================== AUTH DEPENDENCY ====================
async def get_user_from_cookie(access_token: str = Cookie(None)):
    return get_current_user(access_token)


# ==================== PAGE ROUTES ====================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_user_from_cookie)):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "seo": SEO_CONFIG["home"],
        "user": user,
        "current_year": datetime.now().year
    })


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "seo": SEO_CONFIG["signup"],
        "current_year": datetime.now().year
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "seo": SEO_CONFIG["login"],
        "current_year": datetime.now().year
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_user_from_cookie)):
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    subscription_data = None
    audits_data = []

    if supabase:
        subscription_data = ensure_user_subscription(user.id, user.email)

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
    audits_remaining = None
    plan = "free"

    if user and supabase:
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
    return templates.TemplateResponse("tos.html", {
        "request": request,
        "seo": {
            "title": "Terms of Service - OccupancyOS",
            "description": "OccupancyOS Terms of Service.",
            "keywords": "terms of service, legal agreement",
            "og_image": f"{BASE_URL}/static/og-image.jpg"
        },
        "current_year": datetime.now().year
    })


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    return templates.TemplateResponse("privacy.html", {
        "request": request,
        "seo": {
            "title": "Privacy Policy - OccupancyOS",
            "description": "OccupancyOS Privacy Policy.",
            "keywords": "privacy policy, data protection",
            "og_image": f"{BASE_URL}/static/og-image.jpg"
        },
        "current_year": datetime.now().year
    })


# ==================== API ROUTES ====================
@app.post("/api/signup")
async def signup(request: Request, email: str = Form(...), password: str = Form(...), tos_accepted: str = Form(None)):
    try:
        tos_bool = tos_accepted in ("on", "true")
        if not tos_bool:
            return JSONResponse({"success": False, "error": "You must accept the Terms."}, status_code=400)

        client_ip = request.client.host if request.client else None
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        result = await auth_service.signup_user(email, password, tos_bool, client_ip)
        return JSONResponse(result)

    except Exception as e:
        return JSONResponse({"success": False, "error": "Signup failed."}, status_code=400)


@app.post("/api/login")
async def login(email: str = Form(...), password: str = Form(...)):
    try:
        token = await auth_service.login_user(email, password)
        response = JSONResponse({"success": True, "redirect": "/dashboard"})
        response.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=3600 * 24 * 7)
        return response
    except Exception:
        return JSONResponse({"success": False, "error": "Invalid email or password"}, status_code=401)


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response


@app.post("/api/redeem-license")
async def redeem_license(license_key: str = Form(...), user=Depends(get_user_from_cookie)):
    if not user:
        return JSONResponse({"error": "Please log in", "login_required": True}, status_code=401)

    try:
        result = await license_service.redeem_license(license_key, user.id, user.email)
        return JSONResponse({"success": True, **result})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@app.post("/api/audit")
async def audit(request: Request, title: str = Form(...), description: str = Form(...), property_type: str = Form(...),
                target_audience: str = Form("All Audiences"), amenities: str = Form(""), user=Depends(get_user_from_cookie)):
    try:
        result = await audit_service.analyze_listing(title, description, property_type, target_audience, amenities, user.id if user else None)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ==================== SEO ROUTES ====================
@app.get("/sitemap.xml", include_in_schema=False)
@app.head("/sitemap.xml", include_in_schema=False)
async def sitemap():
    current_date = datetime.now().strftime("%Y-%m-%d")

    pages = ["/", "/audit", "/signup", "/login", "/tos", "/privacy"]

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    for path in pages:
        xml.append("  <url>")
        xml.append(f"    <loc>{BASE_URL}{path}</loc>")
        xml.append(f"    <lastmod>{current_date}</lastmod>")
        xml.append("    <changefreq>weekly</changefreq>")
        xml.append("    <priority>0.8</priority>")
        xml.append("  </url>")

    xml.append("</urlset>")
    return Response("\n".join(xml), media_type="application/xml")


@app.get("/robots.txt", include_in_schema=False)
@app.head("/robots.txt", include_in_schema=False)
async def robots():
    content = f"""User-agent: *
Allow: /
Disallow: /api/
Disallow: /dashboard

Sitemap: {BASE_URL}/sitemap.xml
"""
    return Response(content, media_type="text/plain")


@app.get("/health")
async def health():
    return {"status": "healthy"}
