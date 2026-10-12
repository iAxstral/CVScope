<#
.SYNOPSIS
  Levanta CVScope completo (backend + frontend) para verlo en el navegador.

.DESCRIPTION
  La primera vez prepara todo: crea el entorno virtual del backend, instala las
  dependencias, genera backend\.env con un AUTH_SECRET y una ADMIN_PASSWORD
  aleatorios (si faltan) e instala los paquetes del frontend. Después abre el
  backend y el frontend cada uno en su ventana y el navegador en la aplicación.

.PARAMETER Liviano
  Instala solo la API (sin PyTorch ni el clasificador de rol). Es más rápido,
  pero POST /preseleccion/categorizar responde 503.

.PARAMETER NoAbrir
  No abre el navegador.

.EXAMPLE
  .\iniciar.ps1
  .\iniciar.ps1 -Liviano
#>
param(
    [switch]$Liviano,
    [switch]$NoAbrir
)

$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
$backend = Join-Path $raiz "backend"
$frontend = Join-Path $raiz "frontend"
$venv = Join-Path $backend ".venv"
$python = Join-Path $venv "Scripts\python.exe"

function Paso($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }

function Puerto-Libre([int]$desde) {
    for ($p = $desde; $p -lt $desde + 50; $p++) {
        $ocupado = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
        if (-not $ocupado) { return $p }
    }
    throw "No hay un puerto libre cerca de $desde"
}

function Clave-Aleatoria([int]$bytes) {
    $b = New-Object byte[] $bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    return ([System.BitConverter]::ToString($b) -replace "-", "").ToLower()
}

# --- Requisitos
foreach ($cmd in @("python", "node", "npm")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "Falta '$cmd' en el PATH. Instálalo y vuelve a correr el script."
    }
}

# --- Backend: entorno virtual y dependencias
if (-not (Test-Path $python)) {
    Paso "Creando el entorno virtual del backend"
    python -m venv $venv
}
$requisitos = if ($Liviano) { "requirements-api.txt" } else { "requirements.txt" }
$marca = Join-Path $venv ".instalado-$requisitos"
if (-not (Test-Path $marca) -or ((Get-Item (Join-Path $backend $requisitos)).LastWriteTime -gt (Get-Item $marca).LastWriteTime)) {
    Paso "Instalando dependencias del backend ($requisitos)"
    if (-not $Liviano) { Write-Host "    Incluye PyTorch y el clasificador de rol: la primera vez tarda varios minutos." }
    & $python -m pip install --quiet --disable-pip-version-check -r (Join-Path $backend $requisitos)
    if ($LASTEXITCODE -ne 0) { throw "Falló la instalación de las dependencias del backend" }
    New-Item -ItemType File -Path $marca -Force | Out-Null
}

# --- Backend: backend\.env con las variables obligatorias
$envArchivo = Join-Path $backend ".env"
if (-not (Test-Path $envArchivo)) { New-Item -ItemType File -Path $envArchivo | Out-Null }
$contenido = Get-Content $envArchivo -Raw -ErrorAction SilentlyContinue
if ($null -eq $contenido) { $contenido = "" }
if ($contenido -notmatch "(?m)^AUTH_SECRET=\S") {
    Add-Content $envArchivo "AUTH_SECRET=$(Clave-Aleatoria 32)"
    Write-Host "    AUTH_SECRET generado en backend\.env"
}
if ($contenido -notmatch "(?m)^ADMIN_PASSWORD=\S") {
    $clave = Clave-Aleatoria 6
    Add-Content $envArchivo "ADMIN_PASSWORD=$clave"
    Write-Host "    Usuario inicial -> admin@cvscope.co / $clave  (guardado en backend\.env)" -ForegroundColor Yellow
}
$correo = if ($contenido -match "(?m)^ADMIN_EMAIL=(\S+)") { $Matches[1] } else { "admin@cvscope.co" }
$claveAdmin = ((Get-Content $envArchivo) | Where-Object { $_ -match "^ADMIN_PASSWORD=(\S+)" } | Select-Object -First 1) -replace "^ADMIN_PASSWORD=", ""

# --- Frontend: dependencias
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Paso "Instalando dependencias del frontend"
    Push-Location $frontend
    try { npm install --no-audit --no-fund; if ($LASTEXITCODE -ne 0) { throw "Falló npm install" } } finally { Pop-Location }
}

# --- Puertos libres y arranque
$puertoApi = Puerto-Libre 8000
$puertoWeb = Puerto-Libre 5173
$urlApi = "http://127.0.0.1:$puertoApi"
$urlWeb = "http://localhost:$puertoWeb"

$env:CORS_ORIGINS = "$urlWeb,http://127.0.0.1:$puertoWeb"
$env:VITE_API_URL = $urlApi

Paso "Iniciando el backend en $urlApi"
$procApi = Start-Process powershell -PassThru -WorkingDirectory $backend -ArgumentList @(
    "-NoExit", "-Command",
    "`$Host.UI.RawUI.WindowTitle='CVScope - backend'; & '$python' -m uvicorn app.main:app --host 127.0.0.1 --port $puertoApi"
)

Paso "Iniciando el frontend en $urlWeb"
$procWeb = Start-Process powershell -PassThru -WorkingDirectory $frontend -ArgumentList @(
    "-NoExit", "-Command",
    "`$Host.UI.RawUI.WindowTitle='CVScope - frontend'; npm run dev -- --host localhost --port $puertoWeb --strictPort"
)

# --- Esperar a que respondan
Write-Host "`nEsperando a que arranquen..." -NoNewline
$listo = $false
for ($i = 0; $i -lt 90 -and -not $listo; $i++) {
    Start-Sleep -Seconds 1
    Write-Host "." -NoNewline
    try {
        Invoke-WebRequest "$urlApi/" -UseBasicParsing -TimeoutSec 2 | Out-Null
        Invoke-WebRequest "$urlWeb/" -UseBasicParsing -TimeoutSec 2 | Out-Null
        $listo = $true
    } catch { }
}
Write-Host ""
if (-not $listo) {
    Write-Host "No respondieron a tiempo: revisa las ventanas del backend y del frontend." -ForegroundColor Red
}

Write-Host @"

CVScope está corriendo:
  Aplicación : $urlWeb
  API / docs : $urlApi/docs
  Usuario    : $correo
  Contraseña : $claveAdmin

"@ -ForegroundColor Green

if ($listo -and -not $NoAbrir) { Start-Process $urlWeb }

Read-Host "Pulsa Enter para detener el backend y el frontend"
foreach ($p in @($procApi, $procWeb)) {
    if ($p -and -not $p.HasExited) { taskkill /T /F /PID $p.Id | Out-Null }
}
Write-Host "Detenido."
