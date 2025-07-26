'use client';

import { useState, useEffect } from 'react';

interface Metrics {
  total: number;
  throughput: number;
  avgLatency: number;
  avgAccuracy: number;
  timestamp: number;
}

export default function FloatingDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    // Replace with actual WebSocket endpoint after deployment
    const wsEndpoint = process.env.NEXT_PUBLIC_WS_ENDPOINT || 'wss://hsdtkjqsub.execute-api.us-east-1.amazonaws.com/dev';
    
    const connectWebSocket = () => {
      console.log('Connecting to WebSocket:', wsEndpoint);
      const ws = new WebSocket(wsEndpoint);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        
        // Request current metrics after connection is established
        setTimeout(() => {
          const requestMessage = JSON.stringify({ action: 'get-metrics' });
          ws.send(requestMessage);
          console.log('Requested current metrics');
        }, 100); // Small delay to ensure connection is fully ready
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('Received message:', message);
          
          if (message.type === 'metrics-update') {
            setMetrics(message.data);
            setLastUpdate(new Date());
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event);
        setConnectionStatus('disconnected');
        
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

      return ws;
    };

    const websocket = connectWebSocket();

    return () => {
      websocket.close();
    };
  }, []);

  const formatValue = (val: number) => {
    if (val === 0) return '0';
    if (val < 1) return val.toFixed(2);
    if (val < 100) return val.toFixed(1);
    return Math.round(val).toString();
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'disconnected': return 'text-red-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusDot = () => {
    switch (connectionStatus) {
      case 'connected': return '🟢';
      case 'connecting': return '🟡';
      case 'disconnected': return '🔴';
      case 'error': return '🔴';
      default: return '⚪';
    }
  };

  if (isMinimized) {
    return (
      <div 
        className="fixed bottom-4 right-4 bg-white shadow-lg rounded-lg p-2 cursor-pointer hover:shadow-xl transition-shadow z-50 border border-gray-200"
        onClick={() => setIsMinimized(false)}
        title="Click to expand dashboard"
      >
        <div className="flex items-center gap-1 text-sm">
          <span>📊</span>
          <span className={getStatusColor()}>{getStatusDot()}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white shadow-lg rounded-lg p-3 z-50 border border-gray-200 min-w-64">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">📊 Dashboard</span>
          <span className={`text-xs ${getStatusColor()}`}>
            {getStatusDot()}
          </span>
        </div>
        <button 
          onClick={() => setIsMinimized(true)}
          className="text-gray-400 hover:text-gray-600 text-sm"
          title="Minimize"
        >
          −
        </button>
      </div>

      {/* Metrics */}
      {connectionStatus === 'connected' && metrics ? (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-blue-50 p-2 rounded">
            <div className="text-blue-600 font-medium">Total</div>
            <div className="text-blue-800 font-bold">{metrics.total}</div>
          </div>
          <div className="bg-green-50 p-2 rounded">
            <div className="text-green-600 font-medium">Speed</div>
            <div className="text-green-800 font-bold">{formatValue(metrics.avgLatency)}ms</div>
          </div>
          <div className="bg-purple-50 p-2 rounded">
            <div className="text-purple-600 font-medium">Rate</div>
            <div className="text-purple-800 font-bold">{formatValue(metrics.throughput)}/s</div>
          </div>
          <div className="bg-orange-50 p-2 rounded">
            <div className="text-orange-600 font-medium">Quality</div>
            <div className="text-orange-800 font-bold">{formatValue(metrics.avgAccuracy)}%</div>
          </div>
        </div>
      ) : (
        <div className="text-center py-4">
          {connectionStatus === 'connecting' && (
            <div className="text-gray-500 text-sm">
              <div className="animate-pulse">Connecting...</div>
            </div>
          )}
          {connectionStatus === 'connected' && !metrics && (
            <div className="text-gray-500 text-sm">
              <div>Waiting for data...</div>
              <div className="text-xs mt-1">Process some invoices to see metrics</div>
            </div>
          )}
          {connectionStatus === 'disconnected' && (
            <div className="text-red-500 text-sm">
              <div>Disconnected</div>
              <div className="text-xs mt-1">Reconnecting...</div>
            </div>
          )}
          {connectionStatus === 'error' && (
            <div className="text-red-500 text-sm">
              <div>Connection Error</div>
              <div className="text-xs mt-1">Check configuration</div>
            </div>
          )}
        </div>
      )}

      {/* Last Update */}
      {lastUpdate && (
        <div className="text-xs text-gray-400 mt-2 text-center">
          Updated {lastUpdate.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
} 