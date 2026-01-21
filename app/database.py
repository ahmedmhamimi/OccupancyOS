from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_KEY

# ==================== INITIALIZE SUPABASE ====================
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Supabase connected successfully")
    except Exception as e:
        print(f"✗ Supabase connection failed: {e}")
else:
    print("⚠ Supabase credentials not found in environment")


# ==================== AUTH HELPER ====================
def get_current_user(access_token: str):
    """Get current user from JWT token"""
    if not access_token or not supabase:
        return None
    
    try:
        user = supabase.auth.get_user(access_token)
        return user.user if user else None
    except Exception as e:
        print(f"Auth error: {e}")
        return None


# ==================== SUBSCRIPTION HELPER ====================
def ensure_user_subscription(user_id: str, email: str = None) -> dict:
    """
    Ensure user has a subscription record
    Creates one if it doesn't exist
    Returns the subscription data
    """
    if not supabase:
        return None
    
    try:
        # Check if subscription exists
        subscription = supabase.table("user_subscriptions")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        
        if subscription.data and len(subscription.data) > 0:
            # Subscription exists
            existing_sub = subscription.data[0]
            print(f"✓ Subscription found for user {user_id}")
            
            # Update email if missing and provided
            if not existing_sub.get("email") and email:
                supabase.table("user_subscriptions")\
                    .update({"email": email.strip().lower()})\
                    .eq("user_id", user_id)\
                    .execute()
                print(f"✓ Updated email for subscription")
                existing_sub["email"] = email.strip().lower()
            
            return existing_sub
        else:
            # Create new subscription
            print(f"⚠ No subscription found for user {user_id} - creating one")
            
            new_subscription = {
                "user_id": user_id,
                "email": email.strip().lower() if email else None,
                "plan": "free",
                "audits_remaining": 1
            }
            
            result = supabase.table("user_subscriptions").insert(new_subscription).execute()
            
            if result.data and len(result.data) > 0:
                print(f"✓ Created subscription for user {user_id}")
                return result.data[0]
            else:
                print(f"❌ Failed to create subscription - no data returned")
                return None
                
    except Exception as e:
        print(f"❌ Error in ensure_user_subscription: {e}")
        return None