# /home/ubuntu/genia_backendMPC/test_stripe_tool_mcp.py
import asyncio
import os
import sys
import uuid

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables before importing tools that might need them
from dotenv import load_dotenv
load_dotenv()

# Import the tool
from app.tools.stripe_tool import StripeTool

async def run_stripe_tests():
    """Runs integration tests for the MCP-integrated StripeTool."""
    print("--- Iniciando Pruebas de Integración MCP para StripeTool ---")
    print("Asegúrate de que el servidor MCP de Stripe esté corriendo en localhost:8002")

    stripe_tool = StripeTool() # Assumes config is loaded via .env
    test_user_id = f"test_user_{uuid.uuid4()}" # Unique user ID for testing
    test_email = f"test+{uuid.uuid4()}@example.com" # Unique email for testing
    customer_id = None

    # --- Test create_customer --- 
    print("\n--- Probando StripeTool (create_customer) ---")
    try:
        params_customer = {
            "email": test_email,
            "name": "Test Customer MCP",
            "metadata": {"source": "mcp_test"}
        }
        result_customer = await stripe_tool.execute(user_id=test_user_id, capability="create_customer", params=params_customer)
        print(f"Resultado create_customer: {result_customer}")
        assert result_customer.get("status") in ["success", "partial_success"] # Allow partial if Supabase fails
        assert isinstance(result_customer.get("customer_id"), str) and result_customer.get("customer_id", "").startswith("cus_")
        customer_id = result_customer.get("customer_id")
        print(f"StripeTool (create_customer): OK - Customer ID: {customer_id}")
    except Exception as e:
        print(f"Error en StripeTool (create_customer): {e}")
        # Stop further tests if customer creation fails critically
        print("--- Pruebas de StripeTool Abortadas --- ")
        return

    # --- Test create_payment --- 
    # Note: This only creates a PaymentIntent, doesn't confirm it.
    print("\n--- Probando StripeTool (create_payment) ---")
    try:
        params_payment = {
            "amount": 1000, # e.g., $10.00
            "currency": "usd",
            "description": "Test Payment MCP",
            "metadata": {"order_id": "test_order_123"}
        }
        result_payment = await stripe_tool.execute(user_id=test_user_id, capability="create_payment", params=params_payment)
        print(f"Resultado create_payment: {result_payment}")
        assert result_payment.get("status") == "success"
        assert isinstance(result_payment.get("client_secret"), str)
        assert isinstance(result_payment.get("payment_intent_id"), str) and result_payment.get("payment_intent_id", "").startswith("pi_")
        print("StripeTool (create_payment): OK")
    except Exception as e:
        print(f"Error en StripeTool (create_payment): {e}")

    # --- Test create_subscription --- 
    # Requires a valid customer_id and price_id. Using a common test price ID.
    # Replace 'price_12345' with an actual Stripe test mode Price ID if available.
    # For now, we expect this might fail if the price_id is invalid, but test the flow.
    print("\n--- Probando StripeTool (create_subscription) ---")
    # Use a known test price ID (replace if needed)
    # Find test price IDs in your Stripe dashboard under Products.
    # Example: price_1PGj8X00gy6Lj7juoY1aZ4bA (Test Product - Monthly)
    test_price_id = "price_1PGj8X00gy6Lj7juoY1aZ4bA" 
    if customer_id and test_price_id:
        try:
            params_subscription = {
                "customer_id": customer_id,
                "price_id": test_price_id,
                "metadata": {"plan": "test_monthly"}
            }
            result_subscription = await stripe_tool.execute(user_id=test_user_id, capability="create_subscription", params=params_subscription)
            print(f"Resultado create_subscription: {result_subscription}")
            # Subscription creation might require payment method, so status might be 'incomplete'
            assert result_subscription.get("status") == "success" 
            assert isinstance(result_subscription.get("subscription_id"), str) and result_subscription.get("subscription_id", "").startswith("sub_")
            # assert result_subscription.get("status") in ["active", "incomplete", "trialing"] # Check for expected Stripe status
            print("StripeTool (create_subscription): OK (Check Stripe Dashboard for details)")
        except Exception as e:
            # This might fail legitimately if the customer has no payment method
            print(f"Error en StripeTool (create_subscription): {e} (Puede ser esperado si el cliente no tiene método de pago o price_id es inválido)")
    else:
        print("StripeTool (create_subscription): Omitido (customer_id o price_id no disponible)")

    print("\n--- Pruebas de Integración MCP para StripeTool Finalizadas ---")

if __name__ == "__main__":
    asyncio.run(run_stripe_tests())

