# PagueBem — Lambda

Lambda Function + ECR do projeto PagueBem.

## Função

- **Nome:** `paguebem-api-{env}`
- **Runtime:** Python 3.11 (Docker via ECR)
- **Roteamento:** Catch-all com controller interno
- **ECR:** `paguebem-api-{env}`

## Estrutura do Código

```
lambda/
├── main.py              ← Handler principal (roteamento)
├── Dockerfile           ← Build da imagem Docker
├── requirements.txt     ← Dependências Python
├── controller/          ← Controllers (HTTP request/response)
├── services/            ← Lógica de negócio
├── repository/          ← Acesso a dados (DynamoDB)
├── models/              ← Modelos de domínio
├── dtos/                ← Validação com Pydantic
└── utils/               ← Helpers (response builder, etc.)
```

## Dependências

- **DynamoDB** — ARNs e nomes das tabelas nos `terraform.tfvars`

## Deploy

```powershell
# Init (primeira vez ou troca de ambiente)
terraform init -backend-config="key=lambda/dev/terraform.tfstate"

# Plan
terraform plan -var-file="dev/terraform.tfvars"

# Apply
terraform apply -var-file="dev/terraform.tfvars"
```

## Destroy

```powershell
terraform destroy -var-file="dev/terraform.tfvars"
```

## Outputs

| Output | Descrição |
|--------|-----------|
| `function_name` | Nome da função Lambda |
| `function_arn` | ARN da função Lambda |
| `invoke_arn` | Invoke ARN (para API Gateway) |
| `role_arn` | ARN da role de execução |
| `ecr_repository_url` | URL do repositório ECR |

> Copie `function_name` e `function_arn` para o `terraform.tfvars` do API Gateway.
