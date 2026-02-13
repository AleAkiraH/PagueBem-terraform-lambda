"""Auth Service — lógica de autenticação."""

from __future__ import annotations

import logging
import hashlib
import uuid
from datetime import datetime, timedelta
import jwt
import os

from repository.user_repository import UserRepository

logger = logging.getLogger()

JWT_SECRET = os.environ.get("JWT_SECRET", "seu-secreto-super-seguro-aqui-nao-use-em-prod")


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def hash_password(senha: str) -> str:
        """Gerar hash da senha usando SHA256."""
        return hashlib.sha256(senha.encode()).hexdigest()

    @staticmethod
    def verify_password(senha: str, senha_hash: str) -> bool:
        """Verificar se a senha corresponde ao hash."""
        return AuthService.hash_password(senha) == senha_hash

    @staticmethod
    def registrar(nome_usuario: str, senha: str) -> tuple[bool, str]:
        """Registrar novo usuário."""
        # Validar entrada
        if not nome_usuario or not senha:
            return False, "nome_usuario e senha são obrigatórios"

        if len(senha) < 4:
            return False, "Senha deve ter pelo menos 4 caracteres"

        # Verificar se usuário já existe
        usuario_existente = UserRepository.get_by_nome_usuario(nome_usuario)
        if usuario_existente:
            return False, "Nome de usuário já está em uso"

        # Criar usuário
        usuario_id = str(uuid.uuid4())
        senha_hash = AuthService.hash_password(senha)

        sucesso = UserRepository.create(usuario_id, nome_usuario, senha_hash)
        if sucesso:
            return True, "Conta criada com sucesso!"
        else:
            return False, "Erro ao criar conta"

    @staticmethod
    def entrar(nome_usuario: str, senha: str) -> tuple[bool, str | None]:
        """Autenticar usuário e retornar JWT token."""
        # Validar entrada
        if not nome_usuario or not senha:
            return False, None

        # Buscar usuário
        usuario = UserRepository.get_by_nome_usuario(nome_usuario)
        if not usuario:
            return False, None

        # Verificar senha
        if not AuthService.verify_password(senha, usuario["senha_hash"]):
            return False, None

        # Gerar JWT token
        payload = {
            "usuario_id": usuario["usuario_id"],
            "nome_usuario": usuario["nome_usuario"],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        logger.info(f"Usuário {nome_usuario} autenticado com sucesso")
        return True, token
