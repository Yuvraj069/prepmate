import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthResult:
    ok: bool
    message: str = ""
    user: Optional[dict] = None
    token: Optional[str] = None


class AuthService:
    """Supabase Auth with a deliberately small local demo fallback."""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.client = None
        self.demo_users = {}
        if self.url and self.key:
            try:
                from supabase import create_client
                self.client = create_client(self.url, self.key)
            except ImportError:
                pass

    @property
    def cloud_ready(self):
        return self.client is not None

    def _user(self, user, fallback_name="Candidate"):
        metadata = getattr(user, "user_metadata", None) or {}
        return {"id": str(getattr(user, "id", "demo-user")), "email": getattr(user, "email", ""), "name": metadata.get("full_name", fallback_name)}

    def register(self, email, password, name):
        if self.client:
            try:
                response = self.client.auth.sign_up({"email": email, "password": password, "options": {"data": {"full_name": name}}})
                if not response.user:
                    return AuthResult(False, "We couldn't create that account. Please try another email.")
                if not response.session:
                    return AuthResult(False, "Check your email to confirm your account, then sign in.")
                return AuthResult(True, user=self._user(response.user, name), token=response.session.access_token)
            except Exception as error:
                return AuthResult(False, self._clean_error(error))
        if email in self.demo_users:
            return AuthResult(False, "An account with this email already exists in demo mode.")
        self.demo_users[email] = {"password": password, "name": name}
        return AuthResult(True, user={"id": f"demo-{email}", "email": email, "name": name}, token="demo-session")

    def login(self, email, password):
        if self.client:
            try:
                response = self.client.auth.sign_in_with_password({"email": email, "password": password})
                return AuthResult(True, user=self._user(response.user), token=response.session.access_token)
            except Exception as error:
                return AuthResult(False, self._clean_error(error))
        user = self.demo_users.get(email)
        if not user or user["password"] != password:
            return AuthResult(False, "Incorrect email or password. In demo mode, register first.")
        return AuthResult(True, user={"id": f"demo-{email}", "email": email, "name": user["name"]}, token="demo-session")

    def logout(self, _token):
        if self.client:
            try:
                self.client.auth.sign_out()
            except Exception:
                pass

    @staticmethod
    def _clean_error(error):
        message = str(error).replace("AuthApiError: ", "")
        return message or "We couldn't sign you in. Please try again."
