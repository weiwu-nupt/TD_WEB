<template>
  <section class="section">
    <div class="section-header">
      <i class="header-icon">⚙️</i>
      <h2>参数设置</h2>
    </div>

    <div class="tab-content">
      <!-- 循环显示所有通道,不再使用标签页 -->
      <div v-for="tab in paramTabs" :key="tab.id" class="channel-card">
        <div class="channel-header">
          <i>{{ tab.icon }}</i>
          <h3>{{ tab.name }}</h3>
        </div>

        <div class="form-grid">
          <div v-for="(field, index) in tab.fields" :key="index" class="form-group">
            <label :for="`field-${tab.id}-${index}`" class="field-label">{{ field.label }}</label>

            <!-- 数字输入框 -->
            <input v-if="field.type === 'number'"
                   :id="`field-${tab.id}-${index}`"
                   type="number"
                   :placeholder="field.placeholder"
                   :value="field.value"
                   @input="field.value = $event.target.value"
                   class="input-field" />

            <!-- 下拉选择框 -->
            <select v-else-if="field.type === 'select'"
                    :id="`field-${tab.id}-${index}`"
                    :value="field.value"
                    @change="field.value = $event.target.value"
                    class="select-field">
              <option v-for="option in field.options"
                      :key="option.value"
                      :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- 读取和写入按钮 -->
      <div class="action-buttons">
        <button class="read-button" @click="readParameters">
          📥 读取
        </button>
        <button class="write-button" @click="writeParameters">
          📤 写入
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
  import { reactive, onMounted } from 'vue'
  import axios from 'axios'

  const API_BASE = '/api'

  const paramTabs = reactive([
    {
      id: 'uplink',
      name: '上行通道',
      icon: '📡',
      fields: [
        { label: '带宽(KHz)', type: 'number', value: 100000, placeholder: '请输入带宽，如100000', key: 'bandwidth' },
        {
          label: '编码', type: 'select', value: '4/5', key: 'coding', options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' },
            { label: '4/7', value: '4/7' },
            { label: '4/8', value: '4/8' }
          ]
        },
        { label: '扩频因子', type: 'number', value: 9, placeholder: '请输入扩频因子，如9', key: 'spreading_factor' },
        { label: '中心频率(MHz)', type: 'number', value: 10000, placeholder: '请输入中心频率，如10000', key: 'center_frequency' },
        { label: '功率(W)', type: 'number', value: 1, placeholder: '请输入功率，如1', key: 'power' }
      ]
    },
    {
      id: 'uplink_interference',
      name: '上行通道(干扰)',
      icon: '📡⚡',
      fields: [
        { label: '带宽(KHz)', type: 'number', value: 100000, placeholder: '请输入带宽，如100000', key: 'bandwidth' },
        {
          label: '编码', type: 'select', value: '4/6', key: 'coding', options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' },
            { label: '4/7', value: '4/7' },
            { label: '4/8', value: '4/8' }
          ]
        },
        { label: '扩频因子', type: 'number', value: 8, placeholder: '请输入扩频因子，如8', key: 'spreading_factor' },
        { label: '中心频率(MHz)', type: 'number', value: 10200, placeholder: '请输入中心频率，如10200', key: 'center_frequency' },
        { label: '功率(W)', type: 'number', value: 0.5, placeholder: '请输入功率，如0.5', key: 'power' }
      ]
    },
    {
      id: 'downlink',
      name: '下行通道',
      icon: '📶',
      fields: [
        { label: '带宽(KHz)', type: 'number', value: 100000, placeholder: '请输入带宽，如100000', key: 'bandwidth' },
        {
          label: '编码', type: 'select', value: '4/7', key: 'coding', options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' },
            { label: '4/7', value: '4/7' },
            { label: '4/8', value: '4/8' }
          ]
        },
        { label: '扩频因子', type: 'number', value: 10, placeholder: '请输入扩频因子，如10', key: 'spreading_factor' },
        { label: '中心频率(MHz)', type: 'number', value: 12000, placeholder: '请输入中心频率，如12000', key: 'center_frequency' },
        { label: '功率(W)', type: 'number', value: 2, placeholder: '请输入功率，如2', key: 'power' }
      ]
    }
  ])

  // 读取参数
  const readParameters = async () => {
    try {
      const response = await axios.get(`${API_BASE}/parameters`)

      if (response.data.success) {
        const data = response.data.data

        // 更新每个通道的参数
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
    try {
      // 构建参数对象
      const params = {}

      paramTabs.forEach(tab => {
        params[tab.id] = {}
        tab.fields.forEach(field => {
          if (field.key) {
            params[tab.id][field.key] = field.value
          }
        })
      })

      const response = await axios.post(`${API_BASE}/parameters`, params)

      if (response.data.success) {
        console.log('参数写入成功:', response.data.data)
        alert('✅ 参数写入成功')
      } else {
        throw new Error(response.data.message || '写入失败')
      }
    } catch (error) {
      console.error('写入参数失败:', error)
      alert(`❌ 参数写入失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  // 组件挂载时自动读取参数
  onMounted(() => {
    readParameters()
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

  .action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 15px;
    margin-top: 25px;
    padding-top: 20px;
    border-top: 2px solid #e9ecef;
  }

  .read-button {
    padding: 12px 30px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    background: #17a2b8;
    color: white;
    display: flex;
    align-items: center;
    gap: 8px;
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
    padding: 12px 30px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    background: #28a745;
    color: white;
    display: flex;
    align-items: center;
    gap: 8px;
  }

    .write-button:hover {
      background: #218838;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
    }

    .write-button:active {
      transform: translateY(0);
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

  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
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

  .value {
    background: #e9ecef;
    padding: 4px 8px;
    border-radius: 4px;
    font-family: monospace;
    color: #007bff;
  }


  .range-labels {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #6c757d;
  }

  @media (max-width: 768px) {
    .form-grid {
      grid-template-columns: 1fr;
    }

    .tab-nav {
      flex-wrap: wrap;
    }

    .tab-button {
      padding: 12px 20px;
      font-size: 14px;
    }
  }
</style>
