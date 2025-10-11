"""
Security utilities and middleware for the Agentic RAG API.
"""

import os
import hmac
import hashlib
import time
import logging
from typing import Optional, List, Dict, Any
from functools import wraps
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Security configuration from environment
API_KEY = os.getenv("API_KEY")  # Main API key for all endpoints
API_KEY_REQUIRED = os.getenv("API_KEY_REQUIRED", "true").lower() == "true"
N8N_API_KEY = os.getenv("N8N_API_KEY")
N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET")
ALLOWED_N8N_IPS = os.getenv("ALLOWED_N8N_IPS", "").split(",") if os.getenv("ALLOWED_N8N_IPS") else []
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
ENABLE_IP_WHITELIST = os.getenv("ENABLE_IP_WHITELIST", "false").lower() == "true"

# In-memory rate limiting (use Redis in production)
rate_limit_store: Dict[str, List[float]] = {}

security = HTTPBearer(auto_error=False)


class SecurityError(HTTPException):
    """Custom security exception."""
    pass


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, considering proxy headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address
    """
    # Check common proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Cloudflare specific
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        return cf_connecting_ip.strip()
    
    # Fallback to direct connection
    if request.client:
        return request.client.host
    
    return "unknown"


def verify_n8n_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """
    Verify n8n webhook signature.
    
    Args:
        payload: Raw request payload
        signature: Signature from request headers
        secret: Webhook secret
        
    Returns:
        True if signature is valid
    """
    if not secret:
        logger.warning("N8N_WEBHOOK_SECRET not configured - signature verification disabled")
        return True
    
    try:
        # n8n typically uses HMAC-SHA256
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Handle different signature formats
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


def check_rate_limit(identifier: str, limit: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW) -> bool:
    """
    Check if request is within rate limits.
    
    Args:
        identifier: Unique identifier (IP, API key, etc.)
        limit: Maximum requests allowed
        window: Time window in seconds
        
    Returns:
        True if within limits, False if exceeded
    """
    now = time.time()
    cutoff = now - window
    
    # Clean old entries
    if identifier in rate_limit_store:
        rate_limit_store[identifier] = [
            timestamp for timestamp in rate_limit_store[identifier]
            if timestamp > cutoff
        ]
    else:
        rate_limit_store[identifier] = []
    
    # Check if limit exceeded
    if len(rate_limit_store[identifier]) >= limit:
        return False
    
    # Add current request
    rate_limit_store[identifier].append(now)
    return True


def validate_n8n_request(request: Request) -> Dict[str, Any]:
    """
    Validate that request comes from authorized n8n instance.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Validation metadata
        
    Raises:
        SecurityError: If validation fails
    """
    client_ip = get_client_ip(request)
    
    # IP whitelist check
    if ENABLE_IP_WHITELIST and ALLOWED_N8N_IPS:
        if client_ip not in ALLOWED_N8N_IPS:
            logger.warning(f"IP {client_ip} not in whitelist")
            raise SecurityError(
                status_code=403,
                detail="Access denied - IP not allowed"
            )
    
    # Rate limiting
    if not check_rate_limit(f"ip:{client_ip}"):
        logger.warning(f"Rate limit exceeded for IP {client_ip}")
        raise SecurityError(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    # User-Agent validation (basic bot detection)
    user_agent = request.headers.get("User-Agent", "").lower()
    suspicious_agents = ["curl", "wget", "python-requests", "bot", "crawler", "spider"]
    
    if any(agent in user_agent for agent in suspicious_agents):
        # Allow n8n and specific agents
        if "n8n" not in user_agent and not any(
            allowed in user_agent for allowed in ["n8n", "webhook", "automation"]
        ):
            logger.info(f"Suspicious User-Agent blocked: {user_agent}")
            raise SecurityError(
                status_code=403,
                detail="Access denied - invalid user agent"
            )
    
    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "timestamp": datetime.now(),
        "source": "n8n"
    }


async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Verify API key authentication for general endpoints.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If authentication fails
    """
    # Skip API key check if not required (for development)
    if not API_KEY_REQUIRED:
        return "not_required"
    
    if not API_KEY:
        logger.error("API_KEY not configured but API_KEY_REQUIRED is true")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error - API key not set"
        )
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not hmac.compare_digest(credentials.credentials, API_KEY):
        logger.warning(f"Invalid API key attempted from {credentials.credentials[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return credentials.credentials


async def verify_n8n_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Verify n8n API key authentication.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Validated API key
        
    Raises:
        SecurityError: If authentication fails
    """
    if not N8N_API_KEY:
        logger.warning("N8N_API_KEY not configured - API key validation disabled")
        return "disabled"
    
    if not credentials:
        raise SecurityError(
            status_code=401,
            detail="Missing API key"
        )
    
    if not hmac.compare_digest(credentials.credentials, N8N_API_KEY):
        logger.warning(f"Invalid API key attempted")
        raise SecurityError(
            status_code=401,
            detail="Invalid API key"
        )
    
    return credentials.credentials


def security_headers_middleware(request: Request, call_next):
    """
    Add security headers to responses.

    Args:
        request: FastAPI request object
        call_next: Next middleware function

    Returns:
        Response with security headers
    """
    async def _middleware():
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Allow iframe embedding for widget endpoints, deny for everything else
        if request.url.path.startswith("/widget/"):
            # Allow widget chat to be embedded in any iframe (needed for chat widget)
            response.headers["X-Frame-Options"] = "ALLOWALL"
            # Allow CDN resources for markdown rendering and syntax highlighting
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "frame-ancestors *;"
            )
        else:
            # Deny iframe embedding for all other endpoints
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'none'; object-src 'none';"

        # Only add HSTS in production with HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

    return _middleware()


def require_n8n_auth(func):
    """
    Decorator to require n8n authentication for endpoints.
    
    Args:
        func: FastAPI endpoint function
        
    Returns:
        Decorated function with authentication
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request from args/kwargs
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            for kwarg in kwargs.values():
                if isinstance(kwarg, Request):
                    request = kwarg
                    break
        
        if not request:
            raise SecurityError(
                status_code=500,
                detail="Internal error - request object not found"
            )
        
        # Validate n8n request
        try:
            validation_info = validate_n8n_request(request)
            
            # Add validation info to request state
            request.state.security_info = validation_info
            
            return await func(*args, **kwargs)
            
        except SecurityError:
            raise
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            raise SecurityError(
                status_code=500,
                detail="Security validation failed"
            )
    
    return wrapper


def sanitize_input(data: Any) -> Any:
    """
    Sanitize input data to prevent injection attacks.
    
    Args:
        data: Input data to sanitize
        
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        # Remove potential script tags and other dangerous content
        dangerous_patterns = [
            "<script", "</script>", "javascript:", "vbscript:",
            "onload=", "onerror=", "onclick=", "onmouseover=",
            "<iframe", "</iframe>", "<object", "</object>",
            "<embed", "</embed>", "<link", "<meta"
        ]
        
        sanitized = data
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, "")
            sanitized = sanitized.replace(pattern.upper(), "")
        
        # Limit length to prevent DoS
        max_length = int(os.getenv("MAX_INPUT_LENGTH", "10000"))
        if len(sanitized) > max_length:
            logger.warning(f"Input truncated from {len(sanitized)} to {max_length} characters")
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    
    return data


def get_security_info(request: Request) -> Dict[str, Any]:
    """
    Get security information from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Security information dict
    """
    return getattr(request.state, 'security_info', {})