// Офлайн-режим путеводителя. Страница и данные всегда берутся из сети (кэш — только без интернета),
// фото и куски карты — из кэша, если уже сохранены.
const VERSION = 'cyprus-v6';
const CORE = [
  './', 'index.html', 'data1.js', 'data2.js', 'data3.js', 'routes.js', 'photos.js', 'manifest.webmanifest',
  'img/cape_greco.jpg', 'img/kourion.jpg', 'img/larnaca.jpg', 'img/hala_sultan_tekke.jpg',
  'img/ayia_napa.jpg', 'img/nicosia.jpg', 'img/icon-192.png',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
];
const TILES = 'cyprus-tiles-v2'; // v1 содержал заглушки CARTO «API KEY REQUIRED»
const MAX_TILES = 1500;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => Promise.all(CORE.map(u => c.add(new Request(u, { cache: 'reload' })).catch(() => {})))));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(k => k !== VERSION && k !== TILES).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

async function trim(cache) {
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - MAX_TILES; i++) await cache.delete(keys[i]);
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // куски карты: сначала кэш, потом сеть
  if (url.hostname.endsWith('tile.openstreetmap.org') || url.hostname.endsWith('basemaps.cartocdn.com')) {
    e.respondWith(caches.open(TILES).then(async c => {
      const hit = await c.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok || res.type === 'opaque') { c.put(req, res.clone()); trim(c); }
      return res;
    }));
    return;
  }

  // Википедия API — сеть, при офлайне последний ответ
  if (url.hostname.endsWith('wikipedia.org')) {
    e.respondWith(fetch(req).then(res => {
      const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); return res;
    }).catch(() => caches.match(req)));
    return;
  }

  // свои страница, данные и скрипты: сначала сеть (в обход HTTP-кэша), без интернета — кэш
  const own = url.origin === location.origin && (req.mode === 'navigate' || /\.(html|js|webmanifest)$|\/$/.test(url.pathname));
  if (own) {
    e.respondWith(fetch(req, { cache: 'no-cache' }).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true })));
    return;
  }

  // остальное (фото, шрифты, Leaflet): из кэша, обновляем в фоне
  e.respondWith(caches.open(VERSION).then(async c => {
    const hit = await c.match(req, { ignoreSearch: url.origin === location.origin });
    const net = fetch(req).then(res => {
      // непрозрачные ответы с Wikimedia не храним: за ними может прятаться ошибка 429
      if (res.ok || (res.type === 'opaque' && !url.hostname.endsWith('wikimedia.org'))) c.put(req, res.clone());
      return res;
    }).catch(() => hit);
    return hit || net;
  }));
});
