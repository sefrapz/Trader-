# Montrose MCP — koppla ditt konto till Claude

Montrose exponerar ditt konto som en **MCP-server** på `https://mcp.montrose.io/`.
När den är kopplad kan Claude läsa din portfölj — innehav, fördelning, exponering
mot branscher och nyheter som rör dina positioner.

> ⚠️ **Din kopplingslänk är en inloggning.** Den ska aldrig klistras in i en chatt,
> committas till git eller läggas i en fil som versionshanteras. Den hör hemma i
> `.env` (som är gitignorerad) eller i klientens egen inställning.

---

## Vad kopplingen ger — och inte ger

| Ger | Ger inte |
| --- | --- |
| Läsa innehav och portföljfördelning | Lägga ordrar / handla |
| Se exponering per bransch och region | Flytta pengar |
| Nyheter kopplade till dina innehav | Automatisk exekvering av strategier |

Montrose MCP är i praktiken ett **läsande analyslager**. Boten i det här repot
(`main.py`, `tradebot/`) handlar krypto via ccxt och är helt separat. En
integration mellan dem är alltså *analys in* — inte *ordrar ut*.

---

## 1. Claude.ai (webb, desktop, mobil)

1. Öppna **Settings → Connectors → Add custom connector**.
2. Klistra in din personliga kopplingslänk från Montrose-appen.
3. Godkänn inloggningen i webbläsarfönstret som öppnas.
4. Slå på connectorn i den chatt du vill använda den i (kontrollen för
   connectors i chattfönstret).

Detta är vägen som gäller för vanliga Claude-chattar.

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
frågar. Beslut, riskgränser och exekvering ligger fortfarande hos dig och hos
botens konfiguration — och som README:n säger, ingen bot kan garantera vinst.
