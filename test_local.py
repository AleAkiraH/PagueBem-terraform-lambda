#!/usr/bin/env python3
"""
Script local para testar a Lambda com QR codes reais.
Usa InvokeFunction chamando o handler diretamente.
"""

import base64
import json
import sys
from pathlib import Path

# Adicionar lambda ao path
sys.path.insert(0, str(Path(__file__).parent / "lambda"))

from lambda_function import lambda_handler

def test_qrcode(image_path: str) -> None:
    """Testar decodificação de um QR code local."""
    
    image_path = Path(image_path)
    
    if not image_path.exists():
        print(f"❌ Arquivo não encontrado: {image_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"🔍 Testando: {image_path.name}")
    print(f"{'='*70}")
    
    # Ler imagem e codificar em base64
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    print(f"📷 Tamanho da imagem: {len(image_bytes) / 1024:.1f} KB")
    print(f"📦 Base64 size: {len(b64_image) / 1024:.1f} KB")
    
    # Criar evento Lambda
    event = {
        "version": "2.0",
        "routeKey": "POST /decode",
        "rawPath": "/dev/decode",
        "rawQueryString": "",
        "headers": {
            "content-type": "application/json",
        },
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "hqpzy33kx3",
            "domainName": "hqpzy33kx3.execute-api.us-east-1.amazonaws.com",
            "domainPrefix": "hqpzy33kx3",
            "http": {
                "method": "POST",
                "path": "/dev/decode",
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "local-test",
            },
            "requestId": "test-request-id",
            "routeKey": "POST /decode",
            "stage": "dev",
            "time": "12/Feb/2026:00:00:00 +0000",
            "timeEpoch": 1739347200000,
        },
        "body": json.dumps({"image": b64_image}),
        "isBase64Encoded": False,
    }
    
    # Invocar handler
    context = type('Context', (), {
        'function_name': 'paguebem-api-dev',
        'function_version': '$LATEST',
        'invoked_function_arn': 'arn:aws:lambda:us-east-1:123456789012:function:paguebem-api-dev',
        'memory_limit_in_mb': 512,
        'aws_request_id': 'test-request-id',
        'log_group_name': '/aws/lambda/paguebem-api-dev',
        'log_stream_name': '$LATEST',
        'identity': None,
        'client_context': None,
    })()
    
    print("\n⚙️  Invocando lambda_handler...")
    try:
        import time
        start = time.time()
        
        response = lambda_handler(event, context)
        
        elapsed = time.time() - start
        
        print(f"✅ Status: 200 (em {elapsed:.2f}s)")
        
        body = json.loads(response.get("body", "{}"))
        
        if body.get("found"):
            print(f"✅ QR ENCONTRADO!")
            print(f"   Tipo: {body['results'][0]['type']}")
            print(f"   Dados: {body['results'][0]['data']}")
            print(f"   Transform: {body.get('transform')}")
        else:
            print(f"❌ Nenhum QR/barcode detectado")
            print(f"   Mensagem: {body.get('message')}")
        
        print(f"\n📊 Response completo:")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Erro ao invocar handler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Testar os 3 QR codes
    qrcodes = [
        "C:\\Users\\alexs\\Downloads\\qrcode1.jpeg",
        "C:\\Users\\alexs\\Downloads\\qrcode2.jpeg",
        "C:\\Users\\alexs\\Downloads\\qrcode3.jpeg",
    ]
    
    print("\n" + "="*70)
    print("🚀 TESTE LOCAL - QR CODE DECODER")
    print("="*70)
    
    for qrcode_path in qrcodes:
        test_qrcode(qrcode_path)
    
    print("\n" + "="*70)
    print("✅ Testes concluídos!")
    print("="*70)
