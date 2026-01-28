
# **OccupancyOS – Complete Documentation**

## 📋 **Table of Contents**

* **Project Overview**
* **Features**
* **Tech Stack**
* **Project Structure**
* **Deployment Guide**
* **Environment Variables**
* **API Endpoints**
* **Frontend Pages**
* **Payment Integration**
* **Customization Guide**
* **Troubleshooting**
* **Support**

---

## 🚀 **Project Overview**

**OccupancyOS** is a production-ready SaaS application that provides **AI-powered Airbnb listing optimization**. It analyzes property listings and generates SEO-optimized titles, rewritten descriptions, amenity recommendations, and actionable insights to help hosts increase booking rates.

### **Key Highlights**

* ✅ **Fully functional authentication system** (signup, login, logout)
* ✅ **AI-powered analysis using Groq API (Llama 3.3 70B)**
* ✅ **Credit-based monetization via Gumroad license keys**
* ✅ **Guest preview mode** (blurred results)
* ✅ **User dashboard** with audit history and credit management
* ✅ **SEO optimized** (sitemap, robots.txt, meta tags)
* ✅ **Responsive UI** with Tailwind CSS
* ✅ **PostgreSQL database** via Supabase
* ✅ **Ready for serverless deployment** on Vercel

---

## ✨ **Features**

### **For Users**

* **Free Listing Audit** with AI scoring (0–100)
* **4 Optimized Title Variations** (SEO, emotional, click, audience)
* **Complete Description Rewrite** using storytelling frameworks
* **Amenity Gap Analysis** with high-ROI suggestions
* **Immediate Action Items** prioritized by impact
* **Detailed Performance Metrics** (SEO, emotional appeal, conversion)
* **One-Click Copy** for all generated content

### **For Admins**

* **Subscription management** via Supabase
* **Gumroad license redemption automation**
* **Audit history tracking**
* **TOS acceptance logging** with IP address
* **Credit system** (1 free credit, 100 credits for $4.99)

---

## 🛠️ **Tech Stack**

### **Backend**

* **Framework:** FastAPI (Python 3.11)
* **Database:** PostgreSQL via Supabase
* **Authentication:** Supabase Auth
* **AI Service:** Groq API
* **Payments:** Gumroad

### **Frontend**

* Jinja2 templates
* Tailwind CSS (CDN)
* Vanilla JavaScript

### **Deployment**

* Vercel

---

## 📁 **Project Structure**

```
OccupancyOS-master/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── audit_service.py
│   │   └── license_service.py
│   │
│   ├── static/
│   │   ├── css/styles.css
│   │   └── js/app.js
│   │
│   └── templates/
│       ├── base.html
│       ├── home.html
│       ├── audit.html
│       ├── signup.html
│       ├── login.html
│       ├── dashboard.html
│       ├── tos.html
│       └── privacy.html
│
├── requirements.txt
├── vercel.json
└── .env  (you must create this)
```


## 🚀 **Deployment Guide**

### **Prerequisites**

* Vercel account (& create a project)
* Supabase account (& create a project)
* Groq API key (for AI)
* Gumroad account (for payment)

### **1. Supabase Setup**

* Create project
* Open SQL Editor
* Copy and Paste the DatabaseCommands.txt right into supabase SQL Editor
* Copy `SUPABASE_URL` and `SUPABASE_KEY`
* Disable RLS for the license_keys and tos_acceptances tables

### **2. Groq API Key**

Get from `console.groq.com` (starts with `gsk_`)

### **3. Gumroad (for payment)**

* Create product → enable license keys → copy credentials
* Enable API keys and copy credentials

### **4. Create `.env` File**

```
GROQ_API_KEY=your_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-public-key
GUMROAD_ACCESS_TOKEN=your-token (your API key)
GUMROAD_PRODUCT_ID=your-id
GUMROAD_PRODUCT_URL=https://gumroad.com/l/yourproduct
```

---

### **6. DON'T FORGET**

* Update the Contact Info in app/templates/base.html (mentioned email 3 times)
* Update gumroad product link in app/static/js/app.js (mentioned 5 times)

---


⚠️ **Never commit `.env`**

### **5. Deploy to Vercel**

* Import GitHub repo
* Add environment variables
* Deploy

---

## 🔐 **Environment Variables**

| Variable               | Purpose           |
| ---------------------- | ----------------- |
| `GROQ_API_KEY`         | AI processing     |
| `SUPABASE_URL`         | Database URL      |
| `SUPABASE_KEY`         | Database auth key |
| `GUMROAD_ACCESS_TOKEN` | Payments          |
| `GUMROAD_PRODUCT_ID`   | Product ID        |
| `GUMROAD_PRODUCT_URL`  | Purchase link     |

---

## 🌐 **API Endpoints**

### **Public Pages**

* `GET /`
* `GET /signup`
* `GET /login`
* `GET /audit`
* `GET /tos`
* `GET /privacy`

### **API Routes**

* `POST /api/signup`
* `POST /api/login`
* `POST /api/audit`
* `POST /api/redeem-license`

### **Protected**

* `GET /dashboard`

---

## 💳 **Payment Integration**

**Flow:**

1. User buys license on Gumroad
2. Receives key
3. Enters key in dashboard
4. Backend verifies
5. Credits added

---

## 🎨 **Customization Guide**

**Branding**

* Update site name in `base.html`
* Change Tailwind colors
* Replace logo

**Pricing**

* Modify free credits in `database.py`
* Modify credit pack size in `license_service.py`
* Modify price in gumroad


---

## 🐛 **Troubleshooting**

| Issue                      | Fix                        |
| -------------------------- | -------------------------- |
| Supabase connection failed | Check URL/key              |
| Groq key error             | Verify key format          |
| 0 credits                  | User must purchase         |
| License redemption failed  | Verify Gumroad credentials |
| Blurred results            | Guest mode                 |

---

## 📧 **Support**

**Email:** [a.mhamimi@outlook.com](mailto:a.mhamimi@outlook.com)

---

## 📝 **License**

You may:

* Modify
* Rebrand
* Use commercially
* Resell source code
* Have full ownership

---

**Documentation Version:** 1.0
**Last Updated:** January 2025