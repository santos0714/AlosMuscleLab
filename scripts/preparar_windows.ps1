<#
MuscleSense Lab - preparacion del entorno en Windows.

Que hace, en este orden:
  1. Audita: Windows, CPU, GPU, Python, Node.js, npm, Git, VS Code y sus extensiones.
  2. Crea el entorno virtual .venv (si no existe) e instala requirements.txt dentro de el.
  3. Instala las extensiones de VS Code que falten (se omite con -SinExtensiones).
  4. Ejecuta las pruebas de funcionamiento (tests\test_entorno.py).

Todo queda registrado en docs\entorno\registro_windows.txt.
No cambia configuracion global: no toca PATH, ni la politica de ejecucion, ni los ajustes de VS Code.

Uso, desde la carpeta del proyecto:
  powershell -ExecutionPolicy Bypass -File scripts\preparar_windows.ps1
  powershell -ExecutionPolicy Bypass -File scripts\preparar_windows.ps1 -SoloAuditar
  powershell -ExecutionPolicy Bypass -File scripts\preparar_windows.ps1 -SinExtensiones
#>
param(
    [switch]$SoloAuditar,
    [switch]$SinExtensiones
)

$ErrorActionPreference = 'Continue'
$Raiz = Split-Path -Parent $PSScriptRoot
Set-Location $Raiz
$CarpetaLog = Join-Path $Raiz 'docs\entorno'
New-Item -ItemType Directory -Force -Path $CarpetaLog | Out-Null
$Log = Join-Path $CarpetaLog 'registro_windows.txt'
Set-Content -Path $Log -Encoding UTF8 -Value ('MuscleSense Lab - preparacion en Windows - ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))

function Escribir([string]$Texto) {
    Write-Host $Texto
    Add-Content -Path $Log -Encoding UTF8 -Value $Texto
}

function Ejecutar([string]$Titulo, [scriptblock]$Bloque) {
    Escribir ''
    Escribir ('--- ' + $Titulo)
    $global:LASTEXITCODE = 0
    try {
        & $Bloque 2>&1 | ForEach-Object { Escribir ([string]$_) }
    } catch {
        Escribir ('ERROR: ' + $_.Exception.Message)
        $global:LASTEXITCODE = 1
    }
}

function Buscar-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in '3.12', '3.13', '3.11', '3.10') {
            $ruta = (& py "-$v" -c "import sys; print(sys.executable)" 2>$null)
            if ($LASTEXITCODE -eq 0 -and $ruta) { return ([string]$ruta).Trim() }
        }
    }
    foreach ($v in '312', '313', '311', '310') {
        $ruta = Join-Path $env:LOCALAPPDATA ('Programs\Python\Python' + $v + '\python.exe')
        if (Test-Path $ruta) { return $ruta }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and ($cmd.Source -notlike '*WindowsApps*')) { return $cmd.Source }
    return $null
}

function Buscar-Code {
    $cmd = Get-Command code.cmd -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $ruta = Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code\bin\code.cmd'
    if (Test-Path $ruta) { return $ruta }
    return $null
}

# ---------------------------------------------------------------- 1. Auditoria
Escribir ''
Escribir '=== 1. AUDITORIA ==='
try {
    $so = Get-CimInstance Win32_OperatingSystem
    Escribir ('Windows: ' + $so.Caption + ' ' + $so.Version + ' (' + $so.OSArchitecture + ')')
    Escribir ('RAM (GB): ' + [math]::Round($so.TotalVisibleMemorySize / 1MB, 1))
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    Escribir ('CPU: ' + $cpu.Name + ' | nucleos: ' + $cpu.NumberOfCores + ' | hilos: ' + $cpu.NumberOfLogicalProcessors)
    Get-CimInstance Win32_VideoController | ForEach-Object {
        Escribir ('GPU: ' + $_.Name + ' | controlador: ' + $_.DriverVersion)
    }
} catch {
    Escribir ('No se pudo leer el hardware: ' + $_.Exception.Message)
}

