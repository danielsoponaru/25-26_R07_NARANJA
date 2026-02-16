(() => {
  const container = document.getElementById("aurora");
  if (!container) return;

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  container.appendChild(canvas);

  let viewWidth = 0;
  let viewHeight = 0;

  const resize = () => {
    const dpr = window.devicePixelRatio || 1;
    viewWidth = container.clientWidth;
    viewHeight = container.clientHeight;
    canvas.width = viewWidth * dpr;
    canvas.height = viewHeight * dpr;
    canvas.style.width = `${viewWidth}px`;
    canvas.style.height = `${viewHeight}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };

  const hexToRgba = (hex, alpha) => {
    const clean = hex.replace("#", "");
    const r = parseInt(clean.substring(0, 2), 16);
    const g = parseInt(clean.substring(2, 4), 16);
    const b = parseInt(clean.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  };

  const glowLayers = [
    { color: "#910451", alpha: 0.45, radius: 0.85, speed: 0.00025, offset: 0.0 },
    { color: "#5227FF", alpha: 0.38, radius: 0.75, speed: 0.00032, offset: 1.4 },
    { color: "#abc339", alpha: 0.35, radius: 0.7, speed: 0.00028, offset: 2.8 },
  ];

  const bands = [
    { color: "#5227FF", alpha: 0.35, amplitude: 0.09, speed: 0.0006, offset: 0.0 },
    { color: "#910451", alpha: 0.32, amplitude: 0.08, speed: 0.0005, offset: 1.6 },
    { color: "#abc339", alpha: 0.3, amplitude: 0.07, speed: 0.00045, offset: 2.8 },
  ];

  let lastFrame = 0;

  const draw = (time) => {
    requestAnimationFrame(draw);
    if (time - lastFrame < 33) return;
    lastFrame = time;

    if (!viewWidth || !viewHeight) return;
    ctx.clearRect(0, 0, viewWidth, viewHeight);

    ctx.globalCompositeOperation = "screen";

    glowLayers.forEach((layer, index) => {
      const cx =
        viewWidth * (0.5 + 0.25 * Math.sin(time * layer.speed + layer.offset + index));
      const cy =
        viewHeight * (0.35 + 0.22 * Math.cos(time * layer.speed * 1.3 + index));
      const radius = Math.max(viewWidth, viewHeight) * layer.radius;
      const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
      gradient.addColorStop(0, hexToRgba(layer.color, layer.alpha));
      gradient.addColorStop(0.6, hexToRgba(layer.color, layer.alpha * 0.25));
      gradient.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, viewWidth, viewHeight);
    });

    bands.forEach((band, index) => {
      const baseY = viewHeight * (0.32 + index * 0.12);
      const amplitude = viewHeight * band.amplitude;
      ctx.beginPath();
      ctx.moveTo(0, viewHeight);
      const step = Math.max(20, viewWidth / 70);
      for (let x = 0; x <= viewWidth; x += step) {
        const phase = (x / viewWidth) * Math.PI * 2;
        const y =
          baseY +
          Math.sin(phase + time * band.speed + band.offset) * amplitude +
          Math.sin(phase * 2 + time * band.speed * 0.7) * (amplitude * 0.35);
        ctx.lineTo(x, y);
      }
      ctx.lineTo(viewWidth, viewHeight);
      ctx.closePath();

      const bandGradient = ctx.createLinearGradient(0, baseY - amplitude, 0, viewHeight);
      bandGradient.addColorStop(0, hexToRgba(band.color, band.alpha));
      bandGradient.addColorStop(0.6, "rgba(0,0,0,0)");
      ctx.fillStyle = bandGradient;
      ctx.fill();
    });

    ctx.globalCompositeOperation = "source-over";
  };

  window.addEventListener("resize", resize);
  resize();
  requestAnimationFrame(draw);
})();
