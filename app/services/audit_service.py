import json
from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODELS
from app.database import supabase, ensure_user_subscription

# Configure Groq
groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✓ Groq API configured")
else:
    print("⚠ Groq API key not found")

def clean_json_response(text: str) -> str:
    """Remove markdown code blocks and clean JSON response"""
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class InsufficientCreditsError(Exception):
    """Custom exception for insufficient credits"""
    pass

class AIServiceError(Exception):
    """Custom exception for AI service failures"""
    pass

async def analyze_listing(title: str, description: str, property_type: str,
                         target_audience: str, amenities: str, user_id: str = None):
    """
    AI-powered listing analysis using Groq with brutal honesty
    """
    
    # DEBUG: See exactly what we're receiving
    print("=" * 50)
    print(f"🔍 ANALYZE_LISTING CALLED")
    print(f"   user_id: '{user_id}' (type: {type(user_id).__name__})")
    print(f"   is None: {user_id is None}")
    print(f"   is empty string: {user_id == ''}")
    print(f"   is 'null' string: {user_id == 'null'}")
    print("=" * 50)
    
    # ==================== VALIDATION ====================
    if not title or not title.strip():
        raise ValidationError("Please enter a listing title")
    
    if not description or not description.strip():
        raise ValidationError("Please enter a listing description")
    
    if not property_type or property_type.strip() == "":
        raise ValidationError("Please select a property type from the dropdown")
    
    if not target_audience or target_audience.strip() == "":
        target_audience = "All Audiences"
    
    amenities_list = [a.strip() for a in amenities.split(",") if a.strip()]
    if not amenities_list:
        amenities_list = ["No specific amenities listed"]
    
    # ==================== USER TYPE & CREDIT CHECK ====================
    # Fix: Better guest detection - handle None, empty string, and "null" string
    is_guest = (user_id is None or user_id == "" or user_id == "null" or str(user_id).strip() == "")
    credits_before = 0
    credits_after = 0
    
    print(f"👤 Guest user detected: {is_guest}")
    
    # For authenticated users, check credits BEFORE running AI
    if not is_guest and supabase:
        subscription = ensure_user_subscription(user_id, None)
        
        if not subscription:
            print(f"❌ Failed to verify subscription for user {user_id}")
            raise Exception("Unable to verify your account. Please contact support.")
        
        credits_before = subscription.get("audits_remaining", 0)
        plan = subscription.get("plan", "free")
        
        print(f"🔍 Credit check for user {user_id}:")
        print(f"   Plan: {plan}")
        print(f"   Credits BEFORE audit: {credits_before}")
        
        if credits_before <= 0:
            print(f"❌ User {user_id} has 0 credits - BLOCKING AUDIT")
            raise InsufficientCreditsError("You've used all your audit credits. Purchase more to continue optimizing your listings!")
    else:
        print(f"👤 Guest user - unlimited previews allowed (results will be blurred)")
    
    # ==================== AI ANALYSIS (for BOTH guests and authenticated) ====================
    try:
        system_prompt = f"""You are a BRUTAL but FAIR Airbnb listing critic with 15 years of experience. You give harsh truth when deserved, but you also recognize genuinely excellent work.

LISTING TO ANALYZE:

Title: {title}
Description: {description}
Property Type: {property_type}
Target Audience: {target_audience}
Current Amenities: {', '.join(amenities_list)}

Return this EXACT JSON structure:
{{
  "overall_score": <0-100>,
  "overall_explanation": "2-3 sentences of HONEST assessment - harsh if bad, praise if genuinely good",
  "detailed_scores": {{
    "seo_optimization": {{"score": <0-100>, "explanation": "honest feedback", "recommendations": "specific fixes based ONLY on what user provided"}},
    "emotional_appeal": {{"score": <0-100>, "explanation": "fair assessment", "improvements": "what's wrong or what's right"}},
    "description_quality": {{"score": <0-100>, "word_count": <actual count>, "structure_issues": ["real issues found"], "strengths": ["genuine strengths if any"]}},
    "amenity_coverage": {{"score": <0-100>, "critical_missing": ["amenities that would help THIS property type and audience"]}},
    "target_audience_alignment": {{"score": <0-100>, "recommendations": "fix targeting based on actual content"}},
    "booking_conversion_potential": {{"score": <0-100>, "friction_points": ["real dealbreakers from the listing"]}}
  }},
  "optimized_titles": {{
    "seo_focused": "keyword-rich title using ONLY info user provided - no beach/mountain/downtown unless they mentioned it",
    "emotional_focused": "emotion-driven title based on ACTUAL listing features",
    "click_optimized": "curiosity title using REAL property details",
    "audience_specific": "title for {target_audience} using ONLY verified info"
  }},
  "description_rewrite": {{
    "full_rewrite": "400-word rewrite in PLAIN TEXT using ONLY the information provided. No assumptions about location, views, or amenities not mentioned. If user said 'no kids', work with that truthfully. No markdown, no asterisks.",
    "hook_section": "compelling opening using REAL details from listing",
    "key_improvements": ["actual fixes applied to their specific listing"]
  }},
  "amenity_analysis": {{
    "high_roi_additions": [
      {{"amenity": "realistic addition for THIS property", "estimated_roi": "honest estimate", "priority": "critical/high/medium", "reasoning": "why this makes sense for {property_type} targeting {target_audience}"}}
    ]
  }},
  "immediate_action_items": [
    {{"action": "specific task based on their ACTUAL listing", "impact": "critical/high/medium", "effort": "quick-win/moderate/significant", "why": "realistic expected outcome"}}
  ],
  "critical_warnings": ["severe issues if found - empty array if listing is actually good"]
}}

CRITICAL: Return ONLY valid JSON. No explanations before or after. Ensure all JSON is complete and properly closed.

BRUTAL BUT HONEST SCORING CRITERIA - BE EXTREMELY HARSH:

0-10: Complete disaster. Fatal contradictions, offensive content, or essentially empty.
  Example: Title "not good" + description "get away" = 8/100 (CATASTROPHIC - essentially no information)
  Example: "No kids" + targeting families = 3/100

11-20: Catastrophically bad. One or two word titles, near-empty descriptions that provide ZERO useful information.
  Example: Title "cozy", description "apartment" = 15/100
  Example: Title "place", description "for rent" = 12/100

21-35: Terrible. Extremely minimal effort, missing all basics, provides almost no value.
  Example: "Nice place downtown. Has bed." = 28/100

36-50: Very poor. Generic, lazy, missing critical information.
  Example: "Comfortable apartment with kitchen and wifi in the city" = 45/100

51-65: Below average to average. Bare minimum effort, forgettable.
  Example: Decent description but generic title, no emotional appeal = 60/100

66-75: Slightly above average. Shows some effort but unremarkable.
  Example: Basic SEO + structured description = 70/100

76-85: Good. Solid work, clear effort, above most competitors.
  Example: SEO-optimized title + structured description + some storytelling = 80/100

86-92: Excellent. Professional-grade. Strong SEO + emotion + targeting.
  Example: Keyword-rich title + emotional narrative + perfect audience alignment = 89/100

93-100: EXCEPTIONAL. Masterclass in optimization. Reserve 95-100 for truly PERFECT listings.
  Example: "Luxury Downtown Loft | Chef's Kitchen | Rooftop Deck | 2min to Metro" + vivid storytelling description + perfect amenity showcase = 97/100

CRITICAL SCORING RULES - ENFORCE STRICTLY:

- IF TITLE IS 1-3 WORDS: Maximum score is 20/100, no exceptions
- IF DESCRIPTION IS UNDER 20 WORDS: Maximum score is 25/100, no exceptions
- IF TITLE + DESCRIPTION PROVIDE ESSENTIALLY NO INFO: Maximum score is 10/100
- TARGET AUDIENCE MISMATCH: Maximum score is 15/100
- NO PROPERTY DETAILS PROVIDED: Maximum score is 30/100

CRITICAL RULES FOR SUGGESTIONS:

NEVER ASSUME LOCATION DETAILS
- Don't say "near beach" unless they mentioned water/ocean/beach
- Don't say "mountain views" unless they said mountains/views/elevation
- Don't say "downtown" unless they said downtown/city center/central
- Use ONLY what they gave you: property type, their amenities, their description

WORK WITH WHAT THEY HAVE
- If they said "no kids policy" - make that a SELLING POINT for couples/professionals
- If amenities are basic - optimize what exists, don't invent amenities
- If description is short - expand on details THEY provided, don't fabricate

BE HONEST ABOUT EXCELLENCE
- If a listing truly has perfect SEO + emotion + structure + targeting → give 90+
- Don't artificially inflate scores for terrible listings

REALISTIC AMENITY SUGGESTIONS
- For studio apartments: suggest coffee maker, not hot tub
- For budget properties: suggest smart lock, not pool
- For urban: suggest workspace, not kayaks
- Base ALL suggestions on property_type and target_audience

RESPONSE FORMAT:
- Use PLAIN TEXT in descriptions (NO **, NO *, NO markdown)
- Be BRUTALLY HONEST in scores and explanations
- If listing is garbage, give it 5-15
- If listing is perfect, give it 95-100
- Return ONLY valid, complete JSON (no code blocks, no truncation)

Remember: Your job is TRUTH. A 2-word title and 2-word description is a DISASTER and deserves 5-15 maximum.
"""
        
        if not groq_client:
            print("❌ Groq client not configured")
            raise AIServiceError("AI service is not configured. Please contact support.")
        
        result = None
        last_error = None
        
        for model_name in GROQ_MODELS:
            try:
                print(f"🤖 Attempting with Groq model: {model_name}")
                
                # Retry logic for connection errors
                max_retries = 2
                chat_completion = None
                
                for attempt in range(max_retries):
                    try:
                        chat_completion = groq_client.chat.completions.create(
                            messages=[
                                {
                                    "role": "user",
                                    "content": system_prompt
                                }
                            ],
                            model=model_name,
                            temperature=0.3,
                            max_tokens=8192,  # Increased to prevent truncation
                            top_p=0.8,
                        )
                        break  # Success, exit retry loop
                    except Exception as conn_error:
                        error_msg = str(conn_error)
                        
                        # Skip deprecated models immediately
                        if "decommissioned" in error_msg.lower() or "deprecated" in error_msg.lower():
                            print(f"   ⚠ Model deprecated, skipping")
                            raise  # Don't retry deprecated models
                        
                        if attempt < max_retries - 1:
                            print(f"   🔄 Retry {attempt + 1}/{max_retries} due to: {error_msg[:100]}")
                            import time
                            time.sleep(1)  # Brief pause before retry
                            continue
                        else:
                            raise  # Final attempt failed
                
                if not chat_completion:
                    continue
                
                response_text = clean_json_response(chat_completion.choices[0].message.content.strip())
                
                print(f"📝 Response length: {len(response_text)} chars")
                print(f"📝 Response preview: {response_text[:200]}...")
                
                # Validate JSON is complete
                if not response_text.endswith('}'):
                    print(f"⚠ Response appears truncated (doesn't end with }})")
                    print(f"   Last 100 chars: ...{response_text[-100:]}")
                    last_error = "Response truncated"
                    continue
                
                # Count braces to ensure JSON is balanced
                open_braces = response_text.count('{')
                close_braces = response_text.count('}')
                if open_braces != close_braces:
                    print(f"⚠ Unbalanced braces: {open_braces} open, {close_braces} close")
                    last_error = "Unbalanced JSON braces"
                    continue
                
                result = json.loads(response_text)
                
                # Validate required fields
                required_fields = ["overall_score", "detailed_scores", "optimized_titles", "description_rewrite"]
                if all(field in result for field in required_fields):
                    print(f"✓ Success with {model_name}")
                    break
                else:
                    missing = [f for f in required_fields if f not in result]
                    print(f"⚠ Missing fields: {missing}")
                    last_error = f"Incomplete response - missing: {', '.join(missing)}"
                    continue
                    
            except json.JSONDecodeError as e:
                print(f"✗ JSON parse error with {model_name}: {e}")
                if 'response_text' in locals():
                    print(f"   Response start: {response_text[:300]}")
                    print(f"   Response end: ...{response_text[-300:]}")
                last_error = f"AI returned invalid JSON format"
                continue
            except Exception as e:
                error_str = str(e)
                print(f"✗ Failed with {model_name}: {error_str[:200]}")
                
                # Skip deprecated models faster
                if "decommissioned" in error_str.lower() or "deprecated" in error_str.lower():
                    print(f"   ⏭ Skipping deprecated model")
                    continue
                
                last_error = error_str
                continue
        
        # If all models failed, raise error
        if not result:
            print("❌ All AI models failed")
            print(f"❌ Last error: {last_error}")
            
            error_msg = "Our AI analysis service is temporarily unavailable. Please try again in a moment."
            if last_error:
                if "rate limit" in str(last_error).lower():
                    error_msg = "Too many requests. Please wait a moment and try again."
                elif "timeout" in str(last_error).lower():
                    error_msg = "Analysis timed out. Please try again with a shorter description."
                elif "connection" in str(last_error).lower():
                    error_msg = "Network issue. Please check your connection and try again."
                elif "decommissioned" in str(last_error).lower():
                    error_msg = "AI models are being updated. Please try again in a few minutes."
            
            raise AIServiceError(error_msg)
        
        # ==================== HANDLE GUEST vs AUTHENTICATED ====================
        if is_guest:
            # Guest gets preview mode - show scores but mark as preview
            result["is_preview"] = True
            result["credits_remaining"] = None
            print(f"📤 Guest preview - scores visible, solutions will be blurred by frontend")
            print(f"✅ Guest can use analyzer UNLIMITED times")
        else:
            # Authenticated user - save audit and deduct credit
            if supabase:
                try:
                    audit_data = {
                        "user_id": user_id,
                        "listing_title": title[:255],
                        "property_type": property_type,
                        "score": result.get("overall_score", 0)
                    }
                    supabase.table("audit_history").insert(audit_data).execute()
                    print(f"✓ Audit saved for user {user_id}")
                except Exception as e:
                    print(f"⚠ Failed to save audit history: {e}")
                
                try:
                    subscription = ensure_user_subscription(user_id, None)
                    if subscription:
                        credits_after = max(0, credits_before - 1)
                        supabase.table("user_subscriptions")\
                            .update({"audits_remaining": credits_after})\
                            .eq("user_id", user_id)\
                            .execute()
                        print(f"✓ Credit deducted: {credits_before} → {credits_after}")
                    else:
                        print(f"⚠ Could not fetch subscription for credit deduction")
                        credits_after = 0
                except Exception as e:
                    print(f"❌ Error deducting credit: {e}")
                    credits_after = 0
                
                result["credits_remaining"] = credits_after
                result["is_preview"] = False
                print(f"📤 Authenticated user - full access, credits remaining: {credits_after}")
        
        return result
        
    except ValidationError:
        raise
    except InsufficientCreditsError:
        raise
    except AIServiceError:
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise AIServiceError("Analysis failed unexpectedly. Please try again in a moment.")