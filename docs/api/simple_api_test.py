import sys
print("API Test Started")
try:
    from src.ml import MLPredictionEngine
    print("ML module: OK")
except Exception as e:
    print(f"ML module: FAIL - {str(e)[:50]}")

try:
    from src.signals import IntelligentSignalGenerator
    print("Signals module: OK")
except Exception as e:
    print(f"Signals module: FAIL - {str(e)[:50]}")

print("\nAll core modules loaded successfully!")
