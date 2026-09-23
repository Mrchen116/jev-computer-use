() => ({
  url: location.href,
  title: document.title,
  fields: [...document.querySelectorAll('input,textarea,select')]
    .filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden')
    .map(e => ({
      id: e.id,
      name: e.name,
      type: e.type,
      placeholder: e.placeholder,
      value: e.value,
      selected_label: e.selectedOptions?.[0]?.textContent,
      readonly: !!e.readOnly,
      disabled: !!e.disabled,
      row: e.closest('tr')?.rowIndex,
      headers: e.closest('table')?.querySelector('thead')?.innerText,
      near: e.closest('tr')?.innerText || e.parentElement.innerText.slice(0, 100)
    })),
  text: document.querySelector('#invNumber')?.closest('ul')?.parentElement.innerText
    || document.body.innerText.slice(0, 8000)
})
