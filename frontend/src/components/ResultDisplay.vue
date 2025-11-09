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

              <!-- 文件发送区域 -->
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

                  <!-- 发送控制 -->
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
                      <span class="status-label">当前帧号:</span>
                      <span class="status-value">{{ sendCount }}</span>
                    </div>
                    <div class="status-item">
                      <span class="status-label">循环次数:</span>
                      <span class="status-value">{{ cycleCount }}</span>
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
                    <i>{{ sendStatus.type === 'success' ? '✅' : sendStatus.type === 'error' ? '❌' : 'ℹ️' }}</i>
                    {{ sendStatus.message }}
                  </div>
                </div>
              </div>

              <!-- 接收数据显示 -->
              <div class="receive-section">
                <div class="receive-header">
                  <i>📥</i>
                  <span>接收数据</span>
                  <div class="receive-controls">
                    <button class="clear-receive-btn" @click="clearReceivedData">
                      <i>🗑️</i>
                      清空
                    </button>
                  </div>
                </div>
                <div class="receive-list" ref="receiveListRef">
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
                  </div>

                  <div v-if="receivedMessages.length === 0" class="empty-receive">
                    <i>📭</i>
                    <p>暂无接收数据</p>
                  </div>
                </div>
              </div>

              <!-- 误码率统计 -->
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
                    <div class="description">{{ getTotalFramesDescription() }}</div>
                  </div>
                </div>

                <!-- 其他统计卡片保持不变 -->
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

          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
  import { ref, reactive, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
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
  const sendCount = ref(-1)  // 🔧 初始化为 -1
  const cycleCount = ref(0)
  const isSending = ref(false)
  const sendStatus = ref(null)
  const actualSentFrames = ref(0)
  let sendTimer = null

  // 接收相关
  const receivedMessages = ref([])
  const receiveListRef = ref(null)  
  let lastReceivedFrameCount = null

  // SSE
  let eventSource = null
  const sseConnected = ref(false)

  // 发送的原始数据
  const sentDataHex = ref('')

  // 组件是否已挂载的标志
  const isMounted = ref(false)

  // 计算属性检查是否可以发送
  const canSend = computed(() => {
    return isMounted.value && props.loraFileData && sseConnected.value
  })

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
    totalBits: 0,
    bitsPerFrame: 0  // 🔧 新增：每帧的比特数
  })

  // 生成总帧数描述
  const getTotalFramesDescription = () => {
    if (berStats.totalFrames === 0) {
      return '从帧0到帧0'
    }

    if (cycleCount.value === 0) {
      return `从帧0到帧${sendCount.value} (第1轮)`
    } else {
      return `第${cycleCount.value + 1}轮, 当前帧#${sendCount.value} (共${berStats.totalFrames}帧)`
    }
  }

  // 监听文件数据变化
  watch(() => props.loraFileData, (newData, oldData) => {
    console.log('👀 ResultDisplay: loraFileData changed')
    console.log('  旧值长度:', oldData?.length || 0)
    console.log('  新值长度:', newData?.length || 0)

    if (newData) {
      sentDataHex.value = newData
      berStats.bitsPerFrame = newData.length * 4  // 🔧 修复2：记录每帧比特数
      console.log('  每帧比特数:', berStats.bitsPerFrame)
    } else {
      console.log('⚠️ loraFileData 被清空，停止所有发送')
      forceStopAll()
      sentDataHex.value = ''
      berStats.bitsPerFrame = 0
    }
  })

  // 强制停止所有操作
  const forceStopAll = () => {
    console.log('🛑 forceStopAll: 强制停止所有操作')

    if (sendTimer) {
      clearInterval(sendTimer)
      sendTimer = null
      console.log('  ✅ 定时器已清除')
    }

    isSending.value = false
    window.failCount = 0
    console.log('  ✅ 所有操作已停止')
  }

  // 发送一次
  const sendOnce = async () => {
    console.log('📤 sendOnce 调用')

    if (!canSend.value) {
      console.error('❌ 发送条件不满足')
      forceStopAll()

      if (!props.loraFileData) {
        sendStatus.value = { type: 'error', message: '❌ 请先选择LoRa传输文件' }
      } else if (!sseConnected.value) {
        sendStatus.value = { type: 'error', message: '❌ SSE未连接' }
      }
      return
    }

    try {
      sendCount.value++
      if (sendCount.value > 255) {
        sendCount.value = 0
        cycleCount.value++
        console.log(`🔄 进入第 ${cycleCount.value + 1} 轮循环`)
      }

      console.log(`📨 准备发送帧#${sendCount.value} (第${cycleCount.value + 1}轮)`)

      const response = await axios.post(`${API_BASE}/lora/send`, {
        timing_enable: 0,
        timing_time: 0,
        data_content: props.loraFileData,
        frame_count: sendCount.value
      }, {
        timeout: 5000
      })

      if (response.data.success) {
        actualSentFrames.value++
        window.failCount = 0

        sendStatus.value = {
          type: 'success',
          message: `✅ 发送成功 (帧#${sendCount.value})`
        }
        console.log(`✅ 帧#${sendCount.value} 发送成功 (总计:${actualSentFrames.value}帧)`)
      } else {
        throw new Error(response.data.message || '发送失败')
      }
    } catch (error) {
      let errorMessage = '❌ 发送失败: '

      if (error.code === 'ECONNABORTED') {
        errorMessage += '请求超时'
        console.error(`❌ 帧#${sendCount.value} 发送超时`)
      } else if (error.response) {
        errorMessage += error.response.data?.detail || error.response.statusText
        console.error(`❌ 帧#${sendCount.value} 发送失败:`, error.response.status, error.response.data)
      } else if (error.request) {
        errorMessage += '网络错误，无响应'
        console.error(`❌ 帧#${sendCount.value} 网络错误:`, error.message)
      } else {
        errorMessage += error.message
        console.error(`❌ 帧#${sendCount.value} 发送异常:`, error)
      }

      sendStatus.value = {
        type: 'error',
        message: errorMessage
      }

      // 发送失败时，帧号回退
      if (sendCount.value === 0) {
        sendCount.value = 255
        if (cycleCount.value > 0) {
          cycleCount.value--
        }
      } else {
        sendCount.value--
      }

      // 连续失败3次则停止
      if (!window.failCount) window.failCount = 0
      window.failCount++

      if (window.failCount >= 3) {
        console.error('❌ 连续失败3次，自动停止')
        forceStopAll()
        sendStatus.value = {
          type: 'error',
          message: '❌ 连续失败3次，已自动停止'
        }
      }
    }
  }

  // 开始循环发送
  const startAutoSend = () => {
    console.log('🔄 startAutoSend 调用')

    if (!canSend.value) {
      console.error('❌ 发送条件不满足')
      alert('❌ 请确保已选择文件且SSE已连接')
      return
    }

    if (isSending.value) {
      console.warn('⚠️ 已经在循环发送中')
      return
    }

    if (sendTimer) {
      console.warn('⚠️ 检测到遗留定时器，先清理')
      clearInterval(sendTimer)
      sendTimer = null
    }

    clearStats()
    sendCount.value = -1
    cycleCount.value = 0
    actualSentFrames.value = 0
    isSending.value = true
    window.failCount = 0

    console.log('✅ 开始循环发送, 间隔:', sendInterval.value, '秒')

    sendOnce()

    sendTimer = setInterval(() => {
      console.log('⏰ 定时器触发')

      if (!canSend.value || !isSending.value) {
        console.warn('⚠️ 条件不满足，停止发送')
        stopAutoSend()
        return
      }

      sendOnce()
    }, sendInterval.value * 1000)

    console.log('✅ 定时器已启动, ID:', sendTimer)
  }

  // 停止循环发送
  const stopAutoSend = () => {
    console.log('⏹️ stopAutoSend 调用')

    if (sendTimer) {
      clearInterval(sendTimer)
      sendTimer = null
      console.log('  ✅ 定时器已清除')
    }

    isSending.value = false
    window.failCount = 0
    console.log('  ✅ isSending已设置为false')
  }

  // 清零统计
  const clearStats = () => {
    receivedMessages.value = []
    lastReceivedFrameCount = null
    berStats.totalFrames = 0
    berStats.receivedFrames = 0
    berStats.correctFrames = 0
    berStats.errorFrames = 0
    berStats.lostFrames = 0
    berStats.fer = 0
    berStats.ber = 0
    berStats.errorBits = 0
    berStats.totalBits = 0
    actualSentFrames.value = 0
  }

  // 清空接收数据
  const clearReceivedData = () => {
    console.log('🗑️ 清空接收数据')
    console.log('  清空前 - sendCount:', sendCount.value, 'cycleCount:', cycleCount.value, 'actualSent:', actualSentFrames.value)

    receivedMessages.value = []
    clearStats()
    sendCount.value = -1
    cycleCount.value = 0
    actualSentFrames.value = 0

    console.log('  清空后 - sendCount:', sendCount.value, 'cycleCount:', cycleCount.value, 'actualSent:', actualSentFrames.value)

    sendStatus.value = { type: 'info', message: 'ℹ️ 数据已清空' }
  }

  // 格式化预览
  const formatHexPreview = (hex) => {
    if (!hex) return ''
    return hex.length > 64 ? hex.substring(0, 64) + '...' : hex
  }

  // 🔧 修复1：处理接收到的消息
  const handleReceivedMessage = (msg) => {
    const frameCount = msg.frame_count || 0
    console.log(`\n📥 SSE推送: 收到帧#${frameCount}`)
    console.log(`  已发送: ${actualSentFrames.value}帧`)
    console.log(`  已接收: ${berStats.receivedFrames}帧`)
    console.log(`  isSending: ${isSending.value}`)
    console.log(`  sendCount: ${sendCount.value}`)

    // 🔧 修复1：更好的旧数据判断
    if (!isSending.value && sendCount.value < 0) {
      console.warn(`⚠️ 忽略旧数据: 帧#${frameCount} (循环发送未开始)`)
      return
    }

    // 检查帧号是否合理
    if (!isFrameCountValid(frameCount)) {
      console.warn(`⚠️ 忽略异常帧: 帧#${frameCount} (上一个接收帧=${lastReceivedFrameCount})`)
      return
    }

    // 检测丢帧
    if (lastReceivedFrameCount !== null) {
      const expectedNext = (lastReceivedFrameCount + 1) % 256

      if (frameCount !== expectedNext) {
        const lostCount = calculateLostFrames(lastReceivedFrameCount, frameCount)

        if (lostCount > 0 && lostCount < 128) {
          console.warn(`⚠️ 检测到丢帧: ${lostCount}帧`)

          let currentLost = lastReceivedFrameCount
          for (let i = 0; i < lostCount; i++) {
            currentLost = (currentLost + 1) % 256

            receivedMessages.value.push({
              id: `lost_${currentLost}_${Date.now()}_${i}`,
              time: new Date().toLocaleTimeString(),
              frame_count: currentLost,
              data_hex: '(丢失)',
              isLost: true,
              hasError: false
            })
            berStats.lostFrames++
          }
        } else if (lostCount >= 128) {
          console.warn(`⚠️ 检测到异常丢帧数: ${lostCount}，忽略此帧#${frameCount}`)
          return
        }
      }
    }

    // 添加接收帧
    const receivedMsg = {
      id: `recv_${frameCount}_${Date.now()}`,
      time: new Date().toLocaleTimeString(),
      frame_count: frameCount,
      data_hex: msg.data_hex,
      isLost: false,
      hasError: false
    }

    berStats.receivedFrames++
    lastReceivedFrameCount = frameCount

    // 计算该帧的比特错误
    console.log(`🔍 比对帧#${frameCount}:`)

    if (sentDataHex.value) {
      const frameHasError = checkFrameError(msg.data_hex)
      receivedMsg.hasError = frameHasError

      if (frameHasError) {
        berStats.errorFrames++
        console.log(`❌ 帧#${frameCount} 有比特错误`)
      } else {
        berStats.correctFrames++
        console.log(`✅ 帧#${frameCount} 完全正确`)
      }
    } else {
      console.warn(`⚠️ 没有发送数据用于比对，默认算正确`)
      berStats.correctFrames++
    }

    receivedMessages.value.push(receivedMsg)

    // 使用实际发送的帧数
    berStats.totalFrames = actualSentFrames.value

    // 🔧 修复2：正确计算总比特数 = 每帧比特数 × 总帧数
    berStats.totalBits = berStats.bitsPerFrame * berStats.totalFrames

    console.log(`\n📊 统计更新:`)
    console.log(`  总帧: ${berStats.totalFrames}`)
    console.log(`  接收: ${berStats.receivedFrames}`)
    console.log(`  正确: ${berStats.correctFrames}`)
    console.log(`  错误: ${berStats.errorFrames}`)
    console.log(`  丢失: ${berStats.lostFrames}`)
    console.log(`  每帧比特: ${berStats.bitsPerFrame}`)
    console.log(`  总比特: ${berStats.totalBits}`)
    console.log(`  错误比特: ${berStats.errorBits}`)

    // 计算误帧率
    if (berStats.totalFrames > 0) {
      const totalErrorFrames = berStats.errorFrames + berStats.lostFrames
      berStats.fer = totalErrorFrames / berStats.totalFrames
      console.log(`  误帧率: ${(berStats.fer * 100).toFixed(2)}%`)
    }

    // 🔧 修复2：计算误比特率
    if (berStats.totalBits > 0) {
      berStats.ber = berStats.errorBits / berStats.totalBits
      console.log(`  误比特率: ${berStats.ber.toExponential(2)}`)
    }

    // 限制列表长度
    if (receivedMessages.value.length > 100) {
      receivedMessages.value.shift()
    }
  }

  // 检查帧号是否合理
  const isFrameCountValid = (frameCount) => {
    if (lastReceivedFrameCount === null) {
      return true
    }

    const maxJump = 3
    const minExpected = (lastReceivedFrameCount + 1) % 256
    const maxExpected = (lastReceivedFrameCount + maxJump) % 256

    if (minExpected <= maxExpected) {
      return frameCount >= minExpected && frameCount <= maxExpected
    } else {
      return frameCount >= minExpected || frameCount <= maxExpected
    }
  }

  // 计算丢失的帧数
  const calculateLostFrames = (lastFrame, currentFrame) => {
    if (currentFrame > lastFrame) {
      return currentFrame - lastFrame - 1
    } else if (currentFrame < lastFrame) {
      return (256 - lastFrame) + currentFrame - 1
    } else {
      return 0
    }
  }

  // 检查单帧是否有错误
  const checkFrameError = (receivedHex) => {
    const sentHex = sentDataHex.value
    if (!sentHex) {
      console.log('⚠️ 没有发送数据用于比对')
      return false
    }

    let frameErrorBits = 0
    const minLength = Math.min(sentHex.length, receivedHex.length)

    // 逐字节比较
    for (let i = 0; i < minLength; i += 2) {
      const sentByte = parseInt(sentHex.substring(i, i + 2), 16)
      const recvByte = parseInt(receivedHex.substring(i, i + 2), 16)

      if (sentByte !== recvByte) {
        const xor = sentByte ^ recvByte
        const bits = countBits(xor)
        frameErrorBits += bits
      }
    }

    // 长度不一致也算错误
    if (sentHex.length !== receivedHex.length) {
      const lengthDiff = Math.abs(sentHex.length - receivedHex.length)
      frameErrorBits += lengthDiff * 4
    }

    // 只有当帧有错误时才累加到总错误比特数
    if (frameErrorBits > 0) {
      berStats.errorBits += frameErrorBits
      console.log(`  本帧错误比特: ${frameErrorBits}, 累计错误比特: ${berStats.errorBits}`)
      return true
    } else {
      console.log(`  本帧完全正确`)
      return false
    }
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
    if (!isMounted.value) {
      console.log('⚠️ 组件未挂载，跳过SSE连接')
      return
    }

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
        if (!sseConnected.value && isMounted.value) {
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
    isMounted.value = true
    connectSSE()
  })

  // 组件卸载
  onUnmounted(() => {
    console.log('🛑 ResultDisplay unmounting')
    isMounted.value = false

    forceStopAll()

    if (eventSource) {
      eventSource.close()
      eventSource = null
      console.log('⏹️ SSE 连接已关闭')
    }

    receivedMessages.value = []
    clearStats()
  })
