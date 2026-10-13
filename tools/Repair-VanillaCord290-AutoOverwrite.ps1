#requires -Version 5.1
[CmdletBinding()]param([switch]$SelfTest)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$repo='SupraCraft/VanillaCord';$private='SupraCraft/VanillaCord-private'
$tag='v2.9.0';$name='supracraft-vanillacord-2.9.0.jar'
$good='24e850a261dbf108e2f7ac412c34651ffae753543665ec47d5e40ff9c8981719'
$bad='c9904b481654da4a70c8ae48086466be9b95da84ee39808a165e8a30469b08e4'
$producer='3d81d535ef3664c19a909ca7428ef84a778834c4'
$anchor='ae95c0e64c4b867a60909b71bd2eb8d17051a5e5'
$goodSize=2457878;$badSize=2457579;$badAsset=637560073
$url='https://github.com/SupraCraft/VanillaCord/releases/download/v2.9.0/supracraft-vanillacord-2.9.0.jar'
$script:phase='preflight';$script:gh=$null
function Require([bool]$ok,[string]$why) {if(-not $ok){throw "VC290_REPAIR_BLOCKED [$script:phase]: $why"}}
function Gh([string[]]$Argv) {
 $previous=$ErrorActionPreference
 try{$ErrorActionPreference='Continue';$output=@(& $script:gh @Argv);$code=$LASTEXITCODE}
 finally{$ErrorActionPreference=$previous}
 Require ($code -eq 0) "GitHub CLI $($Argv[0]) failed, exit $code"
 return ([string]::Join([Environment]::NewLine,[string[]]$output)).Trim()
}
function GhJson([string]$endpoint) {return ConvertFrom-Json -InputObject (Gh -Argv @('api',$endpoint))}
function PublicJson([string]$endpoint) {
 return Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/$endpoint" -TimeoutSec 35 -UseBasicParsing -Headers @{'User-Agent'='SupraCraft-v290';'Accept'='application/vnd.github+json'}
}
function IsWrong($asset) {
 return ($null -ne $asset -and [long]$asset.id -eq $badAsset -and $asset.name -eq $name -and [long]$asset.size -eq $badSize -and $asset.digest -eq "sha256:$bad" -and $asset.state -eq 'uploaded' -and $asset.uploader.login -eq 'github-actions[bot]')
}
function IsOriginal($asset) {
 return ($null -ne $asset -and $asset.name -eq $name -and [long]$asset.size -eq $goodSize -and $asset.digest -eq "sha256:$good" -and $asset.state -eq 'uploaded')
}
function FileProof([string]$path,[string]$label) {
 Require (Test-Path -LiteralPath $path -PathType Leaf) "$label file missing"
 Require ((Get-Item -LiteralPath $path).Length -eq $goodSize) "$label file length differs from canonical original"
 Require ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -eq $good) "$label hash differs from canonical original"
 Write-Host "VC290_$($label)_PASS size=$goodSize SHA256=$good"
}
function Policy {
 $head=[string](PublicJson 'git/ref/heads/main').object.sha
 Require ($head -match '^[a-f0-9]{40}$' -and $head -ne $anchor) 'Public release workflow fix has not landed on main'
 $file="https://raw.githubusercontent.com/$repo/$head/.github/workflows/build.yml"
 $yaml=[string](Invoke-WebRequest -Uri $file -UseBasicParsing -TimeoutSec 35).Content
 $triggers=($yaml -split '(?m)^concurrency:')[0]
 Require (-not ($triggers -match '(?m)^  release:\s*$')) 'Unsafe release-published trigger still present'
 Require ($yaml.Contains("if: github.event_name == 'workflow_dispatch'")) 'Release job not explicit-dispatch-only'
 Require ($yaml.Contains('Refuse an existing public release')) 'Existing-release guard absent'
 $tagObj=PublicJson "git/ref/tags/$tag"
 Require ($tagObj.object.type -eq 'commit' -and $tagObj.object.sha -eq $anchor) 'Public distribution tag no longer points to approved source projection'
 Write-Host "VC290_WORKFLOW_POLICY_PASS main=$head"
}
function Assets {
 $release=PublicJson "releases/tags/$tag"
 Require ($release.draft -eq $false) 'Public release is draft'
 return @($release.assets|Where-Object{$_.name -eq $name})
}
function AnonymousProof([string]$output) {
 Invoke-WebRequest -Uri $url -UseBasicParsing -OutFile $output -MaximumRedirection 10 -TimeoutSec 180
 FileProof $output 'ANONYMOUS_PUBLIC'
}
function TestRules {
 Require ($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -eq 1) 'Test must run with native Windows PowerShell 5.1'
 $wrong=[pscustomobject]@{id=$badAsset;name=$name;size=$badSize;digest="sha256:$bad";state='uploaded';uploader=[pscustomobject]@{login='github-actions[bot]'}}
 Require (IsWrong $wrong) 'Known auto-generated wrong asset not recognized'
 $wrong.digest='sha256:not-the-original';Require (-not (IsWrong $wrong)) 'Wrong SHA was accepted'
 $wrong.digest="sha256:$bad";$wrong.id=4;Require (-not (IsWrong $wrong)) 'Foreign asset ID was accepted'
 $wrong.id=$badAsset;$wrong.uploader.login='unknown';Require (-not (IsWrong $wrong)) 'Foreign uploader was accepted'
 $original=[pscustomobject]@{name=$name;size=$goodSize;digest="sha256:$good";state='uploaded'}
 Require (IsOriginal $original) 'Canonical original asset fixture rejected'
 $original.size=$badSize;Require (-not (IsOriginal $original)) 'Incorrect original size admitted'
 Write-Host 'VC290_PS51_REPAIR_SELFTEST_PASS: exact-known-wrong/good and four negative guards'
}
TestRules
if($SelfTest){return}
$tmp=Join-Path ([IO.Path]::GetTempPath()) ('vc290fix-'+[guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $tmp
try{
 $script:phase='policy';Policy
 $script:phase='public-inventory';$items=@(Assets)
 Require ($items.Count -eq 1) 'Expected exactly one versioned public JAR asset'
 if(IsOriginal $items[0]){
  $script:phase='public-noop-proof';AnonymousProof (Join-Path $tmp 'public.jar')
  Write-Host 'VC290_REPAIR_COMPLETE_NOOP: original asset already correctly public'
  return
 }
 Require (IsWrong $items[0]) 'Public asset differs from precisely identified automated overwrite; stop'
 $script:phase='private-original-retrieval'
 $command=Get-Command gh.exe -ErrorAction SilentlyContinue
 Require ($null -ne $command) 'GitHub CLI unavailable; use existing authenticated GitHub CLI'
 $script:gh=$command.Source
 $previous=$ErrorActionPreference
 try{$ErrorActionPreference='Continue';$null=& $script:gh auth status --hostname github.com 2>&1;$authCode=$LASTEXITCODE}
 finally{$ErrorActionPreference=$previous}
 Require ($authCode -eq 0) 'Existing GitHub CLI login unavailable'
 $sourceRelease=GhJson "repos/$private/releases/tags/$tag"
 $sourceTag=GhJson "repos/$private/git/ref/tags/$tag"
 Require ([long]$sourceRelease.id -eq 379240422 -and $sourceRelease.target_commitish -eq $producer -and $sourceTag.object.sha -eq $producer) 'Original private release or Git tag drift'
 $assets=@($sourceRelease.assets|Where-Object{[long]$_.id -eq 536430211 -and (IsOriginal $_)})
 Require ($assets.Count -eq 1) 'Original private JAR identity/size/digest drift'
 $jarPath=Join-Path $tmp $name
 $null=Gh -Argv @('release','download',$tag,'--repo',$private,'--pattern',$name,'--dir',$tmp)
 FileProof $jarPath 'ORIGINAL_PRIVATE'
 $script:phase='recheck-before-mutation';Policy
 $current=@(Assets)
 Require ($current.Count -eq 1 -and (IsWrong $current[0])) 'Public JAR changed before controlled repair'
 $script:phase='remove-exact-known-bad-asset'
 $null=Gh -Argv @('api','-X','DELETE',"repos/$repo/releases/assets/$badAsset")
 Write-Host "VC290_KNOWN_BAD_ASSET_DELETED id=$badAsset"
 $script:phase='upload-original-with-no-overwrite'
 $null=Gh -Argv @('release','upload',$tag,$jarPath,'--repo',$repo)
 Write-Host 'VC290_ORIGINAL_REUPLOADED: no release republished and no --clobber used'
 $script:phase='independent-public-readback'
 $visible=$false
 for($i=0;$i -lt 12;$i++){
  Start-Sleep -Seconds 2
  $candidate=@(Assets)
  if($candidate.Count -eq 1 -and (IsOriginal $candidate[0])){$visible=$true;break}
 }
 Require $visible 'New original SHA has not propagated to public GitHub release API'
 AnonymousProof (Join-Path $tmp 'public.jar')
 Write-Host "VC290_REPAIR_PASS $url"
}catch{
 Write-Host "VC290_REPAIR_STOP: $($_.Exception.Message)" -ForegroundColor Red
 throw
}finally{if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue}}
