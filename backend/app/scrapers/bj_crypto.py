"""Chiffrement des identifiants dossier pour le portail marches-publics.bj."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from urllib.parse import quote

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

BJ_ENCRYPT_SECRET = "MyPort@!l-Crypte"
BJ_BASE_URL = "https://www.marches-publics.bj"
BJ_LISTING_PATH = "/appels-doffres"
MAX_ENCRYPT_ATTEMPTS = 64


def _evp_bytes_to_key(
    password: bytes,
    salt: bytes,
    key_len: int = 32,
    iv_len: int = 16,
) -> tuple[bytes, bytes]:
    digest = b""
    block = b""
    while len(digest) < key_len + iv_len:
        block = hashlib.md5(block + password + salt).digest()
        digest += block
    return digest[:key_len], digest[key_len : key_len + iv_len]


def _encrypt_once(value: int | str, secret: str) -> str:
    plaintext = json.dumps(value, separators=(",", ":"))
    salt = os.urandom(8)
    key, iv = _evp_bytes_to_key(secret.encode("utf-8"), salt)
    ciphertext = AES.new(key, AES.MODE_CBC, iv).encrypt(
        pad(plaintext.encode("utf-8"), AES.block_size)
    )
    return base64.b64encode(b"Salted__" + salt + ciphertext).decode("ascii")


def encrypt_portal_id(value: int | str, secret: str = BJ_ENCRYPT_SECRET) -> str:
    """Reproduit CryptoJS.AES.encrypt(JSON.stringify(value), secret).toString().

    Le portail Apache rejette les « / » et « + » non encodés dans le chemin ;
    on retente avec un sel aléatoire jusqu'à obtenir un token URL-safe.
    """
    token = ""
    for _ in range(MAX_ENCRYPT_ATTEMPTS):
        token = _encrypt_once(value, secret)
        if "/" not in token and "+" not in token:
            return token
    return token


def build_bj_offre_url(dos_id: int | str, base_url: str = BJ_BASE_URL) -> str:
    """Construit l'URL de fiche AO avec l'identifiant chiffré attendu par le SPA."""
    token = encrypt_portal_id(dos_id)
    encoded = quote(token, safe="")
    return f"{base_url.rstrip('/')}{BJ_LISTING_PATH}/{encoded}"
