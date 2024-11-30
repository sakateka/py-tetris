# Прототип в терминале

```
$ python3 ./main.py
@@@@@@@@@@@@@@@@@@@@
@@                @@
@@                @@
@@                @@
@@                @@
@@                @@
@@                @@
@@                @@
@@                @@
@@                @@
@@      ######    @@
@@      ##        @@
@@                @@
@@    ##          @@
@@######        ##@@
@@########    ####@@
@@##########  ####@@
@@##############  @@
@@##########  ####@@
@@@@@@@@@@@@@@@@@@@@
```

# Полученное устройство

## Части для сборки
Все ссылки ведут на примеры товаров и не являются строгой рекомендацией по выбору.
Возьмите на себя ответственность за выбор аналогов товара хорошего качества и надёжных продавцов.

- Neopixel экран https://sl.aliexpress.ru/p?key=CVjyrVA
- Microbit https://sl.aliexpress.ru/p?key=Rqjyr9s
- MicroBit плата расширения https://sl.aliexpress.ru/p?key=d7jyrJh
- Dual-axis XY Joystick https://sl.aliexpress.ru/p?key=zuxCrHR
- Рулон прозрачной тканевой ленты https://sl.aliexpress.ru/p?key=3ctCrPn
- Связка проводов F-F https://sl.aliexpress.ru/p?key=x7tCrLn
- Источник питания, что-то вроде этого или любой на 5v https://sl.aliexpress.ru/p?key=8PjyrVd

## Прошивка устройства
Используй эту Web IDE https://python.microbit.org/v/3

## Фото результата

<img src="https://github.com/user-attachments/assets/fb7825d7-918c-4ba2-9a8f-b0c3114cc4f3" height="600">

## Вариант на основе rp2040bit

rp2040bit: https://sl.aliexpress.ru/p?key=KT7kr8k

Эта плата совместима с платами расширения для microbit, но нужно понять какие пины
куда выведены, я сделал это экспериментальным путём.
rp2040bit можно прошить через mpremote
https://github.com/micropython/micropython/tree/master/tools/mpremote

```
mpremote cp rp2040bit-main.py :main.py
```
