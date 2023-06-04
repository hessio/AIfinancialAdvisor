const title_items = document.querySelectorAll('#capitalised');

// Loop through each element and update its text content
title_items.forEach(element => {
  const text = element.innerText.trim();

  const newText = text.charAt(0).toUpperCase() + text.slice(1);
  element.textContent = newText;
});

