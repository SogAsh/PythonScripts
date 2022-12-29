#NoEnv  
#Warn  
SendMode Input  
SetWorkingDir %A_ScriptDir%

!k::
Run, python kmk_scripts.py setKkt true
return


!1::
Run, python kmk_scripts.py stage 1
return

!2::
Run, python kmk_scripts.py stage 2
return

!9::
Run, python kmk_scripts.py stage 9
return

!Down:: 
Run, python kmk_scripts.py cashbox stop
return

!Up:: 
Run, python kmk_scripts.py cashbox start
return

!p::
Run, python kmk_scripts.py cashboxId paste
return

!i::
Run, python kmk_scripts.py cashboxId copy
return

!d::
Run, python kmk_scripts.py delete db
return

!c::
Run, python kmk_scripts.py delete cashbox
return

!t::
Run, python kmk_scripts.py gen token
return

!g::
Run, python kmk_scripts.py gen guid
return

!-::
Run, python kmk_scripts.py shift set24
return

!o::
Run, python kmk_scripts.py flip_settings moveRemainsToNextShift
return

!e::
Run, python kmk_scripts.py receipt regError
return



::adm1::https://market.testkontur.ru/AdminTools

::adm2::https://market-dev.testkontur.ru/AdminTools

::csadm1::https://market.testkontur.ru/cashboxApi/admin/web/cashbox/

::csadm2::https://market-dev.testkontur.ru/cashboxApi/admin/web/cashbox/

::csdoc::https://developer.kontur.ru/
