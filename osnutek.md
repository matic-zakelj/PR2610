# PR2610: Analiza dirk Formule 1
## Projektna naloga pri predmetu Podatkovno Rudarjenje
Člani skupine: Matic Žakelj, Mark Hafner, Nejc Gnilšek.

### Opis problema
Formula 1 na prvi pogled izgleda zelo nepredvidljiva. Zanima nas, kako različni faktorji vplivajo na rezultat posamezne dirke in uvrstitve v skupnem seštevku.

### Opis podatkov
Uporabljali bomo podatke iz knjižnice <a href="https://docs.fastf1.dev">FastF1</a>, ki ponuja strukturirane telemetrične podatke. 

Podatki iz FastF1 vključujejo numerične, kategorične, logične, časovne in prostorske podatke, ki so večinoma organizirani kot časovne serije telemetrije vozila v dirkah.

Uporabljali bomo predvsem:
- telemetrične podatke vozila (hitrost, DRS status, pritisk na zavoro,...),
- podatki o krogih (čas kroga, čas postanka,...),
- podatki o dogodkih (postanki, nesreče,...),
- podatki o pozicijah (pozicija, čas med vozniki,...)


### Cilji oz. vprašanja
- Kako vremenske razmere vplivajo na čase krogov in rezultate dirk? Ali so nekateri vozniki boljši v slabših vremenskih razmerah?  
- Kako zmogljivost avta vpliva na uvrstitev voznikov (ali se vidi, kateri proizvajalci so boljši).
- Kako uvrstitev na kvalifikacijah vpliva na končni rezultat dirke? Ali obstaja močna korelacija med štartnim položajem in končno uvrstitvijo?
- Ali je za boljsš rezultat  pomembnejša visoka hitrost na ravninah ali učinkovitost v ovinkih.
- Prikazati, kako obraba različnih trdot pnevmatik vpliva na čase krogov skozi dirko.
- Napoved zmagovalca dirke in svetovnega prvaka glede na pretekle dirke in kvalifikacije trenutne sezone.
