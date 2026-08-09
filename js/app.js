/* =========================================================
   MOTIV. — applikation (router, konfigurator, varukorg, kassa)
   ========================================================= */

const app = document.getElementById('app');

/* ------------------------- Varukorg ------------------------- */

let cart = [];
try { cart = JSON.parse(localStorage.getItem('motiv-cart') || '[]'); } catch (e) { cart = []; }

function saveCart() {
  localStorage.setItem('motiv-cart', JSON.stringify(cart));
  updateCartBadge();
}

function cartCount() { return cart.reduce((s, i) => s + i.qty, 0); }
function cartTotal() { return cart.reduce((s, i) => s + i.qty * PRODUCTS[i.product].price, 0); }

function updateCartBadge() {
  const badge = document.getElementById('cartCount');
  const n = cartCount();
  badge.hidden = n === 0;
  badge.textContent = n;
}

function addToCart(item) {
  const key = i => [i.product, i.color, i.size, i.motif, i.placement].join('|');
  const existing = cart.find(i => key(i) === key(item));
  if (existing) existing.qty += item.qty;
  else cart.push(item);
  saveCart();
  renderCartDrawer();
  openCart();
}

function itemPreviewSVG(item, side) {
  const pl = PLACEMENT_BY_ID[item.placement];
  const useSide = side || pl.side;
  return renderGarment(item.product, useSide, COLOR_BY_ID[item.color].hex, {
    motifId: item.motif, placementId: item.placement,
  });
}

function cartItemMeta(item) {
  return `${COLOR_BY_ID[item.color].name} · Stl ${item.size}<br>` +
    `Motiv: ${MOTIF_BY_ID[item.motif].name} · ${PLACEMENT_BY_ID[item.placement].name} (${PLACEMENT_BY_ID[item.placement].size})`;
}

function renderCartDrawer() {
  const wrap = document.getElementById('cartItems');
  const foot = document.getElementById('cartFoot');
  if (cart.length === 0) {
    wrap.innerHTML = `<div class="cart-empty">Din varukorg är tom.<br>Dags att designa något snyggt? 👕</div>`;
    foot.innerHTML = '';
    return;
  }
  wrap.innerHTML = cart.map((item, idx) => `
    <div class="cart-item">
      <div class="cart-item-img">${itemPreviewSVG(item)}</div>
      <div class="cart-item-info">
        <h4>${PRODUCTS[item.product].name}</h4>
        <div class="ci-meta">${cartItemMeta(item)}</div>
        <div class="cart-item-row">
          <span class="ci-qty">
            <button data-cart-dec="${idx}" aria-label="Minska antal">−</button>
            <span>${item.qty}</span>
            <button data-cart-inc="${idx}" aria-label="Öka antal">+</button>
          </span>
          <span class="ci-price">${item.qty * PRODUCTS[item.product].price} kr</span>
        </div>
        <button class="ci-remove" data-cart-remove="${idx}">Ta bort</button>
      </div>
    </div>`).join('');
  foot.innerHTML = `
    <div class="cart-total-row"><span>Summa</span><span>${cartTotal()} kr</span></div>
    <div class="cart-fine">Fri frakt · tryck ingår i priset</div>
    <button class="checkout-btn" id="toCheckoutBtn">Till kassan →</button>`;

  wrap.querySelectorAll('[data-cart-dec]').forEach(b => b.onclick = () => {
    const i = +b.dataset.cartDec;
    cart[i].qty -= 1;
    if (cart[i].qty <= 0) cart.splice(i, 1);
    saveCart(); renderCartDrawer();
  });
  wrap.querySelectorAll('[data-cart-inc]').forEach(b => b.onclick = () => {
    cart[+b.dataset.cartInc].qty += 1;
    saveCart(); renderCartDrawer();
  });
  wrap.querySelectorAll('[data-cart-remove]').forEach(b => b.onclick = () => {
    cart.splice(+b.dataset.cartRemove, 1);
    saveCart(); renderCartDrawer();
  });
  const toCheckout = document.getElementById('toCheckoutBtn');
  if (toCheckout) toCheckout.onclick = () => { closeCart(); location.hash = '#/kassa'; };
}

