# MOTIV. — webbshop för kläder med eget motiv

En modern, komplett webbshop-demo där kunden designar sitt eget plagg:
väljer plagg, färg, storlek, motiv och tryckplacering — och ser resultatet
live innan beställning.

## Kom igång

Ingen byggprocess eller server krävs — allt är statisk HTML/CSS/JS:

```bash
# öppna direkt
open index.html

# eller servera lokalt
python3 -m http.server 8000
# → http://localhost:8000
```

## Flödet

1. **Startsida** — tre klickbara kategorier: T-shirt, Hoodie, Långärmad t-shirt.
2. **Produktsida** — stor produktbild med fram-/baksida, 12 färgminiatyrer
   (klick på miniatyr byter den stora bilden), storleksval XS–5XL samt antal.
3. **Motiv** — knapp som öppnar ett galleri med 25 motiv.
4. **Placering** — Hjärta 10 × 10 cm, Mage 22 × 22 cm eller Rygg 22 × 22 cm.
5. **Live-förhandsvisning** — plagget renderas i vald färg med valt motiv på
   vald plats (väljer man rygg vänds plagget automatiskt till baksidan).
6. **Varukorg → Kassa** — kunduppgifter och betalning i Klarna-stil
   (Betala nu / Betala om 30 dagar / Delbetala). Demobetalning — ingen
   riktig transaktion sker.

## Teknik

| Fil | Ansvar |
| --- | --- |
| `index.html` | Skal: header, footer, varukorgs-drawer, motiv-modal |
| `css/style.css` | Hela designsystemet, responsivt ned till mobil |
| `js/data.js` | Produkter, 12 färger, storlekar, 3 placeringar, 25 motiv (inline-SVG) |
| `js/mockups.js` | SVG-motor som ritar plaggen i valfri färg, fram/bak, med motiv |
| `js/app.js` | Hash-router, konfigurator, varukorg (localStorage), kassa |

Alla produktbilder är programmatiskt genererad SVG i stället för foton.
Det gör att varje kombination (3 plagg × 2 sidor × 12 färger × 25 motiv ×
3 placeringar = 5 400 varianter) renderas exakt, utan en enda bildfil.
Vill man ersätta mockupsen med riktiga produktfoton byts bara
`renderGarment()` ut mot `<img>`-element per färg/sida.

## Klarna på riktigt

Kassan är förberedd för Klarna Checkout: ersätt demo-logiken i
`renderCheckoutPage()` (`js/app.js`) med ett anrop till Klarnas
`orders`-API från en backend och montera deras checkout-snippet i
betalningskortet. Kräver Klarna-merchantkonto och serverdel för
API-nycklarna.
