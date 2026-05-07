# BusinessVisualization Money Model Zoom and Label Placement — 2026-05-07

## Context

Repository: `$HOME/businessvisualization-hosted-site`

This session refined the dynamic Money Model SVG and its zoom playback controls. The user was iterating visually and wanted the live rendered result, not abstract SVG math.

## Durable implementation lessons

- Keep the Money Model's zoom storyboard/player inside `.money-model-block` immediately after `.machine-svg-unified` so it appears directly below the gears, not outside the dashed grid shell.
- Homepage embed mode must not render zoom storyboard controls; verify `doc.querySelectorAll('.money-zoom-storyboard').length === 0` inside the iframe.
- Full Business Model page should render exactly one storyboard.
- Before changing the SVG `viewBox`/canvas width, also update CSS `aspect-ratio` for `.machine-svg-unified` containers so the rendered page does not distort or create unexpected whitespace.
- Playback/step controls should call `svg.scrollIntoView({ block: 'center', inline: 'center' })` before selecting/animating the anchor so the zoom focus is centered in the viewer.
- For the Revenue direct label, special-case the `REVENUE` stage label in the drafting/stage-label loop instead of allowing the shared bottom-label rule to place it under the gear. Place the label/value/hourly stack upper-left of the Revenue gear with `text-anchor='end'` and coordinates based on the Revenue gear bbox/radius.
- Cache-bust both `business-model.html` script/style references and `index.html` homepage iframe URL after JS/CSS/layout edits.
- When the user asks to move right-side expense gears closer to a label column (Royalties / Call Center Fee), tune the generator's shared `expenseColumnX` and the direct expense label X offset together. In this session, shifting `expenseColumnX` right from `moneyGridColumnCenter(8) - MACHINE_CM * 2.75` to `- MACHINE_CM * 1.95` alone kept the label gap effectively unchanged because labels were derived from gear X; tightening the label offset from `gear.x + 124` to `gear.x + 72` produced the visual result. Verify actual `getBBox()` gear-to-label edge gaps, not just gear centers.

## Verification snippets

### Player placement and centering

```js
(() => {
  const block = document.querySelector('.money-model-block');
  const svg = block?.querySelector('.machine-svg-unified');
  const controls = block?.querySelector('.money-zoom-storyboard');
  return {
    controlsAfterSvg: svg?.nextElementSibling === controls,
    fullPageStoryboards: document.querySelectorAll('.money-zoom-storyboard').length,
    overflowX: document.documentElement.scrollWidth - window.innerWidth,
  };
})()
```

```js
(async () => {
  window.scrollTo(0, 0);
  await new Promise(r => setTimeout(r, 80));
  document.querySelector('[data-zoom-control="play"]')?.click();
  await new Promise(r => setTimeout(r, 350));
  const svg = document.querySelector('.money-model-block .machine-svg-unified');
  const r = svg.getBoundingClientRect();
  return {
    centerDeltaPx: +(((r.top + r.height / 2) - (window.innerHeight / 2)).toFixed(1)),
    activeId: document.querySelector('.money-zoom-chip.is-active')?.dataset.zoomAnchor,
  };
})()
```

### Right-side expense gear-to-label gap check

```js
(() => {
  const svg = document.querySelector('.machine-svg-unified');
  const gears = [...svg.querySelectorAll('.machine-gear')].map(g => {
    const name = (g.querySelector('title')?.textContent || '').split(':')[0];
    const bb = g.querySelector('.machine-teeth,.machine-pie-teeth')?.getBBox();
    return bb && { name, right: bb.x + bb.width, cx: bb.x + bb.width / 2 };
  }).filter(Boolean);
  const labelBox = name => {
    const label = [...svg.querySelectorAll('.machine-radial-expense-label,.machine-marketing-direct-label')]
      .find(e => e.getAttribute('data-label-name') === name);
    const value = [...svg.querySelectorAll('.machine-radial-expense-value,.machine-marketing-direct-value')]
      .find(e => e.getAttribute('data-label-name') === name);
    const hourly = value?.nextElementSibling;
    const boxes = [label, value, hourly].filter(Boolean).map(n => n.getBBox());
    return { left: Math.min(...boxes.map(b => b.x)), right: Math.max(...boxes.map(b => b.x + b.width)) };
  };
  return ['Royalties', 'CSC Fee', 'Wages Truck Staff', 'Fuel', 'Dumping Fees', 'Remaining Expenses']
    .map(name => {
      const g = gears.find(x => x.name === name);
      const l = labelBox(name);
      return { name, gap: +(l.left - g.right).toFixed(2), gearCx: +g.cx.toFixed(2), labelLeft: +l.left.toFixed(2) };
    });
})()
```

### Revenue label upper-left check

```js
(() => {
  const svg = document.querySelector('.machine-svg-unified');
  const revenueGear = [...svg.querySelectorAll('.machine-gear')]
    .map(g => ({ g, name: (g.querySelector('title')?.textContent || '').split(':')[0] }))
    .find(x => x.name === 'Revenue')?.g;
  const teeth = revenueGear?.querySelector('.machine-teeth,.machine-pie-teeth');
  const gearBox = teeth?.getBBox();
  const gearCenter = { x: gearBox.x + gearBox.width / 2, y: gearBox.y + gearBox.height / 2 };
  const nodes = [
    svg.querySelector('.machine-direct-gear-label[data-label-name="Revenue"]'),
    svg.querySelector('.machine-direct-gear-value[data-label-name="Revenue"]'),
  ].filter(Boolean);
  const boxes = nodes.map(n => n.getBBox());
  const labelBox = {
    right: Math.max(...boxes.map(b => b.x + b.width)),
    bottom: Math.max(...boxes.map(b => b.y + b.height)),
  };
  return {
    upperLeft: labelBox.right < gearCenter.x && labelBox.bottom < gearCenter.y,
    leftGap: +(gearCenter.x - labelBox.right).toFixed(2),
    aboveGap: +(gearCenter.y - labelBox.bottom).toFixed(2),
  };
})()
```
