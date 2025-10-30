<template>
  <section class="section">
    <div class="section-header">
      <i class="header-icon">🌊</i>
      <h2>多普勒设置</h2>
    </div>

    <div class="doppler-settings">
      <div class="doppler-container">
        <div class="doppler-card">
          <div class="card-content">
            <div class="form-group">
              <label>多普勒类型</label>
              <select v-model="sceneSettings.doppler.type" class="select-field">
                <option value="none">无多普勒</option>
                <option value="constant">恒定多普勒</option>
                <option value="linear">线性多普勒</option>
                <option value="sinusoidal">正弦多普勒</option>
                <option value="random">随机多普勒</option>
              </select>
            </div>

            <div class="frequency-range-group">
              <label class="range-label">频移范围</label>
              <div class="range-inputs">
                <div class="range-input-wrapper">
                  <span class="input-prefix">下限</span>
                  <input type="number"
                         v-model.number="sceneSettings.doppler.frequencyMin"
                         placeholder="-1000"
                         class="range-input" />
                  <span class="input-suffix">Hz</span>
                </div>
                <span class="range-separator">~</span>
                <div class="range-input-wrapper">
                  <span class="input-prefix">上限</span>
                  <input type="number"
                         v-model.number="sceneSettings.doppler.frequencyMax"
                         placeholder="1000"
                         class="range-input" />
                  <span class="input-suffix">Hz</span>
                </div>
              </div>
            </div>

            <!-- 线性变化率 - 仅在线性多普勒时显示 -->
            <div v-if="sceneSettings.doppler.type === 'linear'" class="form-group">
              <label>变化率</label>
              <div class="input-with-unit">
                <input type="number"
                       v-model.number="sceneSettings.doppler.rate"
                       placeholder="10"
                       class="input-field" />
                <span class="unit-label">Hz/s</span>
              </div>
            </div>

            <!-- 正弦变化周期 - 仅在正弦多普勒时显示 -->
            <div v-if="sceneSettings.doppler.type === 'sinusoidal'" class="form-group">
              <label>周期</label>
              <div class="input-with-unit">
                <input type="number"
                       v-model.number="sceneSettings.doppler.period"
                       placeholder="1"
                       step="0.1"
                       class="input-field" />
                <span class="unit-label">s</span>
              </div>
            </div>
          </div>

          <!-- 读取和写入按钮 -->
          <div class="card-footer">
            <button class="read-button" @click="readDopplerSettings">
              📥 读取
            </button>
            <button class="write-button" @click="writeDopplerSettings">
              📤 写入
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
  import { reactive, onMounted } from 'vue'
  import axios from 'axios'

  const API_BASE = '/api'

  const sceneSettings = reactive({
    doppler: {
      type: 'none',
      frequencyMin: -1000,
      frequencyMax: 1000,
      rate: 10,
      period: 1
    }
  })

  // 读取多普勒设置
  const readDopplerSettings = async () => {
    try {
      const response = await axios.get(`${API_BASE}/doppler`)

      if (response.data.success) {
        const data = response.data.data
        Object.assign(sceneSettings.doppler, data)

        console.log('多普勒设置读取成功:', data)
        alert('✅ 多普勒设置读取成功')
      } else {
        throw new Error(response.data.message || '读取失败')
      }
    } catch (error) {
      console.error('读取多普勒设置失败:', error)
      alert(`❌ 多普勒设置读取失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  // 写入多普勒设置
  const writeDopplerSettings = async () => {
    try {
      const response = await axios.post(`${API_BASE}/doppler`, sceneSettings.doppler)

      if (response.data.success) {
        console.log('多普勒设置写入成功:', response.data.data)
        alert('✅ 多普勒设置写入成功')
      } else {
        throw new Error(response.data.message || '写入失败')
      }
    } catch (error) {
      console.error('写入多普勒设置失败:', error)
      alert(`❌ 多普勒设置写入失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  // 组件挂载时自动读取设置
  //onMounted(() => {
 //   readDopplerSettings()
 // })
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
    border-bottom: 3px solid #28a745;
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

  .doppler-settings {
    padding: 30px;
    background: white;
  }

  .doppler-container {
    max-width: 800px;
    margin: 0 auto;
  }

  .doppler-card {
    background: linear-gradient(135deg, #f8f9fa, #fff);
    border: 2px solid #e9ecef;
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.3s ease;
    position: relative;
  }

    .doppler-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(135deg, #28a745, #20c997);
    }

    .doppler-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
      border-color: #28a745;
    }

  .card-content {
    padding: 30px;
  }

  .form-group {
    margin-bottom: 25px;
  }

    .form-group label {
      display: block;
      font-weight: 600;
      color: #2c3e50;
      font-size: 14px;
      margin-bottom: 10px;
    }

  .select-field {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-size: 16px;
    transition: all 0.3s ease;
    background: white;
    cursor: pointer;
  }

    .select-field:focus {
      outline: none;
      border-color: #28a745;
      box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.1);
    }

  /* 频移范围组样式 */
  .frequency-range-group {
    margin-bottom: 25px;
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
    transition: all 0.3s ease;
  }

    .range-inputs:focus-within {
      border-color: #28a745;
      background: white;
      box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.1);
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
    transition: all 0.3s ease;
  }

    .range-input-wrapper:focus-within {
      border-color: #28a745;
      box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.1);
    }

  .input-prefix {
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

    .range-input::placeholder {
      color: #adb5bd;
      font-weight: normal;
    }

  .input-suffix {
    font-size: 13px;
    color: #6c757d;
    font-weight: 500;
    white-space: nowrap;
  }

  .range-separator {
    font-size: 20px;
    color: #6c757d;
    font-weight: bold;
  }

  /* 带单位的输入框样式 */
  .input-with-unit {
    display: flex;
    align-items: center;
    gap: 10px;
  }

    .input-with-unit .input-field {
      flex: 1;
      padding: 12px 16px;
      border: 2px solid #e9ecef;
      border-radius: 8px;
      font-size: 16px;
      transition: all 0.3s ease;
      background: white;
    }

      .input-with-unit .input-field:focus {
        outline: none;
        border-color: #28a745;
        box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.1);
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

  /* 卡片底部按钮区域 */
  .card-footer {
    padding: 20px 30px;
    border-top: 2px solid #e9ecef;
    display: flex;
    justify-content: flex-end;
    gap: 15px;
    background: #f8f9fa;
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

    .read-button:active {
      transform: translateY(0);
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

    .write-button:active {
      transform: translateY(0);
    }

  /* 响应式调整 */
  @media (max-width: 768px) {
    .doppler-settings {
      padding: 20px;
    }

    .card-content {
      padding: 20px;
    }

    .range-inputs {
      flex-direction: column;
      gap: 10px;
    }

    .range-separator {
      transform: rotate(90deg);
    }

    .card-footer {
      flex-direction: column;
      padding: 15px 20px;
    }

    .read-button,
    .write-button {
      width: 100%;
      justify-content: center;
    }
  }
</style>
