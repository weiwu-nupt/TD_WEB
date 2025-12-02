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

        <!-- 节点设置区域 -->
        <div class="mixed-section">
          <div class="section-header">
            <i class="header-icon">⚙️</i>
            <h2>节点配置</h2>
          </div>

          <div class="node-settings-content">
            <!-- 基本配置 -->
            <div class="settings-group">
              <h3>基本配置</h3>
              <div class="form-grid">
                <div class="form-group">
                  <label>节点ID</label>
                  <input type="number"
                         v-model.number="nodeSettings.nodeId"
                         min="0"
                         max="255"
                         class="node-input"
                         placeholder="0-255" />
                </div>

                <div class="form-group">
                  <label>节点模式</label>
                  <select v-model="nodeSettings.nodeMode" class="node-select">
                    <option value="standalone">单机</option>
                    <option value="network">组网</option>
                    <option value="virtual">虚实融合</option>
                  </select>
                </div>

                <div class="form-group">
                  <label>组网总节点数</label>
                  <input type="number"
                         v-model.number="nodeSettings.totalNodes"
                         min="1"
                         max="255"
                         class="node-input"
                         placeholder="1-255" />
                </div>

                <div class="form-group">
                  <label>节点属性</label>
                  <select v-model="nodeSettings.nodeType" class="node-select">
                    <option value="mother">母星</option>
                    <option value="normal">普通</option>
                  </select>
                </div>

                <div class="form-group">
                  <label>工作频率 (kHz)</label>
                  <input type="number"
                         v-model.number="nodeSettings.frequency"
                         class="node-input"
                         placeholder="例如: 900000" />
                </div>

                <div class="form-group">
                  <label>通道衰减 (dB)</label>
                  <input type="number"
                         v-model.number="nodeSettings.attenuation"
                         min="1"
                         max="70"
                         class="node-input"
                         placeholder="1-70" />
                </div>
              </div>
            </div>

            <!-- 前向链路参数 -->
            <div class="settings-group">
              <h3>前向链路参数</h3>
              <div class="form-grid">
                <div class="form-group">
                  <label>带宽 (kHz)</label>
                  <input type="number"
                         v-model.number="nodeSettings.forward.bandwidth"
                         class="node-input"
                         placeholder="例如: 125, 250, 500" />
                </div>

                <div class="form-group">
                  <label>扩频因子</label>
                  <input type="number"
                         v-model.number="nodeSettings.forward.spreadingFactor"
                         min="6"
                         max="12"
                         class="node-input"
                         placeholder="6-12" />
                </div>

                <div class="form-group">
                  <label>限幅率</label>
                  <input type="number"
                         v-model.number="nodeSettings.forward.clippingRate"
                         class="node-input"
                         placeholder="限幅率" />
                </div>
              </div>
            </div>

            <!-- 反向链路参数 -->
            <div class="settings-group">
              <h3>反向链路参数</h3>
              <div class="form-grid">
                <div class="form-group">
                  <label>带宽 (kHz)</label>
                  <input type="number"
                         v-model.number="nodeSettings.backward.bandwidth"
                         class="node-input"
                         placeholder="例如: 125, 250, 500" />
                </div>

                <div class="form-group">
                  <label>扩频因子</label>
                  <input type="number"
                         v-model.number="nodeSettings.backward.spreadingFactor"
                         min="6"
                         max="12"
                         class="node-input"
                         placeholder="6-12" />
                </div>

                <div class="form-group">
                  <label>限幅率</label>
                  <input type="number"
                         v-model.number="nodeSettings.backward.clippingRate"
                         class="node-input"
                         placeholder="限幅率" />
                </div>

                <div class="form-group switch-group">
                  <label>自适应使能</label>
                  <label class="toggle-switch">
                    <input type="checkbox" v-model="nodeSettings.backward.adaptiveEnable">
                    <span class="slider round"></span>
                  </label>
                </div>

                <div class="form-group switch-group">
                  <label>自适应SF</label>
                  <label class="toggle-switch">
                    <input type="checkbox" v-model="nodeSettings.backward.adaptiveSF">
                    <span class="slider round"></span>
                  </label>
                </div>
              </div>
            </div>

            <!-- 目标配置 -->
            <div class="settings-group">
              <h3>目标节点</h3>
              <div class="form-grid">
                <div class="form-group">
                  <label>目标IP</label>
                  <input type="text"
                         v-model="nodeSettings.target.ip"
                         class="node-input"
                         placeholder="192.168.1.100" />
                </div>

                <div class="form-group">
                  <label>目标端口</label>
                  <input type="number"
                         v-model.number="nodeSettings.target.port"
                         class="node-input"
                         placeholder="9003" />
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <button class="send-button" @click="sendNodeSettings">
                📤 发送配置
              </button>
            </div>

            <!-- 状态提示 -->
            <div v-if="nodeSettingsStatus" class="status-message" :class="nodeSettingsStatus.type">
              <i>{{ nodeSettingsStatus.type === 'success' ? '✅' : '❌' }}</i>
              {{ nodeSettingsStatus.message }}
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

  // 节点设置
  const nodeSettings = reactive({
    nodeId: 1,
    nodeMode: 'virtual',  // 'standalone', 'network', 'virtual'
    totalNodes: 1,
    nodeType: 'normal',  // 'mother', 'normal'
    frequency: 900000,
    attenuation: 10,
    forward: {
      bandwidth: 125,
      spreadingFactor: 7,
      clippingRate: 0
    },
    backward: {
      bandwidth: 125,
      spreadingFactor: 7,
      clippingRate: 0,
      adaptiveEnable: false,
      adaptiveSF: false
    },
    target: {
      ip: '192.168.1.100',
      port: 9003
    }
  })

  const nodeSettingsStatus = ref(null)

  // 发送节点设置
  const sendNodeSettings = async () => {
    try {
      nodeSettingsStatus.value = null

      const response = await axios.post(`${API_BASE}/virtual/node-settings`, nodeSettings)

      if (response.data.success) {
        nodeSettingsStatus.value = {
          type: 'success',
          message: '✅ 节点配置发送成功'
        }
        console.log('节点配置发送成功:', response.data)
      } else {
        throw new Error(response.data.message || '发送失败')
      }
    } catch (error) {
      console.error('发送节点配置失败:', error)
      nodeSettingsStatus.value = {
        type: 'error',
        message: `❌ 发送失败: ${error.response?.data?.detail || error.message}`
      }
    }
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

    selectedSystem.value = ''

    if (sharedLoraFileData.value) {
      clearFileData()
    }
  }
   
  // 处理系统切换
  const handleSystemChange = (system: string) => {
    console.log(`🔄 handleSystemChange: ${system}`)
  }

  // 监听系统切换
  watch(selectedSystem, (newValue, oldValue) => {
    console.log(`🔄 系统切换: ${oldValue} -> ${newValue}`)

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

  .node-settings-content {
    padding: 2rem;
  }

  .settings-group {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 1rem;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
    transition: transform 0.3s ease, border-color 0.3s ease;
  }

    .settings-group:hover {
      border-color: rgba(155, 181, 255, 0.3);
      transform: translateY(-2px);
    }

    .settings-group h3 {
      color: #e0c3fc; /* 更亮的紫色 */
      font-size: 1.1rem;
      margin: 0 0 1.2rem 0;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      letter-spacing: 1px;
    }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.25rem;
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

  .node-input,
  .node-select {
    background: rgba(0, 0, 0, 0.2); /* 深色背景，增加对比度 */
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 0.5rem;
    padding: 0.75rem 1rem;
    color: #ffffff; /* 关键修改：暗色模式下文字改为白色 */
    font-size: 0.95rem;
    width: 100%;
    box-sizing: border-box; /* 防止padding撑破布局 */
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

    .node-input::placeholder {
      color: rgba(255, 255, 255, 0.3);
    }

    .node-input:focus,
    .node-select:focus {
      outline: none;
      border-color: #9bb5ff;
      background: rgba(0, 0, 0, 0.4);
      box-shadow: 0 0 15px rgba(155, 181, 255, 0.15); /* 科技感光晕 */
    }
    .node-select option {
      background-color: #16213e;
      color: white;
    }

  .switch-group {
    display: flex;
    flex-direction: row; /* 让标签和开关在一行显示 */
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.05); /* 给开关加个小背景条 */
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    border: 1px solid rgba(255, 255, 255, 0.05);
    height: 52px; /* 与输入框高度对其 */
  }


    .switch-group label {
      margin: 0;
      cursor: pointer;
    }

      .switch-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    padding: 0.75rem 0;
  }

    .switch-label input[type="checkbox"] {
      width: 18px;
      height: 18px;
      cursor: pointer;
    }

  .action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .send-button {
    background: linear-gradient(135deg, #28a745, #218838);
    color: white;
    border: none;
    padding: 0.75rem 2rem;
    border-radius: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

    .send-button:hover {
      background: linear-gradient(135deg, #218838, #1e7e34);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
    }

  .status-message {
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }

    .status-message.success {
      background: rgba(40, 167, 69, 0.2);
      color: #28a745;
      border: 1px solid rgba(40, 167, 69, 0.4);
    }

    .status-message.error {
      background: rgba(220, 53, 69, 0.2);
      color: #dc3545;
      border: 1px solid rgba(220, 53, 69, 0.4);
    }

  @media (max-width: 768px) {
    .form-grid {
      grid-template-columns: 1fr;
    }

    .node-settings-content {
      padding: 1.5rem;
    }
  }
</style>
