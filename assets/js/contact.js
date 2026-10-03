const form = document.querySelector('.contact-form');
if (form && form.dataset.enabled === 'true') {
  const status = document.getElementById('form-status');
  const error = document.getElementById('form-error');
  const button = form.querySelector('button');
  const messages = {
    INVALID_SUBMISSION: 'Some details could not be accepted. Check the fields and their length before trying again.',
    WRONG_ORIGIN: 'Please open the contact form on this website and try again.',
    PAYLOAD_TOO_LARGE: 'Your message is too long. Shorten it before trying again.',
    RATE_LIMITED: 'Please wait ten minutes before sending another enquiry.',
    INTAKE_DISABLED: 'This website is not accepting enquiries through this form. Use the listed contact details.',
    DELIVERY_UNCONFIRMED: 'Delivery could not be confirmed. Please try again later or use the listed contact details.',
  };
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (button.disabled || !form.reportValidity()) return;
    button.disabled = true;
    error.hidden = true;
    status.textContent = 'Sending your enquiry…';
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(form.action, {
        method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded', Accept: 'application/json'},
        body: new URLSearchParams(new FormData(form)).toString(), signal: controller.signal,
      });
      const result = await response.json().catch(() => null);
      if (!response.ok || result?.ok !== true) {
        const failure = new Error('Not accepted');
        failure.code = result?.code;
        throw failure;
      }
      status.textContent = 'Thank you. Your enquiry has been received.';
      status.focus();
      form.reset();
    } catch (failure) {
      status.textContent = '';
      error.textContent = (messages[failure.code] || 'We could not confirm delivery. Check your connection; if the request timed out, it may already have arrived.') + ' Your message is still here.';
      error.hidden = false;
      error.focus();
    } finally {
      clearTimeout(timer);
      button.disabled = false;
    }
  });
}