$Python = Buscar-Python
if ($Python) {
    Ejecutar 'Python' { & $Python --version }
    Escribir ('Ruta: ' + $Python)
} else {
    Escribir ''
    Escribir 'Python: NO ENCONTRADO (se necesita 3.10 a 3.13)'
}
Ejecutar 'Node.js' { & node --version }
Ejecutar 'npm' { & npm.cmd --version }
Ejecutar 'Git' { & git --version }
$Code = Buscar-Code
if ($Code) {
    Ejecutar 'VS Code' { & $Code --version }
    Ejecutar 'Extensiones de VS Code instaladas' { & $Code --list-extensions --show-versions }
} else {
    Escribir ''
    Escribir 'VS Code: no se encontro code.cmd'
}

if ($SoloAuditar) {
    Escribir ''
    Escribir 'Modo -SoloAuditar: no se instalo nada.'
    Escribir ('Registro guardado en: ' + $Log)
    exit 0
}
if (-not $Python) {
    Escribir 'No se puede continuar sin Python.'
    exit 1
}

# ---------------------------------------------------------------- 2. Entorno virtual
Escribir ''
Escribir '=== 2. ENTORNO VIRTUAL Y BIBLIOTECAS ==='
$CarpetaVenv = Join-Path $Raiz '.venv'
$VenvPy = Join-Path $CarpetaVenv 'Scripts\python.exe'
if (Test-Path $VenvPy) {
    Escribir '.venv ya existe: se reutiliza.'
} else {
    Ejecutar 'Crear .venv' { & $Python -m venv $CarpetaVenv }
}
if (-not (Test-Path $VenvPy)) {
    Escribir 'ERROR: no se pudo crear .venv'
    exit 1
}
$Requisitos = Join-Path $Raiz 'requirements.txt'
Ejecutar 'Actualizar pip' { & $VenvPy -m pip install --upgrade pip --disable-pip-version-check -q }
Ejecutar 'Instalar requirements.txt (puede tardar varios minutos)' { & $VenvPy -m pip install -r $Requisitos --disable-pip-version-check -q }
$InstalacionOk = ($LASTEXITCODE -eq 0)
Ejecutar 'pip check' { & $VenvPy -m pip check }
Ejecutar 'Versiones instaladas' { & $VenvPy -m pip list --format=freeze }
Ejecutar 'Dispositivos OpenCL que ve MCX-CL (pmcxcl)' { & $VenvPy -c "import pmcxcl; print([d['name'] for d in pmcxcl.gpuinfo()])" }

# ---------------------------------------------------------------- 3. Extensiones de VS Code
if (-not $SinExtensiones) {
    Escribir ''
    Escribir '=== 3. EXTENSIONES DE VS CODE ==='
    if ($Code) {
        $Instaladas = @(& $Code --list-extensions 2>$null)
        foreach ($ext in 'ms-python.python', 'ms-toolsai.jupyter', 'dbaeumer.vscode-eslint', 'ms-playwright.playwright') {
            if ($Instaladas -contains $ext) {
                Escribir ('Ya instalada: ' + $ext)
            } else {
                Ejecutar ('Instalar extension ' + $ext) { & $Code --install-extension $ext }
            }
        }
    } else {
        Escribir 'No se encontro code.cmd: instala las extensiones recomendadas desde VS Code.'
    }
}

# ---------------------------------------------------------------- 4. Pruebas
Escribir ''
Escribir '=== 4. PRUEBAS DE FUNCIONAMIENTO ==='
$Pruebas = Join-Path $Raiz 'tests\test_entorno.py'
Ejecutar 'pytest tests\test_entorno.py' { & $VenvPy -m pytest $Pruebas -v -p no:cacheprovider }
$PruebasOk = ($LASTEXITCODE -eq 0)

Escribir ''
if ($InstalacionOk -and $PruebasOk) {
    Escribir 'RESULTADO: entorno de Windows preparado y verificado.'
} else {
    Escribir 'RESULTADO: hay problemas. Revisa los mensajes anteriores; Claude puede leer este registro.'
}
Escribir ('Registro guardado en: ' + $Log)
