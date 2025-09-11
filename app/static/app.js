function fmtHour(h) {
  const t = ((h - 1) % 12) + 1;
  const suffix = h < 12 ? 'AM' : 'PM';
  return `${t} ${suffix}`;
}

function openModal(day, hour) {
  const modal = document.getElementById('modal');
  const title = document.getElementById('modal-title');
  const subtitle = document.getElementById('modal-subtitle');
  const fd = document.getElementById('form-day');
  const fh = document.getElementById('form-hour');

  fd.value = day;
  fh.value = hour;
  title.textContent = `Sign up for ${day}`;
  subtitle.textContent = `${fmtHour(hour)}`;

  modal.classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal').classList.add('hidden');
}

function openDeleteModal(signupId, day, hour) {
  const modal = document.getElementById('delete-modal');
  document.getElementById('delete-signup-id').value = signupId;
  document.getElementById('delete-subtitle').textContent = `${day} • ${fmtHour(hour)}`;
  modal.classList.remove('hidden');
}

function closeDeleteModal() {
  document.getElementById('delete-modal').classList.add('hidden');
}

function attachHandlers() {
  const grid = document.getElementById('signup-grid');
  grid.addEventListener('click', (e) => {
    const btn = e.target.closest('button.slot');
    if (btn) {
      if (btn.getAttribute('aria-disabled') === 'true') return;
      const available = btn.dataset.available === 'true';
      const remaining = parseInt(btn.dataset.remaining || '0', 10);
      if (!available || remaining <= 0) return;
      const day = btn.dataset.day;
      const hour = parseInt(btn.dataset.hour, 10);
      openModal(day, hour);
      return;
    }

    const delBtn = e.target.closest('button.delete-signup');
    if (delBtn) {
      const signupId = parseInt(delBtn.dataset.signupId, 10);
      const day = delBtn.dataset.day;
      const hour = parseInt(delBtn.dataset.hour, 10);
      openDeleteModal(signupId, day, hour);
    }
  });

  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('modal-cancel').addEventListener('click', closeModal);

  document.getElementById('delete-close').addEventListener('click', closeDeleteModal);
  document.getElementById('delete-cancel').addEventListener('click', closeDeleteModal);

  // Intercept delete form submit to avoid navigating to an error page
  const deleteForm = document.getElementById('delete-form');
  deleteForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(deleteForm);
    try {
      const res = await fetch('/signup/delete', {
        method: 'POST',
        body: fd,
      });
      if (res.ok) {
        // Success (Redirect handled by server); reload UI
        window.location.reload();
        return;
      }
      if (res.status === 403) {
        closeDeleteModal();
        alert('Not allowed: wrong password.');
        return;
      }
      closeDeleteModal();
      alert('Error deleting signup. Please try again.');
    } catch (err) {
      closeDeleteModal();
      alert('Network error. Please try again.');
    }
  });
}

window.addEventListener('DOMContentLoaded', attachHandlers);
