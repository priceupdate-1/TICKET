param(
  [int]$Port = 4173,
  [string]$Root = $PSScriptRoot
)

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")

try {
  $listener.Start()
  Write-Host "Serving $Root at http://localhost:$Port/"

  while ($listener.IsListening) {
    $context = $listener.GetContext()
    $requestPath = $context.Request.Url.AbsolutePath.TrimStart("/")
    if ([string]::IsNullOrWhiteSpace($requestPath)) {
      $requestPath = "index.html"
    }

    $safePath = $requestPath.Replace("/", "\")
    $filePath = Join-Path $Root $safePath

    if ((Test-Path $filePath) -and -not (Get-Item $filePath).PSIsContainer) {
      $extension = [System.IO.Path]::GetExtension($filePath).ToLowerInvariant()
      $contentType = switch ($extension) {
        ".html" { "text/html; charset=utf-8" }
        ".js" { "text/javascript; charset=utf-8" }
        ".css" { "text/css; charset=utf-8" }
        ".json" { "application/json; charset=utf-8" }
        ".svg" { "image/svg+xml" }
        ".png" { "image/png" }
        ".jpg" { "image/jpeg" }
        ".jpeg" { "image/jpeg" }
        default { "application/octet-stream" }
      }

      $bytes = [System.IO.File]::ReadAllBytes($filePath)
      $context.Response.ContentType = $contentType
      $context.Response.ContentLength64 = $bytes.Length
      $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
      $notFound = [System.Text.Encoding]::UTF8.GetBytes("404 - File not found")
      $context.Response.StatusCode = 404
      $context.Response.ContentType = "text/plain; charset=utf-8"
      $context.Response.ContentLength64 = $notFound.Length
      $context.Response.OutputStream.Write($notFound, 0, $notFound.Length)
    }

    $context.Response.OutputStream.Close()
  }
} finally {
  if ($listener.IsListening) {
    $listener.Stop()
  }

  $listener.Close()
}
