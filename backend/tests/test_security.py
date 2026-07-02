"""Tests de la politique de mot de passe."""

from app.core.security import validate_password_strength


def test_password_valid():
    assert validate_password_strength("Motdepasse1!") is None


def test_password_too_short():
    assert validate_password_strength("Ab1!") == "Le mot de passe doit contenir au moins 8 caractères"


def test_password_missing_uppercase():
    assert validate_password_strength("motdepasse1!") is not None


def test_password_missing_lowercase():
    assert validate_password_strength("MOTDEPASSE1!") is not None


def test_password_missing_digit():
    assert validate_password_strength("Motdepasse!") is not None


def test_password_missing_special():
    assert validate_password_strength("Motdepasse1") is not None
