$ErrorActionPreference = 'Stop'

function Wait-ServiceReady([scriptblock]$Check, [string]$Name, [int]$Attempts = 60) {
    for ($attempt = 0; $attempt -lt $Attempts; $attempt++) {
        if (& $Check) { return }
        Start-Sleep -Seconds 2
    }
    throw "$Name nao ficou disponivel. Confira a instalacao e tente novamente."
}

function Invoke-DockerQuiet {
    $ErrorActionPreference = 'Continue'
    docker @args *> $null
    return $LASTEXITCODE
}

function Test-DockerReady { return (Invoke-DockerQuiet info) -eq 0 }

function Ensure-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        $dockerBin = @(
            (Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin'),
            (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin')
        ) | Where-Object { Test-Path (Join-Path $_ 'docker.exe') } | Select-Object -First 1
        if ($dockerBin) {
            $env:PATH = "$dockerBin;$env:PATH"
        } else {
            throw 'Instale o Docker Desktop: https://www.docker.com/products/docker-desktop/'
        }
    }
    if (-not (Test-DockerReady)) {
        Write-Host 'Iniciando Docker Desktop...'
        if ((Invoke-DockerQuiet desktop start --detach) -ne 0) {
            $desktop = @(
                (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
                (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe')
            ) | Where-Object { Test-Path $_ } | Select-Object -First 1
            if (-not $desktop) { throw 'Nao foi possivel localizar o Docker Desktop.' }
            Start-Process -FilePath $desktop -WindowStyle Hidden
        }
        Wait-ServiceReady { Test-DockerReady } 'Docker'
    }
    if ((Invoke-DockerQuiet compose version) -ne 0) {
        throw 'Instale o Docker Compose junto com o Docker Desktop.'
    }
}

function Test-OllamaReady([string]$Url) {
    $response = $null
    $reader = $null
    try {
        $probe = [UriBuilder]"$($Url.TrimEnd('/'))/api/version"
        if ($probe.Host -eq 'localhost') { $probe.Host = '127.0.0.1' }
        $request = [System.Net.HttpWebRequest]::Create($probe.Uri)
        $request.Proxy = $null
        $request.Timeout = 2000
        $request.ReadWriteTimeout = 2000
        $response = $request.GetResponse()
        $reader = [System.IO.StreamReader]::new($response.GetResponseStream())
        $body = $reader.ReadToEnd() | ConvertFrom-Json
        return [bool]$body.version
    } catch { return $false } finally {
        if ($reader) { $reader.Dispose() }
        if ($response) { $response.Dispose() }
    }
}

function Ensure-Ollama([string]$Url) {
    $endpoint = [Uri]$Url
    if ($endpoint.Scheme -ne 'http' -or -not $endpoint.IsLoopback -or $endpoint.UserInfo -or
        $endpoint.AbsolutePath -ne '/' -or $endpoint.Query -or $endpoint.Fragment) {
        throw 'OLLAMA_BASE_URL deve apontar para localhost ou 127.0.0.1.'
    }
    if (Test-OllamaReady $Url) { return }
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    $ollamaPath = if ($ollama) { $ollama.Source } else {
        Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    }
    if (-not (Test-Path $ollamaPath)) {
        throw 'Instale o Ollama: https://ollama.com/download/windows'
    }
    Write-Host 'Iniciando Ollama...'
    $previousHost = $env:OLLAMA_HOST
    try {
        $env:OLLAMA_HOST = $endpoint.Authority
        Start-Process -FilePath $ollamaPath -ArgumentList 'serve' -WindowStyle Hidden
    } finally { $env:OLLAMA_HOST = $previousHost }
    Wait-ServiceReady { Test-OllamaReady $Url } 'Ollama' 30
}

function Start-Application {
    Set-Location (Split-Path $PSScriptRoot -Parent)
    if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
    $keys = @('APP_PORT', 'OLLAMA_BASE_URL', 'OLLAMA_DOCKER_URL')
    foreach ($line in Get-Content '.env') {
        if ($line -match '^\s*([A-Z_]+)\s*=(.*)$' -and $Matches[1] -in $keys) {
            [Environment]::SetEnvironmentVariable(
                $Matches[1], $Matches[2].Trim().Trim('"').Trim("'"), 'Process')
        }
    }
    if (-not $env:APP_PORT) { $env:APP_PORT = '8501' }
    if (-not $env:OLLAMA_BASE_URL) { $env:OLLAMA_BASE_URL = 'http://localhost:11434' }
    Ensure-Docker
    if ($env:OLLAMA_DOCKER_URL -eq 'http://ollama:11434') {
        docker compose --profile ollama up -d ollama
        if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel iniciar o Ollama no Docker.' }
        Wait-ServiceReady {
            return (Invoke-DockerQuiet compose exec -T ollama ollama list) -eq 0
        } 'Ollama'
    } else { Ensure-Ollama $env:OLLAMA_BASE_URL }
    docker compose up -d --build app
    if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel iniciar a aplicacao no Docker.' }
    Write-Host "Aplicacao disponivel em http://127.0.0.1:$env:APP_PORT"
}

if ($MyInvocation.InvocationName -ne '.') {
    try { Start-Application } catch {
        Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}
