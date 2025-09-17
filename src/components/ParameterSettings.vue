<template>
  <section class="section">
    <div class="section-header">
      <i class="header-icon">⚙️</i>
      <h2>参数设置</h2>
    </div>

    <div class="tab-container">
      <nav class="tab-nav">
        <button v-for="tab in paramTabs"
                :key="tab.id"
                :class="{ active: activeTab === tab.id }"
                @click="$emit('update-tab', tab.id)"
                class="tab-button">
          <i :class="tab.icon"></i>
          {{ tab.name }}
        </button>
      </nav>

      <div class="tab-content">
        <div v-for="tab in paramTabs"
             :key="tab.id"
             v-show="activeTab === tab.id"
             class="tab-panel">
          <!-- 扩频码设置区域 -->
          <div class="form-section">
            <div class="form-section-title">
              🔢 扩频码设置
            </div>
            <div class="form-grid">
              <FormField v-for="field in tab.fields.slice(0, 2)"
                         :key="field.label"
                         :label="field.label"
                         :type="field.type"
                         :options="field.options"
                         :placeholder="field.placeholder"
                         v-model="field.value" />
            </div>
          </div>

          <!-- 速率设置区域 -->
          <div class="form-section">
            <div class="form-section-title">
              ⚡ 速率设置
            </div>
            <div class="form-grid">
              <FormField v-for="field in tab.fields.slice(2, 4)"
                         :key="field.label"
                         :label="field.label"
                         :type="field.type"
                         :options="field.options"
                         :placeholder="field.placeholder"
                         v-model="field.value" />
            </div>
          </div>

          <!-- 基带码型设置区域 -->
          <div class="form-section">
            <div class="form-section-title">
              📊 基带码型
            </div>
            <div class="form-grid">
              <FormField :key="tab.fields[4].label"
                         :label="tab.fields[4].label"
                         :type="tab.fields[4].type"
                         :options="tab.fields[4].options"
                         :placeholder="tab.fields[4].placeholder"
                         v-model="tab.fields[4].value" />
            </div>
          </div>

          <!-- 帧校验设置区域 -->
          <div class="form-section">
            <div class="form-section-title">
              ✅ 帧校验设置
            </div>
            <div class="form-grid">
              <FormField v-for="field in tab.fields.slice(5, 7)"
                         :key="field.label"
                         :label="field.label"
                         :type="field.type"
                         :options="field.options"
                         :placeholder="field.placeholder"
                         v-model="field.value" />
            </div>
          </div>

          <!-- 其他设置区域 -->
          <div class="form-section">
            <div class="form-section-title">
              🔧 其他设置
            </div>
            <div class="form-grid">
              <FormField :key="tab.fields[7].label"
                         :label="tab.fields[7].label"
                         :type="tab.fields[7].type"
                         :options="tab.fields[7].options"
                         :placeholder="tab.fields[7].placeholder"
                         v-model="tab.fields[7].value" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
  import { reactive } from 'vue'
  import FormField from './FormField.vue'

  interface ParameterField {
    label: string
    type: string
    value: string | number
    placeholder?: string
    options?: Array<{ label: string, value: string }>
  }

  interface ParameterTab {
    id: string
    name: string
    icon: string
    fields: ParameterField[]
  }

  defineProps<{
    activeTab: string
  }>()

  defineEmits<{
    'update-tab': [tabId: string]
  }>()

  const paramTabs = reactive<ParameterTab[]>([
    {
      id: 'uplink',
      name: '上行测距通道',
      icon: '📡',
      fields: [
        // 1. 扩频码设置
        { label: '扩频码多项式', type: 'text', value: 'x^10+x^3+1', placeholder: '请输入多项式，如x^10+x^3+1' },
        { label: '扩频码初项', type: 'text', value: '1111111111', placeholder: '请输入初项，如1111111111' },

        // 2. 速率设置
        { label: '伪码速率 (Mcps)', type: 'number', value: 10.23, placeholder: '请输入伪码速率' },
        { label: '信息速率 (bps)', type: 'number', value: 1000000, placeholder: '请输入信息速率' },

        // 3. 基带码型
        {
          label: 'PCM设置', type: 'select', value: 'NRZ-L', options: [
            { label: 'NRZ-L', value: 'NRZ-L' },
            { label: 'NRZ-M', value: 'NRZ-M' },
            { label: 'NRZ-S', value: 'NRZ-S' },
            { label: 'Bi-φ-L', value: 'Bi-φ-L' },
            { label: 'Bi-φ-M', value: 'Bi-φ-M' }
          ]
        },

        // 4. 帧校验
        {
          label: '帧校验', type: 'select', value: '是', options: [
            { label: '是', value: '是' },
            { label: '否', value: '否' }
          ]
        },
        {
          label: '载波设置', type: 'select', value: '单载波', options: [
            { label: '单载波', value: '单载波' },
            { label: '调制载波', value: '调制载波' }
          ]
        },

        // 5. 其他
        { label: '最大电平 (dBm)', type: 'number', value: 10, placeholder: '请输入最大电平' }
      ]
    },
    {
      id: 'remote',
      name: '遥控通道',
      icon: '🎮',
      fields: [
        // 1. 扩频码设置
        { label: '扩频码多项式', type: 'text', value: 'x^15+x+1', placeholder: '请输入多项式，如x^15+x+1' },
        { label: '扩频码初项', type: 'text', value: '111111111111111', placeholder: '请输入初项' },

        // 2. 速率设置
        { label: '伪码速率 (Mcps)', type: 'number', value: 5.115, placeholder: '请输入伪码速率' },
        { label: '信息速率 (bps)', type: 'number', value: 1000, placeholder: '请输入信息速率' },

        // 3. 基带码型
        {
          label: 'PCM设置', type: 'select', value: 'NRZ-L', options: [
            { label: 'NRZ-L', value: 'NRZ-L' },
            { label: 'NRZ-M', value: 'NRZ-M' },
            { label: 'NRZ-S', value: 'NRZ-S' },
            { label: 'Bi-φ-L', value: 'Bi-φ-L' },
            { label: 'Bi-φ-M', value: 'Bi-φ-M' }
          ]
        },

        // 4. 帧校验
        {
          label: '帧校验', type: 'select', value: '是', options: [
            { label: '是', value: '是' },
            { label: '否', value: '否' }
          ]
        },
        {
          label: '载波设置', type: 'select', value: '单载波', options: [
            { label: '单载波', value: '单载波' },
            { label: '调制载波', value: '调制载波' }
          ]
        },

        // 5. 其他
        { label: '最大电平 (dBm)', type: 'number', value: 5, placeholder: '请输入最大电平' }
      ]
    },
    {
      id: 'downlink',
      name: '下行测距通道',
      icon: '📶',
      fields: [
        // 1. 扩频码设置
        { label: '扩频码多项式', type: 'text', value: 'x^11+x^2+1', placeholder: '请输入多项式，如x^11+x^2+1' },
        { label: '扩频码初项', type: 'text', value: '11111111111', placeholder: '请输入初项' },

        // 2. 速率设置
        { label: '伪码速率 (Mcps)', type: 'number', value: 20.46, placeholder: '请输入伪码速率' },
        { label: '信息速率 (bps)', type: 'number', value: 2000000, placeholder: '请输入信息速率' },

        // 3. 基带码型
        {
          label: 'PCM设置', type: 'select', value: 'NRZ-L', options: [
            { label: 'NRZ-L', value: 'NRZ-L' },
            { label: 'NRZ-M', value: 'NRZ-M' },
            { label: 'NRZ-S', value: 'NRZ-S' },
            { label: 'Bi-φ-L', value: 'Bi-φ-L' },
            { label: 'Bi-φ-M', value: 'Bi-φ-M' }
          ]
        },

        // 4. 帧校验
        {
          label: '帧校验', type: 'select', value: '是', options: [
            { label: '是', value: '是' },
            { label: '否', value: '否' }
          ]
        },
        {
          label: '载波设置', type: 'select', value: '单载波', options: [
            { label: '单载波', value: '单载波' },
            { label: '调制载波', value: '调制载波' }
          ]
        },

        // 5. 其他
        { label: '最大电平 (dBm)', type: 'number', value: -10, placeholder: '请输入最大电平' }
      ]
    },
    {
      id: 'telemetry',
      name: '遥测通道',
      icon: '📊',
      fields: [
        // 1. 扩频码设置
        { label: '扩频码多项式', type: 'text', value: 'x^8+x^4+x^3+x^2+1', placeholder: '请输入多项式' },
        { label: '扩频码初项', type: 'text', value: '11111111', placeholder: '请输入初项' },

        // 2. 速率设置
        { label: '伪码速率 (Mcps)', type: 'number', value: 2.046, placeholder: '请输入伪码速率' },
        { label: '信息速率 (bps)', type: 'number', value: 2048000, placeholder: '请输入信息速率' },

        // 3. 基带码型
        {
          label: 'PCM设置', type: 'select', value: 'NRZ-L', options: [
            { label: 'NRZ-L', value: 'NRZ-L' },
            { label: 'NRZ-M', value: 'NRZ-M' },
            { label: 'NRZ-S', value: 'NRZ-S' },
            { label: 'Bi-φ-L', value: 'Bi-φ-L' },
            { label: 'Bi-φ-M', value: 'Bi-φ-M' }
          ]
        },

        // 4. 帧校验
        {
          label: '帧校验', type: 'select', value: '是', options: [
            { label: '是', value: '是' },
            { label: '否', value: '否' }
          ]
        },
        {
          label: '载波设置', type: 'select', value: '单载波', options: [
            { label: '单载波', value: '单载波' },
            { label: '调制载波', value: '调制载波' }
          ]
        },

        // 5. 其他
        { label: '最大电平 (dBm)', type: 'number', value: -15, placeholder: '请输入最大电平' }
      ]
    },
    {
      id: 'baseband',
      name: '基带调试',
      icon: '🔧',
      fields: [
        // 1. 扩频码设置
        { label: '扩频码多项式', type: 'text', value: 'x^7+x^3+1', placeholder: '请输入多项式，如x^7+x^3+1' },
        { label: '扩频码初项', type: 'text', value: '1111111', placeholder: '请输入初项' },

        // 2. 速率设置
        { label: '伪码速率 (Mcps)', type: 'number', value: 1.023, placeholder: '请输入伪码速率' },
        { label: '信息速率 (bps)', type: 'number', value: 9600, placeholder: '请输入信息速率' },

        // 3. 基带码型
        {
          label: 'PCM设置', type: 'select', value: 'NRZ-L', options: [
            { label: 'NRZ-L', value: 'NRZ-L' },
            { label: 'NRZ-M', value: 'NRZ-M' },
            { label: 'NRZ-S', value: 'NRZ-S' },
            { label: 'Bi-φ-L', value: 'Bi-φ-L' },
            { label: 'Bi-φ-M', value: 'Bi-φ-M' }
          ]
        },

        // 4. 帧校验
        {
          label: '帧校验', type: 'select', value: '否', options: [
            { label: '是', value: '是' },
            { label: '否', value: '否' }
          ]
        },
        {
          label: '载波设置', type: 'select', value: '调制载波', options: [
            { label: '单载波', value: '单载波' },
            { label: '调制载波', value: '调制载波' }
          ]
        },

        // 5. 其他
        { label: '最大电平 (dBm)', type: 'number', value: 0, placeholder: '请输入最大电平' }
      ]
    }
  ])
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

  .form-section {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 25px;
  }

  .form-section-title {
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 15px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e9ecef;
    display: flex;
    align-items: center;
    gap: 8px;
  }

    .form-section-title::before {
      content: '';
      width: 4px;
      height: 16px;
      background: #007bff;
      border-radius: 2px;
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
