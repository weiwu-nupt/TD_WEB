<template>
  <section class="section">
    <div class="section-header">
      <i class="header-icon">📈</i>
      <h2>测试结果</h2>
      <div class="result-controls">
        <div class="connection-status" :class="{ connected: sseConnected }">
          <span class="status-dot"></span>
          <span>{{ sseConnected ? 'SSE已连接' : 'SSE未连接' }}</span>
        </div>
        <button class="refresh-btn" @click="reconnectSSE">
          <i>🔄</i>
          重新连接
        </button>
      </div>
    </div>

    <div class="tab-container">
      <nav class="tab-nav">
        <button v-for="tab in resultTabs"
                :key="tab.id"
                :class="{ active: activeTab === tab.id }"
                @click="$emit('update-tab', tab.id)"
                class="tab-button">
          <i>{{ tab.icon }}</i>
          {{ tab.name }}
        </button>
      </nav>

      <div class="tab-content">
        <div v-for="tab in resultTabs"
             :key="tab.id"
             v-show="activeTab === tab.id"
             class="tab-panel">

          <div class="result-sections">
            <div v-if="tab.id === 'ber'" class="result-section">

              <!-- 文件发送区域 - 简化版 -->
              <div class="file-sender-section">
                <div class="file-sender-header">
                  <i>📡</i>
                  <span>LoRa数据发送</span>
                </div>
                <div class="file-sender-content">

                  <!-- 显示已选择的文件 -->
                  <div v-if="props.loraFileData" class="selected-file-info">
                    <div class="file-badge">
                      <i>📄</i>
                      <span>{{ props.loraFileName }}</span>
                      <span class="file-size">({{ props.loraFileData.length / 2 }} 字节)</span>
                    </div>
                    <div class="file-preview">
                      <div class="preview-header">
                        <span>数据预览 (不含帧计数)</span>
                      </div>
                      <div class="preview-content">
                        {{ formatHexPreview(props.loraFileData) }}
                      </div>
                    </div>
                  </div>

                  <!-- 没有文件时的提示 -->
                  <div v-else class="no-file-warning">
                    <i>⚠️</i>
                    <span>请先在"参数设置"页面选择LoRa传输文件</span>
                  </div>

                  <!-- 发送控制 - 只有选择文件后才显示 -->
                  <div v-if="props.loraFileData" class="send-controls">
                    <div class="control-group">
                      <label>发送间隔 (秒):</label>
                      <input type="number"
                             v-model.number="sendInterval"
                             min="0.1"
                             step="0.1"
                             class="interval-input" />
                    </div>

                    <div class="control-buttons">
                      <button class="send-once-btn"
                              @click="sendOnce"
                              :disabled="!sseConnected">
                        <i>📤</i>
                        发送一次
                      </button>

                      <button v-if="!isSending"
                              class="send-auto-btn"
                              @click="startAutoSend"
                              :disabled="!sseConnected">
                        <i>▶️</i>
                        开始循环
                      </button>

                      <button v-else
                              class="stop-btn"
                              @click="stopAutoSend">
                        <i>⏸️</i>
                        暂停
                      </button>
                    </div>
                  </div>

                  <!-- 发送状态 -->
                  <div v-if="props.loraFileData" class="send-status-box">
                    <div class="status-item">
                      <span class="status-label">发送计数:</span>
                      <span class="status-value">{{ sendCount }}</span>
                    </div>
                    <div class="status-item">
                      <span class="status-label">发送状态:</span>
                      <span class="status-value" :class="{ sending: isSending }">
                        {{ isSending ? '🔄 循环发送中...' : '⏹️ 已停止' }}
                      </span>
                    </div>
                  </div>

                  <!-- 操作提示 -->
                  <div v-if="sendStatus" class="send-status" :class="sendStatus.type">
                    <i>{{ sendStatus.type === 'success' ? '✅' : '❌' }}</i>
                    {{ sendStatus.message }}
                  </div>
                </div>
              </div>

              <!-- 接收数据显示 - 优化样式 -->
              <div class="receive-section">
                <div class="receive-header">
                  <i>📥</i>
                  <span>接收数据</span>
                  <button class="clear-receive-btn" @click="clearReceivedData">
                    <i>🗑️</i>
                    清空
                  </button>
                </div>
                <div class="receive-list">
                  <div v-for="msg in receivedMessages"
                       :key="msg.id"
                       class="receive-item"
                       :class="{
                       'frame-lost': msg.isLost,
                       'frame-error': msg.hasError,
                       'frame-correct': !msg.isLost && !msg.hasError
                     }">
                    <div class="receive-time">{{ msg.time }}</div>
                    <div class="receive-frame"
                         :class="{
                         'frame-num-lost': msg.isLost,
                         'frame-num-error': msg.hasError,
                         'frame-num-correct': !msg.isLost && !msg.hasError
                       }">
                      帧 #{{ msg.frame_count }}
                    </div>
                    <div class="receive-data">
                      <span class="data-label">数据:</span>
                      <span class="data-hex">{{ msg.data_hex }}</span>
                    </div>
                    <!-- 移除字节数和ms显示 -->
                  </div>

                  <div v-if="receivedMessages.length === 0" class="empty-receive">
                    <i>📭</i>
                    <p>暂无接收数据</p>
                  </div>
                </div>
              </div>

              <!-- 误码率统计 - 更新卡片 -->
              <div class="section-title">
                <i>🎯</i>
                <span>误码率统计</span>
              </div>
              <div class="result-grid">
                <!-- 1. 总帧数 -->
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">总帧数</div>
                    <div class="trend-indicator">📊</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">{{ berStats.totalFrames }}</span>
                      <span class="unit">帧</span>
                    </div>
                    <div class="description">从帧1到帧{{ berStats.totalFrames }}</div>
                  </div>
                </div>

                <!-- 2. 正确帧数 -->
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">正确帧数</div>
                    <div class="trend-indicator">✅</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">{{ berStats.correctFrames }}</span>
                      <span class="unit">帧</span>
                    </div>
                    <div class="description">完全正确的帧(无比特错误)</div>
                  </div>
                </div>

                <!-- 3. 错误帧数 -->
                <div class="result-card" :class="berStats.errorFrames > 0 ? 'warning' : 'normal'">
                  <div class="card-header">
                    <div class="card-title">错误帧数</div>
                    <div class="trend-indicator">⚠️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">{{ berStats.errorFrames }}</span>
                      <span class="unit">帧</span>
                    </div>
                    <div class="description">有比特错误的帧(≥1bit错)</div>
                  </div>
                </div>

                <!-- 4. 丢失帧数 -->
                <div class="result-card" :class="berStats.lostFrames > 0 ? 'warning' : 'normal'">
                  <div class="card-header">
                    <div class="card-title">丢失帧数</div>
                    <div class="trend-indicator">❌</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">{{ berStats.lostFrames }}</span>
                      <span class="unit">帧</span>
                    </div>
                    <div class="description">帧号不连续的丢失帧</div>
                  </div>
                </div>

                <!-- 5. 误帧率 (FER) -->
                <div class="result-card" :class="berStats.fer > 0.01 ? 'error' : berStats.fer > 0 ? 'warning' : 'normal'">
                  <div class="card-header">
                    <div class="card-title">误帧率 (FER)</div>
                    <div class="trend-indicator">📊</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">{{ (berStats.fer * 100).toFixed(2) }}</span>
                      <span class="unit">%</span>
                    </div>
                    <div class="description">(错误帧 + 丢失帧) / 总帧数</div>
                  </div>
                </div>

                <!-- 6. 误比特率 (BER) -->
                <div class="result-card" :class="berStats.ber > 1e-4 ? 'error' : berStats.ber > 1e-6 ? 'warning' : 'normal'">
                  <div class="card-header">
                    <div class="card-title">误比特率 (BER)</div>
                    <div class="trend-indicator">🎯</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">{{ berStats.ber > 0 ? berStats.ber.toExponential(2) : '0' }}</span>
                    </div>
                    <div class="description">错误比特 / 总比特</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 测距指标 -->
            <div v-else-if="tab.id === 'ranging'" class="result-section">
              <div class="section-title">
                <i>📏</i>
                <span>测距精度</span>
              </div>
              <div class="result-grid">
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">测距精度RMS</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">0.85</span>
                      <span class="unit">m</span>
                    </div>
                    <div class="description">测距精度均方根误差</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">测距系统偏差</div>
                    <div class="trend-indicator">📉</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">-0.12</span>
                      <span class="unit">m</span>
                    </div>
                    <div class="description">测距系统的固有偏差</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">码相位误差</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">23.4</span>
                      <span class="unit">ns</span>
                    </div>
                    <div class="description">伪码相位测量误差</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">多普勒频移</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">142.6</span>
                      <span class="unit">Hz</span>
                    </div>
                    <div class="description">检测到的多普勒频移值</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">信号锁定时间</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">2.34</span>
                      <span class="unit">s</span>
                    </div>
                    <div class="description">测距信号首次锁定时间</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">跟踪环路信噪比</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">45.8</span>
                      <span class="unit">dB-Hz</span>
                    </div>
                    <div class="description">测距跟踪环路的信噪比</div>
                  </div>
                </div>
              </div>
            </div>


            <!-- 消息测试指标 -->
            <div v-else-if="tab.id === 'message'" class="result-section">
              <div class="section-title">
                <i>💬</i>
                <span>传输统计</span>
              </div>
              <div class="result-grid">
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">消息成功率</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">99.7</span>
                      <span class="unit">%</span>
                    </div>
                    <div class="description">消息传输成功率统计</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">消息总数</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">15,678</span>
                      <span class="unit">条</span>
                    </div>
                    <div class="description">测试期间传输的消息总数</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">平均消息延时</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">45.2</span>
                      <span class="unit">ms</span>
                    </div>
                    <div class="description">消息传输的平均延迟时间</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">消息吞吐量</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">1,024</span>
                      <span class="unit">msg/s</span>
                    </div>
                    <div class="description">每秒处理的消息数量</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">队列深度</div>
                    <div class="trend-indicator">📉</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">12</span>
                      <span class="unit">条</span>
                    </div>
                    <div class="description">消息队列当前深度</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">带宽利用率</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">78.5</span>
                      <span class="unit">%</span>
                    </div>
                    <div class="description">消息传输的带宽利用率</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="chart-container">
            <div class="chart-header">
              <h4>{{ tab.name }}趋势图</h4>
              <select class="time-range-select">
                <option>最近1小时</option>
                <option>最近6小时</option>
                <option>最近24小时</option>
                <option>最近7天</option>
              </select>
            </div>
            <div class="chart-placeholder">
              <div class="chart-content">
                📊 {{ tab.name }}图表区域
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
  import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
  import axios from 'axios'

  const API_BASE = '/api'

  const props = defineProps({
    activeTab: String,
    loraFileName: String,
    loraFileData: String
  })

  const emit = defineEmits(['update-tab'])

  const resultTabs = [
    { id: 'ber', name: '误码率', icon: '🎯' },
    { id: 'ranging', name: '测距', icon: '📏' },
    { id: 'message', name: '消息测试', icon: '💬' }
  ]

  // 发送相关
  const sendInterval = ref(1)
  const sendCount = ref(0)
  const isSending = ref(false)
  const sendStatus = ref(null)
  let sendTimer = null  // 定时器引用

  // 接收相关
  const receivedMessages = ref([])
  let lastReceivedFrameCount = 0

  // SSE
  let eventSource = null
  const sseConnected = ref(false)

  // 发送的原始数据
  const sentDataHex = ref('')

  // 误码率统计
  const berStats = reactive({
    totalFrames: 0,
    receivedFrames: 0,
    correctFrames: 0,
    errorFrames: 0,
    lostFrames: 0,
    fer: 0,
    ber: 0,
    errorBits: 0,
    totalBits: 0
  })

  // 监听props变化
  watch(() => props.loraFileData, (newData) => {
    console.log('👀 ResultDisplay: loraFileData changed, length:', newData?.length || 0)
    if (newData) {
      sentDataHex.value = newData
      berStats.totalBits = newData.length * 4
    }
  }, { immediate: true })

  // 发送一次
  const sendOnce = async () => {
    console.log('📤 sendOnce调用')
    console.log('  props.loraFileData:', props.loraFileData ? '有数据' : '无数据')
    console.log('  sseConnected:', sseConnected.value)

    if (!props.loraFileData) {
      console.error('❌ 没有文件数据，停止发送')
      stopAutoSend()  // 强制停止
      alert('请先在"参数设置"页面选择文件')
      return
    }

    if (!sseConnected.value) {
      console.error('❌ SSE未连接，停止发送')
      stopAutoSend()  // 强制停止
      alert('SSE未连接,请等待连接成功')
      return
    }

    try {
      sendCount.value++
      if (sendCount.value > 255) {
        sendCount.value = 1
      }

      console.log(`📨 发送帧#${sendCount.value}`)

      const response = await axios.post(`${API_BASE}/lora/send`, {
        timing_enable: 0,
        timing_time: 0,
        data_content: props.loraFileData,
        frame_count: sendCount.value
      })

      if (response.data.success) {
        sendStatus.value = {
          type: 'success',
          message: `✅ 发送成功 (帧#${sendCount.value})`
        }
        console.log(`✅ 帧#${sendCount.value} 发送成功`)
      }
    } catch (error) {
      sendStatus.value = {
        type: 'error',
        message: `❌ 发送失败: ${error.response?.data?.detail || error.message}`
      }
      console.error('❌ 发送失败:', error)
      stopAutoSend()  // 发送失败时停止
    }
  }

  // 开始循环发送
  const startAutoSend = () => {
    console.log('🔄 startAutoSend调用')
    console.log('  props.loraFileData:', props.loraFileData ? '有数据' : '无数据')
    console.log('  sseConnected:', sseConnected.value)
    console.log('  当前isSending:', isSending.value)

    if (!props.loraFileData || !sseConnected.value) {
      console.error('❌ 条件不满足，无法开始循环发送')
      return
    }

    if (isSending.value) {
      console.warn('⚠️ 已经在循环发送中，忽略重复调用')
      return
    }

    // 清零统计
    clearStats()
    sendCount.value = 0
    isSending.value = true

    console.log('✅ 开始循环发送, 间隔:', sendInterval.value, '秒')

    // 立即发送第一次
    sendOnce()

    // 启动定时器
    sendTimer = setInterval(() => {
      console.log('⏰ 定时器触发, isSending:', isSending.value)
      if (isSending.value) {
        sendOnce()
      } else {
        console.warn('⚠️ isSending为false，但定时器还在运行，清除定时器')
        stopAutoSend()
      }
    }, sendInterval.value * 1000)

    console.log('✅ 定时器已启动, ID:', sendTimer)
  }

  // 停止循环发送
  const stopAutoSend = () => {
    console.log('⏹️ stopAutoSend调用')
    console.log('  当前sendTimer:', sendTimer)
    console.log('  当前isSending:', isSending.value)

    if (sendTimer) {
      clearInterval(sendTimer)
      sendTimer = null
      console.log('✅ 定时器已清除')
    }

    isSending.value = false
    console.log('✅ isSending已设置为false')
  }

  // 清零统计
  const clearStats = () => {
    receivedMessages.value = []
    lastReceivedFrameCount = 0
    berStats.totalFrames = 0
    berStats.receivedFrames = 0
    berStats.correctFrames = 0
    berStats.errorFrames = 0
    berStats.lostFrames = 0
    berStats.fer = 0
    berStats.ber = 0
    berStats.errorBits = 0
    berStats.totalBits = 0
  }

  // 清空接收数据
  const clearReceivedData = () => {
    receivedMessages.value = []
    sentDataHex.value = ''
    clearStats()
    sendStatus.value = {
      type: 'info',
      message: 'ℹ️ 数据已清空'
    }
  }

  // 格式化预览
  const formatHexPreview = (hex) => {
    if (!hex) return ''
    return hex.length > 64 ? hex.substring(0, 64) + '...' : hex
  }

  // 处理接收到的消息
  const handleReceivedMessage = (msg) => {
    const frameCount = msg.frame_count || 0
    console.log(`📥 SSE推送: 收到帧#${frameCount}`)

    // 检测丢帧
    if (lastReceivedFrameCount > 0 && frameCount > lastReceivedFrameCount + 1) {
      const lostCount = frameCount - lastReceivedFrameCount - 1
      console.warn(`⚠️ 检测到丢帧: 帧#${lastReceivedFrameCount + 1} 到 帧#${frameCount - 1}, 共${lostCount}帧`)

      for (let i = 1; i <= lostCount; i++) {
        const lostFrameNum = lastReceivedFrameCount + i
        receivedMessages.value.push({
          id: `lost_${lostFrameNum}_${Date.now()}`,
          time: new Date().toLocaleTimeString(),
          frame_count: lostFrameNum,
          data_hex: '(丢失)',
          data_bytes: 0,
          duration_ms: 0,
          isLost: true
        })
        berStats.lostFrames++
      }
    }

    // 添加接收帧
    const receivedMsg = {
      id: `recv_${frameCount}_${Date.now()}`,
      time: new Date().toLocaleTimeString(),
      frame_count: frameCount,
      data_hex: msg.data_hex,
      data_bytes: msg.data_bytes,
      duration_ms: msg.duration_ms,
      isLost: false,
      hasError: false
    }

    berStats.receivedFrames++
    lastReceivedFrameCount = frameCount

    // 计算该帧的比特错误
    let frameHasError = false
    if (sentDataHex.value) {
      frameHasError = checkFrameError(msg.data_hex)
      receivedMsg.hasError = frameHasError

      if (frameHasError) {
        berStats.errorFrames++
        console.log(`❌ 帧#${frameCount} 有比特错误`)
      } else {
        berStats.correctFrames++
        console.log(`✅ 帧#${frameCount} 完全正确`)
      }
    }

    receivedMessages.value.push(receivedMsg)

    // 更新总帧数
    berStats.totalFrames = Math.max(berStats.totalFrames, frameCount)

    // 计算误帧率
    if (berStats.totalFrames > 0) {
      const totalErrorFrames = berStats.errorFrames + berStats.lostFrames
      berStats.fer = totalErrorFrames / berStats.totalFrames
    }

    // 计算误比特率
    if (berStats.totalBits > 0) {
      berStats.ber = berStats.errorBits / berStats.totalBits
    }

    // 限制列表长度
    if (receivedMessages.value.length > 100) {
      receivedMessages.value.shift()
    }
  }

  // 检查单帧是否有错误
  const checkFrameError = (receivedHex) => {
    const sentHex = sentDataHex.value
    if (!sentHex) return false

    let frameErrorBits = 0
    const minLength = Math.min(sentHex.length, receivedHex.length)

    for (let i = 0; i < minLength; i += 2) {
      const sentByte = parseInt(sentHex.substr(i, 2), 16)
      const recvByte = parseInt(receivedHex.substr(i, 2), 16)

      if (sentByte !== recvByte) {
        const xor = sentByte ^ recvByte
        frameErrorBits += countBits(xor)
      }
    }

    const lengthDiff = Math.abs(sentHex.length - receivedHex.length)
    frameErrorBits += lengthDiff * 4

    berStats.errorBits += frameErrorBits

    return frameErrorBits > 0
  }

  // 计算比特数
  const countBits = (n) => {
    let count = 0
    while (n) {
      count += n & 1
      n >>= 1
    }
    return count
  }

  // 连接SSE
  const connectSSE = () => {
    if (eventSource) {
      eventSource.close()
    }

    console.log('🔗 正在连接SSE...')
    eventSource = new EventSource(`${API_BASE}/lora/stream`)

    eventSource.onopen = () => {
      sseConnected.value = true
      console.log('✅ SSE 连接成功')
    }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'connected') {
          console.log('📡 SSE 初始连接:', data.message)
        } else if (data.type === 'lora_receive') {
          handleReceivedMessage(data.data)
        }
      } catch (error) {
        console.error('❌ SSE 消息解析错误:', error)
      }
    }

    eventSource.onerror = (error) => {
      sseConnected.value = false
      console.error('❌ SSE 连接错误')

      setTimeout(() => {
        if (!sseConnected.value) {
          console.log('🔄 尝试重新连接SSE...')
          connectSSE()
        }
      }, 5000)
    }
  }

  // 重新连接
  const reconnectSSE = () => {
    console.log('🔄 手动重新连接SSE')
    connectSSE()
  }

  // 组件挂载
  onMounted(() => {
    console.log('🎬 ResultDisplay mounted')
    connectSSE()
  })

  // 组件卸载 - 重要！！！
  onUnmounted(() => {
    console.log('🛑 ResultDisplay unmounting, 清理资源')

    // 强制停止发送
    stopAutoSend()

    // 关闭SSE
    if (eventSource) {
      eventSource.close()
      eventSource = null
      console.log('⏹️ SSE 连接已关闭')
    }
  })
