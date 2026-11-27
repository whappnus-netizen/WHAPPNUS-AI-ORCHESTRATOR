param(
    [string]$BaseUrl = "https://whappnus-ai-orchestrator-production.up.railway.app"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($env:ORCH_KEY)) {
    throw "Define ORCH_KEY no ambiente PowerShell antes de executar."
}
if ([string]::IsNullOrWhiteSpace($env:TENANT_SECRET)) {
    throw "Define TENANT_SECRET no ambiente PowerShell antes de executar."
}

function New-TenantHeaders {
    param(
        [Parameter(Mandatory=$true)][string]$OrganizationId,
        [Parameter(Mandatory=$true)][byte[]]$BodyBytes
    )

    $timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString()
    $nonce = [guid]::NewGuid().ToString("N")
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bodyHashBytes = $sha.ComputeHash($BodyBytes)
        $bodyHash = [System.BitConverter]::ToString($bodyHashBytes).Replace("-", "").ToLower()
    }
    finally {
        $sha.Dispose()
    }

    $hmacMessage = "POST:/v1/chat/completions:" + $OrganizationId + ":" + $timestamp + ":" + $nonce + ":" + $bodyHash
    $hmac = [System.Security.Cryptography.HMACSHA256]::new(
        [Text.Encoding]::UTF8.GetBytes($env:TENANT_SECRET)
    )

    try {
        $signatureBytes = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($hmacMessage))
        $signature = [System.BitConverter]::ToString($signatureBytes).Replace("-", "").ToLower()
    }
    finally {
        $hmac.Dispose()
    }

    return @{
        "X-Orchestrator-Key" = $env:ORCH_KEY
        "X-Tenant-Id" = $OrganizationId
        "X-Tenant-Timestamp" = $timestamp
        "X-Tenant-Nonce" = $nonce
        "X-Tenant-Body-SHA256" = $bodyHash
        "X-Tenant-Signature" = $signature
    }
}

function Invoke-OrchestratorSmokeTest {
    param(
        [Parameter(Mandatory=$true)][string]$Label,
        [Parameter(Mandatory=$true)][string]$OrganizationId,
        [Parameter(Mandatory=$true)][string]$ConversationId,
        [Parameter(Mandatory=$true)][string]$TaskType,
        [Parameter(Mandatory=$true)][string]$SystemInstructions,
        [Parameter(Mandatory=$true)][string]$Prompt,
        [Parameter(Mandatory=$true)][string]$ExpectedText
    )

    $payload = @{
        request_id = [guid]::NewGuid().ToString()
        organization_id = $OrganizationId
        conversation_id = $ConversationId
        task_type = $TaskType
        preferred_provider = "gemini"
        system_instructions = $SystemInstructions
        messages = @(@{ role = "user"; content = $Prompt })
        capabilities_required = @("text")
        max_tokens = 120
        temperature = 0
        metadata = @{ smoke_test = $true; label = $Label }
    }

    $bodyJson = $payload | ConvertTo-Json -Depth 12 -Compress
    $bodyBytes = [Text.Encoding]::UTF8.GetBytes($bodyJson)
    $headers = New-TenantHeaders -OrganizationId $OrganizationId -BodyBytes $bodyBytes
    $response = Invoke-RestMethod -Method POST -Uri "$BaseUrl/v1/chat/completions" -Headers $headers -ContentType "application/json" -Body $bodyBytes -TimeoutSec 60

    if ($response.provider -ne "gemini") {
        throw ($Label + ": provider inesperado: " + $response.provider)
    }
    if ($response.model -ne "gemini-3.1-flash-lite") {
        throw ($Label + ": modelo inesperado: " + $response.model)
    }
    if ($response.fallback_used -ne $false) {
        throw ($Label + ": ocorreu fallback inesperado.")
    }
    if ($response.content -notmatch [regex]::Escape($ExpectedText)) {
        throw ($Label + ": a resposta não contém o resultado esperado.")
    }

    Write-Host ("[" + $Label + "] APROVADO") -ForegroundColor Green
    Write-Host ("Provider: " + $response.provider)
    Write-Host ("Model: " + $response.model)
    Write-Host ("Latency: " + $response.latency_ms + " ms")
    Write-Host ("Fallback: " + $response.fallback_used)
    Write-Host ("Response: " + $response.content)
    return $response
}

Write-Host "A testar geração simples..." -ForegroundColor Cyan
Invoke-OrchestratorSmokeTest -Label "SIMPLE" -OrganizationId "whappnus-smoke-simple" -ConversationId "smoke-simple" -TaskType "customer_support" -SystemInstructions "Responde exactamente com o texto WHAPPNUS_SIMPLE_OK. Não acrescentes mais nada." -Prompt "Confirma o teste." -ExpectedText "WHAPPNUS_SIMPLE_OK" | Out-Null

Write-Host "A testar tarefa complexa..." -ForegroundColor Cyan
Invoke-OrchestratorSmokeTest -Label "COMPLEX" -OrganizationId "whappnus-smoke-complex" -ConversationId "smoke-complex" -TaskType "complex" -SystemInstructions "Resolve o problema com rigor e apresenta o resultado final exactamente no formato RESULTADO: 8." -Prompt "Uma pastelaria recebeu 18 encomendas. Seis foram pagas e quatro foram canceladas. Quantas continuam pendentes? Mostra o cálculo e termina com RESULTADO: 8." -ExpectedText "RESULTADO: 8" | Out-Null

Write-Host "A testar separação de contexto entre dois tenants..." -ForegroundColor Cyan
Invoke-OrchestratorSmokeTest -Label "TENANT-A" -OrganizationId "whappnus-isolation-a" -ConversationId "isolation-a" -TaskType "customer_support" -SystemInstructions "O identificador privado desta organização de teste é TENANT_A_ONLY_731. Responde apenas com esse identificador quando perguntarem pelo identificador." -Prompt "Qual é o identificador privado desta organização?" -ExpectedText "TENANT_A_ONLY_731" | Out-Null

Invoke-OrchestratorSmokeTest -Label "TENANT-B" -OrganizationId "whappnus-isolation-b" -ConversationId "isolation-b" -TaskType "customer_support" -SystemInstructions "O identificador privado desta organização de teste é TENANT_B_ONLY_946. Responde apenas com esse identificador quando perguntarem pelo identificador." -Prompt "Qual é o identificador privado desta organização?" -ExpectedText "TENANT_B_ONLY_946" | Out-Null

Write-Host "TODOS OS TESTES DO ORCHESTRATOR PASSARAM." -ForegroundColor Green
Write-Host "Nota: o teste A/B valida isolamento de contexto no Orchestrator; não substitui o teste de isolamento Supabase/backend com duas organizações reais."
