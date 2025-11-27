from flask import Flask, jsonify, request
import time
import os
import requests
import json
from jose import jwt

# ISSUER của Keycloak (có thể override bằng biến môi trường)
ISSUER = os.getenv(
    "OIDC_ISSUER",
    "http://authentication-identity-server:8080/realms/master"
)

AUDIENCE = os.getenv("OIDC_AUDIENCE", "myapp")
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"

_JWKS = None
_TS = 0


def get_jwks():
    """Cache JWKS 600s để đỡ gọi Keycloak liên tục."""
    global _JWKS, _TS
    now = time.time()
    if not _JWKS or now - _TS > 600:
        resp = requests.get(JWKS_URL, timeout=5)
        resp.raise_for_status()
        _JWKS = resp.json()
        _TS = now
    return _JWKS


app = Flask(__name__)


@app.get("/hello")
def hello():
    return jsonify(message="Hello from App Server!")


@app.get("/secure")
def secure():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify(error="Missing Bearer token"), 401

    token = auth.split(" ", 1)[1]

    try:
        payload = jwt.decode(
        token,
        get_jwks(),
        algorithms=["RS256"],
        audience=AUDIENCE,
        options={"verify_iss": False},
    )

        return jsonify(
            message="Secure resource OK",
            preferred_username=payload.get("preferred_username"),
        )
    except Exception as e:
        return jsonify(error=str(e)), 401


@app.get("/student")
def student():
    """EXT 2: trả danh sách sinh viên từ students.json"""
    try:
        with open("students.json", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        # để nếu lỡ thiếu file / lỗi JSON thì biết lý do
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