const drawer = document.getElementById('cartDrawer');
const overlay = document.getElementById('drawerOverlay');
function openCart() { renderCartDrawer(); drawer.classList.add('open'); overlay.hidden = false; }
function closeCart() { drawer.classList.remove('open'); overlay.hidden = true; }
document.getElementById('cartBtn').onclick = openCart;
document.getElementById('cartCloseBtn').onclick = closeCart;
overlay.onclick = closeCart;

/* ------------------------- Toast ------------------------- */

let toastTimer;
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 2600);
}

/* ------------------------- Router ------------------------- */

function route() {
  const hash = location.hash || '#/';
  const parts = hash.replace(/^#\//, '').split('/');
  window.scrollTo(0, 0);
  if (parts[0] === 'produkt' && PRODUCTS[parts[1]]) renderProductPage(parts[1]);
  else if (parts[0] === 'kassa') renderCheckoutPage();
  else if (parts[0] === 'tack') renderConfirmationPage();
  else renderHomePage();
}
window.addEventListener('hashchange', route);

/* ------------------------- Startsida ------------------------- */

function renderHomePage() {
  const cats = [
    { id: 'tshirt', color: '#28345c', note: 'från 249 kr' },
    { id: 'hoodie', color: '#232327', note: 'från 449 kr' },
    { id: 'longsleeve', color: '#77755b', note: 'från 299 kr' },
  ];
  app.innerHTML = `
    <section class="hero">
      <div class="hero-kicker">Tryckt för hand · Levereras inom 3–5 dagar</div>
      <h1>Ditt motiv.<br><em>Dina</em> kläder.</h1>
      <p class="lead">Välj plagg, färg och storlek. Välj bland 25 unika motiv och bestäm exakt var trycket ska sitta — och se resultatet live innan du beställer.</p>
      <a class="hero-cta" href="#/produkt/tshirt">Börja designa <span>→</span></a>
    </section>

    <section class="category-section">
      <div class="section-head">
        <h2>Välj ditt plagg</h2>
        <span>3 plagg · 12 färger · 25 motiv · 3 placeringar</span>
      </div>
      <div class="category-grid">
        ${cats.map(c => `
          <a class="category-card" href="#/produkt/${c.id}">
            <div class="card-img">${renderGarment(c.id, 'front', c.color)}</div>
            <div class="card-body">
              <div>
                <h3>${PRODUCTS[c.id].name}</h3>
                <small>${c.note}</small>
              </div>
              <span class="card-arrow">→</span>
            </div>
          </a>`).join('')}
      </div>
    </section>

    <section class="steps-strip">
      <div class="steps-inner">
        <div class="step-item">
          <div class="step-num">STEG 01</div>
          <h4>Välj plagg &amp; färg</h4>
          <p>T-shirt, hoodie eller långärmat — i 12 noga utvalda färger, XS till 5XL.</p>
        </div>
        <div class="step-item">
          <div class="step-num">STEG 02</div>
          <h4>Välj motiv</h4>
          <p>25 handplockade motiv, tryckta med slitstarkt och miljövänligt DTG-tryck.</p>
        </div>
        <div class="step-item">
          <div class="step-num">STEG 03</div>
          <h4>Välj placering</h4>
          <p>Hjärta 10×10 cm, mage 22×22 cm eller rygg 22×22 cm — du bestämmer.</p>
        </div>
        <div class="step-item">
          <div class="step-num">STEG 04</div>
          <h4>Se det live &amp; beställ</h4>
          <p>Förhandsgranska exakt hur plagget blir och betala smidigt med Klarna.</p>
        </div>
      </div>
    </section>`;
}

/* ------------------------- Produktsida ------------------------- */

const configState = {};

function renderProductPage(productId) {
  const product = PRODUCTS[productId];

  if (configState.product !== productId) {
    configState.product = productId;
    configState.color = COLORS[0].id;
    configState.side = 'front';
    configState.size = null;
    configState.qty = 1;
    configState.motif = null;
    configState.placement = null;
  }
  const s = configState;

  app.innerHTML = `
    <div class="product-page">
      <div class="breadcrumb"><a href="#/">Hem</a> / ${product.name}</div>
      <div class="product-layout">

        <div class="preview-col">
          <div class="preview-stage">
            <div class="side-toggle">
              <button id="sideFront">FRAMSIDA</button>
              <button id="sideBack">BAKSIDA</button>
            </div>
            <div class="preview-badge" id="previewBadge"></div>
            <div id="previewSvg"></div>
          </div>
          <div class="color-thumbs" id="colorThumbs"></div>
        </div>

        <div class="config-col">
          <h1>${product.name}</h1>
          <p class="product-tagline">${product.tagline}</p>
          <div class="product-price">${product.price} kr <small>· tryck &amp; frakt ingår</small></div>
          <p class="product-desc">${product.desc}</p>

          <div class="config-step done" id="stepColor">
            <div class="config-step-head">
              <span class="step-index">1</span><h3>Färg</h3>
              <span class="step-value" id="colorValue"></span>
            </div>
          </div>

          <div class="config-step" id="stepSize">
            <div class="config-step-head">
              <span class="step-index">2</span><h3>Storlek &amp; antal</h3>
              <span class="step-value" id="sizeValue"></span>
            </div>
            <div class="size-grid" id="sizeGrid"></div>
            <div class="qty-row">
              <label>Antal</label>
              <span class="qty-stepper">
                <button id="qtyDec" aria-label="Minska antal">−</button>
                <span class="qty-val" id="qtyVal">1</span>
                <button id="qtyInc" aria-label="Öka antal">+</button>
              </span>
            </div>
          </div>

          <div class="config-step" id="stepMotif">
            <div class="config-step-head">
              <span class="step-index">3</span><h3>Motiv</h3>
              <span class="step-value" id="motifValue"></span>
            </div>
            <button class="motif-cta" id="motifBtn"></button>
          </div>

          <div class="config-step" id="stepPlacement">
            <div class="config-step-head">
              <span class="step-index">4</span><h3>Placering</h3>
              <span class="step-value" id="placementValue"></span>
            </div>
            <div class="placement-grid" id="placementGrid"></div>
          </div>

          <button class="addtocart-btn" id="addBtn" disabled></button>
          <div class="addtocart-hint" id="addHint"></div>
        </div>
      </div>
    </div>`;

  /* --- färgminiatyrer --- */
  const thumbs = document.getElementById('colorThumbs');
  thumbs.innerHTML = COLORS.map(c => `
    <button class="color-thumb ${c.id === s.color ? 'selected' : ''}" data-color="${c.id}" title="${c.name}">
      ${renderThumb(productId, c.hex)}
      <span class="thumb-name">${c.name}</span>
    </button>`).join('');
  thumbs.querySelectorAll('[data-color]').forEach(b => b.onclick = () => {
    s.color = b.dataset.color;
    thumbs.querySelectorAll('.color-thumb').forEach(t => t.classList.toggle('selected', t.dataset.color === s.color));
    update();
  });

  /* --- fram/bak --- */
  document.getElementById('sideFront').onclick = () => { s.side = 'front'; update(); };
  document.getElementById('sideBack').onclick = () => { s.side = 'back'; update(); };

  /* --- storlekar --- */
  const sizeGrid = document.getElementById('sizeGrid');
  sizeGrid.innerHTML = SIZES.map(sz =>
    `<button class="size-btn ${s.size === sz ? 'selected' : ''}" data-size="${sz}">${sz}</button>`).join('');
  sizeGrid.querySelectorAll('[data-size]').forEach(b => b.onclick = () => {
    s.size = b.dataset.size;
    sizeGrid.querySelectorAll('.size-btn').forEach(x => x.classList.toggle('selected', x.dataset.size === s.size));
    update();
  });

  /* --- antal --- */
  document.getElementById('qtyDec').onclick = () => { s.qty = Math.max(1, s.qty - 1); update(); };
  document.getElementById('qtyInc').onclick = () => { s.qty = Math.min(99, s.qty + 1); update(); };

  /* --- motiv --- */
  document.getElementById('motifBtn').onclick = openMotifModal;

  /* --- placering --- */
  const plGrid = document.getElementById('placementGrid');
  const plIcon = (pl) => {
    const marks = {
      hjarta: { x: 54, y: 30, s: 12 },
      mage:   { x: 38, y: 42, s: 24 },
      rygg:   { x: 38, y: 36, s: 24 },
    };
    const m = marks[pl];
    const neck = pl === 'rygg'
      ? `<path d="M38 14 C42 18 58 18 62 14" stroke="currentColor" stroke-width="5" fill="none"/>`
      : `<path d="M37 13 C40 24 60 24 63 13" stroke="currentColor" stroke-width="5" fill="none"/>`;
    return `<svg viewBox="0 0 100 100" width="36" height="36">
      <path d="M31 13 L14 29 L24 42 L30 37 L30 87 L70 87 L70 37 L76 42 L86 29 L69 13 C62 19 38 19 31 13Z"
        fill="none" stroke="currentColor" stroke-width="5" stroke-linejoin="round"/>
      ${neck}
      <rect x="${m.x}" y="${m.y}" width="${m.s}" height="${m.s}" rx="3" fill="currentColor"/>
    </svg>`;
  };
  plGrid.innerHTML = PLACEMENTS.map(p => `
    <button class="placement-card ${s.placement === p.id ? 'selected' : ''}" data-placement="${p.id}">
      <div class="pl-icon">${plIcon(p.id)}</div>
      <h4>${p.name}</h4>
      <small>${p.size}</small>
    </button>`).join('');
  plGrid.querySelectorAll('[data-placement]').forEach(b => b.onclick = () => {
    s.placement = b.dataset.placement;
    s.side = PLACEMENT_BY_ID[s.placement].side; // visa rätt sida direkt
    plGrid.querySelectorAll('.placement-card').forEach(x =>
      x.classList.toggle('selected', x.dataset.placement === s.placement));
    update();
  });

  /* --- lägg i varukorg --- */
  document.getElementById('addBtn').onclick = () => {
    if (!isConfigComplete()) return;
    addToCart({
      product: s.product, color: s.color, size: s.size,
      qty: s.qty, motif: s.motif, placement: s.placement,
    });
    toast('Tillagd i varukorgen ✓');
  };

  function isConfigComplete() {
    return s.color && s.size && s.motif && s.placement;
  }

  function update() {
    const color = COLOR_BY_ID[s.color];

    /* förhandsvisning */
    document.getElementById('previewSvg').innerHTML = renderGarment(
      s.product, s.side, color.hex,
      { motifId: s.motif, placementId: s.placement, showPrintAreas: !s.placement && !!s.motif }
    );
    document.getElementById('sideFront').classList.toggle('active', s.side === 'front');
    document.getElementById('sideBack').classList.toggle('active', s.side === 'back');
    document.getElementById('previewBadge').textContent =
      `${product.name} · ${color.name} · ${s.side === 'front' ? 'Framsida' : 'Baksida'}`;

    /* stegvärden */
    document.getElementById('colorValue').textContent = color.name;
    document.getElementById('sizeValue').textContent =
      s.size ? `${s.size} · ${s.qty} st` : '';
    document.getElementById('motifValue').textContent = s.motif ? MOTIF_BY_ID[s.motif].name : '';
    document.getElementById('placementValue').textContent =
      s.placement ? `${PLACEMENT_BY_ID[s.placement].name} · ${PLACEMENT_BY_ID[s.placement].size}` : '';

    document.getElementById('stepSize').classList.toggle('done', !!s.size);
    document.getElementById('stepMotif').classList.toggle('done', !!s.motif);
    document.getElementById('stepPlacement').classList.toggle('done', !!s.placement);

    document.getElementById('qtyVal').textContent = s.qty;

    /* motivknapp */
    const motifBtn = document.getElementById('motifBtn');
    if (s.motif) {
      const m = MOTIF_BY_ID[s.motif];
      motifBtn.classList.add('has-motif');
      motifBtn.innerHTML = `
        <span class="motif-preview"><svg viewBox="0 0 100 100">${m.svg}</svg></span>
        <span>${m.name}<small>Klicka för att byta motiv</small></span>
        <span class="cta-arrow">→</span>`;
    } else {
      motifBtn.classList.remove('has-motif');
      motifBtn.innerHTML = `
        <span class="motif-preview" style="display:flex;align-items:center;justify-content:center;font-size:1.4rem;">✦</span>
        <span>Välj motiv<small>25 motiv att välja mellan</small></span>
        <span class="cta-arrow">→</span>`;
    }

    /* knapp */
    const addBtn = document.getElementById('addBtn');
    const hint = document.getElementById('addHint');
    addBtn.disabled = !isConfigComplete();
    addBtn.innerHTML = `Lägg i varukorgen · ${s.qty * product.price} kr`;
    if (!s.size) hint.textContent = 'Välj storlek för att gå vidare.';
    else if (!s.motif) hint.textContent = 'Välj ett motiv — steg 3.';
    else if (!s.placement) hint.textContent = 'Välj placering av trycket — steg 4.';
    else hint.textContent = 'Allt klart! Förhandsvisningen ovan visar exakt hur plagget blir.';
  }

  update();
}

/* ------------------------- Motiv-modal ------------------------- */

const motifModal = document.getElementById('motifModal');
const motifGrid = document.getElementById('motifGrid');

function openMotifModal() {
  motifGrid.innerHTML = MOTIFS.map(m => `
    <button class="motif-tile ${configState.motif === m.id ? 'selected' : ''}" data-motif="${m.id}">
      <svg viewBox="0 0 100 100">${m.svg}</svg>
      <span>${m.name}</span>
    </button>`).join('');
  motifGrid.querySelectorAll('[data-motif]').forEach(b => b.onclick = () => {
    configState.motif = b.dataset.motif;
    closeMotifModal();
    renderProductPage(configState.product);
  });
  motifModal.hidden = false;
  document.body.style.overflow = 'hidden';
}
function closeMotifModal() {
  motifModal.hidden = true;
  document.body.style.overflow = '';
}
document.getElementById('motifCloseBtn').onclick = closeMotifModal;
motifModal.addEventListener('click', e => { if (e.target === motifModal) closeMotifModal(); });

/* ------------------------- Kassa ------------------------- */

function renderCheckoutPage() {
  if (cart.length === 0) {
    app.innerHTML = `
      <div class="checkout-page">
        <h1>Kassan</h1>
        <div class="checkout-card" style="text-align:center;padding:60px 30px;">
          <p style="color:var(--ink-soft);margin-bottom:20px;">Din varukorg är tom.</p>
          <a class="hero-cta" href="#/">Börja designa →</a>
        </div>
      </div>`;
    return;
  }

  const fields = [
    { id: 'email', label: 'E-postadress', type: 'email', full: true, ph: 'namn@exempel.se' },
    { id: 'fname', label: 'Förnamn', ph: 'Anna' },
    { id: 'lname', label: 'Efternamn', ph: 'Andersson' },
    { id: 'address', label: 'Gatuadress', full: true, ph: 'Exempelgatan 12' },
    { id: 'zip', label: 'Postnummer', ph: '123 45' },
    { id: 'city', label: 'Ort', ph: 'Stockholm' },
    { id: 'phone', label: 'Mobilnummer', full: true, ph: '070-123 45 67' },
  ];

  const total = cartTotal();
  const monthly = Math.ceil(total / 3);

  app.innerHTML = `
    <div class="checkout-page">
      <h1>Kassan</h1>
      <div class="checkout-layout">
        <div>
          <div class="checkout-card">
            <h2>1 · Dina uppgifter</h2>
            <div class="form-grid" id="checkoutForm">
              ${fields.map(f => `
                <div class="form-field ${f.full ? 'full' : ''}">
                  <label for="f-${f.id}">${f.label}</label>
                  <input id="f-${f.id}" type="${f.type || 'text'}" placeholder="${f.ph}" autocomplete="on">
                </div>`).join('')}
            </div>
          </div>

          <div class="checkout-card">
            <h2>2 · Betalning</h2>
            <div class="klarna-box">
              <div class="klarna-head">
                <span class="klarna-logo">Klarna.</span>
                <small>Smidiga betalningar</small>
              </div>
              <label class="klarna-option">
                <input type="radio" name="klarna" value="now" checked>
                <span class="ko-body"><strong>Betala nu</strong><small>Direktbetalning med kort eller bank</small></span>
                <span class="ko-price">${total} kr</span>
              </label>
              <label class="klarna-option">
                <input type="radio" name="klarna" value="later">
                <span class="ko-body"><strong>Betala om 30 dagar</strong><small>Först prova hemma, betala sen — utan avgift</small></span>
                <span class="ko-price">${total} kr</span>
              </label>
              <label class="klarna-option">
                <input type="radio" name="klarna" value="split">
                <span class="ko-body"><strong>Delbetala</strong><small>Dela upp köpet på 3 månader, räntefritt</small></span>
                <span class="ko-price">${monthly} kr/mån</span>
              </label>
            </div>
            <button class="pay-btn" id="payBtn">Slutför köp · ${total} kr</button>
            <div class="pay-fine">Demobutik — ingen riktig betalning genomförs. I skarp drift kopplas Klarna Checkout in här.</div>
          </div>
        </div>

        <div class="summary-card">
          <h2>Din beställning</h2>
          ${cart.map(item => `
            <div class="summary-item">
              <div class="cart-item-img">${itemPreviewSVG(item)}</div>
              <div>
                <strong>${item.qty} × ${PRODUCTS[item.product].name}</strong>
                <span class="ci-meta">${cartItemMeta(item)}</span>
              </div>
              <span class="si-price">${item.qty * PRODUCTS[item.product].price} kr</span>
            </div>`).join('')}
          <div class="summary-rows">
            <div><span>Delsumma</span><span>${total} kr</span></div>
            <div><span>Frakt</span><span>0 kr</span></div>
            <div class="total"><span>Totalt</span><span>${total} kr</span></div>
          </div>
        </div>
      </div>
    </div>`;

  document.getElementById('payBtn').onclick = () => {
    /* enkel validering */
    let valid = true;
    fields.forEach(f => {
      const input = document.getElementById(`f-${f.id}`);
      const ok = input.value.trim().length > 1 &&
        (f.type !== 'email' || /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(input.value.trim()));
      input.classList.toggle('invalid', !ok);
      if (!ok) valid = false;
    });
    if (!valid) { toast('Fyll i alla uppgifter för att slutföra köpet.'); return; }

    const btn = document.getElementById('payBtn');
    btn.disabled = true;
    btn.textContent = 'Behandlar betalning …';
    setTimeout(() => {
      const orderNo = 'MV-' + Date.now().toString().slice(-6);
      sessionStorage.setItem('motiv-last-order', JSON.stringify({ orderNo, items: cart, total }));
      cart = [];
      saveCart();
      location.hash = '#/tack';
    }, 1400);
  };
}

/* ------------------------- Orderbekräftelse ------------------------- */

function renderConfirmationPage() {
  let order = null;
  try { order = JSON.parse(sessionStorage.getItem('motiv-last-order')); } catch (e) {}
  if (!order) { location.hash = '#/'; return; }

  app.innerHTML = `
    <div class="confirmation-page">
      <div class="conf-check">✓</div>
      <h1>Tack för din beställning!</h1>
      <p class="conf-order">Ordernummer <strong>${order.orderNo}</strong> · en bekräftelse har skickats till din e-post.<br>
      Ditt plagg trycks för hand och skickas inom 3–5 arbetsdagar.</p>
      <div class="conf-items">
        ${order.items.map(item => `
          <div class="summary-item">
            <div class="cart-item-img">${itemPreviewSVG(item)}</div>
            <div>
              <strong>${item.qty} × ${PRODUCTS[item.product].name}</strong>
              <span class="ci-meta">${cartItemMeta(item)}</span>
            </div>
            <span class="si-price">${item.qty * PRODUCTS[item.product].price} kr</span>
          </div>`).join('')}
        <div class="summary-rows">
          <div class="total"><span>Betalt med Klarna</span><span>${order.total} kr</span></div>
        </div>
      </div>
      <a class="hero-cta" href="#/">Designa ett till plagg →</a>
    </div>`;
}

/* ------------------------- Init ------------------------- */

updateCartBadge();
route();
