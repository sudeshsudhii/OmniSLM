"""
OmniSLM Constants.

Application-wide constants that do not change at runtime.
"""

# ---- API ----
API_V1_PREFIX = "/api/v1"

# ---- Auth ----
AUTH_SCHEME_BEARER = "Bearer"
AUTH_HEADER_API_KEY = "X-API-Key"

# ---- Roles ----
ROLE_SUPER_ADMIN = "super_admin"
ROLE_TENANT_ADMIN = "tenant_admin"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"

DEFAULT_ROLES = [
    {"name": ROLE_TENANT_ADMIN, "description": "Full tenant access", "is_system": True},
    {"name": ROLE_EDITOR, "description": "Create and edit resources", "is_system": True},
    {"name": ROLE_VIEWER, "description": "Read-only access", "is_system": True},
]

# ---- Models ----
SUPPORTED_MODEL_FAMILIES = ["qwen", "gemma", "phi", "llama", "mistral"]
SUPPORTED_RUNTIMES = ["ollama", "llama_cpp", "vllm", "huggingface"]

# ---- Pagination ----
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ---- Rate Limiting ----
RATE_LIMIT_WINDOW_SECONDS = 60
