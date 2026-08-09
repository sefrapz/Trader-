/* =========================================================
   MOTIV. — produktdata, färger, storlekar, placeringar, motiv
   ========================================================= */

const SIZES = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL'];

const COLORS = [
  { id: 'vit',      name: 'Vit',         hex: '#f2f0ea' },
  { id: 'svart',    name: 'Svart',       hex: '#232327' },
  { id: 'marin',    name: 'Marinblå',    hex: '#28345c' },
  { id: 'gra',      name: 'Gråmelerad',  hex: '#aaaaaf' },
  { id: 'sand',     name: 'Sand',        hex: '#d9cba6' },
  { id: 'oliv',     name: 'Oliv',        hex: '#77755b' },
  { id: 'rod',      name: 'Röd',         hex: '#b42430' },
  { id: 'bordeaux', name: 'Bordeaux',    hex: '#722336' },
  { id: 'gron',     name: 'Grön',        hex: '#237a42' },
  { id: 'ljusbla',  name: 'Ljusblå',     hex: '#93bbdd' },
  { id: 'gul',      name: 'Gul',         hex: '#e9b62f' },
  { id: 'rosa',     name: 'Rosa',        hex: '#e9a6b8' },
];

const PLACEMENTS = [
  { id: 'hjarta', name: 'Hjärta', size: '10 × 10 cm', side: 'front',
    desc: 'Diskret tryck på vänster bröst.' },
  { id: 'mage',   name: 'Mage',   size: '22 × 22 cm', side: 'front',
    desc: 'Stort tryck mitt på framsidan.' },
  { id: 'rygg',   name: 'Rygg',   size: '22 × 22 cm', side: 'back',
    desc: 'Stort tryck mitt på ryggen.' },
];

const PRODUCTS = {
  tshirt: {
    id: 'tshirt',
    name: 'T-shirt',
    price: 249,
    tagline: 'Klassisk passform · 100 % ekologisk bomull · 185 g/m²',
    desc: 'Vår klassiska t-shirt i tjock, kammad ekologisk bomull. Förstärkta axelsömmar och en siluett som håller formen tvätt efter tvätt.',
  },
  hoodie: {
    id: 'hoodie',
    name: 'Hoodie',
    price: 449,
    tagline: 'Oversized passform · borstad insida · 350 g/m²',
    desc: 'En tung premiumhoodie med dubbelt tyg i luvan, känguruficka och borstad insida. Trycket appliceras innan plagget sys — för ett resultat som håller.',
  },
  longsleeve: {
    id: 'longsleeve',
    name: 'Långärmad t-shirt',
    price: 299,
    tagline: 'Klassisk passform · ribbade muddar · 205 g/m²',
    desc: 'Långärmad tröja i tät singeljersey med ribbade muddar. Perfekt basplagg året om — och en utmärkt duk för ditt motiv.',
  },
};

/* ---------------------------------------------------------
   25 motiv — varje motiv är en SVG (viewBox 0 0 100 100)
   --------------------------------------------------------- */

