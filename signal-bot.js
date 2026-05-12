#!/usr/bin/env node
/**
 * Jarvis Crypto Signal Bot
 * MEXC Exchange — RSI + MACD Stratejisi
 * 
 * Kurulum: 
 *   1. MEXC'den API Key oluştur
 *   2. Şu env variable'ları ayarla:
 *      export MEXC_API_KEY="xxx"
 *      export MEXC_API_SECRET="xxx"
 *      export TELEGRAM_BOT_TOKEN="xxx"
 *      export TELEGRAM_CHAT_ID="988431816"
 *   3. Çalıştır: node signal-bot.js
 *   4. Otomatik çalışması için cron: 
 *      crontab -e → her 4 saatte bir çalışacak şekilde ayarla
 */

const ccxt = require('ccxt');

// === KONFİGÜRASYON ===
const CONFIG = {
  // Filtreleme
  MIN_VOLUME_USDT: 500000,     // Minimum 24h hacim ($500k)
  MAX_COINS_TO_SCAN: 40,       // En yüksek hacimli kaç coin taranacak
  MIN_PRICE: 0.000001,        // Minimum fiyat (küçük shitcoin'leri ele)
  
  // RSI Ayarları
  RSI_PERIOD: 14,
  RSI_OVERSOLD: 32,           // Aşırı satım (AL sinyali)
  RSI_OVERBOUGHT: 68,         // Aşırı alım (SAT sinyali)
  
  // MACD Ayarları
  MACD_FAST: 12,
  MACD_SLOW: 26,
  MACD_SIGNAL: 9,
  
  // Zaman aralığı
  TIMEFRAME: '4h',            // 4 saatlik mumlar (swing trade)
  
  // Risk
  MAX_SIGNAL_COUNT: 3,         // Tek seferde kaç sinyal gösterilecek
};

// === RSI HESAPLAMA ===
function calculateRSI(closes, period = 14) {
  if (closes.length < period + 1) return null;
  
  let gains = 0, losses = 0;
  for (let i = closes.length - period; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    if (diff > 0) gains += diff;
    else losses -= diff;
  }
  
  const avgGain = gains / period;
  const avgLoss = losses / period;
  
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - (100 / (1 + rs));
}

// === MACD HESAPLAMA ===
function calculateMACD(closes, fast = 12, slow = 26, signal = 9) {
  if (closes.length < slow + signal) return null;
  
  // EMA hesaplama
  function ema(data, period) {
    const multiplier = 2 / (period + 1);
    let result = [data[0]];
    for (let i = 1; i < data.length; i++) {
      result.push((data[i] - result[i - 1]) * multiplier + result[i - 1]);
    }
    return result;
  }
  
  const emaFast = ema(closes, fast);
  const emaSlow = ema(closes, slow);
  
  // MACD Line = EMA(fast) - EMA(slow)
  const macdLine = emaFast.map((v, i) => v - emaSlow[i]);
  
  // Signal Line = EMA(MACD Line)
  const signalLine = ema(macdLine.slice(slow - fast), signal);
  
  // Son değerler
  const lastMacd = macdLine[macdLine.length - 1];
  const lastSignal = signalLine[signalLine.length - 1];
  
  return {
    macd: lastMacd,
    signal: lastSignal,
    histogram: lastMacd - lastSignal,
    macdAboveSignal: lastMacd > lastSignal,
    prevMacd: macdLine[macdLine.length - 2],
    prevSignal: signalLine[signalLine.length - 2],
  };
}

