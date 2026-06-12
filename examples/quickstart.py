"""
OmniSLM Quickstart Example.

Demonstrates the minimal setup to create an AI application.

Usage:
    pip install omnislm
    python quickstart.py
"""

from omnislm import OmniSLM

# Create the app with minimal config
app = OmniSLM(
    name="Quickstart App",
    version="0.1.0",
    debug=True,
)

# Enable features
app.enable_auth()
app.enable_memory()
app.enable_observability(metrics=True)

# Start the server
if __name__ == "__main__":
    print("🚀 Starting OmniSLM Quickstart...")
    print("   Visit http://localhost:8000/docs for the API docs")
    app.run(port=8000, reload=True)
