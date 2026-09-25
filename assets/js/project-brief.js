(() => {
  const widgets = document.querySelectorAll('[data-project-brief]');

  widgets.forEach((widget) => {
    const form = widget.querySelector('[data-brief-form]');
    const steps = [...widget.querySelectorAll('[data-brief-step]')];
    const indicators = [...widget.querySelectorAll('[data-brief-indicator]')];
    const result = widget.querySelector('[data-brief-result]');
    const summaryOutput = widget.querySelector('[data-brief-summary]');
    const status = widget.querySelector('[data-brief-status]');
    const backButton = widget.querySelector('[data-brief-back]');
    const nextButton = widget.querySelector('[data-brief-next]');
    let currentStep = 0;

    if (!form || steps.length !== 3 || !result || !summaryOutput || !status || !backButton || !nextButton) return;

    widget.classList.add('project-brief--enhanced');

    const fieldValue = (name) => form.elements.namedItem(name)?.value.trim() || '';
    const makeSummary = () => [
      'Project brief',
      '',
      `Service: ${fieldValue('service')}`,
      `Project: ${fieldValue('project')}`,
      `Town or general location: ${fieldValue('location')}`,
      `Preferred timing: ${fieldValue('timing')}`,
      `Access or site details: ${fieldValue('access') || 'Not provided'}`,
      '',
      `Name: ${fieldValue('name')}`,
      `Reply email: ${fieldValue('replyEmail')}`,
    ].join('\n');

    const showStep = (index, shouldFocus = true) => {
      currentStep = index;
      steps.forEach((step, i) => { step.hidden = i !== index; });
      indicators.forEach((indicator, i) => {
        if (i === index) indicator.setAttribute('aria-current', 'step');
        else indicator.removeAttribute('aria-current');
      });
      backButton.hidden = index === 0;
      nextButton.textContent = index === steps.length - 1 ? 'Prepare brief' : 'Next step';
      status.textContent = '';
      if (shouldFocus) {
        steps[index].querySelector('input, select, textarea')?.focus();
      }
    };

    const validCurrentStep = () => {
      const invalid = [...steps[currentStep].querySelectorAll('input, select, textarea')]
        .find((field) => !field.checkValidity());
      if (!invalid) return true;
      invalid.reportValidity();
      invalid.focus();
      return false;
    };

    nextButton.addEventListener('click', () => {
      if (!validCurrentStep()) return;
      if (currentStep < steps.length - 1) {
        showStep(currentStep + 1);
        return;
      }
      summaryOutput.textContent = makeSummary();
      form.hidden = true;
      result.hidden = false;
      status.textContent = 'Your project brief is ready. Choose how to handle it.';
      widget.querySelector('[data-brief-email]')?.focus();
    });

    backButton.addEventListener('click', () => showStep(Math.max(0, currentStep - 1)));

    widget.querySelector('[data-brief-copy]')?.addEventListener('click', async () => {
      const summary = summaryOutput.textContent;
      try {
        if (!navigator.clipboard?.writeText) throw new Error('Clipboard access is unavailable.');
        await navigator.clipboard.writeText(summary);
        status.textContent = 'Brief copied to the clipboard.';
      } catch {
        const buffer = document.createElement('textarea');
        buffer.className = 'project-brief__copy-buffer';
        buffer.value = summary;
        buffer.setAttribute('readonly', '');
        widget.append(buffer);
        buffer.select();
        const copied = document.execCommand('copy');
        buffer.remove();
        status.textContent = copied ? 'Brief copied to the clipboard.' : 'Copy was not available. Select the brief text above to copy it.';
      }
    });

    widget.querySelector('[data-brief-download]')?.addEventListener('click', () => {
      const file = new Blob([summaryOutput.textContent], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(file);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'project-brief.txt';
      link.hidden = true;
      widget.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = 'The brief download was prepared on this device.';
    });

    widget.querySelector('[data-brief-email]')?.addEventListener('click', () => {
      const recipient = (widget.dataset.recipient || '').trim();
      if (!recipient || /@example\.invalid$/i.test(recipient)) {
        status.textContent = 'Replace the example email address in data/site.yaml before using email handoff.';
        return;
      }
      const subject = `Project inquiry: ${fieldValue('service')}`;
      const href = `mailto:${recipient}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(summaryOutput.textContent)}`;
      window.location.href = href;
      status.textContent = 'Your email app should open with the project brief. Review it before sending.';
    });

    widget.querySelector('[data-brief-reset]')?.addEventListener('click', () => {
      result.hidden = true;
      form.hidden = false;
      form.reset();
      showStep(0);
    });

    showStep(0, false);
  });
})();
