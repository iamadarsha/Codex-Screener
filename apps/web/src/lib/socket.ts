import { WS_PRICES_URL } from "./constants";
import type { LivePrice } from "./api-types";

type PriceCallback = (price: LivePrice) => void;

function resolveWsUrl(): string {
  // If the configured URL doesn't point to localhost, use it as-is (production config)
  if (!WS_PRICES_URL.includes("localhost") && !WS_PRICES_URL.includes("127.0.0.1")) {
    return WS_PRICES_URL;
  }
  // In production without an explicit WS URL, derive from the current page origin.
  // This requires the backend to be reachable at the same host (or a reverse proxy).
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL;
    if (wsUrl && !wsUrl.includes("localhost")) return `${wsUrl}/ws/prices`;
    // Last resort: same origin (only works if backend is co-located or proxied)
    return `${proto}//${window.location.host}/ws/prices`;
  }
  return WS_PRICES_URL;
}

class PriceSocket {
  private ws: WebSocket | null = null;
  private subscriptions = new Set<string>();
  private listeners = new Set<PriceCallback>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private isConnecting = false;

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) return;
    this.isConnecting = true;

    try {
      this.ws = new WebSocket(resolveWsUrl());

      this.ws.onopen = () => {
        this.isConnecting = false;
        this.reconnectDelay = 1000;

        if (this.subscriptions.size > 0) {
          this.ws?.send(
            JSON.stringify({ subscribe: Array.from(this.subscriptions) })
          );
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "price" && msg.data) {
            this.listeners.forEach((cb) => cb(msg.data));
          } else if (msg.symbol) {
            this.listeners.forEach((cb) => cb(msg as LivePrice));
          }
        } catch {
          // ignore malformed messages
        }
      };

      this.ws.onclose = () => {
        this.isConnecting = false;
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.isConnecting = false;
        this.ws?.close();
      };
    } catch {
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2,
        this.maxReconnectDelay
      );
      this.connect();
    }, this.reconnectDelay);
  }

  subscribe(symbols: string[]) {
    symbols.forEach((s) => this.subscriptions.add(s));
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ subscribe: symbols }));
    } else {
      this.connect();
    }
  }

  unsubscribe(symbols: string[]) {
    symbols.forEach((s) => this.subscriptions.delete(s));
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ unsubscribe: symbols }));
    }
  }

  onPrice(callback: PriceCallback): () => void {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
    this.isConnecting = false;
  }

  getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }
}

export const priceSocket = new PriceSocket();
