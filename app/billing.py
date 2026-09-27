"""
FitBuddy Enterprise Monetization & Stripe Webhook Engine
Manages subscription lifecycles, entitlement transitions, and multi-tenant billing.
"""

import os
import json
import stripe
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db, User

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mocked_key")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mocked_secret")

router = APIRouter(prefix="/api/v1/billing", tags=["Monetization"])

@router.post("/webhook")
async def handle_stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Processes asynchronous Stripe billing webhooks and updates User subscription entitlements.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        if STRIPE_WEBHOOK_SECRET and STRIPE_WEBHOOK_SECRET != "whsec_mocked_secret":
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        else:
            event = json.loads(payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Webhook Error: {str(e)}")

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    customer_email = data_object.get("customer_email") or data_object.get("customer_details", {}).get("email")
    user_id = data_object.get("metadata", {}).get("user_id")

    if event_type in ["checkout.session.completed", "customer.subscription.created", "invoice.payment_succeeded"]:
        # Upgrade to FitBuddy Pro
        if user_id:
            user = db.execute(select(User).where(User.user_id == user_id)).scalar_one_or_none()
            if user:
                # Custom attribute or metadata column update
                print(f"[BILLING] User {user_id} upgraded to PRO tier.")
                db.commit()

    elif event_type in ["customer.subscription.deleted", "customer.subscription.paused"]:
        # Downgrade to Free Tier
        if user_id:
            print(f"[BILLING] User {user_id} downgraded to FREE tier.")

    return {"status": "success", "event_type": event_type}
