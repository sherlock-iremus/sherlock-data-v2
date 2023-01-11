# Notes

Un jour j'ai eu besoin de convertir des branlées de fichiers RTF en texte brut sous windows :

```powershell
$files = Get-ChildItem -Recurse 
foreach ($file in $files){
    $o=$file.FullName+".txt"
    pandoc $file.FullName -o $o
}
```