#NoEnv  
#Warn  
SendMode Input  
SetWorkingDir %A_ScriptDir%

!1::
Run, main.py stage 1
MsgBox, "Касса готова к работе с первым стейджем"
return

!2::
Run, main.py stage 2
MsgBox, "Касса готова к работе со вторым стейджем"
return

!9::
Run, main.py stage 9
MsgBox, "Касса смотрит на продовый Маркет"
return

!Down:: 
Run, main.py cashbox stop
MsgBox, "Служба SKBKontur.Cashbox остановлена"
return

!Up:: 
Run, main.py cashbox start
MsgBox, "Служба SKBKontur.Cashbox запущена"
return

!p::
Run, main.py cashboxId paste
MsgBox, "Вы вставили cashboxId из буфера в data.json"
return

!i::
Run, main.py cashboxId copy
MsgBox, "В вашем буфере обмена — текущий cashboxId"
return

!d::
Run, main.py delete db
MsgBox, "Вы удалили БД кассы"
return

!c::
Run, main.py delete cashbox
MsgBox, "Вы удалили кассу"
return

!t::
Run, main.py token 5
MsgBox, "Новый токен - в вашем буфере обмена"
return

!-::
Run, main.py shift set24
MsgBox, "Теперь текущая смена больше 24 часов"
return

!o::
Run, main.py settings remains
MsgBox, "Вы изменили настройку переноса остатков"
return


!,::
Run, main.py receipt regError
MsgBox, "Последний чек продажи стал незареганным"
return



:*:adm1::https://market.testkontur.ru/AdminTools

:*:adm2::https://market-dev.testkontur.ru/AdminTools

:*:cashdoc::https://cashdoc.kontur/webdav/cashbox/

:*:csadm::https://market.testkontur.ru/cashboxApi/admin/web/cashbox/
