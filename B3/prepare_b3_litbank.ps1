# B3 - Menyiapkan 30+ teks nyata menggunakan LitBank
# LitBank adalah dataset 100 karya fiksi berbahasa Inggris yang
# bersumber dari teks Project Gutenberg. Repository menyediakan
# folder "original" berisi teks sumber.
#
# Jalankan dari folder B3:
#   powershell -ExecutionPolicy Bypass -File .\prepare_b3_litbank.ps1

$ErrorActionPreference = "Stop"

$B3Dir = $PSScriptRoot
$DatasetDir = Join-Path $B3Dir "dataset"
$ZipPath = Join-Path $B3Dir "litbank.zip"
$ExtractDir = Join-Path $B3Dir "litbank_extract"
$RepoUrl = "https://github.com/dbamman/litbank/archive/refs/heads/master.zip"

New-Item -ItemType Directory -Force -Path $DatasetDir | Out-Null

Write-Host ("=" * 70)
Write-Host "B3 - MENYIAPKAN DATASET LITBANK"
Write-Host ("=" * 70)
Write-Host ""

$current = @(Get-ChildItem $DatasetDir -Filter "*.txt" -File)

if ($current.Count -ge 30) {
    Write-Host "Dataset sudah memiliki $($current.Count) file .txt."
    Write-Host "Tidak perlu mengunduh ulang."
    exit 0
}

# Bersihkan ekstraksi sebelumnya jika ada.
if (Test-Path $ExtractDir) {
    Remove-Item $ExtractDir -Recurse -Force
}

if (-not (Test-Path $ZipPath)) {
    Write-Host "Mengunduh repository LitBank dari GitHub..."
    Invoke-WebRequest `
        -Uri $RepoUrl `
        -OutFile $ZipPath `
        -UseBasicParsing `
        -TimeoutSec 180 `
        -Headers @{"User-Agent"="Mozilla/5.0"}
}

if (-not (Test-Path $ZipPath)) {
    throw "File litbank.zip tidak berhasil dibuat."
}

Write-Host "Mengekstrak LitBank..."
Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir -Force

$originalDirs = @(Get-ChildItem $ExtractDir -Directory -Recurse |
    Where-Object { $_.Name -eq "original" })

if ($originalDirs.Count -eq 0) {
    throw "Folder original tidak ditemukan dalam repository LitBank."
}

$OriginalDir = $originalDirs[0].FullName

$sourceFiles = @(
    Get-ChildItem $OriginalDir -File -Recurse |
    Where-Object {
        $_.Extension -eq ".txt"
    } |
    Sort-Object Name
)

Write-Host "Folder sumber: $OriginalDir"
Write-Host "Teks tersedia: $($sourceFiles.Count)"
Write-Host ""

if ($sourceFiles.Count -lt 30) {
    throw "Dataset sumber kurang dari 30 file teks."
}

# Ambil 30 file pertama.
# Kami menggunakan file teks asli dari folder original,
# bukan membuat teks sintetis.
$selected = $sourceFiles | Select-Object -First 30

# Bersihkan .txt dataset lama agar hasil reproducible.
Get-ChildItem $DatasetDir -Filter "*.txt" -File -ErrorAction SilentlyContinue |
    Remove-Item -Force

$manifestRows = @()
$index = 0

foreach ($file in $selected) {
    $index++

    $destinationName = "{0:D2}_{1}" -f $index, $file.Name
    $destination = Join-Path $DatasetDir $destinationName

    Copy-Item -Path $file.FullName -Destination $destination -Force

    $size = (Get-Item $destination).Length

    Write-Host (
        "[{0:D2}/30] {1} -> {2:N0} bytes" -f
        $index, $file.Name, $size
    )

    $manifestRows += [PSCustomObject]@{
        Index = $index
        SourceFile = $file.Name
        DatasetFile = $destinationName
        Source = "LitBank / Project Gutenberg"
    }
}

$ManifestPath = Join-Path $B3Dir "dataset_manifest.csv"

$manifestRows |
    Export-Csv `
        -Path $ManifestPath `
        -NoTypeInformation `
        -Encoding UTF8

Write-Host ""
Write-Host ("=" * 70)
Write-Host "HASIL"
Write-Host ("=" * 70)

$finalFiles = @(Get-ChildItem $DatasetDir -Filter "*.txt" -File)

Write-Host "Jumlah file .txt : $($finalFiles.Count)"
Write-Host "Manifest         : $ManifestPath"

if ($finalFiles.Count -ge 30) {
    Write-Host ""
    Write-Host "DATASET B3 SUDAH SIAP."
} else {
    throw "Dataset belum mencapai 30 file."
}

Write-Host ("=" * 70)
