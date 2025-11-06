<template>
  <div id="app">
    <!-- 选择界面 -->
    <div v-if="!selectedSystem" style="min-height: 100vh; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center;">
      <div style="background: white; padding: 40px; border-radius: 20px; text-align: center;">
        <h1 style="color: #333; margin-bottom: 30px;">选择系统类型</h1>

        <div style="display: flex; gap: 20px;">
          <button style="background: #007bff; color: white; border: none; padding: 20px 40px; border-radius: 10px; cursor: pointer; font-size: 16px;"
                  @click="selectSystem('ground')">
            🏗️ 地面检测系统
          </button>

          <button style="background: #6f42c1; color: white; border: none; padding: 20px 40px; border-radius: 10px; cursor: pointer; font-size: 16px;"
                  @click="selectSystem('mixed')">
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
        <ResultDisplay :active-tab="activeResultTab"
                       :lora-file-name="sharedLoraFileName"
                       :lora-file-data="sharedLoraFileData"
                       @update-tab="activeResultTab = $event" />
      </main>

      <div class="system-switch">
        <button class="switch-button" @click="returnToSelection">
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

        <!-- 事件列表区域 -->
        <div class="mixed-section">
          <div class="section-header">
            <i class="header-icon">📋</i>
            <h2>通信事件</h2>
            <div class="event-controls">
              <!-- 🔧 删除UDP连接状态，添加SSE连接状态 -->
              <div class="status-indicator" :class="{ connected: virtualSseConnected }">
                <span class="status-dot"></span>
                <span>{{ virtualSseConnected ? 'SSE已连接' : 'SSE未连接' }}</span>
              </div>
              <button class="clear-button" @click="clearEvents">
                🗑️ 清空列表
              </button>
              <label class="auto-scroll">
                <input type="checkbox" v-model="autoScroll">
                自动滚动
              </label>
            </div>
          </div>

          <div class="event-list-container">
            <!-- 简化表头：只保留时间和数据 -->
            <div class="event-header">
              <div class="col-time">时间</div>
              <div class="col-data">数据内容</div>
            </div>

            <div class="event-list" ref="eventListRef">
              <div v-for="event in virtualEvents"
                   :key="event.id"
                   class="event-item"
                   :class="{
                     'send-frame': event.type === 'send',
                     'receive-frame': event.type === 'receive'
                   }">
                <div class="col-time">
                  <span class="frame-type-badge" :class="event.type">
                    {{ event.type === 'send' ? '📤 发送' : '📥 接收' }}
                  </span>
                  <span class="time-text">{{ event.time }}</span>
                </div>
                <div class="col-data">
                  <div class="data-preview">{{ event.data }}</div>
                </div>
              </div>

              <!-- 空状态 -->
              <div v-if="virtualEvents.length === 0" class="empty-state">
                <i>📡</i>
                <p>暂无通信事件</p>
                <small>虚实融合节点通信事件将在此显示</small>
              </div>
            </div>
          </div>
        </div>

        <div class="system-switch">
          <button class="switch-button" @click="returnToSelection">
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

  // API基础URL
  const API_BASE = '/api'

  // 初始状态
  const selectedSystem = ref<string>('')
  const activeResultTab = ref('ber')

  // 共享的LoRa文件数据
  const sharedLoraFileName = ref('')
  const sharedLoraFileData = ref('')

  // 🔧 虚实融合事件列表
  const virtualEvents = ref<Array<{
    id: number
    type: string
    time: string
    data: string
  }>>([])

  const autoScroll = ref(true)
  const eventListRef = ref<HTMLElement>()

  // 🔧 虚实融合SSE连接状态
  const virtualSseConnected = ref(false)
  let virtualEventSource: EventSource | null = null

  // 处理参数设置页面的文件选择
  const handleFileSelected = (fileName: string, fileData: string) => {
    sharedLoraFileName.value = fileName
    sharedLoraFileData.value = fileData
    console.log(`✅ App接收到文件: ${fileName}, ${fileData.length / 2} 字节`)
  }

  // 清空文件数据
  const clearFileData = () => {
    sharedLoraFileName.value = ''
    sharedLoraFileData.value = ''
    console.log('🧹 文件数据已清空')
  }

  // 模式切换API调用
  const switchMode = async (mode: string) => {
    try {
      console.log(`🔄 准备切换到 ${mode} 模式`)
      const response = await axios.post(`${API_BASE}/mode/switch/${mode}`)

      if (response.data.success) {
        console.log(`✅ 切换到 ${mode} 模式成功`)
      }
    } catch (error) {
      console.error('❌ 模式切换失败:', error)
    }
  }

  // 选择系统
  const selectSystem = async (system: string) => {
    console.log(`📍 选择系统: ${system}`)
    selectedSystem.value = system

    const mode = system === 'ground' ? 'ground' : 'virtual'
    await switchMode(mode)
  }

  // 返回选择界面
  const returnToSelection = () => {
    console.log('🔙 返回系统选择')

    // 🔧 先断开SSE连接
    disconnectVirtualSSE()

    selectedSystem.value = ''

    if (sharedLoraFileData.value) {
      clearFileData()
    }
  }

  // 🔧 断开虚实融合SSE
  const disconnectVirtualSSE = () => {
    if (virtualEventSource) {
      console.log('🔌 断开虚实融合SSE连接')
      virtualEventSource.close()
      virtualEventSource = null
      virtualSseConnected.value = false
    }
  }

  // 🔧 连接虚实融合SSE
  const connectVirtualSSE = () => {
    // 先断开现有连接
    disconnectVirtualSSE()

    console.log('🔗 正在连接虚实融合SSE...')
    virtualEventSource = new EventSource(`${API_BASE}/virtual/stream`)

    virtualEventSource.onopen = () => {
      virtualSseConnected.value = true
      console.log('✅ 虚实融合SSE 连接成功')
    }

    virtualEventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'connected') {
          console.log('📡 SSE 初始连接:', data.message)
        } else if (data.type === 'virtual_event') {
          handleVirtualEvent(data.data)
        }
      } catch (error) {
        console.error('❌ SSE 消息解析错误:', error)
      }
    }

    virtualEventSource.onerror = (error) => {
      virtualSseConnected.value = false
      console.error('❌ 虚实融合SSE 连接错误')

      // 🔧 只在虚实融合模式下才重连
      setTimeout(() => {
        if (selectedSystem.value === 'mixed') {
          console.log('🔄 尝试重新连接虚实融合SSE...')
          connectVirtualSSE()
        }
      }, 5000)
    }
  }

  // 🔧 处理虚实融合事件
  const handleVirtualEvent = (msg: any) => {
    const msgType = msg.message_type

    // 只处理 0x00 (发送) 和 0x01 (接收)
    if (msgType !== 0x00 && msgType !== 0x01) {
      return
    }

    const now = new Date()
    const time = now.toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    })

    let eventType = ''
    let eventData = ''

    if (msgType === 0x00) {
      // 🔧 信号发送帧 - 使用 virtual_send_info
      eventType = 'send'
      const info = msg.virtual_send_info || {}
      eventData = `发送时间: ${info.send_time || '无'}, 传播参数: ${info.propagation_param || '无'}, 数据: ${info.data_hex || '无'}`
    } else if (msgType === 0x01) {
      // 🔧 信号接收帧 - 使用 virtual_receive_info
      eventType = 'receive'
      const info = msg.virtual_receive_info || {}
      eventData = `接收时间: ${info.receive_time || '无'}, 时间戳: ${info.receive_timestamp || '无'}, 数据: ${info.data_hex || '无'}`
    }

    virtualEvents.value.push({
      id: Date.now() + Math.random(),
      type: eventType,
      time,
      data: eventData
    })

    // 限制列表长度
    if (virtualEvents.value.length > 100) {
      virtualEvents.value.shift()
    }

    // 自动滚动
    if (autoScroll.value) {
      nextTick(() => {
        if (eventListRef.value) {
          eventListRef.value.scrollTop = eventListRef.value.scrollHeight
        }
      })
    }
  }

  // 清空虚实事件
  const clearEvents = () => {
    virtualEvents.value = []
    console.log('🗑️ 事件列表已清空')
  }

  // 处理系统切换
  const handleSystemChange = (system: string) => {
    console.log(`🔄 handleSystemChange: ${system}`)

    if (system === 'mixed') {
      // 🔧 切换到虚实融合模式 - 连接SSE
      connectVirtualSSE()
    } else {
      // 🔧 切换到其他模式 - 断开SSE
      disconnectVirtualSSE()
    }
  }

  // 监听系统切换
  watch(selectedSystem, (newValue, oldValue) => {
    console.log(`🔄 系统切换: ${oldValue} -> ${newValue}`)

    // 🔧 切换时先断开旧的SSE连接
    if (oldValue === 'mixed') {
      disconnectVirtualSSE()
    }

    if (oldValue === 'ground' && newValue !== 'ground') {
      clearFileData()
    }

    handleSystemChange(newValue)
  })

  // 组件挂载
  onMounted(() => {
    console.log('🎬 App.vue 已加载')
  })

  // 组件卸载