// === ANA FONKSİYON ===
async function scanMarket() {
  console.log('🔍 Jarvis Signal Bot taramaya başlıyor...');
  console.log(`⏰ ${new Date().toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' })}`);
  console.log('─'.repeat(50));
  
  try {
    const exchange = new ccxt.mexc();
    exchange.enableRateLimit = true;
    
    // 1. Tüm marketleri çek
    const markets = await exchange.loadMarkets();
    const usdtMarkets = Object.values(markets).filter(m => 
      m.quote === 'USDT' && m.active && m.spot
    );
    
    // 2. 24h ticker verilerini çek
    const tickers = await exchange.fetchTickers();
    
    // 3. Hacme göre sırala
    const sortedByVolume = usdtMarkets
      .map(m => ({
        symbol: m.symbol,
        base: m.base,
        volume: tickers[m.symbol]?.quoteVolume || 0,
        price: tickers[m.symbol]?.last || 0,
      }))
      .filter(m => m.volume >= CONFIG.MIN_VOLUME_USDT && m.price >= CONFIG.MIN_PRICE)
      .sort((a, b) => b.volume - a.volume)
      .slice(0, CONFIG.MAX_COINS_TO_SCAN);
    
    console.log(`📊 ${sortedByVolume.length} coin taranıyor (hacim: $${CONFIG.MIN_VOLUME_USDT.toLocaleString()}+)`);
    console.log('─'.repeat(50));
    
    const signals = [];
    
    // 4. Her coin için teknik analiz yap
    for (const coin of sortedByVolume) {
      try {
        await new Promise(r => setTimeout(r, 200)); // Rate limit koruması
        
        const ohlcv = await exchange.fetchOHLCV(coin.symbol, CONFIG.TIMEFRAME, undefined, 50);
        const closes = ohlcv.map(c => c[4]);
        
        if (closes.length < 50) continue;
        
        const rsi = calculateRSI(closes, CONFIG.RSI_PERIOD);
        const macd = calculateMACD(closes, CONFIG.MACD_FAST, CONFIG.MACD_SLOW, CONFIG.MACD_SIGNAL);
        
        if (rsi === null || macd === null) continue;
        
        let signal = null;
        let reason = '';
        
        // AL SİNYALİ: RSI düşük + MACD yükseliyor
        if (rsi < CONFIG.RSI_OVERSOLD && macd.macdAboveSignal && !(macd.prevMacd > macd.prevSignal)) {
          signal = '🟢 AL';
          reason = `RSI(${rsi.toFixed(1)}) aşırı satım bölgesinde + MACD yukarı kesişim`;
        }
        
        // SAT SİNYALİ: RSI yüksek + MACD düşüyor
        else if (rsi > CONFIG.RSI_OVERBOUGHT && !macd.macdAboveSignal && macd.prevMacd > macd.prevSignal) {
          signal = '🔴 SAT';
          reason = `RSI(${rsi.toFixed(1)}) aşırı alım bölgesinde + MACD aşağı kesişim`;
        }
        
        // GÜÇLÜ AL: RSI çok düşük
        else if (rsi < 28) {
          signal = '🟢 GÜÇLÜ AL';
          reason = `RSI(${rsi.toFixed(1)}) çok düşük, aşırı satım`;
        }
        
        // GÜÇLÜ SAT: RSI çok yüksek
        else if (rsi > 72) {
          signal = '🔴 GÜÇLÜ SAT';
          reason = `RSI(${rsi.toFixed(1)}) çok yüksek, aşırı alım`;
        }
        
        // DİP ALANI: MACD yukarı dönüyor
        else if (!macd.macdAboveSignal && macd.macd > macd.prevMacd && rsi < 45) {
          signal = '🟡 DİP ALANI';
          reason = `MACD yukarı dönüş, RSI(${rsi.toFixed(1)}) orta-düşük`;
        }
        
        if (signal) {
          signals.push({
            symbol: coin.symbol.replace('/USDT', ''),
            signal,
            reason,
            price: coin.price,
            volume: coin.volume,
            rsi: rsi.toFixed(1),
          });
        }
        
      } catch (e) {
        // Sessiz geç
      }
    }
    
    // 5. Sinyalleri göster
    console.log('');  
    if (signals.length === 0) {
      console.log('😴 Şu anda anlamlı sinyal yok.');
      console.log('📡 Bir sonraki tarama 4 saat sonra.');
      
      // Özet bilgi
      const btcTicker = Object.values(markets).find(m => m.symbol === 'BTC/USDT');
      const ethTicker = Object.values(markets).find(m => m.symbol === 'ETH/USDT');
      if (btcTicker && tickers['BTC/USDT']) {
        console.log(`\n📈 BTC: $${tickers['BTC/USDT'].last?.toLocaleString() || '?'}`);
        console.log(`📈 ETH: $${tickers['ETH/USDT']?.last?.toLocaleString() || '?'}`);
      }
      
      return { signals: [] };
    }
    
    // Sinyalleri önem sırasına koy
    signals.sort((a, b) => {
      const order = { '🟢 GÜÇLÜ AL': 0, '🟢 AL': 1, '🟡 DİP ALANI': 2, '🔴 SAT': 3, '🔴 GÜÇLÜ SAT': 4 };
      return (order[a.signal] || 99) - (order[b.signal] || 99);
    });
    
    const topSignals = signals.slice(0, CONFIG.MAX_SIGNAL_COUNT);
    
    console.log(`🎯 ${topSignals.length} sinyal bulundu:\n`);
    
    topSignals.forEach((s, i) => {
      console.log(`#${i + 1} ${s.signal} — ${s.symbol}`);
      console.log(`   Fiyat: $${s.price.toFixed(8)}`);
      console.log(`   RSI: ${s.rsi} | Hacim: $${(s.volume / 1000000).toFixed(1)}M`);
      console.log(`   Sebep: ${s.reason}`);
      console.log('');
    });
    
    console.log('📡 Bir sonraki tarama 4 saat sonra.');
    
    return { signals: topSignals };
    
  } catch (error) {
    console.error('❌ Hata:', error.message);
    return { signals: [], error: error.message };
  }
}

// === ÇALIŞTIR ===
scanMarket().then(result => {
  if (result.signals.length > 0) {
    console.log('─'.repeat(50));
    console.log('🤖 Jarvis Signal Bot — Hazır');
    console.log('📊 Orta risk · $100 bütçe · MEXC');
    
    // Öneri
    console.log('\n💡 Öneri:');
    console.log('• Her sinyal için max $30-40 ayır');
    console.log('• Take-profit: %5-8 | Stop-loss: %3-5');
    console.log('• Aynı anda en fazla 2-3 pozisyon');
    console.log('• Sinyal alındıktan sonra 4 saat içinde işlem aç');
  }
  process.exit(0);
}).catch(e => {
  console.error('Fatal:', e.message);
  process.exit(1);
});
