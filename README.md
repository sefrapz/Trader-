# Montrose MCP-koppling

Det här repot innehåller uppsättningen för att koppla en **Montrose-depå** till
Claude via MCP (`https://mcp.montrose.io/`). När kopplingen är aktiv kan Claude
läsa dina innehav, slå upp instrument, hantera bevakningslistor och förbereda
orderlappar som du själv godkänner i Montrose-appen.

**→ [docs/MONTROSE.md](docs/MONTROSE.md)** — hur du aktiverar kopplingen, var
kopplingslänken finns, vad den ger och vilka verktyg som blir tillgängliga.

## Snabbstart

1. Aktivera MCP-kopplingen i Montrose-appen (sidan **Montrose MCP**).
2. Öppna <https://claude.ai/settings/connectors> **i en webbläsare** — mobilappen
   kan inte lägga till custom connectors.
3. **Add custom connector**, klistra in kopplingslänken, godkänn inloggningen.
4. Slå på connectorn i den chatt du vill använda den i.

Kopplingen gäller i 90 dagar och kan avslutas av dig när som helst.

> ⚠️ **Kopplingslänken är en inloggning till din depå.** Klistra aldrig in den i
> en chatt och committa den aldrig.

## Vad kopplingen inte är

Montrose MCP är inte en trading-bot och inte automatiserad förvaltning. Ordrar
förbereds åt dig, men sista steget kräver alltid att du loggar in i Montrose och
godkänner själv.

---

*Repot innehöll tidigare en kryptohandelsbot. Den koden är borttagen — den finns
kvar i git-historiken och på grenen `claude/live-tradebot-profit-ep4hcr`.*
