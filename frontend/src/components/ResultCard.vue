<template>
  <div class="result-card" :class="getStatusClass()">
    <div class="card-header">
      <div class="card-title">{{ title }}</div>
      <div class="trend-indicator">
        <i :class="getTrendIcon()"></i>
      </div>
    </div>

    <div class="card-content">
      <div class="value-display">
        <span class="value">{{ formattedValue }}</span>
        <span class="unit" v-if="unit">{{ unit }}</span>
      </div>

      <div class="status-bar">
        <div class="status-fill"
             :style="{ width: getStatusPercent() + '%' }"></div>
      </div>

      <div class="threshold-info">
        <span class="threshold-label">阈值:</span>
        <span class="threshold-warning">{{ threshold.warning }}{{ unit }}</span>
        <span class="threshold-error">{{ threshold.error }}{{ unit }}</span>
      </div>
    </div>

    <div class="card-footer">
      <div class="description">{{ description }}</div>
      <div class="last-update">
        <i>⏱️</i>
        <span>{{ lastUpdateTime }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'

interface Props {
  title: string
  value: number | string
  unit: string
  trend: 'up' | 'down' | 'stable'
  threshold: { warning: number, error: number }
  description: string
}

const props = defineProps<Props>()

const lastUpdateTime = ref('')
let updateTimer: number

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    if (props.value >= 1e6) {
      return (props.value / 1e6).toFixed(2) + 'M'
    } else if (props.value >= 1e3) {
      return (props.value / 1e3).toFixed(2) + 'K'
    } else if (props.value < 1 && props.value > 0) {
      return props.value.toExponential(2)
    } else {
      return props.value.toFixed(2)
    }
  }
  return props.value
})

const getStatusClass = () => {
  if (typeof props.value !== 'number') return 'normal'

  const numValue = Math.abs(props.value)
  if (numValue >= props.threshold.error) return 'error'
  if (numValue >= props.threshold.warning) return 'warning'
  return 'normal'
}

const getTrendIcon = () => {
  switch (props.trend) {
    case 'up': return '📈'
    case 'down': return '📉'
    case 'stable': return '➡️'
    default: return '➡️'
  }
}

const getStatusPercent = () => {
  if (typeof props.value !== 'number') return 0

  const numValue = Math.abs(props.value)
  const maxThreshold = Math.max(props.threshold.warning, props.threshold.error)

  if (maxThreshold === 0) return 0
  return Math.min((numValue / maxThreshold) * 100, 100)
}

const updateTime = () => {
  const now = new Date()
  lastUpdateTime.value = now.toLocaleTimeString('zh-CN')
}

onMounted(() => {
  updateTime()
  updateTimer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (updateTimer) {
    clearInterval(updateTimer)
  }
})
</script>

<style scoped>
  .result-card {
    background: linear-gradient(135deg, #f8f9fa, #fff);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #007bff;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
  }

    .result-card::before {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, rgba(0, 123, 255, 0.1), rgba(0, 123, 255, 0.05));
      border-radius: 0 0 0 60px;
    }

    .result-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    }

    .result-card.warning {
      border-left-color: #ffc107;
    }

    .result-card.error {
      border-left-color: #dc3545;
    }

    .result-card.normal {
      border-left-color: #28a745;
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

  .card-content {
    margin-bottom: 15px;
  }

  .value-display {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 12px;
  }

  .value {
    font-size: 32px;
    font-weight: bold;
    color: #2c3e50;
    font-family: 'Courier New', monospace;
  }

  .unit {
    font-size: 16px;
    color: #6c757d;
    font-weight: 500;
  }

  .status-bar {
    height: 6px;
    background: #e9ecef;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 10px;
  }

  .status-fill {
    height: 100%;
    background: linear-gradient(90deg, #28a745, #ffc107, #dc3545);
    transition: width 0.5s ease;
    border-radius: 3px;
  }

  .result-card.normal .status-fill {
    background: #28a745;
  }

  .result-card.warning .status-fill {
    background: #ffc107;
  }

  .result-card.error .status-fill {
    background: #dc3545;
  }

  .threshold-info {
    display: flex;
    gap: 10px;
    font-size: 12px;
    color: #6c757d;
    flex-wrap: wrap;
  }

  .threshold-label {
    font-weight: 600;
  }

  .threshold-warning {
    color: #ffc107;
    background: rgba(255, 193, 7, 0.1);
    padding: 2px 6px;
    border-radius: 3px;
  }

  .threshold-error {
    color: #dc3545;
    background: rgba(220, 53, 69, 0.1);
    padding: 2px 6px;
    border-radius: 3px;
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 10px;
  }

  .description {
    font-size: 13px;
    color: #6c757d;
    flex: 1;
    line-height: 1.4;
  }

  .last-update {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #adb5bd;
    white-space: nowrap;
  }

  @media (max-width: 768px) {
    .result-card {
      padding: 15px;
    }

    .value {
      font-size: 24px;
    }

    .card-footer {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    .threshold-info {
      flex-direction: column;
      gap: 4px;
    }
  }
</style>
