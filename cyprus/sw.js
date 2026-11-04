// Офлайн-режим путеводителя: страница, данные и фото кэшируются при первом открытии,
// фото из Википедии и куски карты — по мере просмотра.
const VERSION = 'cyprus-v2';
const CORE = [
  './', 'index.html', 'data1.js', 'data2.js', 'data3.js', 'routes.js', 'photos.js', 'manifest.webmanifest',
  'img/cape_greco.jpg', 'img/kourion.jpg', 'img/larnaca.jpg', 'img/hala_sultan_tekke.jpg',
  'img/ayia_napa.jpg', 'img/nicosia.jpg', 'img/icon-192.png',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
];
const TILES = 'cyprus-tiles';
const MAX_TILES = 1500;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => Promise.all(CORE.map(u => c.add(u).catch(() => {})))));
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
  if (url.hostname.endsWith('tile.openstreetmap.org')) {
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

  // всё остальное (страница, данные, фото, шрифты, Leaflet): отдаём из кэша и обновляем в фоне
  e.respondWith(caches.open(VERSION).then(async c => {
    const hit = await c.match(req, { ignoreSearch: url.origin === location.origin });
    const net = fetch(req).then(res => {
      if (res.ok || res.type === 'opaque') c.put(req, res.clone());
      return res;
    }).catch(() => hit);
    return hit || net;
  }));
});
