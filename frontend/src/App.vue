<template>
  <div id="app">
    <!-- 简单的选择界面 -->
    <div v-if="!selectedSystem" style="min-height: 100vh; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center;">
      <div style="background: white; padding: 40px; border-radius: 20px; text-align: center;">
        <h1 style="color: #333; margin-bottom: 30px;">选择系统类型</h1>

        <div style="display: flex; gap: 20px;">
          <button style="background: #007bff; color: white; border: none; padding: 20px 40px; border-radius: 10px; cursor: pointer; font-size: 16px;"
                  @click="selectedSystem = 'ground'">
            🏗️ 地面检测系统
          </button>

          <button style="background: #6f42c1; color: white; border: none; padding: 20px 40px; border-radius: 10px; cursor: pointer; font-size: 16px;"
                  @click="selectedSystem = 'mixed'">
            🔮 虚实融合系统
          </button>
        </div>
      </div>
    </div>

    <!-- 地面检测系统 -->
    <div v-else-if="selectedSystem === 'ground'" class="app-container">
      <AppHeader />

      <main class="main-content">
        <ParameterSettings @file-selected="handleFileSelected" />
        <!-- 🔧 移除 SceneSettings -->
        <ResultDisplay :active-tab="activeResultTab"
                       :lora-file-name="sharedLoraFileName"
                       :lora-file-data="sharedLoraFileData"
                       @update-tab="activeResultTab = $event" />
      </main>

      <div class="system-switch">
        <button class="switch-button" @click="selectedSystem = ''">
          🔄 返回选择
        </button>
      </div>
    </div>

    <!-- 虚实融合系统 -->
    <div v-else-if="selectedSystem === 'mixed'" class="app-container mixed-reality">
      <div class="mixed-system-content">
        <div class="mixed-header">
          <h1>🔮 虚实融合系统</h1>
          <p>Virtual-Reality Integration System</p>
        </div>

        <!-- 参数设置区域 -->
        <div class="mixed-section">
          <div class="section-header">
            <i class="header-icon">⚙️</i>
            <h2>参数设置</h2>
            <div class="status-indicator" :class="udpStatus.connected ? 'connected' : 'disconnected'">
              <span class="status-dot"></span>
              <span>{{ udpStatus.connected ? 'UDP已连接' : 'UDP未连接' }}</span>
            </div>
          </div>
          <div class="udp-settings">
            <div class="setting-group">
              <h4>🔗 UDP端口配置</h4>
              <div class="udp-form">
                <div class="form-row">
                  <div class="form-group">
                    <label>接收UDP端口</label>
                    <input type="number"
                           v-model.number="udpSettings.receivePort"
                           placeholder="8002"
                           class="udp-input"
                           :disabled="updating" />
                  </div>
                </div>

                <div class="button-row">
                  <button class="update-button"
                          @click="updateUDPConfig"
                          :disabled="updating">
                    {{ updating ? '更新中...' : '🔄 更新' }}
                  </button>
                  <button class="test-button"
                          @click="testUDPSend"
                          :disabled="!udpStatus.connected">
                    📤 测试发送
                  </button>
                </div>

                <!-- 状态显示 -->
                <div class="status-info" v-if="udpStatus.message">
                  <div class="status-message" :class="udpStatus.type">
                    <i>{{ udpStatus.type === 'success' ? '✅' : udpStatus.type === 'error' ? '❌' : 'ℹ️' }}</i>
                    {{ udpStatus.message }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 事件列表区域 -->
        <div class="mixed-section">
          <div class="section-header">
            <i class="header-icon">📋</i>
            <h2>事件列表</h2>
            <div class="event-controls">
              <button class="clear-button" @click="clearEvents">
                🗑️ 清空列表
              </button>
              <button class="refresh-button" @click="refreshStatus">
                🔄 刷新状态
              </button>
              <label class="auto-scroll">
                <input type="checkbox" v-model="autoScroll">
                自动滚动
              </label>
            </div>
          </div>

          <div class="event-list-container">
            <div class="event-header">
              <div class="col-direction">方向</div>
              <div class="col-source">源地址</div>
              <div class="col-destination">目的地址</div>
              <div class="col-time">时间</div>
              <div class="col-data">数据</div>
            </div>

            <div class="event-list" ref="eventListRef">
              <div v-for="event in eventList"
                   :key="event.id"
                   class="event-item"
                   :class="{ 'send': event.direction === '发', 'receive': event.direction === '收' }">
                <div class="col-direction">
                  <span class="direction-badge" :class="event.direction === '发' ? 'send' : 'receive'">
                    {{ event.direction === '发' ? '📤' : '📥' }} {{ event.direction }}
                  </span>
                </div>
                <div class="col-source">{{ event.sourceAddress }}</div>
                <div class="col-destination">{{ event.destinationAddress }}</div>
                <div class="col-time">{{ event.time }}</div>
                <div class="col-data">
                  <div class="data-preview">{{ event.data }}</div>
                </div>
              </div>

              <!-- 空状态 -->
              <div v-if="eventList.length === 0" class="empty-state">
                <i>📡</i>
                <p>暂无UDP通信事件</p>
                <small>启动UDP通信后，事件将在此显示</small>
              </div>
            </div>
          </div>
        </div>

        <div class="system-switch">
          <button class="switch-button" @click="selectedSystem = ''">
            🔄 返回选择
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, nextTick, onMounted, onUnmounted, watch } from 'vue'
  import axios from 'axios'
  import AppHeader from './components/AppHeader.vue'
  import ParameterSettings from './components/ParameterSettings.vue'
  import ResultDisplay from './components/ResultDisplay.vue'

  // 初始状态：空字符串表示显示选择界面
  const selectedSystem = ref<string>('')
  const activeResultTab = ref('ber')

  // 共享的LoRa文件数据
  const sharedLoraFileName = ref('')
  const sharedLoraFileData = ref('')

  // 处理参数设置页面的文件选择
  const handleFileSelected = (fileName: string, fileData: string) => {
    sharedLoraFileName.value = fileName
    sharedLoraFileData.value = fileData
    console.log(`✅ App接收到文件: ${fileName}, ${fileData.length / 2} 字节`)
  }

  // 清空文件数据的函数
  const clearFileData = () => {
    sharedLoraFileName.value = ''
    sharedLoraFileData.value = ''
    console.log('🧹 文件数据已清空')
  }

  // 在虚实融合系统的数据中添加
  const messages = ref([])
  const messagePolling = ref(null)

  // UDP设置
  const udpSettings = reactive({
    receivePort: 8002  // 删除了 sendPort
  })

  // UDP状态
  const udpStatus = reactive({
    connected: false,
    message: '',
    type: 'info' // success, error, info
  })

  // 更新状态
  const updating = ref(false)

  // 事件列表
  const eventList = ref<Array<{
    id: number
    direction: string
    sourceAddress: string
    destinationAddress: string
    time: string
    data: string
  }>>([])

  const autoScroll = ref(true)
  const eventListRef = ref<HTMLElement>()

  // API基础URL
  const API_BASE = '/api'

  // 显示状态消息
  const showStatus = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    udpStatus.message = message
    udpStatus.type = type

    // 3秒后自动清除消息
    setTimeout(() => {
      if (udpStatus.message === message) {
        udpStatus.message = ''
      }
    }, 3000)
  }

  // 更新UDP配置
  const updateUDPConfig = async () => {
    if (updating.value) return

    updating.value = true

    try {
      const response = await axios.post(`${API_BASE}/udp/config`, {
        receivePort: udpSettings.receivePort
      })

      if (response.data.success) {
        // 直接从POST响应中获取状态，不依赖GET请求
        udpStatus.connected = true
        showStatus(`UDP配置更新成功 - 接收端口: ${udpSettings.receivePort}`, 'success')
        console.log('UDP配置更新成功:', response.data)
      } else {
        throw new Error(response.data.message || '配置更新失败')
      }
    } catch (error) {
      console.error('UDP配置更新失败:', error)
      udpStatus.connected = false
      showStatus(`配置更新失败: ${error.response?.data?.detail || error.message}`, 'error')
    } finally {
      updating.value = false
    }
  }

  // 测试UDP发送
  const testUDPSend = async () => {
    try {
      const testMessage = `测试消息 - ${new Date().toLocaleTimeString()}`

      const response = await axios.post(`${API_BASE}/udp/send`, {
        message: testMessage,
        target_ip: "127.0.0.1"
      })

      if (response.data.success) {
        showStatus('UDP测试消息发送成功', 'success')

        // 使用后端返回的详细信息
        const details = response.data.details
        if (details) {
          addEvent('发', details.from, details.to, details.data)
        } else {
          // 兜底方案，不显示随机端口
          addEvent('发', `127.0.0.1`, `127.0.0.1:${udpSettings.receivePort}`, testMessage)
        }
      } else {
        throw new Error(response.data.message || '发送失败')
      }
    } catch (error) {
      console.error('UDP发送测试失败:', error)
      showStatus(`测试发送失败: ${error.response?.data?.detail || error.message}`, 'error')
    }
  }

  // 刷新UDP状态
  const loadInitialConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE}/udp/config`)

      if (response.data.success) {
        const config = response.data.data
        udpSettings.receivePort = config.receivePort  
        udpStatus.connected = response.data.receiver_status.running

        console.log('初始UDP配置加载:', config)
      }
    } catch (error) {
      console.error('加载初始配置失败:', error)
      showStatus('无法连接到后端服务', 'error')
    }
  }

  // 添加事件到列表
  const addEvent = (direction: string, source: string, destination: string, data: string) => {
    const now = new Date()
    const time = now.toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    })

    eventList.value.push({
      id: Date.now() + Math.random(),
      direction,
      sourceAddress: source,
      destinationAddress: destination,
      time,
      data
    })

    // 限制事件列表长度
    if (eventList.value.length > 100) {
      eventList.value.shift()
    }

    // 自动滚动到底部
    if (autoScroll.value) {
      nextTick(() => {
        if (eventListRef.value) {
          eventListRef.value.scrollTop = eventListRef.value.scrollHeight
        }
      })
    }
  }

  // 清空事件列表
  const clearEvents = () => {
    eventList.value = []
    showStatus('事件列表已清空', 'info')
  }

  // 组件挂载时加载初始配置
  onMounted(() => {
    console.log('App.vue 已加载，selectedSystem 初始值:', selectedSystem.value)
    loadInitialConfig()
  })

  // 定时刷新状态（可选）
  let statusInterval: number | null = null

  // 监听系统选择变化
  const startStatusPolling = () => {
    if (statusInterval) clearInterval(statusInterval)
    // 每30秒刷新一次状态
    statusInterval = setInterval(refreshStatus, 30000)
  }

  const stopStatusPolling = () => {
    if (statusInterval) {
      clearInterval(statusInterval)
      statusInterval = null
    }
  }

  // 监听系统切换
  const handleSystemChange = (system) => {
    if (system === 'mixed') {
      startStatusPolling()
      startMessagePolling() // 添加这行
    } else {
      stopStatusPolling()
      stopMessagePolling() // 添加这行
    }
  }

  // 在 onUnmounted 中添加清理
  onUnmounted(() => {
    stopStatusPolling()
    stopMessagePolling() // 添加这行
  })

  // 监听选择的系统变化
  import { watch } from 'vue'
  //watch(selectedSystem, (newValue) => {
  //  handleSystemChange(newValue)
  //})

  watch(selectedSystem, (newValue, oldValue) => {
  console.log(`🔄 系统切换: ${oldValue} -> ${newValue}`)
  
  // 当从地面检测系统切换到其他系统时，清空文件数据
  if (oldValue === 'ground' && newValue !== 'ground') {
    clearFileData()
  }
  
  handleSystemChange(newValue)
})

  // 组件卸载时清理
  onUnmounted(() => {
    stopStatusPolling()
  })

  // 获取消息
  //const fetchMessages = async () => {
  //  try {
  //    const response = await axios.get(`${API_BASE}/udp/messages?limit=100`)
  //    if (response.data.success) {
  //      messages.value = response.data.data.messages
  //    }
  //  } catch (error) {
  //    console.error('获取消息失败:', error)
  //  }
  //}

  //// 开始消息轮询
  //const startMessagePolling = () => {
  //  if (messagePolling.value) return

  //  messagePolling.value = setInterval(fetchMessages, 1000) // 每秒获取一次
  //}

  //// 停止消息轮询
  //const stopMessagePolling = () => {
  //  if (messagePolling.value) {
  //    clearInterval(messagePolling.value)
  //    messagePolling.value = null
  //  }
  //}

  // 清空消息
  const clearMessages = async () => {
    try {
      await axios.delete(`${API_BASE}/udp/messages`)
      messages.value = []
      showStatus('消息队列已清空', 'info')
    } catch (error) {
      console.error('清空消息失败:', error)
      showStatus('清空消息失败', 'error')
    }
  }

  console.log('App.vue 已加载，selectedSystem 初始值:', selectedSystem.value)

  // 刷新UDP状态
  const refreshStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/udp/config`)

      if (response.data.success) {
        udpStatus.connected = response.data.receiver_status.running
        console.log('✅ UDP状态刷新成功')
      }
    } catch (error) {
      console.error('❌ 刷新UDP状态失败:', error)
      udpStatus.connected = false
    }
  }

  const switchMode = async (mode) => {
    try {
      const response = await axios.post(`/api/mode/switch/${mode}`)
      if (response.data.success) {
        console.log(`✅ 切换到${mode}模式成功`)
      }
    } catch (error) {
      console.error('模式切换失败:', error)
    }
  }

  // 在选择系统时调用
  const selectSystem = (system) => {
    selectedSystem.value = system
    const mode = system === 'ground' ? 'ground' : 'virtual'
    switchMode(mode)
  }
