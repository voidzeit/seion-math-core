const controls = {
  massFlow: document.querySelector('#mass-flow'),
  exhaustVelocity: document.querySelector('#exhaust-velocity'),
  efficiency: document.querySelector('#efficiency')
};

const output = {
  massFlow: document.querySelector('#mass-flow-value'),
  exhaustVelocity: document.querySelector('#exhaust-velocity-value'),
  efficiency: document.querySelector('#efficiency-value'),
  thrust: document.querySelector('#thrust-output'),
  jetPower: document.querySelector('#jet-power-output'),
  isp: document.querySelector('#isp-output'),
  efficiencyBar: document.querySelector('#efficiency-bar'),
  efficiencyReadout: document.querySelector('#efficiency-readout')
};

const formatNumber = (value, digits = 1) => new Intl.NumberFormat('es-ES', {
  minimumFractionDigits: digits,
  maximumFractionDigits: digits
}).format(value);

function updateProgress(input) {
  const ratio = ((input.value - input.min) / (input.max - input.min)) * 100;
  input.style.setProperty('--progress', `${ratio}%`);
}

function updateModel() {
  const massFlowMgS = Number(controls.massFlow.value);
  const exhaustVelocityKmS = Number(controls.exhaustVelocity.value);
  const efficiency = Number(controls.efficiency.value);

  // Relaciones ideales de primer orden: empuje = flujo másico × velocidad de escape.
  const massFlowKgS = massFlowMgS / 1e6;
  const exhaustVelocityMS = exhaustVelocityKmS * 1000;
  const thrustMn = massFlowKgS * exhaustVelocityMS * 1000;
  const jetPowerW = 0.5 * massFlowKgS * (exhaustVelocityMS ** 2);
  const ispS = exhaustVelocityMS / 9.80665;

  output.massFlow.textContent = formatNumber(massFlowMgS, 2);
  output.exhaustVelocity.textContent = formatNumber(exhaustVelocityKmS, 1);
  output.efficiency.textContent = formatNumber(efficiency, 0);
  output.thrust.textContent = formatNumber(thrustMn, 1);
  output.jetPower.textContent = formatNumber(jetPowerW, 1);
  output.isp.textContent = Math.round(ispS).toLocaleString('es-ES');
  output.efficiencyBar.style.width = `${efficiency}%`;
  output.efficiencyReadout.textContent = `${efficiency}%`;

  Object.values(controls).forEach(updateProgress);
}

Object.values(controls).forEach((control) => control.addEventListener('input', updateModel));
updateModel();
