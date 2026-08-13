# Montrose MCP — koppla ditt konto till Claude

Montrose exponerar ditt konto som en **MCP-server** på `https://mcp.montrose.io/`.
När den är kopplad kan Claude läsa din portfölj — innehav, fördelning, exponering
mot branscher och nyheter som rör dina positioner.

> ⚠️ **Din kopplingslänk är en inloggning.** Den ska aldrig klistras in i en chatt,
> committas till git eller läggas i en fil som versionshanteras. Den hör hemma i
> `.env` (som är gitignorerad) eller i klientens egen inställning.

---

## Kopplingslänken

Du aktiverar MCP-kopplingen själv inne i Montrose-appen (sidan **Montrose MCP**,
ovanför avsnittet "Guider"). Först då finns länken.

- Accessen gäller **90 dagar** och kan sedan förnyas eller avslutas.
- Kopplingen är frivillig och kan stängas av dig när som helst.
- Claude ansluter från Anthropics moln, inte från din enhet.

Guiden i appen visar en URL utan personlig del (`https://mcp.montrose.io`), vilket
tyder på att inloggningen sker via OAuth efter att adressen lagts till. Börja med
den vanliga adressen; ber klienten om en personlig URL hämtar du den i appen.

## Vad kopplingen ger — och inte ger

| Ger | Ger inte |
| --- | --- |
| Läsa innehav och portföljfördelning | Handel utan ditt godkännande |
| Se exponering per bransch och region | Automatisk exekvering av strategier |
| Nyheter kopplade till dina innehav | Flytta pengar |
| **Förbereda köporder** för manuellt godkännande | Koppling till botens krypto-affärer |

Montrose MCP kan **initiera** köp: du ber om att köpa ett innehav för tillgänglig
kassa, agenten förbereder ordern och skickar tillbaka en länk till Montrose —
där du loggar in och godkänner själv. Sista steget är alltid manuellt. Det är
alltså inte en trading-bot eller automatiserad förvaltning.

Boten i det här repot (`main.py`, `tradebot/`) handlar krypto via ccxt och är en
helt separat sak — Montrose rör aktier och fonder i din depå.

---

## 1. Claude.ai — måste göras i webbläsare, inte i mobilappen

> 🚫 **Mobilappen kan inte lägga till custom connectors.** Knappen finns inte
> där. Lägg till den på claude.ai i en webbläsare (eller Claude Desktop) — sedan
> blir connectorn tillgänglig även på mobilen.

1. Öppna <https://claude.ai/settings/connectors> i en webbläsare, helst på dator.
2. Klicka **Add custom connector**.
3. Klistra in din personliga kopplingslänk från Montrose-appen.
4. Godkänn inloggningen i fönstret som öppnas.
5. Slå på connectorn i den chatt du vill använda den i (connector-kontrollen i
   chattfönstret).

Två begränsningar som kan blockera steg 2:

- **Free-plan** tillåter bara **en** custom connector totalt.
- **Team/Enterprise:** endast kontots **Owner** kan lägga till custom
  connectors; medlemmar kan sedan aktivera dem.

Claude ansluter till Montrose från Anthropics moln, inte från din enhet — så
servern måste vara nåbar från publikt internet (vilket `mcp.montrose.io` är).

## 2. Claude Code lokalt i terminalen

```bash
claude mcp add --transport http montrose-mcp https://mcp.montrose.io/
```

Starta sedan `claude` och kör `/mcp` för att autentisera. Efter det syns
Montrose-verktygen i sessionen.

Vill du ha kopplingen bunden till det här projektet i stället för globalt, finns
`.mcp.json` i repo-roten redan förberedd. Den läser URL:en från miljövariabeln
`MONTROSE_MCP_URL`, så den personliga länken hamnar aldrig i git:

```bash
# i .env (gitignorerad)
MONTROSE_MCP_URL=https://mcp.montrose.io/<din-personliga-del>
```

Claude Code frågar om godkännande första gången ett projekt-`.mcp.json` läses in.

## 3. Claude Code på webben (moln-sessioner)

Fungerar **inte** direkt, av två skäl:

1. **MCP-servrar laddas vid sessionsstart.** En pågående session kan inte koppla
   in en ny server mitt i — konfigurationen måste finnas innan sessionen startar.
2. **Nätverkspolicyn blockerar värden.** Moln-containern går ut via en
   agent-proxy som avvisar `mcp.montrose.io:443` med `403` (policy denial).

För att få det att fungera i moln-sessioner:

- Lägg till `mcp.montrose.io` i miljöns nätverkspolicy (den som valdes när
  environment skapades) — se
  <https://code.claude.com/docs/en/claude-code-on-the-web>.
- Sätt `MONTROSE_MCP_URL` som environment-variabel på miljön, så plockar
  `.mcp.json` upp den vid nästa sessionsstart.

Verifiera att policyn släpper igenom värden:

```bash
curl -sS "$HTTPS_PROXY/__agentproxy/status" | grep -A5 recentRelayFailures
```

---

## Rimlig förväntan

En "money making machine" byggs inte av kopplingen i sig. Vad kopplingen ger är
att analysen slipper handmatning: portföljen finns redan i kontexten när du
frågar, och en order kan förberedas åt dig. Men beslutet och godkännandet ligger
kvar hos dig — och som README:n säger, ingen bot kan garantera vinst.
