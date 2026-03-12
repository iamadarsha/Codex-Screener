import { WS_PRICES_URL } from "./constants";
import type { LivePrice } from "./api-types";

type PriceCallback = (price: LivePrice) => void;

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
      this.ws = new WebSocket(WS_PRICES_URL);

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
