# Installation Instructions

## Important: Preserving Your CUDA PyTorch Installation

If you have **torch 2.5.1+cu121** (CUDA version) installed, use this command to install requirements **without** changing your PyTorch installation:

```bash
pip install -r requirements.txt --upgrade-strategy only-if-needed
```

This will:
- ✅ Install missing packages
- ✅ Preserve your existing CUDA PyTorch installation
- ✅ Only upgrade packages if necessary

## Alternative: Install Without Dependencies

If you still encounter issues, you can install packages individually or exclude torch dependencies:

```bash
# Install Flask and web dependencies first
pip install Flask Werkzeug

# Install other packages (will use your existing torch)
pip install -r requirements.txt --upgrade-strategy only-if-needed
```

## If Torch Gets Uninstalled

If your CUDA torch gets uninstalled accidentally, reinstall it with:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

## Why This Happens

Some packages in `requirements.txt` (like `transformers`, `ultralytics`, `timm`) have optional dependencies on PyTorch. When pip sees a version mismatch, it may try to "fix" it by installing a CPU version. Using `--upgrade-strategy only-if-needed` prevents this.

