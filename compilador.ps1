$ErrorActionPreference = "Stop"

# ---------------------------------------------------------
# Caminhos principais
# ---------------------------------------------------------

$RepoPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourcePath = Join-Path $RepoPath "App"

$MainFile = Join-Path $SourcePath "main.py"
$ModulesSource = Join-Path $SourcePath "modules"
$EnvSource = Join-Path $SourcePath ".env"

$DistPath = Join-Path $RepoPath "dist"
$WorkPath = Join-Path $RepoPath "build"
$SpecPath = Join-Path $RepoPath "build_spec"

$AppName = "Controles Almox"
$AppDistPath = Join-Path $DistPath $AppName
$ModulesDestination = Join-Path $AppDistPath "modules"

# ---------------------------------------------------------
# Validações
# ---------------------------------------------------------

if (-not (Test-Path $MainFile)) {
    throw "Arquivo principal nao encontrado: $MainFile"
}

if (-not (Test-Path $ModulesSource)) {
    throw "Pasta de modulos nao encontrada: $ModulesSource"
}

Write-Host ""
Write-Host "============================================"
Write-Host " Compilacao da aplicacao Controles Almox"
Write-Host "============================================"
Write-Host ""

Write-Host "Codigo-fonte:"
Write-Host "  $SourcePath"
Write-Host ""

# ---------------------------------------------------------
# Limpeza da compilacao anterior
# ---------------------------------------------------------

if (Test-Path $DistPath) {
    Write-Host "Removendo compilacao anterior..."
    
    Remove-Item `
        -Path $DistPath `
        -Recurse `
        -Force

    Write-Host "Removido: $DistPath"
    Write-Host ""
}

# ---------------------------------------------------------
# Argumentos do PyInstaller
# ---------------------------------------------------------

$PyInstallerArgs = @(
    "--clean"
    "--noconfirm"
    "--onedir"
    "--windowed"

    "--name=$AppName"

    "--paths=$SourcePath"
    "--distpath=$DistPath"
    "--workpath=$WorkPath"
    "--specpath=$SpecPath"

    # Impede que os modulos sejam compilados.
    "--exclude-module=modules"

    # Dependencias utilizadas pelos modulos.
    "--hidden-import=dotenv"
    "--collect-all=supabase"
    "--collect-all=extract_msg"
    "--collect-all=bs4"
    "--collect-all=lxml"
    "--collect-all=tkinterdnd2"
    "--collect-submodules=win32com"
    "--hidden-import=pythoncom"
    "--hidden-import=pywintypes"

    $MainFile
)

# ---------------------------------------------------------
# Compilacao
# ---------------------------------------------------------

Write-Host "Executando PyInstaller..."
Write-Host ""

& py -m PyInstaller @PyInstallerArgs

if ($LASTEXITCODE -ne 0) {
    throw "A compilacao do PyInstaller falhou. Codigo: $LASTEXITCODE"
}

if (-not (Test-Path $AppDistPath)) {
    throw "A pasta compilada nao foi encontrada: $AppDistPath"
}

# ---------------------------------------------------------
# Copia os modulos
# ---------------------------------------------------------

Write-Host ""
Write-Host "Sincronizando modulos..."

New-Item `
    -ItemType Directory `
    -Path $ModulesDestination `
    -Force |
    Out-Null

# /MIR mantem o destino identico a origem.
# Exclui caches do Python.
& robocopy `
    $ModulesSource `
    $ModulesDestination `
    /MIR `
    /XD "__pycache__" `
    /XF "*.pyc" "*.pyo" `
    /NFL `
    /NDL `
    /NJH `
    /NJS `
    /NP

$RobocopyExitCode = $LASTEXITCODE

# Robocopy considera códigos de 0 a 7 como sucesso.
if ($RobocopyExitCode -ge 8) {
    throw "Falha ao copiar modulos. Codigo Robocopy: $RobocopyExitCode"
}

# ---------------------------------------------------------
# Copia o arquivo .env externo
# ---------------------------------------------------------

if (Test-Path $EnvSource) {
    Copy-Item `
        -Path $EnvSource `
        -Destination (Join-Path $AppDistPath ".env") `
        -Force

    Write-Host "Arquivo .env copiado."
}
else {
    Write-Warning (
        "O arquivo .env nao foi encontrado em: " +
        $EnvSource
    )
}

# ---------------------------------------------------------
# Remove arquivos temporarios da compilacao
# ---------------------------------------------------------

Write-Host ""
Write-Host "Removendo arquivos temporarios..."

$TemporaryPaths = @(
    $WorkPath
    $SpecPath
)

foreach ($TemporaryPath in $TemporaryPaths) {
    if (Test-Path $TemporaryPath) {
        Remove-Item `
            -Path $TemporaryPath `
            -Recurse `
            -Force

        Write-Host "Removido: $TemporaryPath"
    }
}

Write-Host "Limpeza concluida."

# ---------------------------------------------------------
# Resultado
# ---------------------------------------------------------

Write-Host ""
Write-Host "============================================"
Write-Host " Compilacao concluida"
Write-Host "============================================"
Write-Host ""
Write-Host "Aplicacao gerada em:"
Write-Host "  $AppDistPath"
Write-Host ""
Write-Host "Modulos em:"
Write-Host "  $ModulesDestination"
Write-Host ""

# Evita que o codigo de retorno do Robocopy
# seja interpretado como falha pelo terminal.
exit 0