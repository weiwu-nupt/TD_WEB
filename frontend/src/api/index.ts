import axios from 'axios'

// ����axiosʵ��
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// ����������
apiClient.interceptors.request.use(
  (config) => {
    // �ڷ�������֮ǰ��Щʲô
    console.log('��������:', config)
    return config
  },
  (error) => {
    console.error('�������:', error)
    return Promise.reject(error)
  }
)

// ��Ӧ������
apiClient.interceptors.response.use(
  (response) => {
    console.log('��Ӧ����:', response)
    return response.data
  },
  (error) => {
    console.error('��Ӧ����:', error)
    // ͳһ������
    if (error.response) {
      switch (error.response.status) {
        case 401:
          console.error('δ��Ȩ����')
          break
        case 403:
          console.error('��ֹ����')
          break
        case 404:
          console.error('������Դ������')
          break
        case 500:
          console.error('�������ڲ�����')
          break
        default:
          console.error(`����״̬��: ${error.response.status}`)
      }
    }
    return Promise.reject(error)
  }
)

// �����������API
export const parameterAPI = {
  // ��ȡ��������
  getParameters: (channelType: string) => 
    apiClient.get(`/parameters/${channelType}`),
  
  // ���²�������
  updateParameters: (channelType: string, params: any) => 
    apiClient.put(`/parameters/${channelType}`, params),
  
  // �����������
  saveParameters: (channelType: string, params: any) => 
    apiClient.post(`/parameters/${channelType}/save`, params),
  
  // ����Ԥ������
  loadPreset: (presetName: string) => 
    apiClient.get(`/parameters/preset/${presetName}`)
}

// �����������API
export const sceneAPI = {
  // ��ȡ��������
  getSceneSettings: () => 
    apiClient.get('/scene/settings'),
  
  // ���³�������
  updateSceneSettings: (settings: any) => 
    apiClient.put('/scene/settings', settings),
  
  // ��ʼ����
  startSimulation: (config: any) => 
    apiClient.post('/simulation/start', config),
  
  // ֹͣ����
  stopSimulation: () => 
    apiClient.post('/simulation/stop'),
  
  // ��ȡ����״̬
  getSimulationStatus: () => 
    apiClient.get('/simulation/status'),
  
  // ���ó�������
  resetSceneSettings: () => 
    apiClient.post('/scene/reset')
}

// ����������API
export const resultAPI = {
  // ��ȡʵʱ�������
  getRealTimeResults: (resultType: string) => 
    apiClient.get(`/results/${resultType}`),
  
  // ��ȡ��ʷ����
  getHistoryData: (resultType: string, timeRange: string) => 
    apiClient.get(`/results/${resultType}/history`, {
      params: { range: timeRange }
    }),
  
  // �������Խ��
  exportResults: (format: string) => 
    apiClient.post('/results/export', { format }, {
      responseType: 'blob'
    }),
  
  // ��ȡͳ����Ϣ
  getStatistics: () => 
    apiClient.get('/results/statistics'),
  
  // �����ʷ����
  clearHistory: () => 
    apiClient.delete('/results/history')
}

// ϵͳ�������API
export const systemAPI = {
  // ��ȡϵͳ״̬
  getSystemStatus: () => 
    apiClient.get('/system/status'),
  
  // ��ȡϵͳ��Ϣ
  getSystemInfo: () => 
    apiClient.get('/system/info'),
  
  // ��ȡ��־
  getLogs: (level: string, count: number) => 
    apiClient.get('/system/logs', {
      params: { level, count }
    }),
  
  // ϵͳ����
  systemRestart: () => 
    apiClient.post('/system/restart'),
  
  // ��ȡ�汾��Ϣ
  getVersion: () => 
    apiClient.get('/system/version')
}

// WebSocket���ӹ���
export class WebSocketManager {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 3000

  connect(url: string = 'ws://localhost:8000/ws') {
    try {
      this.ws = new WebSocket(url)
      
      this.ws.onopen = (event) => {
        console.log('WebSocket ���ӳɹ�', event)
        this.reconnectAttempts = 0
      }
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('����WebSocket��Ϣʧ��:', error)
        }
      }
      
      this.ws.onclose = (event) => {
        console.log('WebSocket ���ӹر�', event)
        this.handleReconnect()
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket ����:', error)
      }
    } catch (error) {
      console.error('WebSocket ����ʧ��:', error)
    }
  }

  private handleMessage(data: any) {
    // ����ʵʱ���ݸ���
    switch (data.type) {
      case 'realtime_data':
        // ����ʵʱ���ݸ����¼�
        window.dispatchEvent(new CustomEvent('realtime-update', {
          detail: data.payload
        }))
        break
      case 'system_alert':
        // ����ϵͳ����
        window.dispatchEvent(new CustomEvent('system-alert', {
          detail: data.payload
        }))
        break
      case 'simulation_status':
        // �������״̬����
        window.dispatchEvent(new CustomEvent('simulation-status', {
          detail: data.payload
        }))
        break
      default:
        console.log('δ֪��WebSocket��Ϣ����:', data.type)
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`��������WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      setTimeout(() => {
        this.connect()
      }, this.reconnectInterval)
    } else {
      console.error('WebSocket����������������')
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocketδ����')
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

// ����WebSocket������ʵ��
export const wsManager = new WebSocketManager()

// ���ߺ���
export const utils = {
  // ��ʽ���ļ���С
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },

  // ��ʽ������
  formatNumber: (num: number, precision: number = 2): string => {
    return num.toLocaleString(undefined, {
      minimumFractionDigits: precision,
      maximumFractionDigits: precision
    })
  },

  // ��������
  debounce: <T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): ((...args: Parameters<T>) => void) => {
    let timeout: NodeJS.Timeout
    return (...args: Parameters<T>) => {
      clearTimeout(timeout)
      timeout = setTimeout(() => func.apply(null, args), wait)
    }
  },

  // ��������
  throttle: <T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): ((...args: Parameters<T>) => void) => {
    let inThrottle: boolean
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func.apply(null, args)
        inThrottle = true
        setTimeout(() => inThrottle = false, limit)
      }
    }
  }
}