<template>
  <header class="app-header">
    <div class="header-content">
      <div class="title-section">
        <div class="logo">
          <i class="icon">📡</i>
        </div>
        <div class="title-text">
          <h1>地面检测系统</h1>
          <span class="subtitle">Ground Detection System</span>
        </div>
      </div>

      <div class="status-section">
        <div class="status-indicators">
          <div class="status-item">
            <span class="status-dot" :class="systemStatus"></span>
            <span class="status-text">{{ statusText }}</span>
          </div>
          <div class="separator"></div>
          <div class="time-display">
            <i class="time-icon">🕐</i>
            <span class="time">{{ currentTime }}</span>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted } from 'vue'

  const currentTime = ref('')
  const systemStatus = ref('online')

  const statusText = computed(() => {
    return systemStatus.value === 'online' ? '系统在线' : '系统离线'
  })

  let timeInterval: number

  const updateTime = () => {
    const now = new Date()
    currentTime.value = now.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
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
    border-radius: 1.25rem 1.25rem 0 0;
    box-shadow: 0 0.25rem 1.25rem rgba(0, 0, 0, 0.1);
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.2);
    /* 关键：让整个header跟随页面缩放 */
    transform-origin: top center;
    width: 90vw;
    max-width: 87.5rem; /* 1400px at 1rem = 16px */
    min-width: 25rem; /* 400px minimum */
    margin: 0 auto;
    font-size: 1rem;
  }

  .header-content {
    background: linear-gradient(135deg, #2c3e50 0%, #3498db 50%, #2980b9 100%);
    color: white;
    padding: 1.25em 1.875em;
    display: flex;
    justify-content: space-between;
    align-items: center;
    min-height: 5em;
    position: relative;
    overflow: hidden;
    width: 100%;
  }

    .header-content::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
      opacity: 0.3;
      pointer-events: none;
    }

  .title-section {
    display: flex;
    align-items: center;
    gap: 0.9375em;
    position: relative;
    z-index: 1;
  }

  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 3.75em;
    height: 3.75em;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 0.9375em;
    border: 2px solid rgba(255, 255, 255, 0.2);
    transition: all 0.3s ease;
  }

    .logo:hover {
      background: rgba(255, 255, 255, 0.25);
      transform: scale(1.05);
    }

  .icon {
    font-size: 2em;
    filter: drop-shadow(0 0.125em 0.25em rgba(0, 0, 0, 0.3));
  }

  .title-text h1 {
    font-size: 2em;
    font-weight: bold;
    margin: 0;
    text-shadow: 0.125em 0.125em 0.25em rgba(0, 0, 0, 0.3);
    line-height: 1.2;
    letter-spacing: 0.05em;
  }

  .subtitle {
    font-size: 1em;
    opacity: 0.8;
    font-weight: 300;
    letter-spacing: 0.03125em;
    text-transform: uppercase;
    margin-top: 0.25em;
  }

  .status-section {
    position: relative;
    z-index: 1;
  }

  .status-indicators {
    display: flex;
    align-items: center;
    gap: 0.9375em;
    background: rgba(255, 255, 255, 0.1);
    padding: 0.75em 1.25em;
    border-radius: 1.5625em;
    border: 1px solid rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(5px);
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 0.5em;
  }

  .status-dot {
    width: 0.75em;
    height: 0.75em;
    border-radius: 50%;
    animation: pulse 2s infinite;
    box-shadow: 0 0 0.625em currentColor;
  }

    .status-dot.online {
      background: #2ecc71;
      color: #2ecc71;
    }

    .status-dot.offline {
      background: #e74c3c;
      color: #e74c3c;
    }

  .status-text {
    font-size: 0.875em;
    font-weight: 500;
    white-space: nowrap;
  }

  .separator {
    width: 1px;
    height: 1.25em;
    background: rgba(255, 255, 255, 0.3);
  }

  .time-display {
    display: flex;
    align-items: center;
    gap: 0.375em;
  }

  .time-icon {
    font-size: 0.875em;
    opacity: 0.8;
  }

  .time {
    font-size: 0.875em;
    font-weight: 500;
    font-family: 'Courier New', monospace;
    white-space: nowrap;
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
      opacity: 1;
    }

    50% {
      transform: scale(1.2);
      opacity: 0.7;
    }

    100% {
      transform: scale(1);
      opacity: 1;
    }
  }

  /* 响应式设计 - 处理布局变化和宽度适应 */
  @media (max-width: 768px) {
    .app-header {
      width: 95vw;
      min-width: 20rem;
    }

    .header-content {
      flex-direction: column;
      gap: 1em;
      text-align: center;
      padding: 1.25em;
      min-height: auto;
    }

    .title-section {
      justify-content: center;
    }

    .status-section {
      width: 100%;
    }

    .status-indicators {
      justify-content: center;
      width: 100%;
      max-width: 25em;
      margin: 0 auto;
    }

    .subtitle {
      display: block;
      margin-top: 0.25em;
    }
  }

  @media (max-width: 480px) {
    .app-header {
      width: 98vw;
      min-width: 18rem;
    }

    .header-content {
      gap: 0.75em;
      padding: 1em;
    }

    .title-section {
      gap: 0.75em;
    }

    .logo {
      width: 3em;
      height: 3em;
    }

    .icon {
      font-size: 1.5em;
    }

    .title-text h1 {
      font-size: 1.5em;
    }

    .subtitle {
      font-size: 0.8em;
    }

    .status-indicators {
      flex-direction: column;
      gap: 0.75em;
      padding: 1em;
    }

    .separator {
      width: 4em;
      height: 1px;
    }

    .status-text,
    .time {
      font-size: 0.75em;
    }

    .time-icon {
      font-size: 0.75em;
    }
  }
</style>
