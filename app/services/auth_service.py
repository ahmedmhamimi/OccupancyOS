from app.database import supabase, ensure_user_subscription
from datetime import datetime


async def record_tos_acceptance(user_id: str, email: str, ip_address: str = None):
    """
    Record TOS acceptance in database with user_id, email, version, timestamp, and IP
    """
    if not supabase:
        print(f"⚠ Supabase not configured - cannot record TOS acceptance")
        return False
    
    try:
        tos_record = {
            "user_id": user_id,
            "email": email,
            "tos_version": "1.0",
            "accepted_at": datetime.utcnow().isoformat(),
            "ip_address": ip_address
        }
        
        result = supabase.table("tos_acceptances").insert(tos_record).execute()
        
        if result.data:
            print(f"✓ TOS acceptance recorded for user {user_id} (IP: {ip_address})")
            return True
        else:
            print(f"⚠ TOS acceptance insert returned no data")
            return False
            
    except Exception as e:
        print(f"❌ Failed to record TOS acceptance: {e}")
        return False


async def signup_user(email: str, password: str, tos_accepted: bool = False, ip_address: str = None):
    """Sign up new user with subscription and TOS acceptance tracking"""
    if not supabase:
        raise Exception("Authentication not configured")
    
    if not tos_accepted:
        raise Exception("You must accept the Terms of Service to create an account")
    
    email = email.strip().lower()
    print(f"📝 Signup attempt for: {email}")
    
    auth_response = supabase.auth.sign_up({
        "email": email,
        "password": password
    })
    
    if auth_response.user:
        user_id = auth_response.user.id
        print(f"✓ User created with ID: {user_id}")
        
        # Ensure subscription is created
        subscription = ensure_user_subscription(user_id, email)
        
        if subscription:
            print(f"✓ Subscription confirmed for new user {user_id}")
        else:
            print(f"⚠ Subscription creation may have failed for {user_id}")
        
        # Record TOS acceptance in database
        tos_recorded = await record_tos_acceptance(user_id, email, ip_address)
        
        if not tos_recorded:
            print(f"⚠ WARNING: TOS acceptance recording failed for {user_id} - account created but TOS not logged")
        
        email_confirmed = hasattr(auth_response.user, 'email_confirmed_at') and auth_response.user.email_confirmed_at
        
        if email_confirmed:
            message = "Account created successfully! You can now log in."
        else:
            message = "Account created! Please check your email to confirm your account before logging in."
        
        return {"success": True, "message": message}
    
    raise Exception("Signup failed")


async def login_user(email: str, password: str):
    """Login user with subscription guarantee"""
    if not supabase:
        raise Exception("Authentication not configured")
    
    email = email.strip().lower()
    print(f"🔐 Login attempt for: {email}")
    
    auth_response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    
    if auth_response.session:
        user_id = auth_response.user.id
        print(f"✓ User authenticated: {email} (ID: {user_id})")
        
        # ALWAYS ensure subscription exists on every login
        subscription = ensure_user_subscription(user_id, email)
        
        if subscription:
            print(f"✓ Subscription confirmed for user {user_id}")
            print(f"   Plan: {subscription.get('plan')}")
            print(f"   Credits: {subscription.get('audits_remaining')}")
        else:
            print(f"⚠ Warning: Subscription check failed for {user_id}")
        
        return auth_response.session.access_token
    
    raise Exception("Invalid email or password")