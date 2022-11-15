#NoEnv  
#Warn  
SendMode Input  
SetWorkingDir %A_ScriptDir%

!1::
Run, kmk_scripts.py stage 1
return

!2::
Run, kmk_scripts.py stage 2
return

!9::
Run, kmk_scripts.py stage 9
return

!Down:: 
Run, kmk_scripts.py cashbox stop
return

!Up:: 
Run, kmk_scripts.py cashbox start
return

!p::
Run, kmk_scripts.py cashboxId paste
return

!i::
Run, kmk_scripts.py cashboxId copy
return

!d::
Run, kmk_scripts.py delete db
return

!c::
Run, kmk_scripts.py delete cashbox
return

!t::
Run, kmk_scripts.py gen token
return

!g::
Run, kmk_scripts.py gen guid
return

!-::
Run, kmk_scripts.py shift set24
return

!o::
Run, kmk_scripts.py flip_settings moveRemainsToNextShift
return

!e::
Run, kmk_scripts.py receipt regError
return



:*:adm1::https://market.testkontur.ru/AdminTools

:*:adm2::https://market-dev.testkontur.ru/AdminTools

:*:cashdoc::https://cashdoc.kontur/webdav/cashbox/

:*:csadm::https://market.testkontur.ru/cashboxApi/admin/web/cashbox/
