from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from jose import jwt, exceptions as jose_exceptions
import codecs # Import codecs for hex decoding

security = HTTPBearer()

# --- JWT Configuration --- 
JWT_SECRET_HEX = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not JWT_SECRET_HEX:
    raise RuntimeError("JWT_SECRET environment variable not set. Cannot validate tokens.")

# Decode the hex secret into bytes
try:
    JWT_SECRET_BYTES = codecs.decode(JWT_SECRET_HEX, 'hex')
    # Check key length for HS256
    if JWT_ALGORITHM == "HS256" and len(JWT_SECRET_BYTES) < 32:
         raise ValueError(f"Decoded JWT_SECRET key length ({len(JWT_SECRET_BYTES)}) is less than the required 32 bytes for HS256.")
    # Add checks for other algorithms if needed
    # elif JWT_ALGORITHM == "HS384" and len(JWT_SECRET_BYTES) < 48:
    #     raise ValueError("Key length too short for HS384")
    # elif JWT_ALGORITHM == "HS512" and len(JWT_SECRET_BYTES) < 64:
    #     raise ValueError("Key length too short for HS512")
except (ValueError, TypeError) as e:
     # Catch errors from codecs.decode if JWT_SECRET_HEX is not valid hex
     # or if length check fails
    raise RuntimeError(f"Invalid JWT_SECRET environment variable: {e}")

# --- Authentication Dependencies --- 

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validates the JWT token locally and returns the decoded payload."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_BYTES, # Use the decoded bytes as the key
            algorithms=[JWT_ALGORITHM]
        )
        # Optionally, you could add checks for specific claims like 'iss' (issuer) or 'aud' (audience)
        # if needed, e.g.:
        # if payload.get("iss") != "expected_issuer":
        #     raise jose_exceptions.JWTClaimsError("Invalid issuer")
        return payload # The payload is the user data dictionary
    except jose_exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jose_exceptions.JWTClaimsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token claims: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jose_exceptions.JWTError as e: # Catch other JWT errors (e.g., invalid signature)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e: # Catch unexpected errors during decoding
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during token validation: {e}"
        )

def get_current_user_with_role(required_role: str):
    """Dependency to get the current user and verify they have the required role."""
    def dependency(user: dict = Depends(get_current_user)):
        roles = user.get("roles", [])
        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"'{required_role}' role required"
            )
        return user # Return the full user payload if role check passes
    return dependency

def get_current_user_with_permission(required_permission: str):
    """Dependency to get the current user and verify they have the required permission."""
    def dependency(user: dict = Depends(get_current_user)):
        # Assuming permissions might also be in the token, adjust key if needed
        permissions = user.get("permissions", []) 
        # Or maybe permissions are derived from roles? Adapt logic as needed.
        if required_permission not in permissions:
            # You might also want to check roles here if permissions aren't explicit
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"'{required_permission}' permission required"
            )
        return user
    return dependency