</script>

<style scoped>
  /* 地面检测系统样式 */
  .app-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.25rem;
    transform-origin: top center;
    position: relative;
  }

  .main-content {
    width: 90vw;
    max-width: 87.5rem;
    min-width: 25rem;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 1.875rem;
  }

  /* 虚实融合系统样式 */
  .mixed-reality {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white;
  }

  .mixed-system-content {
    width: 90vw;
    max-width: 87.5rem;
    min-width: 25rem;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .mixed-header {
    text-align: center;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 1.5rem;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

    .mixed-header h1 {
      font-size: 3rem;
      margin: 0 0 0.5rem 0;
      background: linear-gradient(135deg, #e0c3fc, #9bb5ff);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .mixed-header p {
      font-size: 1.2rem;
      opacity: 0.8;
      margin: 0;
    }

  /* 混合系统区域样式 */
  .mixed-section {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 1.5rem;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
  }

  .section-header {
    background: rgba(255, 255, 255, 0.1);
    padding: 1.5rem 2rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    align-items: center;
    gap: 1rem;
    justify-content: space-between;
  }

  .header-icon {
    font-size: 1.5rem;
  }

  .section-header h2 {
    font-size: 1.5rem;
    margin: 0;
    color: #e0c3fc;
    flex: 1;
  }

  /* 状态指示器 */
  .status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 1.5rem;
    font-size: 0.9rem;
    font-weight: 500;
  }

    .status-indicator.connected {
      background: rgba(40, 167, 69, 0.2);
      color: #28a745;
      border: 1px solid rgba(40, 167, 69, 0.4);
    }

    .status-indicator.disconnected {
      background: rgba(220, 53, 69, 0.2);
      color: #dc3545;
      border: 1px solid rgba(220, 53, 69, 0.4);
    }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s infinite;
  }

  /* UDP设置样式 */
  .udp-settings {
    padding: 2rem;
  }

  .setting-group h4 {
    color: #9bb5ff;
    margin-bottom: 1.5rem;
    font-size: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .port-explanation {
    background: rgba(23, 162, 184, 0.1);
    border: 1px solid rgba(23, 162, 184, 0.3);
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1.5rem;
    color: #b8c5d6;
    font-size: 0.9rem;
  }

    .port-explanation p {
      margin: 0 0 0.5rem 0;
      font-weight: 500;
    }

    .port-explanation ul {
      margin: 0;
      padding-left: 1.5rem;
      list-style-type: disc;
    }

    .port-explanation li {
      margin-bottom: 0.25rem;
    }

    .port-explanation strong {
      color: #9bb5ff;
    }

  .udp-form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

    .form-group label {
      color: #b8c5d6;
      font-size: 0.9rem;
      font-weight: 500;
    }

  .udp-input {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0.5rem;
    padding: 0.75rem 1rem;
    color: white;
    font-size: 1rem;
    transition: all 0.3s ease;
  }

    .udp-input:focus {
      outline: none;
      border-color: #9bb5ff;
      background: rgba(255, 255, 255, 0.15);
      box-shadow: 0 0 0 3px rgba(155, 181, 255, 0.2);
    }

    .udp-input:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .udp-input::placeholder {
      color: rgba(255, 255, 255, 0.5);
    }

  /* 按钮行样式 */
  .button-row {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }

  .update-button,
  .test-button {
    padding: 0.5rem 1rem; /* 减少padding */
    border: none;
    border-radius: 0.5rem;
    font-size: 0.9rem; /* 减小字体 */
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    white-space: nowrap; /* 防止换行 */
  }

  .update-button {
    background: rgba(0, 123, 255, 0.8);
    color: white;
    flex: 1;
    min-width: 120px; /* 设置最小宽度 */
    max-width: 140px; /* 设置最大宽度 */
  }

    .update-button:hover:not(:disabled) {
      background: rgba(0, 123, 255, 1);
      transform: translateY(-1px);
    }

    .update-button:disabled {
      background: rgba(108, 117, 125, 0.5);
      cursor: not-allowed;
      transform: none;
    }

  .test-button {
    background: rgba(40, 167, 69, 0.8);
    color: white;
  }

    .test-button:hover:not(:disabled) {
      background: rgba(40, 167, 69, 1);
      transform: translateY(-1px);
    }

    .test-button:disabled {
      background: rgba(108, 117, 125, 0.5);
      cursor: not-allowed;
      transform: none;
    }

  /* 状态信息样式 */
  .status-info {
    margin-top: 1rem;
  }

  .status-message {
    padding: 1rem;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }

    .status-message.success {
      background: rgba(40, 167, 69, 0.1);
      color: #28a745;
      border: 1px solid rgba(40, 167, 69, 0.3);
    }

    .status-message.error {
      background: rgba(220, 53, 69, 0.1);
      color: #dc3545;
      border: 1px solid rgba(220, 53, 69, 0.3);
    }

    .status-message.info {
      background: rgba(23, 162, 184, 0.1);
      color: #17a2b8;
      border: 1px solid rgba(23, 162, 184, 0.3);
    }

  /* 事件列表样式 */
  .event-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .clear-button,
  .refresh-button {
    background: rgba(220, 53, 69, 0.2);
    border: 1px solid rgba(220, 53, 69, 0.4);
    color: #ff6b8a;
    padding: 0.5rem 1rem;
    border-radius: 1rem;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.3s ease;
  }

  .refresh-button {
    background: rgba(23, 162, 184, 0.2);
    border-color: rgba(23, 162, 184, 0.4);
    color: #17a2b8;
  }

    .clear-button:hover,
    .refresh-button:hover {
      background: rgba(220, 53, 69, 0.3);
      border-color: rgba(220, 53, 69, 0.6);
    }

    .refresh-button:hover {
      background: rgba(23, 162, 184, 0.3);
      border-color: rgba(23, 162, 184, 0.6);
    }

  .auto-scroll {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    color: #b8c5d6;
    cursor: pointer;
  }

    .auto-scroll input[type="checkbox"] {
      margin: 0;
    }

  .event-list-container {
    padding: 0;
    background: rgba(0, 0, 0, 0.2);
  }

  .event-header {
    display: grid;
    grid-template-columns: 120px 200px 200px 120px 1fr;
    gap: 1rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    font-weight: 600;
    font-size: 0.9rem;
    color: #e0c3fc;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .event-list {
    max-height: 400px;
    overflow-y: auto;
    padding: 0;
  }

  .event-item {
    display: grid;
    grid-template-columns: 120px 200px 200px 120px 1fr;
    gap: 1rem;
    padding: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    transition: background 0.2s ease;
    align-items: center;
  }

    .event-item:hover {
      background: rgba(255, 255, 255, 0.05);
    }

    .event-item.send {
      border-left: 3px solid #28a745;
    }

    .event-item.receive {
      border-left: 3px solid #007bff;
    }

  .direction-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.8rem;
    font-weight: 500;
  }

    .direction-badge.send {
      background: rgba(40, 167, 69, 0.2);
      color: #28a745;
      border: 1px solid rgba(40, 167, 69, 0.3);
    }

    .direction-badge.receive {
      background: rgba(0, 123, 255, 0.2);
      color: #007bff;
      border: 1px solid rgba(0, 123, 255, 0.3);
    }

  .col-source,
  .col-destination {
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    color: #b8c5d6;
  }

  .col-time {
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    color: #9bb5ff;
  }

  .data-preview {
    background: rgba(0, 0, 0, 0.3);
    padding: 0.5rem;
    border-radius: 0.25rem;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    color: #e0c3fc;
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem;
    color: #666;
    text-align: center;
  }

    .empty-state i {
      font-size: 3rem;
      margin-bottom: 1rem;
      opacity: 0.5;
    }

    .empty-state p {
      font-size: 1.1rem;
      margin: 0 0 0.5rem 0;
    }

    .empty-state small {
      opacity: 0.7;
    }

  /* 滚动条样式 */
  .event-list::-webkit-scrollbar {
    width: 8px;
  }

  .event-list::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
  }

  .event-list::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 4px;
  }

    .event-list::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.5);
    }

  /* 系统切换按钮 */
  .system-switch {
    position: fixed;
    top: 2rem;
    right: 2rem;
    z-index: 1000;
  }

  .switch-button {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(255, 255, 255, 0.3);
    color: #2c3e50;
    padding: 0.75rem 1.5rem;
    border-radius: 2rem;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.1);
  }

    .switch-button:hover {
      background: rgba(255, 255, 255, 1);
      transform: translateY(-2px);
    }

  .mixed-reality .switch-button {
    background: rgba(157, 181, 255, 0.2);
    color: white;
    border-color: rgba(157, 181, 255, 0.3);
  }

    .mixed-reality .switch-button:hover {
      background: rgba(157, 181, 255, 0.4);
    }

  /* 动画效果 */
  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
      opacity: 1;
    }

    50% {
      transform: scale(1.1);
      opacity: 0.8;
    }
  }

  @media (max-width: 768px) {
    .app-container {
      padding: 0.625rem;
    }

    .main-content,
    .mixed-system-content {
      gap: 1.25rem;
      width: 95vw;
      min-width: 20rem;
    }

    .mixed-header h1 {
      font-size: 2rem;
    }

    .udp-settings {
      padding: 1.5rem;
    }

    .form-row {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .button-row {
      flex-direction: column;
    }

    .event-header,
    .event-item {
      grid-template-columns: 80px 1fr 1fr 80px 150px;
      gap: 0.5rem;
      padding: 0.75rem;
      font-size: 0.8rem;
    }

    .col-source,
    .col-destination {
      font-size: 0.75rem;
    }

    .data-preview {
      max-width: 120px;
      font-size: 0.7rem;
    }

    .system-switch {
      position: relative;
      top: auto;
      right: auto;
      text-align: center;
      margin-top: 2rem;
    }

    .event-controls {
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .section-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .status-indicator {
      align-self: stretch;
      justify-content: center;
    }
  }

  @media (max-width: 480px) {
    .mixed-header {
      padding: 1.5rem;
    }

      .mixed-header h1 {
        font-size: 1.8rem;
      }

    .section-header {
      padding: 1rem;
    }

    .event-controls {
      width: 100%;
      justify-content: space-between;
    }

    .udp-settings {
      padding: 1rem;
    }

    .event-header,
    .event-item {
      grid-template-columns: 60px 1fr;
      gap: 0.5rem;
    }

    .col-source,
    .col-destination,
    .col-time {
      display: none;
    }

    .data-preview {
      max-width: none;
    }
  }
</style>