const MOTIFS = [
  { id: 'tiger', name: 'Tiger', svg: `
    <g stroke-linejoin='round'>
      <path d='M29 22 L17 7 L37 12Z' fill='#e0882a'/><path d='M71 22 L83 7 L63 12Z' fill='#e0882a'/>
      <path d='M50 10 C30 10 18 26 18 44 C18 66 30 84 50 90 C70 84 82 66 82 44 C82 26 70 10 50 10Z' fill='#e0882a'/>
      <path d='M50 58 C40 58 34 66 36 76 C40 84 44 86 50 86 C56 86 60 84 64 76 C66 66 60 58 50 58Z' fill='#f6efe4'/>
      <path d='M50 13 L46 24 L54 24Z' fill='#26251f'/>
      <path d='M24 30 L35 34 L26 41Z' fill='#26251f'/><path d='M76 30 L65 34 L74 41Z' fill='#26251f'/>
      <path d='M20 50 L32 52 L22 59Z' fill='#26251f'/><path d='M80 50 L68 52 L78 59Z' fill='#26251f'/>
      <circle cx='38' cy='42' r='5.5' fill='#cddc39'/><circle cx='62' cy='42' r='5.5' fill='#cddc39'/>
      <circle cx='38' cy='42' r='2.2' fill='#111'/><circle cx='62' cy='42' r='2.2' fill='#111'/>
      <path d='M50 62 L44 68 L56 68Z' fill='#3a2a24'/>
      <path d='M50 68 L50 76 M43 80 C46 83 54 83 57 80' stroke='#3a2a24' stroke-width='2.5' fill='none' stroke-linecap='round'/>
    </g>` },
  { id: 'blixt', name: 'Blixten', svg: `
    <path d='M58 4 L24 56 L44 56 L38 96 L78 40 L55 40 L68 4Z' fill='#f7c626' stroke='#1b1b1f' stroke-width='4' stroke-linejoin='round'/>` },
  { id: 'berg', name: 'Bergstopp', svg: `
    <circle cx='73' cy='25' r='11' fill='#f2b632'/>
    <path d='M6 82 L38 30 L58 62 L70 44 L94 82Z' fill='#2e4057' stroke='#f4efe6' stroke-width='3' stroke-linejoin='round'/>
    <path d='M38 30 L46 43 L40 47 L33 40Z' fill='#f4efe6'/>
    <path d='M70 44 L76 53 L71 56 L66 51Z' fill='#f4efe6'/>` },
  { id: 'vag', name: 'Vågen', svg: `
    <circle cx='50' cy='50' r='45' fill='#eef4f8' stroke='#1d3557' stroke-width='4'/>
    <path d='M12 62 C24 42 42 38 54 46 C45 48 40 54 43 60 C51 52 63 53 68 61 C74 50 84 51 89 59 L88 67 C64 86 30 83 13 67Z' fill='#2f80c3'/>
    <circle cx='56' cy='41' r='3' fill='#2f80c3'/><circle cx='66' cy='47' r='2.5' fill='#2f80c3'/><circle cx='47' cy='44' r='2' fill='#2f80c3'/>` },
  { id: 'solnedgang', name: 'Solnedgång', svg: `
    <defs><clipPath id='mvSunClip'><circle cx='50' cy='44' r='30'/></clipPath></defs>
    <g clip-path='url(#mvSunClip)'>
      <rect x='18' y='12' width='64' height='64' fill='#f7b32b'/>
      <rect x='18' y='38' width='64' height='4' fill='#e2725b'/>
      <rect x='18' y='48' width='64' height='5' fill='#e2725b'/>
      <rect x='18' y='59' width='64' height='7' fill='#d64550'/>
    </g>
    <path d='M8 78 L92 78' stroke='#2a2a2e' stroke-width='4' stroke-linecap='round'/>
    <path d='M26 68 l5 -4 5 4 M62 64 l4 -3 4 3' stroke='#2a2a2e' stroke-width='2.5' fill='none' stroke-linecap='round' stroke-linejoin='round'/>` },
  { id: 'skalle', name: 'Dödskalle', svg: `
    <path d='M50 8 C28 8 16 24 16 42 C16 56 24 66 32 70 L32 84 C32 90 38 94 44 94 L56 94 C62 94 68 90 68 84 L68 70 C76 66 84 56 84 42 C84 24 72 8 50 8Z' fill='#f2f0ea' stroke='#1b1b1f' stroke-width='3'/>
    <ellipse cx='37' cy='44' rx='8' ry='10' fill='#1b1b1f'/><ellipse cx='63' cy='44' rx='8' ry='10' fill='#1b1b1f'/>
    <path d='M50 54 L44 66 L56 66Z' fill='#1b1b1f'/>
    <path d='M40 76 L40 90 M50 78 L50 92 M60 76 L60 90' stroke='#1b1b1f' stroke-width='3' stroke-linecap='round'/>` },
  { id: 'ros', name: 'Ros', svg: `
    <path d='M50 50 C50 66 50 78 50 92' stroke='#2e6b34' stroke-width='4' fill='none'/>
    <path d='M50 74 C40 74 32 68 30 60 C40 60 48 64 50 74Z' fill='#2e6b34'/>
    <path d='M50 66 C60 66 68 60 70 52 C60 52 52 56 50 66Z' fill='#2e6b34'/>
    <circle cx='50' cy='30' r='22' fill='#c22b3d'/>
    <circle cx='50' cy='30' r='10' fill='none' stroke='#8f1f2d' stroke-width='3'/>
    <path d='M50 12 C38 14 30 22 30 32 M50 16 C58 18 66 24 66 32 M38 42 C44 48 56 48 62 42' stroke='#8f1f2d' stroke-width='3' fill='none' stroke-linecap='round'/>` },
  { id: 'orm', name: 'Orm', svg: `
    <path d='M24 88 C10 80 12 62 28 58 C48 52 66 58 72 46 C78 34 66 26 52 30 C46 32 42 29 45 24' fill='none' stroke='#3f9142' stroke-width='9' stroke-linecap='round'/>
    <circle cx='47' cy='18' r='8' fill='#3f9142'/>
    <circle cx='45' cy='16' r='1.8' fill='#111'/>
    <path d='M40 13 L31 7 M31 7 L34 12 M31 7 L27 10' stroke='#d64550' stroke-width='2' stroke-linecap='round'/>
    <path d='M20 84 C14 80 14 68 26 64' stroke='#2e6b34' stroke-width='3' fill='none' stroke-linecap='round'/>` },
  { id: 'orn', name: 'Örn', svg: `
    <path d='M6 40 C22 28 38 26 48 34 C52 24 58 18 66 16 C62 22 62 28 64 32 C74 30 86 34 94 44 C82 42 74 44 68 48 C64 62 56 72 50 88 C48 72 44 62 40 52 C28 50 14 46 6 40Z' fill='#23262b' stroke='#f4efe6' stroke-width='2.5' stroke-linejoin='round'/>
    <circle cx='60' cy='24' r='1.6' fill='#f4efe6'/>` },
  { id: 'kompass', name: 'Kompass', svg: `
    <circle cx='50' cy='50' r='42' fill='#f4efe6' stroke='#1d3557' stroke-width='5'/>
    <circle cx='50' cy='50' r='33' fill='none' stroke='#1d3557' stroke-width='1.5'/>
    <path d='M50 18 L58 50 L50 82 L42 50Z' fill='#c22b3d'/>
    <path d='M18 50 L50 42 L82 50 L50 58Z' fill='#1d3557'/>
    <circle cx='50' cy='50' r='5' fill='#f4efe6' stroke='#1d3557' stroke-width='3'/>` },
  { id: 'ankare', name: 'Ankare', svg: `
    <g stroke='#1d3557' stroke-linecap='round' fill='none'>
      <circle cx='50' cy='16' r='8' stroke-width='6'/>
      <path d='M50 24 L50 80' stroke-width='7'/>
      <path d='M32 38 L68 38' stroke-width='6'/>
      <path d='M50 84 C36 82 24 72 22 56 L34 62 M50 84 C64 82 76 72 78 56 L66 62' stroke-width='6'/>
    </g>` },
  { id: 'krona', name: 'Krona', svg: `
    <path d='M18 70 L12 30 L34 48 L50 22 L66 48 L88 30 L82 70Z' fill='#f2b632' stroke='#a26a12' stroke-width='3' stroke-linejoin='round'/>
    <rect x='17' y='73' width='66' height='11' rx='3' fill='#f2b632' stroke='#a26a12' stroke-width='3'/>
    <circle cx='12' cy='25' r='4' fill='#f2b632'/><circle cx='50' cy='17' r='4' fill='#f2b632'/><circle cx='88' cy='25' r='4' fill='#f2b632'/>
    <circle cx='34' cy='63' r='3.5' fill='#c22b3d'/><circle cx='50' cy='60' r='3.5' fill='#2f80c3'/><circle cx='66' cy='63' r='3.5' fill='#2e8b57'/>` },
  { id: 'stjarna', name: 'Stjärna', svg: `
    <path d='M50 6 L61 38 L95 38 L67 57 L78 90 L50 70 L22 90 L33 57 L5 38 L39 38Z' fill='#f2b632' stroke='#1b1b1f' stroke-width='3' stroke-linejoin='round'/>` },
  { id: 'hjarta', name: 'Krossat hjärta', svg: `
    <path d='M50 88 C28 70 14 56 14 40 C14 28 24 20 34 20 C42 20 48 25 50 30 C52 25 58 20 66 20 C76 20 86 28 86 40 C86 56 72 70 50 88Z' fill='#c22b3d' stroke='#7c1626' stroke-width='2.5'/>
    <path d='M55 26 L46 46 L56 50 L44 72' stroke='#f4efe6' stroke-width='4' fill='none' stroke-linecap='round' stroke-linejoin='round'/>` },
  { id: 'fjaril', name: 'Fjäril', svg: `
    <path d='M50 32 C34 8 10 10 12 32 C13 46 30 52 46 50Z' fill='#8e6bbf'/>
    <path d='M50 32 C66 8 90 10 88 32 C87 46 70 52 54 50Z' fill='#8e6bbf'/>
    <path d='M46 52 C30 52 18 62 22 74 C26 84 42 80 48 66Z' fill='#c98bc9'/>
    <path d='M54 52 C70 52 82 62 78 74 C74 84 58 80 52 66Z' fill='#c98bc9'/>
    <ellipse cx='50' cy='52' rx='4' ry='20' fill='#2b2b2f'/>
    <path d='M47 32 C43 24 39 19 33 15 M53 32 C57 24 61 19 67 15' stroke='#2b2b2f' stroke-width='2' fill='none' stroke-linecap='round'/>` },
  { id: 'smiley', name: 'Smiley', svg: `
    <circle cx='50' cy='50' r='40' fill='#f7c626' stroke='#1b1b1f' stroke-width='3'/>
    <ellipse cx='36' cy='42' rx='5' ry='8' fill='#1b1b1f'/><ellipse cx='64' cy='42' rx='5' ry='8' fill='#1b1b1f'/>
    <path d='M30 60 C38 72 62 72 70 60' stroke='#1b1b1f' stroke-width='5' fill='none' stroke-linecap='round'/>` },
  { id: 'yinyang', name: 'Yin & Yang', svg: `
    <circle cx='50' cy='50' r='44' fill='#f4f4f4' stroke='#111' stroke-width='3'/>
    <path d='M50 6 A44 44 0 0 1 50 94 A22 22 0 0 1 50 50 A22 22 0 0 0 50 6Z' fill='#111'/>
    <circle cx='50' cy='28' r='7' fill='#f4f4f4'/><circle cx='50' cy='72' r='7' fill='#111'/>` },
  { id: 'attan', name: 'Åttan', svg: `
    <circle cx='50' cy='50' r='42' fill='#1a1a1e'/>
    <ellipse cx='37' cy='29' rx='14' ry='9' fill='#ffffff' opacity='.18'/>
    <circle cx='50' cy='50' r='16' fill='#fff'/>
    <text x='50' y='58' font-family='Arial, sans-serif' font-size='22' font-weight='700' text-anchor='middle' fill='#111'>8</text>` },
  { id: 'tarningar', name: 'Tärningar', svg: `
    <g transform='rotate(-12 34 40)'>
      <rect x='12' y='18' width='44' height='44' rx='8' fill='#fff' stroke='#1b1b1f' stroke-width='3'/>
      <circle cx='24' cy='30' r='4' fill='#c22b3d'/><circle cx='34' cy='40' r='4' fill='#c22b3d'/><circle cx='44' cy='50' r='4' fill='#c22b3d'/>
    </g>
    <g transform='rotate(14 66 66)'>
      <rect x='46' y='46' width='40' height='40' rx='8' fill='#1b1b1f'/>
      <circle cx='56' cy='56' r='4' fill='#fff'/><circle cx='76' cy='56' r='4' fill='#fff'/>
      <circle cx='56' cy='76' r='4' fill='#fff'/><circle cx='76' cy='76' r='4' fill='#fff'/>
    </g>` },
  { id: 'raket', name: 'Raket', svg: `
    <path d='M50 4 C62 14 68 32 68 50 L68 66 L32 66 L32 50 C32 32 38 14 50 4Z' fill='#e8e6e0' stroke='#1b1b1f' stroke-width='3'/>
    <circle cx='50' cy='36' r='9' fill='#2f80c3' stroke='#1b1b1f' stroke-width='3'/>
    <path d='M32 50 L14 72 L32 68Z' fill='#c22b3d' stroke='#1b1b1f' stroke-width='3' stroke-linejoin='round'/>
    <path d='M68 50 L86 72 L68 68Z' fill='#c22b3d' stroke='#1b1b1f' stroke-width='3' stroke-linejoin='round'/>
    <path d='M42 66 L58 66 L54 74 L46 74Z' fill='#1b1b1f'/>
    <path d='M44 76 C42 86 46 92 50 97 C54 92 58 86 56 76 C54 82 46 82 44 76Z' fill='#f2a71b'/>` },
  { id: 'kaktus', name: 'Kaktus', svg: `
    <path d='M42 20 C42 11 58 11 58 20 L58 64 L42 64Z' fill='#3f9142'/>
    <path d='M42 46 L32 46 L32 30' stroke='#3f9142' stroke-width='10' fill='none' stroke-linecap='round'/>
    <path d='M58 52 L70 52 L70 36' stroke='#3f9142' stroke-width='10' fill='none' stroke-linecap='round'/>
    <path d='M46 24 L46 28 M54 30 L54 34 M50 44 L50 48 M46 54 L46 58' stroke='#e6f2e6' stroke-width='1.6' stroke-linecap='round'/>
    <circle cx='50' cy='12' r='5' fill='#e9a6b8'/>
    <path d='M34 64 L66 64 L64 72 L60 72 L58 90 L42 90 L40 72 L36 72Z' fill='#c96f4a' stroke='#8a4630' stroke-width='2.5' stroke-linejoin='round'/>` },
  { id: 'kassett', name: 'Kassett', svg: `
    <rect x='8' y='24' width='84' height='52' rx='6' fill='#2b2b31' stroke='#0e0e10' stroke-width='2.5'/>
    <rect x='16' y='31' width='68' height='24' rx='4' fill='#e8e2d2'/>
    <rect x='16' y='31' width='68' height='7' rx='3' fill='#c22b3d'/>
    <circle cx='34' cy='46' r='7' fill='#fff' stroke='#111' stroke-width='2'/><circle cx='66' cy='46' r='7' fill='#fff' stroke='#111' stroke-width='2'/>
    <circle cx='34' cy='46' r='2' fill='#111'/><circle cx='66' cy='46' r='2' fill='#111'/>
    <rect x='43' y='43' width='14' height='6' fill='#111' opacity='.15'/>
    <path d='M30 76 L36 62 L64 62 L70 76' fill='none' stroke='#0e0e10' stroke-width='2.5'/>` },
  { id: 'peace', name: 'Peace', svg: `
    <g fill='none' stroke-linecap='round'>
      <circle cx='50' cy='50' r='40' stroke='#f4efe6' stroke-width='13'/>
      <path d='M50 10 L50 90 M50 50 L22 78 M50 50 L78 78' stroke='#f4efe6' stroke-width='13'/>
      <circle cx='50' cy='50' r='40' stroke='#1d3557' stroke-width='7'/>
      <path d='M50 10 L50 90 M50 50 L22 78 M50 50 L78 78' stroke='#1d3557' stroke-width='7'/>
    </g>` },
  { id: 'est1994', name: 'Est. 1994', svg: `
    <circle cx='50' cy='50' r='45' fill='#f4efe6' stroke='#1b1b1f' stroke-width='4'/>
    <circle cx='50' cy='50' r='37' fill='none' stroke='#1b1b1f' stroke-width='1.5'/>
    <text x='50' y='43' font-family='Georgia, serif' font-size='13' letter-spacing='3' text-anchor='middle' fill='#1b1b1f'>EST.</text>
    <text x='50' y='72' font-family='Georgia, serif' font-size='24' font-weight='700' letter-spacing='2' text-anchor='middle' fill='#1b1b1f'>1994</text>
    <path d='M26 51 L36 51 M64 51 L74 51' stroke='#1b1b1f' stroke-width='2'/>` },
  { id: 'sthlm', name: 'STHLM', svg: `
    <path d='M8 22 L92 22 M8 78 L92 78' stroke='#1d3557' stroke-width='5' stroke-linecap='round'/>
    <rect x='8' y='31' width='84' height='38' rx='4' fill='#1d3557'/>
    <text x='50' y='58' font-family='Arial, sans-serif' font-weight='900' font-size='23' letter-spacing='3' text-anchor='middle' fill='#f7c626'>STHLM</text>` },
];

const MOTIF_BY_ID = Object.fromEntries(MOTIFS.map(m => [m.id, m]));
const COLOR_BY_ID = Object.fromEntries(COLORS.map(c => [c.id, c]));
const PLACEMENT_BY_ID = Object.fromEntries(PLACEMENTS.map(p => [p.id, p]));
