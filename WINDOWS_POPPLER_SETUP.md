# Windows Poppler Setup Guide

## Option 1: Hardcode Poppler Path (Recommended if you can't install system-wide)

If you cannot install poppler system-wide or add it to PATH, you can hardcode the path directly in the code.

### Steps:

1. **Download Poppler for Windows:**
   - Go to: https://github.com/oschwartz10612/poppler-windows/releases
   - Download the latest release (e.g., `Release-XX.XX.X-X.zip`)
   - Extract to a folder, for example: `C:\poppler`

2. **Find the bin folder:**
   - Inside the extracted folder, navigate to `Library\bin`
   - This folder should contain `pdftoppm.exe` and other poppler executables
   - Full path example: `C:\poppler\Library\bin`

3. **Edit `pdf_to_image_converter.py`:**
   - Open the file in a text editor
   - Find the section at the top that says:
     ```python
     POPPLER_PATH = None
     ```
   - Change it to your poppler bin path:
     ```python
     POPPLER_PATH = r"C:\poppler\Library\bin"
     ```
   - **Important:** Use `r"..."` (raw string) to handle Windows backslashes correctly
   - **Important:** Make sure the path points to the `bin` folder (where `pdftoppm.exe` is located)

4. **Verify the path:**
   - Check that `pdftoppm.exe` exists in the folder you specified
   - Example: `C:\poppler\Library\bin\pdftoppm.exe` should exist

5. **Test:**
   ```bash
   python pdf_to_image_converter.py test.pdf
   ```

### Example Configurations:

```python
# Example 1: Poppler in C drive
POPPLER_PATH = r"C:\poppler\Library\bin"

# Example 2: Poppler in D drive
POPPLER_PATH = r"D:\tools\poppler\Library\bin"

# Example 3: Poppler in user directory
POPPLER_PATH = r"C:\Users\YourName\poppler\Library\bin"

# Example 4: Poppler in project directory (relative paths work too)
POPPLER_PATH = r".\poppler\Library\bin"
```

## Option 2: Environment Variable

You can also set the `POPPLER_PATH` environment variable instead of hardcoding:

### Windows Command Prompt:
```cmd
set POPPLER_PATH=C:\poppler\Library\bin
```

### Windows PowerShell:
```powershell
$env:POPPLER_PATH = "C:\poppler\Library\bin"
```

### Permanent (System Environment Variables):
1. Open "System Properties" → "Environment Variables"
2. Add new variable:
   - Name: `POPPLER_PATH`
   - Value: `C:\poppler\Library\bin`
3. Restart your terminal/IDE

## Option 3: Add to PATH (System-wide)

1. Extract poppler to `C:\poppler`
2. Add `C:\poppler\Library\bin` to your system PATH
3. Restart your terminal/IDE

## Troubleshooting

### Error: "Unable to get page count"
- **Cause:** Poppler path is incorrect or poppler is not found
- **Solution:** 
  - Verify the path points to the `bin` folder
  - Check that `pdftoppm.exe` exists in that folder
  - Use raw strings (`r"..."`) for Windows paths

### Error: "FileNotFoundError" or "pdftoppm not found"
- **Cause:** The executable is not in the specified path
- **Solution:**
  - Make sure you're pointing to the `bin` folder, not the root poppler folder
  - Check that the path uses backslashes correctly (use raw string `r"..."`)

### Testing Your Configuration

You can test if poppler is found by running:
```python
from pdf_to_image_converter import get_poppler_path
print(get_poppler_path())
```

This will show which path is being used (hardcoded, env var, or None).

## Priority Order

The code checks for poppler path in this order:
1. **Hardcoded `POPPLER_PATH`** in `pdf_to_image_converter.py` (highest priority)
2. **`POPPLER_PATH` environment variable**
3. **System PATH** (lowest priority)

This means if you hardcode the path, it will always use that path, even if environment variables are set.

