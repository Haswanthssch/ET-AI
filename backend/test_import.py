"""Test that backend modules import correctly"""
import sys
sys.path.insert(0, '.')

try:
    from backend.routers import router
    print("routers OK")
except Exception as e:
    print(f"routers ERROR: {e}")

try:
    from backend.agents import run_risk_prediction
    print("agents OK")
except Exception as e:
    print(f"agents ERROR: {e}")

try:
    from backend.main import app
    print("main OK")
    for r in app.routes:
        if hasattr(r, 'path') and hasattr(r, 'methods'):
            print(f"  {r.path} {r.methods}")
except Exception as e:
    print(f"main ERROR: {e}")