/* Runs before first paint so the saved (or system) theme applies without a flash. Same logic as the prototype. */
try {
  var t = localStorage.getItem('sf-theme');
  if (t) document.documentElement.dataset.theme = t;
  else if (matchMedia('(prefers-color-scheme: dark)').matches) document.documentElement.dataset.theme = 'dark';
} catch (e) {}
