/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./App.{js,jsx,ts,tsx}",
    "./src/**/*.{js,jsx,ts,tsx}",
    "./screens/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Spor24 Ana Marka & Arka Plan Paleti
        spor24: {
          bg: '#0B0E14',          // En derin zemin (Canvas Black)
          surface: '#10131A',     // Kart ve App Bar zemini
          elevated: '#141822',    // İkincil yükseltilmiş kartlar
          card: '#121620',        // İçerik ve federasyon kartları
          border: '#1E232E',      // Standart çizgi ve ayraçlar
          borderLight: '#262B36', // Vurgulu kart kenarlıkları
          crimson: '#E11D48',     // Spor24 Kırmızı Marka Rengi (Primary)
          crimsonDark: '#BE123C', // Koyu kırmızı aksan
          gold: '#FFD700',        // 👁 Okunma ve VIP rozet rengi
          verified: '#10B981',    // 🛡 Dijital Mühür & Canlı veri yeşili
          sky: '#38BDF8',         // SHA-256 Hash ve dış bağlantı mavisi
        },
        // Metin & İkincil Renk Skalası
        text: {
          primary: '#FFFFFF',
          secondary: '#CBD5E1',
          muted: '#94A3B8',
          subtle: '#64748B',
        },
      },
      fontFamily: {
        outfit: ['Outfit', 'sans-serif'],
        mono: ['Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
};