</script>

<style scoped>
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

.frame-lost .data-hex {
  color: #dc3545;
  font-style: italic;
}

.frame-error .data-hex {
  color: #856404;
}

  .receive-list {
    max-height: 400px;
    overflow-y: auto;
  }

    /* 🔧 滚动条样式 */
    .receive-list::-webkit-scrollbar {
      width: 8px;
    }

    .receive-list::-webkit-scrollbar-track {
      background: #f8f9fa;
    }

    .receive-list::-webkit-scrollbar-thumb {
      background: #ced4da;
      border-radius: 4px;
    }

      .receive-list::-webkit-scrollbar-thumb:hover {
        background: #adb5bd;
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

    .empty-receive p {
      margin: 0.5rem 0;
      font-size: 16px;
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

  @media (max-width: 768px) {
    .receive-item {
      grid-template-columns: 80px 100px 1fr;
      gap: 10px;
      padding: 12px;
      font-size: 12px;
    }

    .receive-time {
      font-size: 11px;
    }

    .receive-frame {
      font-size: 12px;
    }

    .data-hex {
      font-size: 11px;
    }
  }

  @media (max-width: 480px) {
    .receive-item {
      grid-template-columns: 1fr;
      gap: 8px;
    }

    .receive-time,
    .receive-frame {
      display: inline-block;
      margin-right: 10px;
    }

    .receive-data {
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }
  }

  .send-controls {
    display: flex;
    flex-direction: column;
    gap: 20px;
    background: white;
    padding: 25px;
    border-radius: 10px;
    border: 2px solid #e9ecef;
    margin-top: 15px;
  }

  /* 🔧 发送间隔控制组 */
  .control-group {
    display: flex;
    align-items: center;
    gap: 15px;
    padding-bottom: 20px;
    border-bottom: 2px solid #f8f9fa;
  }

    .control-group label {
      font-weight: 600;
      color: #2c3e50;
      font-size: 15px;
      min-width: 130px;
      white-space: nowrap;
    }

  .interval-input {
    flex: 1;
    max-width: 150px;
    padding: 10px 15px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    text-align: center;
    transition: all 0.3s ease;
  }

    .interval-input:focus {
      outline: none;
      border-color: #007bff;
      box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
    }

  /* 🔧 按钮组布局 */
  .control-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }

  .send-once-btn,
  .send-auto-btn,
  .stop-btn {
    padding: 14px 24px;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .send-once-btn {
    background: linear-gradient(135deg, #17a2b8, #138496);
    color: white;
  }

    .send-once-btn:hover:not(:disabled) {
      background: linear-gradient(135deg, #138496, #117a8b);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(23, 162, 184, 0.4);
    }

  .send-auto-btn {
    background: linear-gradient(135deg, #28a745, #218838);
    color: white;
  }

    .send-auto-btn:hover:not(:disabled) {
      background: linear-gradient(135deg, #218838, #1e7e34);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
    }

  .stop-btn {
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    grid-column: 1 / -1; /* 占满整行 */
  }

    .stop-btn:hover {
      background: linear-gradient(135deg, #c82333, #bd2130);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
    }

  .send-once-btn:disabled,
  .send-auto-btn:disabled {
    background: linear-gradient(135deg, #6c757d, #5a6268);
    cursor: not-allowed;
    opacity: 0.6;
    transform: none;
    box-shadow: none;
  }

  .send-once-btn i,
  .send-auto-btn i,
  .stop-btn i {
    font-size: 18px;
  }

  /* 🔧 发送状态盒子优化 */
  .send-status-box {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    background: #f8f9fa;
    padding: 15px;
    border-radius: 10px;
    border: 2px solid #e9ecef;
  }

  .status-item {
    display: flex;
    flex-direction: column;
    gap: 6px; /* 从8px改为6px */
    background: white;
    padding: 12px; /* 从15px改为12px */
    border-radius: 8px;
    border-left: 4px solid #007bff;
    transition: all 0.3s ease;
  }

  .status-label {
    font-size: 12px; /* 从13px改为12px */
    font-weight: 600;
    color: #6c757d;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .status-value {
    font-size: 20px; /* 从24px改为20px */
    font-weight: 700;
    color: #2c3e50;
    font-family: 'Courier New', monospace;
  }

    .status-value.sending {
      color: #28a745;
      animation: pulse 1.5s infinite;
    }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }

    50% {
      opacity: 0.7;
      transform: scale(1.02);
    }
  }

  /* 🔧 操作提示优化 */
  .send-status {
    margin-top: 15px;
    padding: 14px 18px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 500;
    font-size: 14px;
    border-left: 4px solid;
    animation: slideIn 0.3s ease;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-10px);
    }

    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .send-status.success {
    background: #d4edda;
    color: #155724;
    border-left-color: #28a745;
  }

  .send-status.error {
    background: #f8d7da;
    color: #721c24;
    border-left-color: #dc3545;
  }

  .send-status.info {
    background: #d1ecf1;
    color: #0c5460;
    border-left-color: #17a2b8;
  }

  .send-status i {
    font-size: 18px;
  }

  /* 🔧 连接状态指示器 */
  .connection-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    background: #f8d7da;
    color: #721c24;
    border: 2px solid #f5c6cb;
    transition: all 0.3s ease;
  }

    .connection-status.connected {
      background: #d4edda;
      color: #155724;
      border: 2px solid #c3e6cb;
    }

    .connection-status .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: currentColor;
    }

    .connection-status.connected .status-dot {
      animation: pulse-dot 2s infinite;
    }

  @keyframes pulse-dot {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }

    50% {
      opacity: 0.6;
      transform: scale(1.3);
    }
  }

  /* 🔧 响应式优化 */
  @media (max-width: 768px) {
    .control-group {
      flex-direction: column;
      align-items: stretch;
      gap: 10px;
    }

      .control-group label {
        min-width: auto;
      }

    .interval-input {
      max-width: none;
    }

    .control-buttons {
      grid-template-columns: 1fr;
    }

    .stop-btn {
      grid-column: 1;
    }

    .send-status-box {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 480px) {
    .send-controls {
      padding: 20px;
    }

    .send-once-btn,
    .send-auto-btn,
    .stop-btn {
      padding: 12px 20px;
      font-size: 14px;
    }

    .status-value {
      font-size: 20px;
    }
  }

  .receive-controls {
    display: flex;
    align-items: center;
    gap: 15px;
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
    transition: all 0.3s ease;
  }

    .clear-receive-btn:hover {
      background: #c82333;
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
    }

  @media (max-width: 768px) {
    .send-status-box {
      grid-template-columns: 1fr;
    }

    .receive-controls {
      flex-direction: column;
      align-items: flex-start;
      gap: 10px;
    }
  }

</style>
