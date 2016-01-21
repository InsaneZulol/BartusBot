# BartusBot
@BartusBot to bot stworzony na potrzeby tajnej grupy na Telegramie. Podstawowymi założeniami były dwie funkcjonalności:
- obsługa planu lekcji (sprawdzanie następnej lekcji itp.)
- powiadomienia o newsach z Facebooka (z grupy pubu i z grupy klasowej)

## Używane biblioteki
Oprócz bibliotek używanych przez [telebot](https://github.com/yukuku/telebot) (repozytorium startowe) używamy takich bibliotek jak:
- [beautifulsoup4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/) - do parsowania stron www (wykorzystywane w parsowaniu planu)
- [facebook-sdk](https://github.com/pythonforfacebook/facebook-sdk) - do komunikacji z facebookiem

## Planowane funkcjonalności
Wszystkie planowane funcjonalności do wprowadzenia można sprawdzić [tutaj](https://github.com/r3tard/BartusBot/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement)

## Jak korzystać z @BartusBot?
Wystarczy dodać do kontaktów lub do grupy bota po nazwie @BartusBot

### Komendy

Komenda | Opis
:------ | :------------------------------
`/help` | Wyświetla pomoc
`/pon`  | Wyświetla plan dla poniedziałku
`/wt`   | Wyświetla plan dla wtorku
`/sr`   | Wyświetla plan dla środy
`/cz`   | Wyświetla plan dla czwartku
`/pt`   | Wyświetla plan dla piątku
`/j`    | Wyświetla plan na jutro
`/n`    | Wyświetla następną lekcje
`/d`    | Wyświetla plan na dzisiaj
`/remind data "wiadomosc"` | Przypomnienie wiadomosc o danej dacie w formie 1d, 1m, tomorrow, eod etc.
`/stats` | Wyświetla statystyki czatu (użytkownik, ilość wiadomości, procent udziału wiadomości)