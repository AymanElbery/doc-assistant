#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Installing GPU-accelerated PyTorch for Windows" -ForegroundColor Cyan
Write-Host "  CUDA 12.0+ Support" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking NVIDIA GPU..." -ForegroundColor Yellow
try {
    nvidia-smi | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "NVIDIA GPU not detected"
    }
    Write-Host "✅ NVIDIA GPU detected" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: NVIDIA GPU not detected or drivers not installed" -ForegroundColor Red
    Write-Host "Please install NVIDIA drivers and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Installing PyTorch with CUDA support..." -ForegroundColor Yellow
Write-Host "This will download ~2-3GB of packages" -ForegroundColor White
Write-Host ""

# Install PyTorch with CUDA 12.1 support
Write-Host "Installing PyTorch with CUDA 12.1..." -ForegroundColor Cyan
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Failed to install PyTorch with CUDA, trying CPU-only fallback..." -ForegroundColor Yellow
    pip install torch torchvision torchaudio
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: Failed to install PyTorch" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "⚠️ WARNING: Installed CPU-only PyTorch (no GPU acceleration)" -ForegroundColor Yellow
} else {
    Write-Host "✅ SUCCESS: PyTorch with CUDA support installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Testing GPU availability..." -ForegroundColor Cyan
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    print(f'GPU name: {torch.cuda.get_device_name(0)}')
    print(f'GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
else:
    print('CUDA not available - using CPU only')
"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  GPU Package Installation Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install other requirements: pip install -r backend/requirements.txt" -ForegroundColor White
Write-Host "2. Start the system: .\start.ps1" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to continue"
