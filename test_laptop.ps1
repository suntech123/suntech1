<#
.SYNOPSIS
    Refurbished Laptop Condition Checker
.DESCRIPTION
    Retrieves critical hardware information, battery health, storage health, 
    and activation status to validate a used/refurbished laptop.
    Requires 'Run as Administrator'.
#>

# --- Check for Admin Rights ---
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator to access Battery and Disk Health data."
    Start-Sleep -s 3
    Exit
}

Clear-Host
$host.UI.RawUI.WindowTitle = "Refurbished Laptop Inspection Tool"

# --- Helper Function for Formatting ---
function Write-Header ($text) {
    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host " $text" -ForegroundColor White
    Write-Host "==========================================" -ForegroundColor Cyan
}

function Write-Info ($label, $value, $status="Normal") {
    $color = "White"
    if ($status -eq "Good") { $color = "Green" }
    if ($status -eq "Warning") { $color = "Yellow" }
    if ($status -eq "Critical") { $color = "Red" }
    
    Write-Host "$label: " -NoNewline -ForegroundColor Gray
    Write-Host $value -ForegroundColor $color
}

# --- 1. SYSTEM SUMMARY ---
Write-Header "SYSTEM INFORMATION"
$sysInfo = Get-CimInstance Win32_ComputerSystem
$bios = Get-CimInstance Win32_BIOS
$os = Get-CimInstance Win32_OperatingSystem

Write-Info "Manufacturer" $sysInfo.Manufacturer
Write-Info "Model" $sysInfo.Model
Write-Info "Serial Number" $bios.SerialNumber
Write-Info "OS Version" $os.Caption
Write-Info "BIOS Version" $bios.SMBIOSBIOSVersion

# --- 2. CPU DETAILS ---
Write-Header "PROCESSOR (CPU)"
$cpu = Get-CimInstance Win32_Processor
Write-Info "Name" $cpu.Name
Write-Info "Cores/Logical" "$($cpu.NumberOfCores) Cores / $($cpu.NumberOfLogicalProcessors) Threads"
Write-Info "Current Clock" "$($cpu.MaxClockSpeed) MHz"

# --- 3. MEMORY (RAM) ---
Write-Header "MEMORY (RAM)"
$ramSticks = Get-CimInstance Win32_PhysicalMemory
$totalRam = 0
foreach ($stick in $ramSticks) {
    $gb = [math]::Round($stick.Capacity / 1GB, 0)
    $totalRam += $gb
    Write-Info "Slot Info" "$gb GB | Speed: $($stick.Speed) MHz | Maker: $($stick.Manufacturer)"
}
Write-Info "Total Installed" "$totalRam GB" "Good"

# --- 4. STORAGE HEALTH (SSD/HDD) ---
Write-Header "STORAGE DRIVES & HEALTH"
try {
    $disks = Get-PhysicalDisk | Sort-Object DeviceId
    foreach ($disk in $disks) {
        $sizeGB = [math]::Round($disk.Size / 1GB, 0)
        $healthColor = if ($disk.HealthStatus -eq "Healthy") { "Good" } else { "Critical" }
        
        Write-Info "Drive $($disk.DeviceId)" "$($disk.FriendlyName) ($($disk.MediaType))"
        Write-Info "  - Capacity" "$sizeGB GB"
        Write-Info "  - Health Status" $disk.HealthStatus $healthColor
        
        # Check for SMART failures
        if ($disk.HealthStatus -ne "Healthy") {
            Write-Warning "  Warning: This drive is reporting S.M.A.R.T errors!"
        }
    }
} catch {
    Write-Warning "Could not retrieve detailed disk health. Ensure you are running as Admin."
}

# --- 5. GRAPHICS / DISPLAY ---
Write-Header "GRAPHICS & DISPLAY"
$gpu = Get-CimInstance Win32_VideoController
foreach ($g in $gpu) {
    $res = if ($g.CurrentHorizontalResolution) { "$($g.CurrentHorizontalResolution) x $($g.CurrentVerticalResolution)" } else { "Unknown (Driver Issue?)" }
    Write-Info "GPU Name" $g.Name
    Write-Info "Resolution" $res
    Write-Info "Driver Date" $g.DriverDate
}

# --- 6. BATTERY HEALTH REPORT ---
Write-Header "BATTERY HEALTH"
try {
    # Attempt to calculate wear level via WMI
    $battStatic = Get-WmiObject -Class BatteryStaticData -Namespace root\wmi -ErrorAction SilentlyContinue
    $battFull   = Get-WmiObject -Class BatteryFullChargedCapacity -Namespace root\wmi -ErrorAction SilentlyContinue
    
    if ($battStatic -and $battFull) {
        $designCap = $battStatic.DesignedCapacity
        $fullCap   = $battFull.FullChargedCapacity
        
        # Determine specific battery (usually the first one found)
        $dCap = $designCap[0]
        $fCap = $fullCap[0]
        
        if ($dCap -gt 0) {
            $healthPct = [math]::Round(($fCap / $dCap) * 100, 1)
            $wearLevel = [math]::Round(100 - $healthPct, 1)
            
            $statusColor = "Good"
            if ($healthPct -lt 70) { $statusColor = "Warning" }
            if ($healthPct -lt 50) { $statusColor = "Critical" }

            Write-Info "Design Capacity" "$dCap mWh"
            Write-Info "Current Full Cap" "$fCap mWh"
            Write-Info "Battery Health" "$healthPct%" $statusColor
            Write-Info "Wear Level" "$wearLevel% (Lower is better)"
        } else {
             Write-Warning "Battery firmware not reporting correct capacity data."
        }
    } else {
        # Fallback to standard class if WMI detailed data is missing
        $batt = Get-CimInstance Win32_Battery
        Write-Info "Status" $batt.Status
        Write-Info "Estimated Charge" "$($batt.EstimatedChargeRemaining)%"
        Write-Host "  Note: Could not calculate exact wear level on this model." -ForegroundColor Yellow
    }
} catch {
    Write-Info "Battery Info" "No Battery Detected or Driver Error" "Critical"
}

# --- 7. WINDOWS ACTIVATION ---
Write-Header "WINDOWS LICENSE"
try {
    $license = Get-CimInstance SoftwareLicensingProduct | Where-Object { $_.PartialProductKey -and $_.Name -like "*Windows*" } | Select-Object -First 1
    
    if ($license) {
        $statusMap = @{
            0 = "Unlicensed"; 
            1 = "Licensed (Activated)"; 
            2 = "OOBE Grace"; 
            3 = "OOT Grace"; 
            4 = "Non-Genuine Grace"; 
            5 = "Notification"; 
            6 = "Extended Grace"
        }
        $stat = $statusMap[[int]$license.LicenseStatus]
        $color = if ($license.LicenseStatus -eq 1) { "Good" } else { "Warning" }
        Write-Info "License Status" $stat $color
    } else {
        Write-Info "License" "Could not determine status" "Warning"
    }
} catch {
    Write-Warning "Could not check license status."
}

Write-Header "INSPECTION COMPLETE"
Write-Host "Press any key to close..." -NoNewline
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")