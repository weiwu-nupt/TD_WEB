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

      <!-- 循环显示所有通道 -->
      <div v-for="tab in paramTabs" :key="tab.id" class="channel-card">
        <div class="channel-header">
          <i>{{ tab.icon }}</i>
          <h3>{{ tab.name }}</h3>
        </div>

        <div class="form-grid">
          <div v-for="(field, index) in tab.fields" :key="index" class="form-group">
            <label :for="`field-${tab.id}-${index}`" class="field-label">{{ field.label }}</label>

            <!-- 带宽下拉框 -->
            <select v-if="field.type === 'bandwidth'"
                    :id="`field-${tab.id}-${index}`"
                    v-model.number="field.value"
                    class="select-field">
              <option :value="125">125 kHz</option>
              <option :value="250">250 kHz</option>
              <option :value="500">500 kHz</option>
            </select>

            <!-- 编码下拉框 -->
            <select v-else-if="field.type === 'select'"
                    :id="`field-${tab.id}-${index}`"
                    v-model="field.value"
                    class="select-field">
              <option v-for="option in field.options"
                      :key="option.value"
                      :value="option.value">
                {{ option.label }}
              </option>
            </select>

            <!-- 扩频因子输入框 -->
            <input v-else-if="field.type === 'number'"
                   :id="`field-${tab.id}-${index}`"
                   type="number"
                   :placeholder="field.placeholder"
                   v-model.number="field.value"
                   :min="field.min"
                   :max="field.max"
                   class="input-field" />
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
  import { ref, reactive } from 'vue'
  import axios from 'axios'

  const API_BASE = '/api'

  // LoRa文件相关
  const loraFileInput = ref(null)
  const loraFileName = ref('')
  const loraFileData = ref('')

  const paramTabs = reactive([
    {
      id: 'uplink',
      name: '上行通道',
      icon: '📡',
      fields: [
        { label: '带宽', type: 'bandwidth', value: 125, key: 'bandwidth' },
        {
          label: '编码', type: 'select', value: '4/5', key: 'coding',
          options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' },
            { label: '4/7', value: '4/7' },
            { label: '4/8', value: '4/8' }
          ]
        },
        { label: '扩频因子', type: 'number', value: 9, min: 6, max: 12, placeholder: '6-12', key: 'spreading_factor' }
      ]
    },
    {
      id: 'uplink_interference',
      name: '上行通道(干扰)',
      icon: '📡⚡',
      fields: [
        { label: '带宽', type: 'bandwidth', value: 125, key: 'bandwidth' },
        {
          label: '编码', type: 'select', value: '4/6', key: 'coding',
          options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' },
            { label: '4/7', value: '4/7' },
            { label: '4/8', value: '4/8' }
          ]
        },
        { label: '扩频因子', type: 'number', value: 8, min: 6, max: 12, placeholder: '6-12', key: 'spreading_factor' }
      ]
    },
    {
      id: 'downlink',
      name: '下行通道',
      icon: '📶',
      fields: [
        { label: '带宽', type: 'bandwidth', value: 125, key: 'bandwidth' },
        {
          label: '编码', type: 'select', value: '4/5', key: 'coding',
          options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' }
          ]
        },
        { label: '扩频因子', type: 'number', value: 10, min: 6, max: 12, placeholder: '6-12', key: 'spreading_factor' }
      ]
    }
  ])

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
      console.log(`✅ LoRa文件读取成功: ${cleanHex.length / 2} 字节`)
      alert(`✅ LoRa文件读取成功 (${cleanHex.length / 2} 字节)`)
    } catch (error) {
      loraFileData.value = ''
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

        paramTabs.forEach(tab => {
          const channelData = data[tab.id]
          if (channelData) {
            tab.fields.forEach(field => {
              if (field.key && channelData[field.key] !== undefined) {
                field.value = channelData[field.key]
              }
            })
          }
        })

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
      // 构建参数对象
      const params = {
        lora_data_length: loraFileData.value.length / 2  // 字节数
      }

      paramTabs.forEach(tab => {
        params[tab.id] = {}
        tab.fields.forEach(field => {
          if (field.key) {
            params[tab.id][field.key] = field.value
          }
        })
      })

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

  .field-label {
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

    .input-field::placeholder {
      color: #adb5bd;
    }

  .select-field {
    cursor: pointer;
  }

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
  }

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

  .warning-tip {
    padding: 12px 20px;
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    color: #856404;
    font-weight: 500;
    text-align: center;
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
</style>
