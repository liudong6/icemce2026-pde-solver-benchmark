$ErrorActionPreference = 'Stop'
$manuscriptRoot = Split-Path -Parent $PSScriptRoot
$manuscriptPath = Join-Path $manuscriptRoot 'paper/icemce2026_iop_manuscript.docx'
$manuscriptPdfPath = Join-Path $manuscriptRoot 'paper/icemce2026_iop_manuscript.pdf'
$manuscriptApp = New-Object -ComObject Word.Application
$manuscriptDocument = $null
try {
    $manuscriptApp.Visible = $false
    $manuscriptApp.DisplayAlerts = 0
    $manuscriptDocument = $manuscriptApp.Documents.Open($manuscriptPath, $false, $true)
    $manuscriptDocument.ExportAsFixedFormat($manuscriptPdfPath, 17)
} finally {
    if ($null -ne $manuscriptDocument) { $manuscriptDocument.Close(0) }
    try { $manuscriptApp.Quit() }
    catch [System.Runtime.InteropServices.COMException] {
        # WPS can terminate its automation server when the last document closes.
        if ($_.Exception.HResult -ne -2147023170) { throw }
    }
}
Get-Item -LiteralPath $manuscriptPdfPath | Select-Object FullName, Length
