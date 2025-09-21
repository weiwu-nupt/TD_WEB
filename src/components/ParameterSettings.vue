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

              <!-- 滑块控件（扩频因子） -->
              <div v-else-if="field.type === 'range'" class="slider-container">
                <div class="slider-label">
                  <span>{{ field.label }}: </span>
                  <span class="value">{{ field.value }}{{ field.unit }}</span>
                </div>
                <input type="range"
                       class="slider"
                       v-model="field.value"
                       :min="field.min"
                       :max="field.max"
                       :step="field.step">
                <div class="range-labels">
                  <span>{{ field.min }}{{ field.unit }}</span>
                  <span>{{ field.max }}{{ field.unit }}</span>
                </div>
              </div>
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
    min?: number
    max?: number
    step?: number
    unit?: string
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
      name: '上行通道',
      icon: '📡',
      fields: [
        { label: '带宽（MHz）', type: 'number', value: 100, placeholder: '请输入带宽，如100' },
        {
          label: '编码', type: 'select', value: '4/5', options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' },
            { label: '4/7', value: '4/7' },
            { label: '4/8', value: '4/8' }
          ]
        },
        { label: '扩频因子', type: 'range', value: 9, min: 6, max: 12, step: 1, unit: 'dB' },
        { label: '中心频率（GHz）', type: 'number', value: 10, placeholder: '请输入中心频率，如10' },
        { label: '功率（W）', type: 'number', value: 1, placeholder: '请输入功率，如1' }
      ]
    },
    {
      id: 'uplink_interference',
      name: '上行通道（干扰）',
      icon: '📡⚡',
      fields: [
        { label: '带宽（MHz）', type: 'number', value: 100, placeholder: '请输入带宽，如100' },
        {
          label: '编码', type: 'select', value: '4/6', options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' },
            { label: '4/7', value: '4/7' },
            { label: '4/8', value: '4/8' }
          ]
        },
        { label: '扩频因子', type: 'range', value: 8, min: 6, max: 12, step: 1, unit: 'dB' },
        { label: '中心频率（GHz）', type: 'number', value: 10.2, placeholder: '请输入中心频率，如10.2' },
        { label: '功率（W）', type: 'number', value: 0.5, placeholder: '请输入功率，如0.5' }
      ]
    },
    {
      id: 'downlink',
      name: '下行通道',
      icon: '📶',
      fields: [
        { label: '带宽（MHz）', type: 'number', value: 100, placeholder: '请输入带宽，如100' },
        {
          label: '编码', type: 'select', value: '4/7', options: [
            { label: '4/5', value: '4/5' },
            { label: '4/6', value: '4/6' },
            { label: '4/7', value: '4/7' },
            { label: '4/8', value: '4/8' }
          ]
        },
        { label: '扩频因子', type: 'range', value: 10, min: 6, max: 12, step: 1, unit: 'dB' },
        { label: '中心频率（GHz）', type: 'number', value: 12, placeholder: '请输入中心频率，如12' },
        { label: '功率（W）', type: 'number', value: 2, placeholder: '请输入功率，如2' }
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

  .slider-container {
    margin: 10px 0;
  }

  .slider-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    color: #2c3e50;
    font-size: 14px;
    margin-bottom: 10px;
  }

  .value {
    background: #e9ecef;
    padding: 4px 8px;
    border-radius: 4px;
    font-family: monospace;
    color: #007bff;
  }

  .slider {
    width: 100%;
    height: 6px;
    border-radius: 3px;
    background: #e9ecef;
    outline: none;
    appearance: none;
    margin-bottom: 10px;
  }

    .slider::-webkit-slider-thumb {
      appearance: none;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #007bff;
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    }

    .slider::-moz-range-thumb {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #007bff;
      cursor: pointer;
      border: none;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
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
