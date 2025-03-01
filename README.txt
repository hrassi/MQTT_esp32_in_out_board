subscribed topics:
esp1/led25 = 0 or 1
esp1/led26 = 0 or 1
esp1/led27 = 0 or 1
esp1/refresh   =  0 or 1

publish: 
esp1/status    =  online   or   offline
esp1/button32  =  0 or 1
esp1/button34  =  0 or 1
esp1/button35  =  0 or 1
esp1/pot       =  the actual potentiometer value
esp1/time_now  = the actual time now

you can add many board by changing esp1/... to esp2/... esp3/...
you can also add more inputs outputs ...

this script handle wifi and internet and sever connections errors by
checking always the connectivity with a thread , and reconnect or reboot
in case of errors
