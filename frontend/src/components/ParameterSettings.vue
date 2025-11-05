<template>
  <section class="section">
    <div class="section-header">
      <i class="header-icon">⚙️</i>
      <h2>参数设置</h2>
    </div>

    <div class="tab-content">
      <!-- LoRa数据文件选择 -->
      <div class="file-section">
        <div class="file-header">
          <i>📄</i>
          <h3>LoRa传输文件</h3>
        </div>
        <div class="file-content">
          <input type="file"
                 ref="loraFileInput"
                 @change="handleLoraFileSelect"
                 accept=".txt"
                 class="file-input"
                 id="loraFileInput" />
          <label for="loraFileInput" class="file-label">
            <i>📂</i>
            <span>{{ loraFileName || '选择16进制TXT文件' }}</span>
          </label>

          <div v-if="loraFileData" class="file-info">
            <div class="info-item">
              <span class="info-label">文件大小:</span>
              <span class="info-value">{{ loraFileData.length / 2 }} 字节</span>
            </div>
            <div class="info-item">
              <span class="info-label">数据预览:</span>
              <span class="info-value preview-hex">{{ formatHexPreview(loraFileData) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 上行通道 -->
      <div class="channel-card">
        <div class="channel-header">
          <i>📡</i>
          <h3>上行通道</h3>
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label>带宽</label>
            <select v-model.number="paramTabs.uplink.bandwidth" class="select-field">
              <option :value="125">125 kHz</option>
              <option :value="250">250 kHz</option>
              <option :value="500">500 kHz</option>
            </select>
          </div>

          <div class="form-group">
            <label>编码</label>
            <select v-model="paramTabs.uplink.coding" class="select-field">
              <option value="4/5">4/5</option>
              <option value="4/6">4/6</option>
              <option value="4/7">4/7</option>
              <option value="4/8">4/8</option>
            </select>
          </div>

          <div class="form-group">
            <label>扩频因子</label>
            <input type="number"
                   v-model.number="paramTabs.uplink.spreading_factor"
                   placeholder="6-12"
                   min="6"
                   max="12"
                   class="input-field" />
          </div>
        </div>
      </div>

      <!-- 上行干扰 -->
      <div class="channel-card interference-card">
        <div class="channel-header">
          <i>📡⚡</i>
          <h3>上行干扰</h3>
          <div class="interference-switch">
            <label class="switch-label">
              <input type="checkbox" v-model="interferenceSettings.enabled" />
              <span>启用干扰</span>
            </label>
          </div>
        </div>

        <div v-if="interferenceSettings.enabled" class="interference-content">
          <!-- 干扰模式 -->
          <div class="form-grid">
            <div class="form-group">
              <label>干扰模式</label>
              <select v-model="interferenceSettings.mode" class="select-field">
                <option value="shared">共通道</option>
                <option value="independent">独立通道</option>
              </select>
            </div>

            <div class="form-group">
              <label>干扰类型</label>
              <select v-model="interferenceSettings.type" class="select-field">
                <option value="single_tone">单音噪声</option>
                <option value="low_noise">底噪</option>
                <option value="channel_noise">通道噪声</option>
              </select>
            </div>
          </div>

          <!-- 单音噪声参数 -->
          <div v-if="interferenceSettings.type === 'single_tone'" class="form-grid">
            <div class="form-group">
              <label>中心频率</label>
              <div class="input-with-unit">
                <input type="number"
                       v-model.number="interferenceSettings.center_frequency"
                       placeholder="0"
                       class="input-field" />
                <span class="unit-label">Hz</span>
              </div>
            </div>

            <div class="form-group">
              <label>噪声功率</label>
              <div class="input-with-unit">
                <input type="number"
                       v-model.number="interferenceSettings.power"
                       placeholder="0"
                       class="input-field" />
                <span class="unit-label">dBm</span>
              </div>
            </div>
          </div>

          <!-- 底噪参数 -->
          <div v-else-if="interferenceSettings.type === 'low_noise'" class="form-grid">
            <div class="form-group">
              <label>噪声功率</label>
              <div class="input-with-unit">
                <input type="number"
                       v-model.number="interferenceSettings.power"
                       placeholder="0"
                       class="input-field" />
                <span class="unit-label">dBm</span>
              </div>
            </div>
          </div>

          <!-- 通道噪声参数 -->
          <div v-else-if="interferenceSettings.type === 'channel_noise'" class="form-grid">
            <div class="form-group">
              <label>扩频因子</label>
              <input type="number"
                     v-model.number="interferenceSettings.spreading_factor"
                     placeholder="6-12"
                     min="6"
                     max="12"
                     class="input-field" />
            </div>

            <div class="form-group">
              <label>噪声功率</label>
              <div class="input-with-unit">
                <input type="number"
                       v-model.number="interferenceSettings.power"
                       placeholder="0"
                       class="input-field" />
                <span class="unit-label">dBm</span>
              </div>
            </div>
          </div>

          <!-- 独立通道参数（仅在独立通道模式下显示）-->
          <div v-if="interferenceSettings.mode === 'independent'" class="form-grid">
            <div class="form-group">
              <label>带宽</label>
              <select v-model.number="paramTabs.uplink_interference.bandwidth" class="select-field">
                <option :value="125">125 kHz</option>
                <option :value="250">250 kHz</option>
                <option :value="500">500 kHz</option>
              </select>
            </div>

            <div class="form-group">
              <label>编码</label>
              <select v-model="paramTabs.uplink_interference.coding" class="select-field">
                <option value="4/5">4/5</option>
                <option value="4/6">4/6</option>
                <option value="4/7">4/7</option>
                <option value="4/8">4/8</option>
              </select>
            </div>

            <div class="form-group">
              <label>扩频因子</label>
              <input type="number"
                     v-model.number="paramTabs.uplink_interference.spreading_factor"
                     placeholder="6-12"
                     min="6"
                     max="12"
                     class="input-field" />
            </div>
          </div>
        </div>
      </div>

      <!-- 下行通道 -->
      <div class="channel-card">
        <div class="channel-header">
          <i>📶</i>
          <h3>下行通道</h3>
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label>带宽</label>
            <select v-model.number="paramTabs.downlink.bandwidth" class="select-field">
              <option :value="125">125 kHz</option>
              <option :value="250">250 kHz</option>
              <option :value="500">500 kHz</option>
            </select>
          </div>

          <div class="form-group">
            <label>编码</label>
            <select v-model="paramTabs.downlink.coding" class="select-field">
              <option value="4/5">4/5</option>
              <option value="4/6">4/6</option>
            </select>
          </div>

          <div class="form-group">
            <label>扩频因子</label>
            <input type="number"
                   v-model.number="paramTabs.downlink.spreading_factor"
                   placeholder="6-12"
                   min="6"
                   max="12"
                   class="input-field" />
          </div>
        </div>
      </div>

      <!-- 多普勒设置 -->
      <div class="channel-card doppler-card">
        <div class="channel-header">
          <i>🌊</i>
          <h3>多普勒设置</h3>
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label>多普勒类型</label>
            <select v-model="dopplerSettings.type" class="select-field">
              <option value="none">无多普勒</option>
              <option value="constant">恒定多普勒</option>
              <option value="linear">线性多普勒</option>
            </select>
          </div>
        </div>

        <div v-if="dopplerSettings.type !== 'none'" class="frequency-range-group">
          <label class="range-label">频移范围</label>
          <div class="range-inputs">
            <div class="range-input-wrapper">
              <span class="input-prefix">下限</span>
              <input type="number"
                     v-model.number="dopplerSettings.frequencyMin"
                     placeholder="-1000"
                     class="range-input" />
              <span class="input-suffix">Hz</span>
            </div>
            <span class="range-separator">~</span>
            <div class="range-input-wrapper">
              <span class="input-prefix">上限</span>
              <input type="number"
                     v-model.number="dopplerSettings.frequencyMax"
                     placeholder="1000"
                     class="range-input" />
              <span class="input-suffix">Hz</span>
            </div>
          </div>
        </div>

        <!-- 线性变化率 -->
        <div v-if="dopplerSettings.type === 'linear'" class="form-group">
          <label>变化率</label>
          <div class="input-with-unit">
            <input type="number"
                   v-model.number="dopplerSettings.rate"
                   placeholder="10"
                   class="input-field" />
            <span class="unit-label">Hz/s</span>
          </div>
        </div>
      </div>

      <!-- 读取和写入按钮 -->
      <div class="action-buttons">
        <button class="read-button" @click="readParameters">
          📥 读取
        </button>
        <button class="write-button"
                @click="writeParameters"
                :disabled="!loraFileData">
          📤 写入
        </button>
      </div>

      <!-- 写入提示 -->
      <div v-if="!loraFileData" class="warning-tip">
        ⚠️ 请先选择LoRa传输文件再写入参数
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
  import { ref, reactive, computed } from 'vue'
  import axios from 'axios'

  const API_BASE = '/api'

  const emit = defineEmits(['file-selected'])

  // LoRa文件相关
  const loraFileInput = ref(null)
  const loraFileName = ref('')
  const loraFileData = ref('')

  // 通道参数
  const paramTabs = reactive({
    uplink: {
      bandwidth: 125,
      coding: '4/5',
      spreading_factor: 9
    },
    downlink: {
      bandwidth: 125,
      coding: '4/5',
      spreading_factor: 10
    }
  })

  // 干扰设置
  const interferenceSettings = reactive({
    enabled: false,
    mode: 'shared',  // 'shared' 或 'independent'
    type: 'single_tone',  // 'single_tone', 'low_noise', 'channel_noise'
    center_frequency: 0,
    power: 0,
    spreading_factor: 7
  })

  // 多普勒设置
  const dopplerSettings = reactive({
    type: 'none',  // 'none', 'constant', 'linear'
    frequencyMin: -1000,
    frequencyMax: 1000,
    rate: 10
  })

  // 计算f_b (基带频率)
  const f_b = computed(() => {
    const bw = paramTabs.uplink.bandwidth
    if (bw === 125) return 1e6
    if (bw === 250) return 2e6
    if (bw === 500) return 4e6
    return 1e6
  })

  // 处理LoRa文件选择
  const handleLoraFileSelect = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    loraFileName.value = file.name

    try {
      const text = await file.text()
      const cleanHex = text.replace(/\s/g, '').toUpperCase()
      const hexPattern = /^[0-9A-F]+$/

      if (!hexPattern.test(cleanHex)) {
        throw new Error('文件内容包含非16进制字符')
      }

      if (cleanHex.length % 2 !== 0) {
        throw new Error('16进制数据长度必须是偶数')
      }

      loraFileData.value = cleanHex
      emit('file-selected', loraFileName.value, loraFileData.value)

      console.log(`✅ LoRa文件读取成功: ${cleanHex.length / 2} 字节`)
      alert(`✅ LoRa文件读取成功 (${cleanHex.length / 2} 字节)`)
    } catch (error) {
      loraFileData.value = ''
      emit('file-selected', '', '')
      console.error('文件读取失败:', error)
      alert(`❌ ${error.message}`)
    }
  }

  // 格式化16进制预览
  const formatHexPreview = (hex) => {
    return hex.length > 40 ? hex.substring(0, 40) + '...' : hex
  }

  // 读取参数
  const readParameters = async () => {
    try {
      const response = await axios.get(`${API_BASE}/parameters`)

      if (response.data.success) {
        const data = response.data.data

        // 更新通道参数
        if (data.uplink) Object.assign(paramTabs.uplink, data.uplink)
        if (data.downlink) Object.assign(paramTabs.downlink, data.downlink)

        // 更新干扰设置
        if (data.interference) Object.assign(interferenceSettings, data.interference)

        // 更新多普勒设置
        if (data.doppler) Object.assign(dopplerSettings, data.doppler)

        console.log('参数读取成功:', data)
        alert('✅ 参数读取成功')
      } else {
        throw new Error(response.data.message || '读取失败')
      }
    } catch (error) {
      console.error('读取参数失败:', error)
      alert(`❌ 参数读取失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  // 写入参数
  const writeParameters = async () => {
    if (!loraFileData.value) {
      alert('❌ 请先选择LoRa传输文件')
      return
    }

    try {
      const params = {
        lora_data_length: loraFileData.value.length / 2,
        uplink: paramTabs.uplink,
        downlink: paramTabs.downlink,
        interference: interferenceSettings,
        doppler: dopplerSettings
      }

      console.log('准备写入参数:', params)

      const response = await axios.post(`${API_BASE}/parameters`, params)

      if (response.data.success) {
        console.log('参数写入成功:', response.data)
        alert(`✅ 参数写入成功\n${response.data.message}`)
      } else {
        throw new Error(response.data.message || '写入失败')
      }
    } catch (error) {
      console.error('写入参数失败:', error)
      alert(`❌ 参数写入失败: ${error.response?.data?.detail || error.message}`)
    }
  }
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
    border-bottom: 3px solid #007bff;
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
  }

  .tab-content {
    padding: 30px;
  }

  .channel-card {
    background: #f8f9fa;
    border: 2px solid #e9ecef;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 20px;
    transition: all 0.3s ease;
  }

    .channel-card:hover {
      border-color: #007bff;
      box-shadow: 0 8px 20px rgba(0, 123, 255, 0.1);
    }

  .interference-card {
    border-color: #ffc107;
  }

    .interference-card:hover {
      border-color: #ff9800;
      box-shadow: 0 8px 20px rgba(255, 152, 0, 0.15);
    }

  .doppler-card {
    border-color: #28a745;
  }

    .doppler-card:hover {
      border-color: #20c997;
      box-shadow: 0 8px 20px rgba(32, 201, 151, 0.15);
    }

  .channel-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #e9ecef;
  }

    .channel-header i {
      font-size: 24px;
    }

    .channel-header h3 {
      margin: 0;
      color: #2c3e50;
      font-size: 18px;
      font-weight: 600;
      flex: 1;
    }

  .interference-switch {
    margin-left: auto;
  }

  .switch-label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-weight: 500;
    color: #6c757d;
  }

    .switch-label input[type="checkbox"] {
      width: 18px;
      height: 18px;
      cursor: pointer;
    }

  .interference-content {
    margin-top: 20px;
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 25px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

    .form-group label {
      font-weight: 600;
      color: #2c3e50;
      font-size: 14px;
      margin-bottom: 4px;
    }

  .input-field,
  .select-field {
    padding: 12px 16px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-size: 16px;
    transition: all 0.3s ease;
    background: white;
  }

    .input-field:focus,
    .select-field:focus {
      outline: none;
      border-color: #007bff;
      box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
    }

  .select-field {
    cursor: pointer;
  }

  .input-with-unit {
    display: flex;
    align-items: center;
    gap: 10px;
  }

    .input-with-unit .input-field {
      flex: 1;
    }

  .unit-label {
    font-size: 14px;
    font-weight: 600;
    color: #6c757d;
    background: #e9ecef;
    padding: 12px 16px;
    border-radius: 8px;
    white-space: nowrap;
  }

  /* 频移范围样式 */
  .frequency-range-group {
    margin-top: 20px;
  }

  .range-label {
    display: block;
    font-weight: 600;
    color: #2c3e50;
    font-size: 14px;
    margin-bottom: 10px;
  }

  .range-inputs {
    display: flex;
    align-items: center;
    gap: 15px;
    background: #f8f9fa;
    padding: 15px;
    border-radius: 10px;
    border: 2px solid #e9ecef;
  }

  .range-input-wrapper {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 8px;
    background: white;
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid #dee2e6;
  }

  .input-prefix,
  .input-suffix {
    font-size: 13px;
    color: #6c757d;
    font-weight: 500;
    white-space: nowrap;
  }

  .range-input {
    flex: 1;
    border: none;
    outline: none;
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
    padding: 4px;
    text-align: center;
    min-width: 80px;
    font-family: 'Courier New', monospace;
  }

  .range-separator {
    font-size: 20px;
    color: #6c757d;
    font-weight: bold;
  }

  /* 文件选择样式 */
  .file-section {
    background: #e3f2fd;
    border: 2px solid #2196f3;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
  }

  .file-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid #2196f3;
  }

    .file-header i {
      font-size: 24px;
    }

    .file-header h3 {
      margin: 0;
      color: #1976d2;
      font-size: 16px;
      font-weight: 600;
    }

  .file-content {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }

  .file-input {
    display: none;
  }

  .file-label {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 12px 24px;
    background: white;
    border: 2px solid #2196f3;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
    color: #1976d2;
  }

    .file-label:hover {
      background: #2196f3;
      color: white;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
    }

  .file-info {
    background: white;
    border-radius: 8px;
    padding: 15px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .info-item {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .info-label {
    font-weight: 600;
    color: #1976d2;
    min-width: 80px;
  }

  .info-value {
    color: #424242;
  }

  .preview-hex {
    font-family: 'Courier New', monospace;
    font-size: 13px;
    background: #f5f5f5;
    padding: 4px 8px;
    border-radius: 4px;
  }

  /* 按钮样式 */
  .action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 15px;
    margin-top: 25px;
    padding-top: 20px;
    border-top: 2px solid #e9ecef;
  }

  .read-button,
  .write-button {
    padding: 12px 30px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .read-button {
    background: #17a2b8;
    color: white;
  }

    .read-button:hover {
      background: #138496;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(23, 162, 184, 0.3);
    }

  .write-button {
    background: #28a745;
    color: white;
  }

    .write-button:hover {
      background: #218838;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
    }

    .write-button:disabled {
      background: #9e9e9e;
      cursor: not-allowed;
      opacity: 0.6;
    }

      .write-button:disabled:hover {
        background: #9e9e9e;
        transform: none;
        box-shadow: none;
      }

  .warning-tip {
    padding: 12px 20px;
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    color: #856404;
    font-weight: 500;
    text-align: center;
  }

  @media (max-width: 768px) {
    .form-grid {
      grid-template-columns: 1fr;
    }

    .action-buttons {
      flex-direction: column;
    }

    .read-button,
    .write-button {
      width: 100%;
      justify-content: center;
    }

    .range-inputs {
      flex-direction: column;
    }

    .range-separator {
      transform: rotate(90deg);
    }
  }
</style>
