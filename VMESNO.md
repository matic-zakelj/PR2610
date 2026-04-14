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

Rezultati (za sezono 2025):

**Povprečna degradacija po spojini (s/krog)**

| Compound |  mean  |  std   |   min   |   max   |
|----------|--------|--------|---------|---------|
| HARD     | 0.0196 | 0.5444 | -1.4602 | 2.0937  |
| MEDIUM   | 0.0035 | 0.1555 | -0.3995 | 0.6032  |
| SOFT     | -0.0691| 0.1504 | -0.5280 | 0.0678  |

**Najhitrejša in najpočasnejša degradacija po dirki**

| Dirka                        | Najslabša trdota | Najslabša degredacija | Najboljša trdota | Najboljša degredacija |
|------------------------------|------------------|-----------------------|------------------|-----------------------|
| Abu Dhabi Grand Prix         | MEDIUM           | -0.004250             | SOFT             | -0.167251             |
| Australian Grand Prix        | HARD             | 2.093713              | MEDIUM           | 0.603167              |
| Austrian Grand Prix          | MEDIUM           | 0.044309              | SOFT             | -0.022610             |
| Azerbaijan Grand Prix        | MEDIUM           | 0.010169              | HARD             | -0.028282             |
| Bahrain Grand Prix           | HARD             | 0.017109              | SOFT             | -0.025706             |
| Belgian Grand Prix           | HARD             | -0.061889             | MEDIUM           | -0.069547             |
| British Grand Prix           | MEDIUM           | -0.399450             | HARD             | -1.460246             |
| Canadian Grand Prix          | MEDIUM           | 0.110571              | HARD             | 0.011326              |
| Chinese Grand Prix           | HARD             | -0.037571             | MEDIUM           | -0.055228             |
| Dutch Grand Prix             | HARD             | 0.019441              | SOFT             | -0.027893             |
| Emilia Romagna Grand Prix    | HARD             | 0.005351              | MEDIUM           | -0.023440             |
| Hungarian Grand Prix         | HARD             | 0.011983              | SOFT             | -0.024789             |
| Italian Grand Prix           | HARD             | -0.011160             | SOFT             | -0.229198             |
| Japanese Grand Prix          | MEDIUM           | -0.011676             | SOFT             | -0.108805             |
| Las Vegas Grand Prix         | HARD             | -0.028902             | MEDIUM           | -0.035904             |
| Mexico City Grand Prix       | SOFT             | 0.018253              | HARD             | -0.010693             |
| Miami Grand Prix             | MEDIUM           | -0.000255             | HARD             | -0.021960             |
| Monaco Grand Prix            | SOFT             | 0.015627              | MEDIUM           | -0.013877             |
| Qatar Grand Prix             | HARD             | -0.039624             | SOFT             | -0.073416             |
| Saudi Arabian Grand Prix     | MEDIUM           | 0.019864              | HARD             | -0.001380             |
| Singapore Grand Prix         | SOFT             | 0.030043              | MEDIUM           | -0.009871             |
| Spanish Grand Prix           | SOFT             | 0.052697              | MEDIUM           | 0.018005              |
| São Paulo Grand Prix         | SOFT             | 0.067758              | HARD             | 0.011744              |
| United States Grand Prix     | SOFT             | -0.012766             | HARD             | -0.024987             |

- soft pnevmatike imajo največjo degradacijo
- hard pnevmatike so najbolj stabilne
- razlike med dirkami so velike, na nekaterih progah so nekatere trdote boljše kot na drugih

Vizualizacije:

- scatter + regresijske premice
- heatmap (dirka / spojina)
- primerjava med vozniki

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

Rezultat (za sezono 2025):
Analiza časov krogov pokaže, da je bila najuspešnejša ekipa McLaren, ki je dosegala najnižje mediane relativnih časov krogov. Najbližji konkurenti sto bili Ferrari, Mercedes in Red Bull Racing, ki sto zaostajali za približno 0.45%, 0.57% oziroma za 0.67%, kljub temu pa je bil končni rezultat drugačen.

Ostale ekipe so imele opazno slabšo zmogljivost, saj njihov zaostanek presega 1.3%, kar kaže na jasno ločnico med vodilnimi štirimi ekipami in preostankom startne vrste.

---

### 4. Kvalifikacije vs. dirka


---

### 5. Ravnine vs. ovinki


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
- odstopanja od najhitrejšega kroga dirke oziroma najhitrejše ekipe še ne pomeni, da bo taka tudi končna razvrstitev

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
plt.bar(...)
plt.hist(...)
plt.boxplot(...)
sns.heatmap(...)
```

---

## Zaključek in nadaljnje delo
