// Browser regression check for the desktop hero portrait.
// Run in the homepage with agent-browser eval or browser developer tools.
(() => {
  if (innerWidth < 1021) return { skipped: 'Desktop portrait check' };
  const image = document.querySelector('.hero-background');
  const panel = document.querySelector('.hero-copy');
  if (!image?.complete || !image.naturalWidth) throw new Error('Hero image not loaded');
  const box = image.getBoundingClientRect();
  const copy = panel.getBoundingClientRect();
  const scale = Math.max(box.width / image.naturalWidth, box.height / image.naturalHeight);
  const position = getComputedStyle(image).objectPosition.split(' ').map(parseFloat);
  const x = box.left + (box.width - image.naturalWidth * scale) * position[0] / 100;
  const y = box.top + (box.height - image.naturalHeight * scale) * position[1] / 100;
  // Conservative head/face bounds measured on the 1536 x 864 desktop source.
  const face = { left: x + 850 * scale, right: x + 1190 * scale, top: y, bottom: y + 330 * scale };
  if (face.top < box.top - 1 || face.bottom > box.bottom || face.left < box.left || face.right > box.right) {
    throw new Error('Portrait is cropped by the hero image container');
  }
  if (face.left < copy.right && face.right > copy.left && face.top < copy.bottom && face.bottom > copy.top) {
    throw new Error('Hero text panel overlaps the portrait');
  }
  return { passed: true, viewport: [innerWidth, innerHeight], heroHeight: box.height, faceBottom: face.bottom, panelTop: copy.top };
})()
