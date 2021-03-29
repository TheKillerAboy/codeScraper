param ($param1)

$directory = [System.IO.Path]::GetDirectoryName($param1)
$base_file = [System.IO.Path]::GetFileNameWithoutExtension($param1)
$in_files = Join-Path -Path $directory -ChildPath $base_file".in.*"
$exe_file = Join-Path -Path $directory -ChildPath $base_file".exe"
$temp_file = Join-Path -Path $directory -ChildPath ".temp.$base_file.out"

Write-Output "Building executable $base_file.exe"
g++ $param1 -o $exe_file

$exe_path = Convert-Path $exe_file

Get-ChildItem $in_files | ForEach-Object{
	Write-Output $_.Name
	Start-Process $exe_path -RedirectStandardInput $_  -RedirectStandardOutput $temp_file -Wait
	Write-Output (Get-Content $temp_file)
}