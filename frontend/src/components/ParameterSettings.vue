<template>
  <section class="section">
    <div class="section-header">
      <i class="header-icon">⚙️</i>
      <h2>参数设置</h2>
    </div>

    <div class="tab-content">
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
        <button class="write-button" @click="writeParameters">
          📤 写入
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
  import { reactive } from 'vue'
  import axios from 'axios'

  const API_BASE = '/api'

  const paramTabs = reactive([
    {
      id: 'uplink',
      name: '上行通道',
      icon: '📡',
      fields: [
        {
          label: '带宽',
          type: 'bandwidth',
          value: 125,
          key: 'bandwidth'
        },
        {
          label: '编码',
          type: 'select',
          value: '4/5',
          key: 'coding',
          options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' },
            { label: '4/7', value: '4/7' },
            { label: '4/8', value: '4/8' }
          ]
        },
        {
          label: '扩频因子',
          type: 'number',
          value: 9,
          min: 6,
          max: 12,
          placeholder: '6-12',
          key: 'spreading_factor'
        }
      ]
    },
    {
      id: 'uplink_interference',
      name: '上行通道(干扰)',
      icon: '📡⚡',
      fields: [
        {
          label: '带宽',
          type: 'bandwidth',
          value: 125,
          key: 'bandwidth'
        },
        {
          label: '编码',
          type: 'select',
          value: '4/6',
          key: 'coding',
          options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' },
            { label: '4/7', value: '4/7' },
            { label: '4/8', value: '4/8' }
          ]
        },
        {
          label: '扩频因子',
          type: 'number',
          value: 8,
          min: 6,
          max: 12,
          placeholder: '6-12',
          key: 'spreading_factor'
        }
      ]
    },
    {
      id: 'downlink',
      name: '下行通道',
      icon: '📶',
      fields: [
        {
          label: '带宽',
          type: 'bandwidth',
          value: 125,
          key: 'bandwidth'
        },
        {
          label: '编码',
          type: 'select',
          value: '4/5',
          key: 'coding',
          options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' }
          ]
        },
        {
          label: '扩频因子',
          type: 'number',
          value: 10,
          min: 6,
          max: 12,
          placeholder: '6-12',
          key: 'spreading_factor'
        }
      ]
    }
  ])

  // 读取参数
  const readParameters = async () => {
    try {
      const response = await axios.get(`${API_BASE}/parameters`)

      if (response.data.success) {
        const data = response.data.data

        // 更新界面
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
</style>
