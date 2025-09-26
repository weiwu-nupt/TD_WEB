import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    console.log('发送请求:', config)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('响应数据:', response)
    return response.data
  },
  (error) => {
    console.error('响应错误:', error)
    // 统一错误处理
    if (error.response) {
      switch (error.response.status) {
        case 401:
          console.error('未授权访问')
          break
        case 403:
          console.error('禁止访问')
          break
        case 404:
          console.error('请求资源不存在')
          break
        case 500:
          console.error('服务器内部错误')
          break
        default:
          console.error(`错误状态码: ${error.response.status}`)
      }
    }
    return Promise.reject(error)
  }
)

// 参数设置相关API
export const parameterAPI = {
  // 获取参数配置
  getParameters: (channelType: string) => 
    apiClient.get(`/parameters/${channelType}`),
  
  // 更新参数配置
  updateParameters: (channelType: string, params: any) => 
    apiClient.put(`/parameters/${channelType}`, params),
  
  // 保存参数配置
  saveParameters: (channelType: string, params: any) => 
    apiClient.post(`/parameters/${channelType}/save`, params),
  
  // 加载预设配置
  loadPreset: (presetName: string) => 
    apiClient.get(`/parameters/preset/${presetName}`)
}

// 场景设置相关API
export const sceneAPI = {
  // 获取场景配置
  getSceneSettings: () => 
    apiClient.get('/scene/settings'),
  
  // 更新场景配置
  updateSceneSettings: (settings: any) => 
    apiClient.put('/scene/settings', settings),
  
  // 开始仿真
  startSimulation: (config: any) => 
    apiClient.post('/simulation/start', config),
  
  // 停止仿真
  stopSimulation: () => 
    apiClient.post('/simulation/stop'),
  
  // 获取仿真状态
  getSimulationStatus: () => 
    apiClient.get('/simulation/status'),
  
  // 重置场景设置
  resetSceneSettings: () => 
    apiClient.post('/scene/reset')
}

// 结果数据相关API
export const resultAPI = {
  // 获取实时结果数据
  getRealTimeResults: (resultType: string) => 
    apiClient.get(`/results/${resultType}`),
  
  // 获取历史数据
  getHistoryData: (resultType: string, timeRange: string) => 
    apiClient.get(`/results/${resultType}/history`, {
      params: { range: timeRange }
    }),
  
  // 导出测试结果
  exportResults: (format: string) => 
    apiClient.post('/results/export', { format }, {
      responseType: 'blob'
    }),
  
  // 获取统计信息
  getStatistics: () => 
    apiClient.get('/results/statistics'),
  
  // 清空历史数据
  clearHistory: () => 
    apiClient.delete('/results/history')
}

// 系统管理相关API
export const systemAPI = {
  // 获取系统状态
  getSystemStatus: () => 
    apiClient.get('/system/status'),
  
  // 获取系统信息
  getSystemInfo: () => 
    apiClient.get('/system/info'),
  
  // 获取日志
  getLogs: (level: string, count: number) => 
    apiClient.get('/system/logs', {
      params: { level, count }
    }),
  
  // 系统重启
  systemRestart: () => 
    apiClient.post('/system/restart'),
  
  // 获取版本信息
  getVersion: () => 
    apiClient.get('/system/version')
}

// WebSocket连接管理
export class WebSocketManager {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 3000

  connect(url: string = 'ws://localhost:8000/ws') {
    try {
      this.ws = new WebSocket(url)
      
      this.ws.onopen = (event) => {
        console.log('WebSocket 连接成功', event)
        this.reconnectAttempts = 0
      }
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }
      
      this.ws.onclose = (event) => {
        console.log('WebSocket 连接关闭', event)
        this.handleReconnect()
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket 错误:', error)
      }
    } catch (error) {
      console.error('WebSocket 连接失败:', error)
    }
  }

  private handleMessage(data: any) {
    // 处理实时数据更新
    switch (data.type) {
      case 'realtime_data':
        // 触发实时数据更新事件
        window.dispatchEvent(new CustomEvent('realtime-update', {
          detail: data.payload
        }))
        break
      case 'system_alert':
        // 处理系统警告
        window.dispatchEvent(new CustomEvent('system-alert', {
          detail: data.payload
        }))
        break
      case 'simulation_status':
        // 处理仿真状态更新
        window.dispatchEvent(new CustomEvent('simulation-status', {
          detail: data.payload
        }))
        break
      default:
        console.log('未知的WebSocket消息类型:', data.type)
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`尝试重连WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      setTimeout(() => {
        this.connect()
      }, this.reconnectInterval)
    } else {
      console.error('WebSocket重连次数超过限制')
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocket未连接')
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

// 导出WebSocket管理器实例
export const wsManager = new WebSocketManager()

// 工具函数
export const utils = {
  // 格式化文件大小
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },

  // 格式化数字
  formatNumber: (num: number, precision: number = 2): string => {
    return num.toLocaleString(undefined, {
      minimumFractionDigits: precision,
      maximumFractionDigits: precision
    })
  },

  // 防抖函数
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

  // 节流函数
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