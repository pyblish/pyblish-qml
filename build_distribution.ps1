#
# Generate a self-contained distribution of Pyblish QML for Windows 10+
#

param (
    # Find available versions @ https://www.python.org/downloads/windows
    [string]$pythonVersion = "3.10.11",

    # Find available versions @ https://pypi.org/project/PySide2/#history
    [string]$qtVersion = "5.15.2.1"
)

$versionParts = $pythonVersion -split '\.' | Select-Object -First 2
$pythonPrefix = $versionParts -join ''

# Step 1: Download Python embeddable package
$pythonZipUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-embed-win32.zip"
$pythonZipFile = "python-$pythonVersion-embed-win32.zip"
Write-Host "Downloading Python embeddable package..."
Invoke-WebRequest -Uri $pythonZipUrl -OutFile $pythonZipFile
Write-Host "Download completed."

# Step 2: Extract the zip file
$targetDir = "pyblish-qml-dist"
Write-Host "Extracting the Python package..."
Expand-Archive -Path $pythonZipFile -DestinationPath $targetDir
Write-Host "Extraction completed."

# Step 3: Modify python$pythonPrefix._pth to expose pip and later PySide and Pyblish
$pthFile = Join-Path -Path $targetDir -ChildPath "python$pythonPrefix._pth"
$pthContent = @"
python$pythonPrefix.zip
.
Lib
Lib/site-packages
"@
Write-Host "Modifying python$pythonPrefix._pth file..."
Set-Content -Path $pthFile -Value $pthContent
Write-Host "Modification completed."

# Change directory
Set-Location -Path $targetDir

# Step 4: Download get-pip.py
$pipScriptUrl = "https://bootstrap.pypa.io/get-pip.py"
$pipScriptFile = "get-pip.py"
Write-Host "Downloading get-pip.py..."
Invoke-WebRequest -Uri $pipScriptUrl -OutFile $pipScriptFile
Write-Host "Download of get-pip.py completed."

# Step 5: Install pip
Write-Host "Installing pip..."
./python.exe $pipScriptFile
Write-Host "Pip installation completed."

# Step 6: Install pyblish-qml and PySide2
Write-Host "Installing pyblish-qml..."
./python.exe -m pip install git+https://github.com/pyblish/pyblish-qml.git
Write-Host "pyblish-qml installation completed."

Write-Host "Installing PySide2==$qtVersion..."
./python.exe -m pip install PySide2==$qtVersion
Write-Host "PySide2 installation completed."

# Step 7: Create a new PowerShell script for the demo
$executable = @"
#pwsh
`$env:PYTHONPATH="`$psscriptroot\Lib\site-packages"
`$env:PYBLISH_QML_PYTHON_EXECUTABLE="`$psscriptroot/python.exe"
& ./python.exe -m pyblish_qml --demo
"@
$executableFile = "pyblish-qml.ps1"
$executable | Out-File -FilePath $executableFile -Encoding UTF8
Write-Host "pyblish_qml.ps1 has been created."

# Reminder to change back to the original directory if needed
# Set-Location -Path $originalPath

Write-Host "Setup complete. Run .\$executableFile to start"
