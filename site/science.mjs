// Live geometry and bounded display-grid thresholding. Heavy focusing stays offline.
export function geometry(angleDeg, altitudeM = 1000, bandwidthHz = 40e6) {
  if (!Number.isFinite(angleDeg) || angleDeg <= 0 || angleDeg >= 90) throw new Error('Incidence must be between 0 and 90 degrees.');
  const theta = angleDeg * Math.PI / 180;
  const slantWidthM = 0.886 * 299792458 / (2 * bandwidthHz);
  return { groundM: altitudeM * Math.tan(theta), slantM: altitudeM / Math.cos(theta), slantWidthM, groundWidthM: slantWidthM / Math.sin(theta) };
}

export function thresholdMask(db, valid, thresholdDb) {
  let candidates = 0, validCount = 0;
  const mask = db.map((row, y) => row.map((value, x) => {
    if (!valid[y][x]) return -1;
    validCount++;
    const water = value < thresholdDb;
    if (water) candidates++;
    return water ? 1 : 0;
  }));
  if (!validCount) throw new Error('Display grid contains no valid samples.');
  return { mask, fraction: candidates / validCount };
}
