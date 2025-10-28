@echo off
echo ================================================
echo  Installing GPU-accelerated PyTorch for Windows
echo  CUDA 12.0+ Support
echo ================================================
echo.

echo Checking NVIDIA GPU...
nvidia-smi
if %errorlevel% neq 0 (
    echo ERROR: NVIDIA GPU not detected or drivers not installed
    echo Please install NVIDIA drivers and try again
    pause
    exit /b 1
)

echo.
echo Installing PyTorch with CUDA support...
echo This will download ~2-3GB of packages
echo.

REM Install PyTorch with CUDA 12.1 support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyTorch with CUDA
    echo Trying CPU-only fallback...
    pip install torch torchvision torchaudio
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install PyTorch
        pause
        exit /b 1
    )
    echo WARNING: Installed CPU-only PyTorch (no GPU acceleration)
) else (
    echo SUCCESS: PyTorch with CUDA support installed
)

echo.
echo Testing GPU availability...
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}'); print(f'GPU count: {torch.cuda.device_count()}'); print(f'GPU name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

echo.
echo ================================================
echo  GPU Package Installation Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Install other requirements: pip install -r backend/requirements.txt
echo 2. Start the system: .\start.ps1
echo.
pause
