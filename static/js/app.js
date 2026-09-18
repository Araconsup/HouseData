/**
 * HOUSEDATA - Global Client Utilities
 */

const PERSIAN_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];

function toPersianDigits(num) {
  if (num === null || num === undefined) return '';
  return num.toString().replace(/\d/g, d => PERSIAN_DIGITS[d]);
}

function formatToman(amount, usePersian = true) {
  if (!amount || amount === 0) return 'توافقی';
  amount = Math.round(amount);

  let formatted = '';
  if (amount >= 1_000_000_000) {
    const val = (amount / 1_000_000_000).toFixed(2).replace(/\.?0+$/, '');
    formatted = `${val} میلیارد تومان`;
  } else if (amount >= 1_000_000) {
    const val = (amount / 1_000_000).toFixed(1).replace(/\.?0+$/, '');
    formatted = `${val} میلیون تومان`;
  } else if (amount >= 1_000) {
    formatted = `${Math.round(amount / 1_000)} هزار تومان`;
  } else {
    formatted = `${amount.toLocaleString('fa-IR')} تومان`;
  }

  if (usePersian) {
    return toPersianDigits(formatted).replace('.', '٫');
  }
  return formatted;
}

// Register PWA Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
      .then((reg) => console.log('[PWA] Service Worker registered:', reg.scope))
      .catch((err) => console.warn('[PWA] Service Worker registration error:', err));
  });
}

if (window.Chart) {
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = 'Vazirmatn, sans-serif';
  Chart.defaults.plugins.legend.labels.color = '#cbd5e1';
  Chart.defaults.scale.grid = {
    color: 'rgba(255, 255, 255, 0.06)',
  };
}
