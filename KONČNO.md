# Končno poročilo – Analiza podatkov Formule 1

## Opis problema

Cilj projekta je analizirati različne dejavnike, ki vplivajo na uspešnost v Formuli 1. Osredotočamo se na več ključnih vprašanj:

- Kako vremenske razmere vplivajo na čase krogov in rezultate dirk? Ali so nekateri vozniki boljši v slabših vremenskih razmerah?  
- Kako zmogljivost avta vpliva na uvrstitev voznikov (ali se vidi, kateri proizvajalci so boljši).
- Kako uvrstitev na kvalifikacijah vpliva na končni rezultat dirke? Ali obstaja močna korelacija med štartnim položajem in končno uvrstitvijo?
- Ali je za boljši rezultat pomembnejša visoka hitrost na ravninah ali učinkovitost v ovinkih.
- Prikazati, kako obraba različnih trdot pnevmatik vpliva na čase krogov skozi dirko.
- Napoved zmagovalca dirke in svetovnega prvaka glede na pretekle dirke in kvalifikacije trenutne sezone.

---

## Podatki

Podatki so pridobljeni s knjižnico `fastf1`, ki omogoča dostop do uradnih F1 podatkov (časi krogov, telemetrija, vreme, rezultati). Večinoma smo uporabljali le natančne kroge (brez postankov, varnostnih avtomobilov...).

Uporabljeni atributi:

- LapTime, TyreLife
- Driver, Team
- GridPosition, Position
- Compound
- Race, Season
- Weather, Speed, Telemetry

---

## Izvedene analize

### 1. Degradacija pnevmatik

Analizirali smo, kako se čas kroga spreminja z obrabo pnevmatik.

Metoda:
- linearna regresija (TyreLife / LapTime)
- izračun naklona (s / krog)

Rezultati (za sezono 2026):

<img src="slike/degradacija_Miami.png" alt="Degradacija gum">

**Najhitrejša in najpočasnejša degradacija po dirki**

| Dirka                 | Mediana časa (s) | Najboljša trdota | Najpočasnejša degradacija | Najslabša trdota | Najhitrejša degradacija |
| --------------------- | ---------------: | ---------------- | ------------------------: | ---------------- | ----------------------: |
| Australian Grand Prix |           84.862 | MEDIUM           |                   -0.1322 | HARD             |                 -0.0143 |
| Canadian Grand Prix   |           77.062 | SOFT             |                   -0.1028 | HARD             |                 -0.0376 |
| Chinese Grand Prix    |           98.121 | HARD             |                   -0.0543 | SOFT             |                  0.2561 |
| Japanese Grand Prix   |           95.263 | HARD             |                   -0.0359 | MEDIUM           |                  0.0071 |
| Miami Grand Prix      |           94.298 | SOFT             |                   -0.0111 | MEDIUM           |                  0.0190 |


- Hitrost degradacije gum je odvisna od proge in vremena, zato imajo nekatere gume manjšo degradacijo na eni progi in večjo na drugi, zato ni najboljše trdote.
- V sezoni 2026 je na dirki Miamiju so imele SOFT gume najboljšo degradacijo (Vsak krog je bil hitrejši), ampak HARD gume so bile povprečno 1.5 sekunde hitrejše na krog, in kljub slabši degradaciji v kombinaciji z daljšo uporabo na koncu najboljša izbira.

---

### 2. Vpliv vremena


---

### 3. Vpliv zmogljivosti ekip

Načrt analize:
- primerjava ekip glede na:
    - povprečno odstopanje ekip od najhitrejšega kroga na dirki v sezoni (Graf 1)
    - odstopanje ekip od najhitrejšega kroga na dirki (Graf 2)
    - odstopanje ekip od najhitrejše ekipe na dirki (Graf 3)
    - odstopanje ekip od najhitrejše ekipe v sezoni (Graf 4)

Cilj:
- ugotoviti, katere ekipe (proizvajalci) so najbolj konkurenčne

Rezultat (za sezono 2026):

<img src="slike/mercedes_vs_ferrari.png" alt="Mercedes vs. Ferrari">

Iz radarskega grafa se vidi, da je ekipa Mercedes boljša kot ekipa Ferrari v hitrosti in imajo posledično tudi več najhitrejših krogov, hkrati pa je ekipa Ferrari bolj konsistentna in ima več podatkov, zaradi odstopa Georgea Russlla na zadnji dirki v Kanadi.

---

### 4. Kvalifikacije vs. dirka

---

### 5. Ravnine vs. ovinki

---

### 6. Napovedovanje rezultatov