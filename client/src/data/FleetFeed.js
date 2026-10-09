import { Emitter } from '../util/emitter.js';

// Eventi: 'snapshot' (snapshot), 'status' ('connected' | 'disconnected').
export class FleetFeed extends Emitter {
  constructor({ wsUrl, retryMs }) {
    super();
    this.wsUrl = wsUrl;
    this.retryMs = retryMs;
    this.lastSnapshot = null;
  }

  start() {
    const ws = new WebSocket(this.wsUrl);
    ws.onopen = () => this.emit('status', 'connected');
    ws.onmessage = e => {
      this.lastSnapshot = JSON.parse(e.data);
      this.emit('snapshot', this.lastSnapshot);
    };
    ws.onclose = () => {
      this.emit('status', 'disconnected');
      setTimeout(() => this.start(), this.retryMs);
    };
  }
}
