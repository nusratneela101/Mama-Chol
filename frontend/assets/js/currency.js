// MAMA CHOL VPN — Currency Conversion Module

const BASE_PRICES = {
  basic:    { USD: 4.99,  BDT: 70,  CNY: 9.90,  INR: 99  },
  standard: { USD: 9.99,  BDT: 180, CNY: 19.90, INR: 199 },
  premium:  { USD: 14.99, BDT: 300, CNY: 29.90, INR: 349 }
};

const CURRENCY_SYMBOLS = {
  USD: '$', BDT: '৳', CNY: '¥', INR: '₹',
  EUR: '€', GBP: '£', JPY: '¥', BTC: '₿',
  ETH: 'Ξ', USDT: '₮'
};

const CURRENCY_NAMES = {
  USD: 'US Dollar', BDT: 'Bangladeshi Taka',
  CNY: 'Chinese Yuan', INR: 'Indian Rupee',
  EUR: 'Euro', GBP: 'British Pound', JPY: 'Japanese Yen',
  BTC: 'Bitcoin', ETH: 'Ethereum', USDT: 'Tether USDT'
};

// Fallback exchange rates (relative to USD)
const FALLBACK_RATES = {
  USD: 1, BDT: 110, CNY: 7.24, INR: 83.5,
  EUR: 0.92, GBP: 0.79, JPY: 149.5,
  BTC: 0.000024, ETH: 0.00038, USDT: 1
};

const CACHE_KEY = 'mamachol_exchange_rates';
const CACHE_DURATION = 3600000; // 1 hour in ms

class CurrencyConverter {
  constructor() {
    this.rates = null;
    this.currentCurrency = localStorage.getItem('mamachol_currency') || 'BDT';
    this.init();
  }

  async init() {
    await this.loadRates();
    this.updateAllPrices();
    this.setupSelectors();
  }

  async loadRates() {
    // Check cache
    const cached = this.getCachedRates();
    if (cached) { this.rates = cached; return; }

    try {
      // Try free exchange rate API
      const res = await fetch('https://open.er-api.com/v6/latest/USD', {
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) {
        const data = await res.json();
        if (data.result === 'success') {
          this.rates = data.rates;
          this.cacheRates(data.rates);
          return;
        }
      }
    } catch (e) {
      console.warn('Currency API unavailable, using fallback rates');
    }

    // Use fallback rates
    this.rates = FALLBACK_RATES;
  }

  getCachedRates() {
    try {
      const raw = localStorage.getItem(CACHE_KEY);
      if (!raw) return null;
      const { rates, timestamp } = JSON.parse(raw);
      if (Date.now() - timestamp < CACHE_DURATION) return rates;
    } catch(e) {}
    return null;
  }

  cacheRates(rates) {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({ rates, timestamp: Date.now() }));
    } catch(e) {}
  }

  convert(usdAmount, toCurrency) {
    if (!this.rates) return usdAmount;
    const rate = this.rates[toCurrency] || FALLBACK_RATES[toCurrency] || 1;
    return usdAmount * rate;
  }

  formatPrice(amount, currency) {
    const symbol = CURRENCY_SYMBOLS[currency] || currency;
    if (['BTC', 'ETH'].includes(currency)) {
      return `${symbol}${amount.toFixed(6)}`;
    }
    if (currency === 'JPY') {
      return `${symbol}${Math.round(amount).toLocaleString()}`;
    }
    if (['BDT', 'INR'].includes(currency)) {
      return `${symbol}${Math.round(amount).toLocaleString()}`;
    }
    return `${symbol}${amount.toFixed(2)}`;
  }

  getPlanPrice(plan, currency) {
    // Use fixed prices for main currencies to avoid floating point issues
    if (BASE_PRICES[plan] && BASE_PRICES[plan][currency] !== undefined) {
      return this.formatPrice(BASE_PRICES[plan][currency], currency);
    }
    // Convert from USD for other currencies
    const usdPrice = BASE_PRICES[plan]?.USD || 0;
    const converted = this.convert(usdPrice, currency);
    return this.formatPrice(converted, currency);
  }

  updateAllPrices() {
    const currency = this.currentCurrency;
    // Update all price display elements
    document.querySelectorAll('[data-plan-price]').forEach(el => {
      const plan = el.dataset.planPrice;
      if (BASE_PRICES[plan]) {
        el.textContent = this.getPlanPrice(plan, currency);
      }
    });
    // Update currency labels
    document.querySelectorAll('[data-currency-name]').forEach(el => {
      el.textContent = CURRENCY_NAMES[currency] || currency;
    });
  }

  setupSelectors() {
    document.querySelectorAll('.currency-selector').forEach(sel => {
      sel.value = this.currentCurrency;
      sel.addEventListener('change', (e) => {
        this.currentCurrency = e.target.value;
        localStorage.setItem('mamachol_currency', this.currentCurrency);
        // Sync all selectors
        document.querySelectorAll('.currency-selector').forEach(s => s.value = this.currentCurrency);
        this.updateAllPrices();
      });
    });
  }

  setCurrency(currency) {
    this.currentCurrency = currency;
    localStorage.setItem('mamachol_currency', currency);
    document.querySelectorAll('.currency-selector').forEach(s => s.value = currency);
    this.updateAllPrices();
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.currencyConverter = new CurrencyConverter();
});

window.CURRENCY_SYMBOLS = CURRENCY_SYMBOLS;
window.BASE_PRICES = BASE_PRICES;
