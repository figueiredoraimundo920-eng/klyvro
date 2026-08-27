"use client";

import { useEffect } from "react";

export default function PwaRegister() {
  useEffect(() => {
    // O domínio padrão do GitHub Pages suporta HTTPS. Se o Pages não estiver
    // aplicando o redirect por configuração, fazemos isso no cliente antes
    // que recursos como microfone/WebRTC sejam usados.
    if (window.location.protocol === "http:" && window.location.hostname.endsWith(".github.io")) {
      const secureUrl = new URL(window.location.href);
      secureUrl.protocol = "https:";
      window.location.replace(secureUrl.toString());
      return;
    }

    // Durante o beta, evitar que um service worker antigo prenda amigos em builds diferentes.
    if ("serviceWorker" in navigator) {
      void navigator.serviceWorker.getRegistrations().then((registrations) => Promise.all(
        registrations
          .filter((registration) => registration.scope.includes("/klyvro/"))
          .map((registration) => registration.unregister()),
      )).catch(() => undefined);
    }
    if ("caches" in window) {
      void caches.keys().then((keys) => Promise.all(
        keys.filter((key) => key.startsWith("klyvro-")).map((key) => caches.delete(key)),
      )).catch(() => undefined);
    }
  }, []);
  return null;
}
