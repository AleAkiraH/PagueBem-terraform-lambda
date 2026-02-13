"""User Repository — DynamoDB operations for users."""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()

dynamodb = boto3.resource("dynamodb")
USERS_TABLE = os.environ.get("USUARIOS_TABLE_NAME", "PagueBem-Usuarios-dev")


class UserRepository:
    """Repository for user operations in DynamoDB."""

    @staticmethod
    def get_by_nome_usuario(nome_usuario: str) -> Optional[Dict[str, Any]]:
        """Buscar usuário pelo nome de usuário."""
        try:
            table = dynamodb.Table(USERS_TABLE)
            response = table.query(
                IndexName="nome_usuario-index",
                KeyConditionExpression="nome_usuario = :nome",
                ExpressionAttributeValues={":nome": nome_usuario},
            )
            if response["Items"]:
                return response["Items"][0]
            return None
        except ClientError as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            return None

    @staticmethod
    def create(usuario_id: str, nome_usuario: str, senha_hash: str) -> bool:
        """Criar novo usuário."""
        try:
            table = dynamodb.Table(USERS_TABLE)
            table.put_item(
                Item={
                    "usuario_id": usuario_id,
                    "nome_usuario": nome_usuario,
                    "senha_hash": senha_hash,
                    "criado_em": datetime.now(timezone.utc).isoformat(),
                },
                ConditionExpression="attribute_not_exists(usuario_id)",
            )
            logger.info(f"Usuário {nome_usuario} criado com sucesso")
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logger.warning(f"Usuário {nome_usuario} já existe")
                return False
            logger.error(f"Erro ao criar usuário: {e}")
            return False

    @staticmethod
    def get_by_id(usuario_id: str) -> Optional[Dict[str, Any]]:
        """Buscar usuário pelo ID."""
        try:
            table = dynamodb.Table(USERS_TABLE)
            response = table.get_item(Key={"usuario_id": usuario_id})
            return response.get("Item")
        except ClientError as e:
            logger.error(f"Erro ao buscar usuário por ID: {e}")
            return None
