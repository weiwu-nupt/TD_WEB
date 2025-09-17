<template>
  <header class="app-header">
    <div class="header-content">
      <div class="title">
        <i class="icon">📡</i>
        <h1>地面检测设备控制面板</h1>
      </div>
      <div class="status-info">
        <span class="status-item">
          <span class="status-dot" :class="systemStatus"></span>
          {{ statusText }}
        </span>
        <span class="time">{{ currentTime }}</span>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const currentTime = ref('')
const systemStatus = ref('online')

const statusText = computed(() => {
  return systemStatus.value === 'online' ? '系统在线' : '系统离线'
})

let timeInterval: number

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN')
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
  .app-header {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px 20px 0 0;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }

  .header-content {
    background: linear-gradient(135deg, #2c3e50, #3498db);
    color: white;
    padding: 25px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .title {
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .icon {
    font-size: 32px;
  }

  .title h1 {
    font-size: 28px;
    font-weight: bold;
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  }

  .status-info {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
  }

  .status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

    .status-dot.online {
      background: #28a745;
    }

    .status-dot.offline {
      background: #dc3545;
    }

  .time {
    font-size: 12px;
    opacity: 0.8;
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
    }

    50% {
      transform: scale(1.2);
    }

    100% {
      transform: scale(1);
    }
  }

  @media (max-width: 768px) {
    .header-content {
      flex-direction: column;
      gap: 15px;
      text-align: center;
    }

    .title h1 {
      font-size: 24px;
    }

    .status-info {
      align-items: center;
    }
  }
</style>
