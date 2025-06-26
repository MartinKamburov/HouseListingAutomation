<#  HouseListingAutomation one‑shot installer (sub‑folder version) #>

$ErrorActionPreference = "Stop"

$repoUrl   = "https://github.com/MartinKamburov/HouseListingAutomation.git"
$rootDir = Split-Path $PSScriptRoot -Parent
$project = Join-Path $rootDir "HouseListingAutomation"
$venvDir   = Join-Path $project "scraping"

Write-Host "`n=== HouseListingAutomation setup ===`n"

# ------------------------------------------------------------
# 1. Clone or update the repo
# ------------------------------------------------------------
if (Test-Path (Join-Path $project ".git")) {
    Write-Host "Updating existing repository in $project"
    git -C $project pull
} elseif (Test-Path $project) {
    Write-Host "ERROR: $project exists but is not a git repo."
    Write-Host "       Move or delete it, or rename the folder in the script."
    exit 1
} else {
    Write-Host "Cloning repository into $project"
    git clone $repoUrl $project
}

# ------------------------------------------------------------
# 2. Create / reuse virtual environment
# ------------------------------------------------------------
if (-not (Test-Path $venvDir)) {
    Write-Host "Creating virtual environment at $venvDir"
    python -m venv $venvDir
}

Write-Host "Activating virtual environment"
& (Join-Path $venvDir "Scripts\Activate.ps1")

# ------------------------------------------------------------
# 3. Install / update Python tooling & deps
# ------------------------------------------------------------
Write-Host "Upgrading pip, wheel, setuptools"
python -m pip install --upgrade pip wheel setuptools

Write-Host "Installing Python requirements"
pip install -r (Join-Path $project "requirements.txt")

# ------------------------------------------------------------
# 4. Finish
# ------------------------------------------------------------
Write-Host "`nInstallation complete!"
Write-Host "`nNext steps:"
Write-Host "  1. Edit $(Join-Path $project 'config.json') with your Facebook and proxy credentials."
Write-Host "  2. Launch the Streamlit app:"
Write-Host "       cd $project"
Write-Host "       .\scraping\Scripts\Activate.ps1"
Write-Host "       streamlit run main.py"
Write-Host "`nHappy scraping!"