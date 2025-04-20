from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any, List
from app.core.security import get_current_active_user
from app.db.supabase_manager import get_supabase_client
from pydantic import BaseModel
import stripe
from app.core.config import settings

router = APIRouter()

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSession(BaseModel):
    plan_id: str
    success_url: str
    cancel_url: str

class CreatePortalSession(BaseModel):
    return_url: str

@router.post("/create-checkout", summary="Crear sesión de checkout de Stripe")
async def create_checkout_session(
    data: CreateCheckoutSession,
    current_user = Depends(get_current_active_user)
):
    """
    Crea una sesión de checkout de Stripe para suscripción a un plan.
    
    - **plan_id**: ID del plan en Stripe
    - **success_url**: URL de redirección en caso de éxito
    - **cancel_url**: URL de redirección en caso de cancelación
    """
    try:
        supabase = get_supabase_client()
        user = current_user
        
        # Verificar si el usuario ya tiene un customer_id de Stripe
        customer_id = user.get("stripe_customer_id")
        
        if not customer_id:
            # Crear customer en Stripe
            customer = stripe.Customer.create(
                email=user["email"],
                name=user.get("name", ""),
                metadata={"user_id": user["id"]}
            )
            customer_id = customer.id
            
            # Guardar customer_id en Supabase
            await supabase.update_user(user["id"], {"stripe_customer_id": customer_id})
        
        # Crear sesión de checkout
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": data.plan_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            metadata={"user_id": user["id"]}
        )
        
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/create-portal", summary="Crear sesión de portal de cliente de Stripe")
async def create_portal_session(
    data: CreatePortalSession,
    current_user = Depends(get_current_active_user)
):
    """
    Crea una sesión de portal de cliente de Stripe para gestionar suscripciones.
    
    - **return_url**: URL de redirección al salir del portal
    """
    try:
        user = current_user
        customer_id = user.get("stripe_customer_id")
        
        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario no tiene una suscripción activa"
            )
        
        # Crear sesión de portal
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=data.return_url,
        )
        
        return {"portal_url": portal_session.url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/webhook", summary="Webhook de Stripe")
async def stripe_webhook(request: Request):
    """
    Procesa eventos de webhook de Stripe.
    """
    try:
        # Obtener payload y firma
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falta la firma de Stripe"
            )
        
        # Verificar evento
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payload inválido"
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Firma inválida"
            )
        
        # Procesar evento
        supabase = get_supabase_client()
        
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session["metadata"]["user_id"]
            
            # Actualizar plan del usuario según la suscripción
            subscription_id = session["subscription"]
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            plan_map = {
                "price_basic": "basic",
                "price_pro": "pro",
                "price_enterprise": "enterprise"
            }
            
            # Obtener el plan a partir del precio
            price_id = subscription["items"]["data"][0]["price"]["id"]
            plan = "free"  # Por defecto
            
            for price_key, plan_value in plan_map.items():
                if price_key in price_id:
                    plan = plan_value
                    break
            
            # Actualizar usuario en Supabase
            credits_map = {
                "basic": 500,
                "pro": 2000,
                "enterprise": 10000
            }
            
            await supabase.update_user(user_id, {
                "plan": plan,
                "creditos": credits_map.get(plan, 100),
                "stripe_subscription_id": subscription_id,
                "stripe_subscription_status": subscription["status"]
            })
        
        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            customer_id = subscription["customer"]
            
            # Buscar usuario por customer_id
            # (Aquí se necesitaría una función adicional en SupabaseManager)
            # Por ahora, simplemente registramos el evento
            print(f"Suscripción actualizada para customer: {customer_id}")
        
        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            customer_id = subscription["customer"]
            
            # Buscar usuario por customer_id y actualizar a plan gratuito
            # (Aquí se necesitaría una función adicional en SupabaseManager)
            print(f"Suscripción cancelada para customer: {customer_id}")
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/plans", summary="Obtener planes disponibles")
async def get_plans():
    """
    Obtiene los planes disponibles para suscripción.
    """
    try:
        # En un entorno real, estos datos podrían venir de Stripe o de la base de datos
        plans = [
            {
                "id": "basic",
                "name": "Plan Básico",
                "price": 9.99,
                "currency": "USD",
                "billing_cycle": "monthly",
                "features": [
                    "Acceso a herramientas básicas",
                    "500 créditos mensuales",
                    "Soporte por email"
                ],
                "stripe_price_id": "price_basic"
            },
            {
                "id": "pro",
                "name": "Plan Profesional",
                "price": 29.99,
                "currency": "USD",
                "billing_cycle": "monthly",
                "features": [
                    "Acceso a todas las herramientas",
                    "2000 créditos mensuales",
                    "Soporte prioritario",
                    "Análisis avanzados"
                ],
                "stripe_price_id": "price_pro"
            },
            {
                "id": "enterprise",
                "name": "Plan Empresarial",
                "price": 99.99,
                "currency": "USD",
                "billing_cycle": "monthly",
                "features": [
                    "Acceso a todas las herramientas",
                    "10000 créditos mensuales",
                    "Soporte 24/7",
                    "API personalizada",
                    "Integraciones avanzadas"
                ],
                "stripe_price_id": "price_enterprise"
            }
        ]
        
        return {"plans": plans}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
