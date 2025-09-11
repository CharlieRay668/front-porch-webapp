function fmtHour(h) {
  const t = ((h - 1) % 12) + 1;
  const suffix = h < 12 ? 'AM' : 'PM';
  return `${t} ${suffix}`;
}

function openModal(day, hour, maxPeople = 4) {
  const modal = document.getElementById('modal');
  const title = document.getElementById('modal-title');
  const subtitle = document.getElementById('modal-subtitle');
  const fd = document.getElementById('form-day');
  const fh = document.getElementById('form-hour');
  const pc = document.getElementById('people-count');

  fd.value = day;
  fh.value = hour;
  title.textContent = `Sign up for ${day}`;
  subtitle.textContent = `${fmtHour(hour)}`;

  // Limit people options to remaining capacity
  for (const opt of pc.options) opt.disabled = false;
  for (let v = 4; v > maxPeople; v--) {
    const opt = [...pc.options].find(o => parseInt(o.value, 10) === v);
    if (opt) opt.disabled = true;
  }
  if (parseInt(pc.value, 10) > maxPeople) pc.value = String(maxPeople);

  renderPeopleFields();
  modal.classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal').classList.add('hidden');
}

function renderPeopleFields() {
  const container = document.getElementById('people-fields');
  const count = parseInt(document.getElementById('people-count').value, 10);
  container.innerHTML = '';
  for (let i = 1; i <= count; i++) {
    const row = document.createElement('div');
    row.className = 'people-row';
    row.innerHTML = `
      <div class="field inline">
        <label for="first_name_${i}">Person ${i} First Name</label>
        <input type="text" id="first_name_${i}" name="first_name_${i}" required />
      </div>
      <div class="field inline">
        <label for="last_name_${i}">Person ${i} Last Name</label>
        <input type="text" id="last_name_${i}" name="last_name_${i}" required />
      </div>
    `;
    container.appendChild(row);
  }
}

function attachHandlers() {
  const grid = document.getElementById('signup-grid');
  grid.addEventListener('click', (e) => {
    const btn = e.target.closest('button.slot');
    if (!btn) return;
    if (btn.getAttribute('aria-disabled') === 'true') return;
    const available = btn.dataset.available === 'true';
    const remaining = parseInt(btn.dataset.remaining || '0', 10);
    if (!available || remaining <= 0) return;
    const day = btn.dataset.day;
    const hour = parseInt(btn.dataset.hour, 10);
    openModal(day, hour, Math.min(4, remaining));
  });

  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('modal-cancel').addEventListener('click', closeModal);
  document.getElementById('people-count').addEventListener('change', renderPeopleFields);
}

window.addEventListener('DOMContentLoaded', () => {
  attachHandlers();
  renderPeopleFields(); // ensure initial render
});