onUnmounted(() => {
  console.log('🛑 App.vue 卸载')
  
  // 🔧 断开SSE连接
  disconnectVirtualSSE()
})
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

  .event-header {
    display: grid;
    grid-template-columns: 200px 1fr; /* 时间 + 数据 */
    gap: 1rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    font-weight: 600;
    font-size: 0.9rem;
    color: #e0c3fc;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .event-item {
    display: grid;
    grid-template-columns: 200px 1fr; /* 时间 + 数据 */
    gap: 1rem;
    padding: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    transition: background 0.2s ease;
    align-items: center;
  }

    .event-item.send-frame {
      border-left: 3px solid #28a745;
      background: rgba(40, 167, 69, 0.05);
    }

    .event-item.receive-frame {
      border-left: 3px solid #007bff;
      background: rgba(0, 123, 255, 0.05);
    }

  .col-time {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .frame-type-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    font-weight: 600;
  }

    .frame-type-badge.send {
      background: rgba(40, 167, 69, 0.2);
      color: #28a745;
    }

    .frame-type-badge.receive {
      background: rgba(0, 123, 255, 0.2);
      color: #007bff;
    }

  .time-text {
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    color: #9bb5ff;
  }

  .data-preview {
    background: rgba(0, 0, 0, 0.3);
    padding: 0.75rem;
    border-radius: 0.5rem;
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    color: #e0c3fc;
    word-break: break-all;
    line-height: 1.4;
  }
</style>
