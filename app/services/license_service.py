import requests
from datetime import datetime
from app.config import GUMROAD_ACCESS_TOKEN, GUMROAD_PRODUCT_ID
from app.database import supabase, ensure_user_subscription


def verify_gumroad_license(license_key: str) -> dict:
    """
    Verify license key with Gumroad API
    Returns dict with 'success' and 'data' or 'error'
    """
    if not GUMROAD_ACCESS_TOKEN or not GUMROAD_PRODUCT_ID:
        return {
            "success": False,
            "error": "Gumroad API not configured"
        }
    
    try:
        print(f"🔍 Verifying license with Gumroad API")
        print(f"   License Key: {license_key}")
        print(f"   Product ID: {GUMROAD_PRODUCT_ID}")
        
        payload = {
            "product_id": GUMROAD_PRODUCT_ID,
            "license_key": license_key,
            "access_token": GUMROAD_ACCESS_TOKEN
        }
        
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data=payload,
            timeout=10
        )
        
        result = response.json()
        
        print(f"📡 Gumroad API Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Success: {result.get('success')}")
        print(f"   Message: {result.get('message', 'N/A')}")
        
        if result.get("success"):
            purchase_data = result.get("purchase", {})
            print(f"✓ Valid license found!")
            print(f"   Email: {purchase_data.get('email')}")
            print(f"   Product: {purchase_data.get('product_name')}")
            
            if purchase_data.get("chargebacked") or purchase_data.get("refunded"):
                return {
                    "success": False,
                    "error": "This license key has been refunded or chargebacked"
                }
            
            return {
                "success": True,
                "data": {
                    "email": purchase_data.get("email"),
                    "product_name": purchase_data.get("product_name"),
                    "sale_id": purchase_data.get("sale_id"),
                    "purchase_email": purchase_data.get("email")
                }
            }
        else:
            error_message = result.get("message", "Invalid license key")
            print(f"❌ Verification failed: {error_message}")
            return {
                "success": False,
                "error": f"License verification failed: {error_message}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Verification timeout. Please try again."
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": "Network error. Please check your connection."
        }
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {
            "success": False,
            "error": f"Verification failed: {str(e)}"
        }


def increment_gumroad_license_uses(license_key: str) -> bool:
    """
    Mark license as used in Gumroad (increments use count)
    Returns True if successful
    """
    if not GUMROAD_ACCESS_TOKEN or not GUMROAD_PRODUCT_ID:
        return False
    
    try:
        print(f"📝 Incrementing license uses in Gumroad: {license_key}")
        
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_id": GUMROAD_PRODUCT_ID,
                "license_key": license_key,
                "access_token": GUMROAD_ACCESS_TOKEN,
                "increment_uses_count": "true"
            },
            timeout=10
        )
        
        result = response.json()
        
        if result.get("success"):
            print(f"✓ License use count incremented in Gumroad")
            return True
        else:
            print(f"⚠ Failed to increment use count")
            return False
            
    except Exception as e:
        print(f"❌ Error incrementing uses: {e}")
        return False


async def redeem_license(license_key: str, user_id: str, email: str):
    """
    Redeem license key with Gumroad API verification
    Ensures user has subscription before redemption
    """
    if not supabase:
        raise Exception("Service not configured")
    
    try:
        license_key = license_key.strip()
        
        print(f"🔑 License redemption attempt:")
        print(f"   User: {email}")
        print(f"   User ID: {user_id}")
        print(f"   Key: {license_key}")
        
        # STEP 0: Ensure user has subscription (create if missing)
        subscription = ensure_user_subscription(user_id, email)
        
        if not subscription:
            print(f"❌ Failed to create/get subscription for user {user_id}")
            raise Exception("Failed to access your subscription. Please contact support.")
        
        print(f"✓ Subscription confirmed for user {user_id}")
        
        # STEP 1: Check if already redeemed in our database
        existing_redemption = supabase.table("license_keys")\
            .select("*")\
            .eq("license_key", license_key)\
            .eq("redeemed", True)\
            .execute()
        
        if existing_redemption.data and len(existing_redemption.data) > 0:
            redeemed_at = existing_redemption.data[0].get("redeemed_at", "unknown date")
            print(f"❌ License already redeemed in our database")
            raise Exception(f"This license key has already been redeemed on {redeemed_at[:10]}")
        
        # STEP 2: Verify with Gumroad API
        verification = verify_gumroad_license(license_key)
        
        if not verification["success"]:
            raise Exception(verification["error"])
        
        # STEP 3: Add credits to user account
        current_credits = subscription.get("audits_remaining", 0)
        credits_to_add = 100
        new_total = current_credits + credits_to_add
        
        supabase.table("user_subscriptions")\
            .update({
                "audits_remaining": new_total,
                "plan": "pro"
            })\
            .eq("user_id", user_id)\
            .execute()
        
        print(f"✓ Credits updated in database")
        
        # STEP 4: Store redemption in our database
        supabase.table("license_keys")\
            .insert({
                "license_key": license_key,
                "email": verification["data"].get("purchase_email"),
                "credits": credits_to_add,
                "redeemed": True,
                "redeemed_by": user_id,
                "redeemed_at": datetime.utcnow().isoformat()
            })\
            .execute()
        
        print(f"✓ License redemption recorded")
        
        # STEP 5: Increment use count in Gumroad (marks as used)
        increment_gumroad_license_uses(license_key)
        
        print(f"✓ License redeemed successfully!")
        print(f"   User: {email}")
        print(f"   Credits added: {credits_to_add}")
        print(f"   Previous credits: {current_credits}")
        print(f"   New total: {new_total}")
        
        return {
            "credits_added": credits_to_add,
            "new_total": new_total
        }
        
    except Exception as e:
        print(f"❌ Redemption error: {e}")
        raise