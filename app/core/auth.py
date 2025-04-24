from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests

security = HTTPBearer()
MAI_SERVICES_VALIDATE_URL = "http://localhost:8080/api/v1/auth/validate-token"  # Update if your port/path differs

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(MAI_SERVICES_VALIDATE_URL, headers=headers, timeout=5)
        if resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        data = resp.json().get("data", {})
        if not data.get("valid"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=data.get("message", "Invalid authentication credentials"))
        return data  # Contains id, username, email, roles, permissions, etc.
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials with mai-services")

def get_current_user_with_role(required_role: str):
    def dependency(user=Depends(get_current_user)):
        roles = user.get("roles", [])
        if required_role in roles:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{required_role} role required")
    return dependency

def get_current_user_with_permission(required_permission: str):
    def dependency(user=Depends(get_current_user)):
        permissions = user.get("permissions", [])
        if required_permission in permissions:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{required_permission} permission required")
    return dependency
