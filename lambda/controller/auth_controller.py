"""Auth Controller — handles login and registration."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from services.auth_service import AuthService
from utils.response import build_response

logger = logging.getLogger()


class AuthController:
    """Controller for authentication endpoints."""

    @staticmethod
    def registrar(event: Dict[str, Any]) -> Dict[str, Any]:
        """POST /registrar — Register a new user."""
        try:
            body = event.get("body", "")
            if isinstance(body, str):
                body = json.loads(body)

            nome_usuario = body.get("nome_usuario", "").strip()
            senha = body.get("senha", "").strip()

            sucesso, mensagem = AuthService.registrar(nome_usuario, senha)

            if sucesso:
                return build_response(201, {"mensagem": mensagem})
            else:
                return build_response(400, {"error": mensagem})

        except Exception as e:
            logger.exception("Erro ao registrar")
            return build_response(500, {"error": "Erro ao registrar usuário"})

    @staticmethod
    def entrar(event: Dict[str, Any]) -> Dict[str, Any]:
        """POST /entrar — Login user."""
        try:
            body = event.get("body", "")
            if isinstance(body, str):
                body = json.loads(body)

            nome_usuario = body.get("nome_usuario", "").strip()
            senha = body.get("senha", "").strip()

            if not nome_usuario or not senha:
                return build_response(400, {"error": "nome_usuario e senha são obrigatórios"})

            sucesso, token = AuthService.entrar(nome_usuario, senha)

            if sucesso:
                return build_response(200, {"token": token})
            else:
                return build_response(401, {"error": "nome_usuario ou senha incorretos"})

        except Exception as e:
            logger.exception("Erro ao fazer login")
            return build_response(500, {"error": "Erro ao fazer login"})
