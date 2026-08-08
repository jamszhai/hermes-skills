# MSIX first-run registration failure — diagnostic recipe (ASCII only)

Run in a normal PowerShell. Do NOT rely on `WindowsPrincipal.IsInRole` for admin check.

## 1. Real admin membership (trust this, not IsInRole)
```
net localgroup administrators
```
Current user appears in the member list => true admin (even if IsInRole said False, that was UAC token filtering).

## 2. Is the package registered to current user?
```
Get-AppxPackage *ChatGPT*      # empty => not registered -> the root cause
Get-AppxPackage *OpenAI*       # old Codex/OpenAI leftovers?
```

## 3. Registry residue (HKCU staging)
```
Get-ChildItem 'HKCU:\Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppModel\Repository\Packages' |
  Where-Object { $_.Name -match 'ChatGPT|OpenAI' } | Select PSChildName
```
If only old `OpenAI.Codex_*` remains and no ChatGPT => store install rolled back after failed registration.

## 4. Start-menu shortcut
```
$sm=[Environment]::GetFolderPath('StartMenu')+'\Programs'
$smc=[Environment]::GetFolderPath('CommonStartMenu')+'\Programs'
Get-ChildItem $sm,$smc -Recurse -EA SilentlyContinue | Where-Object { $_.Name -match 'ChatGPT' }
```

## 5. UAC policy
```
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' |
  Select EnableLUA,ConsentPromptBehaviorAdmin,ConsentPromptBehaviorUser,PromptOnSecureDesktop
```
- `ConsentPromptBehaviorUser = 3` => standard users' elevation is auto-denied (no prompt). Relevant only if current user is NOT in administrators group.
- If current user IS admin but still stuck, the process was running under the filtered (non-elevated) token — needs an explicit elevated launch.

## 6. All enabled admin accounts (to know if self-elevation is even possible)
```
Get-LocalUser | Select Name,Enabled,@{N='IsAdmin';E={(Get-LocalGroupMember -Group 'Administrators' -EA 0).Name -contains $_.Name}}
```
If no enabled admin exists (only disabled `Administrator` + the user as standard), fullTrust MSIX cannot be installed by the user; needs built-in Administrator enable or IT push.
