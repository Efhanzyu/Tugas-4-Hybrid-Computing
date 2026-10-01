# B3 - Download dataset teks nyata dari Project Gutenberg
# Tidak menggunakan Gutendex API, sehingga menghindari timeout metadata.
#
# Jalankan dari folder B3:
#   powershell -ExecutionPolicy Bypass -File .\download_b3_dataset.ps1
#
# Script mengambil 35 judul sebagai cadangan. Minimal 30 file diperlukan.
# File yang gagal akan dilewati dan dapat dicoba lagi dengan menjalankan
# script ini kembali.

$ErrorActionPreference = "Continue"

$DatasetDir = Join-Path $PSScriptRoot "dataset"
$ManifestPath = Join-Path $PSScriptRoot "dataset_manifest.csv"

New-Item -ItemType Directory -Force -Path $DatasetDir | Out-Null

$books = @(
    @{Id=11; Title="Alice's Adventures in Wonderland"},
    @{Id=12; Title="Through the Looking-Glass"},
    @{Id=16; Title="Peter Pan"},
    @{Id=35; Title="The Time Machine"},
    @{Id=36; Title="The War of the Worlds"},
    @{Id=42; Title="The Strange Case of Dr. Jekyll and Mr. Hyde"},
    @{Id=43; Title="A Christmas Carol"},
    @{Id=45; Title="Anne of Green Gables"},
    @{Id=74; Title="The Adventures of Tom Sawyer"},
    @{Id=84; Title="Frankenstein"},
    @{Id=98; Title="A Tale of Two Cities"},
    @{Id=118; Title="The Count of Monte Cristo"},
    @{Id=120; Title="Treasure Island"},
    @{Id=126; Title="Black Beauty"},
    @{Id=200; Title="Don Quixote"},
    @{Id=244; Title="A Study in Scarlet"},
    @{Id=408; Title="The Souls of Black Folk"},
    @{Id=514; Title="Little Women"},
    @{Id=520; Title="Metamorphosis"},
    @{Id=521; Title="The Life and Adventures of Robinson Crusoe"},
    @{Id=730; Title="Oliver Twist"},
    @{Id=766; Title="David Copperfield"},
    @{Id=768; Title="Wuthering Heights"},
    @{Id=844; Title="The Importance of Being Earnest"},
    @{Id=1184; Title="The Count of Monte Cristo"},
    @{Id=1342; Title="Pride and Prejudice"},
    @{Id=1400; Title="Great Expectations"},
    @{Id=1661; Title="The Adventures of Sherlock Holmes"},
    @{Id=1952; Title="The Yellow Wallpaper"},
    @{Id=1998; Title="Thus Spoke Zarathustra"},
    @{Id=2097; Title="The Wonderful Wizard of Oz"},
    @{Id=2554; Title="Crime and Punishment"},
    @{Id=2591; Title="Grimms' Fairy Tales"},
    @{Id=2600; Title="War and Peace"},
    @{Id=2701; Title="Moby Dick"}
)

# Cari URL plain text dari beberapa pola umum Project Gutenberg.
# Pola pertama biasanya yang paling cepat.
function Get-TextUrl($id) {
    return @(
        "https://www.gutenberg.org/cache/epub/$id/pg$id.txt",
        "https://www.gutenberg.org/files/$id/$id-8.txt",
        "https://www.gutenberg.org/files/$id/$id-0.txt",
        "https://www.gutenberg.org/files/$id/$id.txt"
    )
}

Write-Host ("=" * 70)
Write-Host "B3 - DOWNLOAD DATASET TEKS NYATA"
Write-Host ("=" * 70)
Write-Host "Target minimum: 30 file .txt"
Write-Host "Folder dataset : $DatasetDir"
Write-Host ""

$manifest = @()
$success = 0

for ($i = 0; $i -lt $books.Count; $i++) {

    $book = $books[$i]
    $number = $i + 1
    $id = $book.Id
    $title = $book.Title

    $safeTitle = $title -replace '[<>:"/\\|?*]', ''
    $filename = "{0:D2}_pg{1}_{2}.txt" -f $number, $id, $safeTitle
    $destination = Join-Path $DatasetDir $filename

    if (Test-Path $destination) {
        $size = (Get-Item $destination).Length
        if ($size -gt 1000) {
            Write-Host ("[{0:D2}/{1}] ADA: {2} ({3:N0} bytes)" -f $number, $books.Count, $title, $size)
            $success++
            $manifest += [PSCustomObject]@{
                Index=$number
                GutenbergID=$id
                Title=$title
                Filename=$filename
                SourceURL="https://www.gutenberg.org/ebooks/$id"
            }
            continue
        }
    }

    $downloaded = $false

    foreach ($url in (Get-TextUrl $id)) {
        try {
            Write-Host ("[{0:D2}/{1}] Download: {2}" -f $number, $books.Count, $title)
            Invoke-WebRequest `
                -Uri $url `
                -OutFile $destination `
                -UseBasicParsing `
                -TimeoutSec 120 `
                -Headers @{"User-Agent"="Mozilla/5.0"}

            if (Test-Path $destination) {
                $size = (Get-Item $destination).Length
                if ($size -gt 1000) {
                    Write-Host ("       OK - {0:N0} bytes" -f $size)
                    $downloaded = $true
                    break
                }
            }
        }
        catch {
            Write-Host ("       URL gagal, mencoba URL berikutnya...")
        }
    }

    if ($downloaded) {
        $success++
        $manifest += [PSCustomObject]@{
            Index=$number
            GutenbergID=$id
            Title=$title
            Filename=$filename
            SourceURL="https://www.gutenberg.org/ebooks/$id"
        }
        Start-Sleep -Seconds 2
    }
    else {
        if (Test-Path $destination) {
            Remove-Item $destination -Force -ErrorAction SilentlyContinue
        }
        Write-Host "       GAGAL - akan bisa dicoba lagi saat script dijalankan ulang."
    }
}

$manifest |
    Sort-Object Index |
    Export-Csv -Path $ManifestPath -NoTypeInformation -Encoding UTF8

$files = @(Get-ChildItem -Path $DatasetDir -Filter "*.txt" -File)

Write-Host ""
Write-Host ("=" * 70)
Write-Host "HASIL DATASET"
Write-Host ("=" * 70)
Write-Host ("Jumlah file .txt : {0}" -f $files.Count)
Write-Host ("Manifest         : {0}" -f $ManifestPath)
Write-Host ""

if ($files.Count -ge 30) {
    Write-Host "STATUS: DATASET SUDAH MEMENUHI SYARAT MINIMAL 30 FILE."
}
else {
    Write-Host "STATUS: MASIH KURANG DARI 30 FILE."
    Write-Host "Jalankan lagi script ini untuk mencoba file yang gagal."
}

Write-Host ("=" * 70)
