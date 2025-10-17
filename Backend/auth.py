import os
import json
from dotenv import load_dotenv
from urllib.request import urlopen
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session
from . import models, database

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_public_key():
    """Grabs the public key from Auth0 to verify JWTs."""
    jsonurl = urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    return jwks

def verify_token(token: str = Depends(oauth2_scheme)):
    """Verifies the JWT token and returns the payload if valid."""
    jwks = get_public_key()
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token header")
    
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"], "kid": key["kid"], "use": key["use"],
                "n": key["n"], "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/",
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTClaimsError:
            raise HTTPException(status_code=401, detail="Invalid claims, please check audience and issuer")
        except Exception:
            raise HTTPException(status_code=401, detail="Unable to parse authentication token.")
    
    raise HTTPException(status_code=401, detail="Unable to find appropriate key.")

def get_current_user(payload: dict = Depends(verify_token), db: Session = Depends(database.get_db)):
    """
    Takes a verified token payload, finds the user in the local database,
    or creates a new user if they don't exist.
    """
    user_id = payload.get("sub") 
    if user_id is None:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    user = db.query(models.User).filter(models.User.clerk_user_id == user_id).first()
    if user is None:
        user = models.User(clerk_user_id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