</script>

  <style scoped >
  .section {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    backdrop-filter: blur(10px);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }

  .section:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  }

  .section-header {
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    padding: 20px 30px;
    border-bottom: 3px solid #17a2b8;
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .header-icon {
    font-size: 24px;
  }

  .section-header h2 {
    font-size: 20px;
    font-weight: 600;
    color: #2c3e50;
    margin: 0;
    flex: 1;
  }

  .result-controls {
    display: flex;
    gap: 10px;
  }

  .export-btn,
  .refresh-btn {
    padding: 8px 16px;
    border: 2px solid #17a2b8;
    background: white;
    color: #17a2b8;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.3s ease;
  }

    .export-btn:hover,
    .refresh-btn:hover {
      background: #17a2b8;
      color: white;
    }

  .tab-container {
    background: #f8f9fa;
  }

  .tab-nav {
    display: flex;
    background: #fff;
    border-bottom: 2px solid #e9ecef;
    overflow-x: auto;
  }

  .tab-button {
    background: none;
    border: none;
    padding: 15px 25px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    color: #6c757d;
    transition: all 0.3s ease;
    position: relative;
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: 8px;
  }

    .tab-button:hover {
      background: #f8f9fa;
      color: #007bff;
    }

    .tab-button.active {
      color: #007bff;
      background: #fff;
    }

      .tab-button.active::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(135deg, #007bff, #0056b3);
        border-radius: 2px 2px 0 0;
      }

  .tab-content {
    padding: 30px;
    background: white;
  }

  .tab-panel {
    animation: fadeIn 0.3s ease;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }

    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .summary-card {
    background: linear-gradient(135deg, #e3f2fd, #bbdefb);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    border: 2px solid #2196f3;
  }

  .summary-title {
    font-size: 14px;
    color: #1976d2;
    margin-bottom: 10px;
    font-weight: 500;
  }

  .summary-value {
    font-size: 24px;
    font-weight: bold;
    color: #0d47a1;
  }

    .summary-value.good {
      color: #2e7d32;
    }

  .status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
    animation: pulse 2s infinite;
  }

    .status-dot.good {
      background: #28a745;
    }

  .result-sections {
    display: flex;
    flex-direction: column;
    gap: 30px;
  }

  .result-section {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 25px;
    border: 2px solid #e9ecef;
    transition: all 0.3s ease;
  }

    .result-section:hover {
      border-color: #007bff;
      box-shadow: 0 8px 25px rgba(0, 123, 255, 0.1);
    }

  .section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 18px;
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e9ecef;
  }

  .result-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
  }

  .result-card {
    background: linear-gradient(135deg, #f8f9fa, #fff);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #007bff;
    transition: all 0.3s ease;
  }

    .result-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    }

    .result-card.normal {
      border-left-color: #28a745;
    }

    .result-card.warning {
      border-left-color: #ffc107;
    }

    .result-card.error {
      border-left-color: #dc3545;
    }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }

  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
  }

  .trend-indicator {
    font-size: 18px;
  }

  .value-display {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 12px;
  }

  .value {
    font-size: 28px;
    font-weight: bold;
    color: #2c3e50;
    font-family: 'Courier New', monospace;
  }

  .unit {
    font-size: 16px;
    color: #6c757d;
    font-weight: 500;
  }

  .description {
    font-size: 13px;
    color: #6c757d;
    line-height: 1.4;
  }

  .chart-container {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    border: 2px solid #e9ecef;
    margin-top: 30px;
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

    .chart-header h4 {
      margin: 0;
      color: #2c3e50;
      font-size: 18px;
    }

  .time-range-select {
    padding: 6px 12px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    background: white;
  }

  .chart-placeholder {
    height: 200px;
    background: white;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #dee2e6;
  }

  .chart-content {
    text-align: center;
    color: #6c757d;
    font-size: 16px;
  }

  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
      opacity: 1;
    }

    50% {
      transform: scale(1.05);
      opacity: 0.8;
    }
  }

  /* 新增: 文件读取区域样式 */
  .file-reader-section {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 30px;
    border: 2px solid #e9ecef;
    transition: all 0.3s ease;
  }

    .file-reader-section:hover {
      border-color: #007bff;
      box-shadow: 0 8px 25px rgba(0, 123, 255, 0.1);
    }

  .file-reader-header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 18px;
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #e9ecef;
  }

  .file-reader-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .file-input-group {
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .file-input {
    display: none;
  }

  .file-label {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 20px;
    background: white;
    border: 2px dashed #ced4da;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 14px;
    color: #6c757d;
  }

    .file-label:hover {
      border-color: #007bff;
      background: #f8f9fa;
      color: #007bff;
    }

    .file-label i {
      font-size: 18px;
    }

  .read-file-btn {
    padding: 12px 24px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
  }

    .read-file-btn:hover:not(:disabled) {
      background: #0056b3;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
    }

    .read-file-btn:disabled {
      background: #6c757d;
      cursor: not-allowed;
      opacity: 0.6;
    }

  /* 文件内容显示 */
  .file-content-display {
    background: white;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    overflow: hidden;
  }

  .content-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    background: #f8f9fa;
    border-bottom: 2px solid #e9ecef;
    font-weight: 600;
    color: #2c3e50;
  }

  .copy-btn {
    padding: 6px 12px;
    background: #28a745;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 5px;
  }

    .copy-btn:hover {
      background: #218838;
      transform: translateY(-1px);
    }

  .content-body {
    max-height: 400px;
    overflow-y: auto;
    padding: 15px 20px;
    background: #1e1e1e;
  }

  .hex-display {
    font-family: 'Courier New', Consolas, monospace;
    font-size: 13px;
    line-height: 1.6;
  }

  .hex-line {
    display: flex;
    gap: 20px;
    margin-bottom: 4px;
  }

  .line-number {
    color: #858585;
    user-select: none;
    min-width: 80px;
  }

  .hex-bytes {
    color: #4ec9b0;
    flex: 1;
    min-width: 400px;
  }

  .ascii-chars {
    color: #ce9178;
    min-width: 150px;
    font-size: 12px;
  }

  .content-footer {
    display: flex;
    justify-content: space-between;
    padding: 12px 20px;
    background: #f8f9fa;
    border-top: 2px solid #e9ecef;
    font-size: 13px;
    color: #6c757d;
  }

  /* 滚动条样式 */
  .content-body::-webkit-scrollbar {
    width: 10px;
  }

  .content-body::-webkit-scrollbar-track {
    background: #2d2d2d;
  }

  .content-body::-webkit-scrollbar-thumb {
    background: #555;
    border-radius: 5px;
  }

    .content-body::-webkit-scrollbar-thumb:hover {
      background: #777;
    }

  /* 响应式 */
  @media (max-width: 768px) {
    .file-input-group {
      flex-direction: column;
    }

    .file-label {
      width: 100%;
    }

    .read-file-btn {
      width: 100%;
      justify-content: center;
    }

    .hex-line {
      flex-direction: column;
      gap: 5px;
    }

    .ascii-chars {
      display: none;
    }
  }

  .file-sender-section,
  .receive-section {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 30px;
    border: 2px solid #e9ecef;
  }

  .file-sender-header,
  .receive-header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 18px;
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #e9ecef;
  }

  .receive-header {
    justify-content: space-between;
  }

  .clear-receive-btn {
    padding: 6px 12px;
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .file-input-group {
    display: flex;
    gap: 15px;
    align-items: center;
  }

  .file-input {
    display: none;
  }

  .file-label {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 20px;
    background: white;
    border: 2px dashed #ced4da;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
  }

    .file-label:hover {
      border-color: #007bff;
    }

  .send-lora-btn {
    padding: 12px 24px;
    background: #28a745;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }

    .send-lora-btn:disabled {
      background: #6c757d;
      cursor: not-allowed;
    }

  .file-preview {
    background: white;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    overflow: hidden;
    margin-top: 15px;
  }

  .preview-header {
    display: flex;
    justify-content: space-between;
    padding: 10px 15px;
    background: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
    font-size: 13px;
    font-weight: 600;
  }

  .preview-content {
    padding: 15px;
    font-family: 'Courier New', monospace;
    color: #2c3e50;
    word-break: break-all;
  }

  .send-status {
    margin-top: 15px;
    padding: 12px 15px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

    .send-status.success {
      background: #d4edda;
      color: #155724;
    }

    .send-status.error {
      background: #f8d7da;
      color: #721c24;
    }

  .receive-list {
    max-height: 400px;
    overflow-y: auto;
  }

  .receive-item {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 10px;
    display: grid;
    grid-template-columns: 100px 80px 1fr 150px;
    gap: 15px;
    align-items: center;
  }

  .receive-time {
    font-size: 13px;
    color: #6c757d;
    font-family: monospace;
  }

  .receive-frame {
    font-weight: 600;
    color: #007bff;
    font-size: 14px;
  }

  .receive-data {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .data-hex {
    font-family: 'Courier New', monospace;
    color: #2c3e50;
    font-size: 13px;
    word-break: break-all;
  }

  .receive-stats {
    display: flex;
    gap: 10px;
    font-size: 12px;
    color: #6c757d;
  }

  .empty-receive {
    text-align: center;
    padding: 40px;
    color: #adb5bd;
  }

    .empty-receive i {
      font-size: 48px;
      display: block;
      margin-bottom: 10px;
    }

    .receive-item.frame-lost {
      background: #fff5f5;
      border-left: 3px solid #dc3545;
    }

    .frame-lost .data-hex {
      color: #dc3545;
      font-style: italic;
    }

    .connection-status {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      background: #f8d7da;
      color: #721c24;
      border: 1px solid #f5c6cb;
    }

      .connection-status.connected {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
      }

      .connection-status .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
      }

      .connection-status.connected .status-dot {
        animation: pulse 2s infinite;
      }

    @keyframes pulse {
      0%, 100% {
        opacity: 1;
        transform: scale(1);
      }

      50% {
        opacity: 0.6;
        transform: scale(1.2);
      }
    }

    .result-controls {
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .send-lora-btn:disabled {
      background: #6c757d;
      cursor: not-allowed;
      opacity: 0.6;
    }

    .lost-badge {
      background: #dc3545;
      color: white;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      margin-left: 8px;
    }

    .receive-item.frame-lost {
      background: #fff5f5;
      border-left: 3px solid #dc3545;
    }

    .frame-lost .data-hex {
      color: #dc3545;
      font-style: italic;
    }

    .receive-item.frame-error {
      background: #fff8e5;
      border-left: 3px solid #ffc107;
    }

    .frame-error .data-hex {
      color: #856404;
    }
    .send-controls {
      display: flex;
      flex-direction: column;
      gap: 15px;
      background: #f8f9fa;
      padding: 20px;
      border-radius: 8px;
    }

    .control-group {
      display: flex;
      align-items: center;
      gap: 10px;
    }

      .control-group label {
        font-weight: 600;
        color: #2c3e50;
        min-width: 120px;
      }

    .interval-input {
      width: 120px;
      padding: 8px 12px;
      border: 2px solid #e9ecef;
      border-radius: 6px;
      font-size: 16px;
    }

      .interval-input:focus {
        outline: none;
        border-color: #007bff;
      }

    .control-buttons {
      display: flex;
      gap: 10px;
    }

    .send-once-btn,
    .send-auto-btn,
    .stop-btn {
      flex: 1;
      padding: 12px 24px;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .send-once-btn {
      background: #17a2b8;
      color: white;
    }

      .send-once-btn:hover:not(:disabled) {
        background: #138496;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(23, 162, 184, 0.3);
      }

    .send-auto-btn {
      background: #28a745;
      color: white;
    }

      .send-auto-btn:hover:not(:disabled) {
        background: #218838;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
      }

    .stop-btn {
      background: #dc3545;
      color: white;
    }

      .stop-btn:hover {
        background: #c82333;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
      }

    .send-once-btn:disabled,
    .send-auto-btn:disabled {
      background: #6c757d;
      cursor: not-allowed;
      opacity: 0.6;
    }

    .send-status-box {
      display: flex;
      gap: 20px;
      background: white;
      padding: 15px;
      border-radius: 8px;
      border: 2px solid #e9ecef;
    }

    .status-item {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .status-label {
      font-weight: 600;
      color: #6c757d;
    }

    .status-value {
      font-size: 18px;
      font-weight: 700;
      color: #2c3e50;
    }

      .status-value.sending {
        color: #28a745;
        animation: pulse 1.5s infinite;
      }

    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }

      50% {
        opacity: 0.6;
      }
    }

    .info-tip {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 16px;
      background: #e3f2fd;
      border-left: 4px solid #2196f3;
      border-radius: 4px;
      font-size: 14px;
      color: #1565c0;
    }

    .preview-note {
      margin-top: 10px;
      padding: 8px 12px;
      background: #fff3cd;
      border-radius: 4px;
      font-size: 13px;
      color: #856404;
      font-weight: 500;
    }

    .no-file-warning {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 20px;
      background: #fff3cd;
      border: 2px solid #ffc107;
      border-radius: 8px;
      color: #856404;
      font-weight: 500;
      font-size: 16px;
      margin-bottom: 20px;
    }

    .selected-file-info {
      background: #e3f2fd;
      border: 2px solid #2196f3;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 20px;
    }

    .file-badge {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px;
      background: white;
      border-radius: 8px;
      margin-bottom: 15px;
      font-weight: 500;
    }

    .file-size {
      color: #6c757d;
      font-size: 14px;
    }

    /* 接收数据颜色优化 */
    .receive-item {
      background: white;
      border: 1px solid #e9ecef;
      border-radius: 8px;
      padding: 15px;
      margin-bottom: 10px;
      display: grid;
      grid-template-columns: 100px 120px 1fr;
      gap: 15px;
      align-items: center;
      transition: all 0.3s ease;
    }

      .receive-item.frame-correct {
        border-left: 4px solid #28a745;
        background: #f8fff9;
      }

      .receive-item.frame-error {
        border-left: 4px solid #ffc107;
        background: #fffef8;
      }

      .receive-item.frame-lost {
        border-left: 4px solid #dc3545;
        background: #fff5f5;
      }

    .frame-num-correct {
      color: #28a745;
      font-weight: 700;
    }

    .frame-num-error {
      color: #ffc107;
      font-weight: 700;
    }

    .frame-num-lost {
      color: #dc3545;
      font-weight: 700;
    }
</style>
