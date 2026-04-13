# Vmesno poročilo – analiza podatkov Formule 1

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

Podatki so pridobljeni s knjižnico `fastf1`, ki omogoča dostop do uradnih F1 podatkov (časi krogov, telemetrija, vreme, rezultati).

Uporabljeni atributi:

- LapTime, TyreLife
- Driver, Team
- GridPosition, Position
- Compound
- Race, Season
- (v nadaljevanju: Weather, Speed, Telemetry)

---

## Izvedene analize

### 1. Degradacija pnevmatik

Analizirali smo, kako se čas kroga spreminja z obrabo pnevmatik.

Metoda:

- linearna regresija (TyreLife / LapTime)
- izračun naklona (s / krog)

Rezultati (za sezono 2022):

*Povprečna degradacija po spojini (s/krog)*
| Compound| mean    | std    | min     | max    |
|---------|---------|--------|---------|--------|
| HARD    | -0.0075 | 0.0776 | -0.2465 | 0.1174 |
| MEDIUM  | -0.0207 | 0.0933 | -0.3252 | 0.1502 |
| SOFT    | -0.0599 | 0.2900 | -1.0793 | 0.1090 |

*Najhitrejša in najpočasnejša degradacija po dirki*

| Dirka | Najslabša trdota | Povprečna sprememba čas/krog (s) | Najboljša trdota | Povprečna sprememba čas/krog (s) |
|------|------------------|----------------------|------------------|----------------------|
| Abu Dhabi Grand Prix | MEDIUM | 0.053503 | HARD | 0.006180 |
| Australian Grand Prix | MEDIUM | -0.025264 | HARD | -0.063563 |
| Austrian Grand Prix | HARD | 0.034611 | MEDIUM | 0.010151 |
| Azerbaijan Grand Prix | SOFT | 0.017218 | HARD | -0.009203 |
| Bahrain Grand Prix | MEDIUM | 0.150201 | SOFT | 0.005580 |
| Belgian Grand Prix | MEDIUM | 0.115988 | HARD | 0.055530 |
| British Grand Prix | SOFT | 0.054110 | MEDIUM | -0.061115 |
| Canadian Grand Prix | HARD | 0.011349 | MEDIUM | -0.079614 |
| Dutch Grand Prix | HARD | 0.019772 | SOFT | -0.049428 |
| Emilia Romagna Grand Prix | SOFT | 0.099488 | HARD | -0.052612 |
| French Grand Prix | MEDIUM | -0.019864 | HARD | -0.038717 |
| Hungarian Grand Prix | SOFT | 0.090725 | HARD | -0.011971 |
| Italian Grand Prix | SOFT | 0.016242 | MEDIUM | -0.016718 |
| Mexico City Grand Prix | SOFT | 0.009331 | MEDIUM | -0.011335 |
| Miami Grand Prix | HARD | -0.031154 | SOFT | -0.148457 |
| Monaco Grand Prix | MEDIUM | -0.094657 | SOFT | -1.079286 |
| Saudi Arabian Grand Prix | MEDIUM | -0.055379 | HARD | -0.077834 |
| Singapore Grand Prix | SOFT | -0.065369 | MEDIUM | -0.325209 |
| Spanish Grand Prix | HARD | 0.116106 | SOFT | 0.029786 |
| São Paulo Grand Prix | HARD | 0.117370 | SOFT | -0.030997 |
| United States Grand Prix | HARD | -0.004544 | MEDIUM | -0.032145 |

- soft pnevmatike imajo največjo degradacijo
- hard pnevmatike so najbolj stabilne
- razlike med dirkami so velike, na nekaterih progah so nekatere trdote boljše kot na drugih

Vizualizacije:

- scatter + regresijske premice
- heatmap (dirka / spojina)
- primerjava med vozniki

---

### 2. Vpliv vremena

Analiza še ni dokončana.

Načrt:
- povezava med:
    - temperaturo steze
    - dežjem (wet/intermediate)
    - časi krogov

---

### 3. Vpliv zmogljivosti ekip

Analiza še ni dokončana.

Načrt analize:
- primerjava ekip glede na:
    - povprečno uvrstitev
    - povprečen čas kroga
    - povprečna pozicija po dirkah
    - variance med vozniki iste ekipe

Cilj:
- ugotoviti, katere ekipe (proizvajalci) so najbolj konkurenčne

---

### 4. Kvalifikacije vs. dirka

Analiza še ni dokončana.

Cilj:
- preveriti korelacijo med:
    - štartnim položajem
    - končno uvrstitvijo

Načrt:
- Scatter plot
- Pearsonova korelacija

Pričakovanje:
- pozitivna korelacija

---

### 5. Ravnine vs. ovinki

Analiza še ni dokončana.

Načrt:
- uporaba telemetrije:
    - hitrost na ravninah
    - čas v ovinkih

Cilj:
- ugotoviti, ali je pomembnejša maksimalna hitrost ali hitrost v ovinkih

---

### 6. Napovedovanje rezultatov

Cilj:
- napoved zmagovalca dirke
- napoved svetovnega prvaka

Načrt:
- uporaba:
    - kvalifikacij
    - rezultatov dirk
    - trendov uspešnosti

---

## Glavne ugotovitve (trenutne)

- na različnih progah so različne trdote gum boljše
- čas na krog se v večini primerov izboljšuje z obrabo
- na nekaterih prizoriščih niso uporabljali vseh trdot

---

## Uporabljena koda

- nalaganje podatkov:
```python
fastf1.get_session(...)
```

- filtriranje:
```python
laps.pick_accurate()
```

- regresija:
```python
stats.linregress(x, y)
```

- vizualizacija:
```python
plt.scatter(...)
plt.plot(...)
sns.heatmap(...)
```

---

## Zaključek in nadaljnje delo

Projekt je trenutno v fazi, kjer je ena analiza že implementirana in daje smiselne rezultate.

Naslednji koraki vključujejo:

- vključitev vremenskih podatkov
- analizo kvalifikacij
- modeliranje napovedi rezultatov

Končni cilj je celovito razumeti dejavnike, ki vplivajo na uspeh v Formuli 1.
