// 参数设置相关类型
export interface ParameterField {
  label: string
  type: 'text' | 'number' | 'select'
  value: string | number
  placeholder?: string
  options?: Array<{ label: string, value: string }>
  unit?: string
  min?: number
  max?: number
  step?: number
  required?: boolean
  disabled?: boolean
}

export interface ParameterTab {
  id: string
  name: string
  icon: string
  fields: ParameterField[]
  description?: string
}

// 场景设置相关类型
export interface InterferenceSettings {
  type: 'none' | 'white' | 'narrow' | 'pulse' | 'sweep'
  intensity: number
  frequency?: number
  bandwidth?: number
  enabled: boolean
}

export interface NoiseSettings {
  type: 'awgn' | 'colored' | 'impulsive' | 'phase'
  snr: number
  powerSpectralDensity?: number
  enabled: boolean
}

export interface DynamicSettings {
  mode: 'static' | 'linear' | 'acceleration' | 'circular' | 'orbit'
  velocity: number
  acceleration?: number
  trajectory?: Array<{ x: number, y: number, z: number, t: number }>
  enabled: boolean
}

export interface ChannelSettings {
  model: 'awgn' | 'rayleigh' | 'rician' | 'multipath'
  dopplerShift: number
  fadingParameters?: {
    k_factor?: number // 莱斯因子
    maxDopplerFreq?: number
    pathDelays?: number[]
    pathGains?: number[]
  }
}

export interface SceneSettings {
  interference: InterferenceSettings
  noise: NoiseSettings
  dynamic: DynamicSettings
  channel: ChannelSettings
  environment?: {
    temperature: number
    humidity: number
    pressure: number
  }
}

// 测试结果相关类型
export interface MetricThreshold {
  warning: number
  error: number
  unit: string
}

export interface Metric {
  id: string
  title: string
  value: number | string
  unit: string
  trend: 'up' | 'down' | 'stable'
  threshold: MetricThreshold
  description: string
  timestamp?: number
  history?: Array<{ value: number | string, timestamp: number }>
}

export interface ResultTab {
  id: string
  name: string
  icon: string
  hasAlert: boolean
  hasChart: boolean
  chartTitle: string
  metrics: Metric[]
  chartConfig?: ChartConfig
}

// 图表配置类型
export interface ChartConfig {
  type: 'line' | 'bar' | 'scatter' | 'pie'
  xAxis: {
    label: string
    type: 'time' | 'category' | 'value'
  }
  yAxis: {
    label: string
    type: 'value' | 'log'
    min?: number
    max?: number
  }
  series: Array<{
    name: string
    data: Array<{ x: any, y: any }>
    color?: string
  }>
  options?: {
    grid?: boolean
    legend?: boolean
    zoom?: boolean
    animation?: boolean
  }
}

// 仿真相关类型
export interface SimulationConfig {
  duration: number // 仿真时长（秒）
  timeStep: number // 时间步长（秒）
  parameters: Record<string, any>
  scene: SceneSettings
  outputFormat: 'json' | 'csv' | 'binary'
  realTimeUpdate: boolean
}

export interface SimulationStatus {
  id: string
  status: 'idle' | 'running' | 'paused' | 'stopped' | 'error'
  progress: number // 0-100
  currentTime: number
  totalTime: number
  startTime?: number
  endTime?: number
  errorMessage?: string
  statistics?: {
    processedSamples: number
    errorCount: number
    warningCount: number
    performance: {
      cpu: number
      memory: number
      throughput: number
    }
  }
}

// 系统状态相关类型
export interface SystemStatus {
  status: 'online' | 'offline' | 'maintenance'
  version: string
  uptime: number
  lastUpdate: number
  services: Array<{
    name: string
    status: 'running' | 'stopped' | 'error'
    port?: number
    lastHeartbeat?: number
  }>
  hardware: {
    cpu: {
      usage: number
      cores: number
      temperature?: number
    }
    memory: {
      total: number
      used: number
      available: number
    }
    disk: {
      total: number
      used: number
      available: number
    }
    network: {
      interfaces: Array<{
        name: string
        status: 'up' | 'down'
        ipAddress?: string
        rxBytes: number
        txBytes: number
      }>
    }
  }
}

// 日志相关类型
export interface LogEntry {
  id: string
  timestamp: number
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical'
  component: string
  message: string
  details?: any
  source?: {
    file: string
    line: number
    function: string
  }
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: {
    code: string
    message: string
    details?: any
  }
  pagination?: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'realtime_data' | 'system_alert' | 'simulation_status' | 'parameter_update'
  timestamp: number
  payload: any
  source?: string
}

// 实时数据更新类型
export interface RealTimeData {
  metrics: Record<string, Metric>
  charts: Record<string, ChartConfig>
  simulation: SimulationStatus
  system: SystemStatus
}

// 配置文件类型
export interface AppConfig {
  api: {
    baseURL: string
    timeout: number
    retryCount: number
  }
  websocket: {
    url: string
    reconnectInterval: number
    maxReconnectAttempts: number
  }
  ui: {
    theme: 'light' | 'dark' | 'auto'
    language: 'zh-CN' | 'en-US'
    refreshInterval: number
    chartUpdateInterval: number
  }
  simulation: {
    maxDuration: number
    defaultTimeStep: number
    autoSave: boolean
    saveInterval: number
  }
}

// 用户偏好设置类型
export interface UserPreferences {
  dashboardLayout: Array<{
    component: string
    position: { x: number, y: number }
    size: { width: number, height: number }
    visible: boolean
  }>
  favorites: {
    parameters: string[]
    scenes: string[]
    results: string[]
  }
  notifications: {
    enabled: boolean
    types: Array<'error' | 'warning' | 'info' | 'success'>
    sound: boolean
  }
  export: {
    defaultFormat: 'json' | 'csv' | 'excel'
    includeCharts: boolean
    includeMetadata: boolean
  }
}

// 错误处理类型
export interface AppError {
  code: string
  message: string
  type: 'network' | 'validation' | 'system' | 'simulation' | 'unknown'
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: number
  context?: any
  stack?: string
}

// 事件类型
export interface AppEvent {
  type: string
  source: string
  timestamp: number
  data: any
}

// 导出所有类型
export type {
  ParameterField,
  ParameterTab,
  InterferenceSettings,
  NoiseSettings,
  DynamicSettings,
  ChannelSettings,
  SceneSettings,
  MetricThreshold,
  Metric,
  ResultTab,
  ChartConfig,
  SimulationConfig,
  SimulationStatus,
  SystemStatus,
  LogEntry,
  ApiResponse,
  WebSocketMessage,
  RealTimeData,
  AppConfig,
  UserPreferences,
  AppError,
  AppEvent
}

// 常量定义
export const PARAMETER_TYPES = {
  UPLINK: 'uplink',
  REMOTE: 'remote',
  DOWNLINK: 'downlink',
  TELEMETRY: 'telemetry',
  BASEBAND: 'baseband'
} as const

export const RESULT_TYPES = {
  BER: 'ber',
  RANGING: 'ranging',
  MESSAGE: 'message'
} as const

export const SIMULATION_STATUS = {
  IDLE: 'idle',
  RUNNING: 'running',
  PAUSED: 'paused',
  STOPPED: 'stopped',
  ERROR: 'error'
} as const

export const LOG_LEVELS = {
  DEBUG: 'debug',
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical'
} as const
