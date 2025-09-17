<template>
  <div class="app-container">
    <AppHeader />

    <main class="main-content">
      <!-- 参数设置区域 -->
      <ParameterSettings :active-tab="activeParamTab"
                         @update-tab="activeParamTab = $event" />

      <!-- 场景设置区域 -->
      <SceneSettings :settings="sceneSettings"
                     @start-simulation="handleStartSimulation"
                     @reset-settings="handleResetSettings"
                     @stop-simulation="handleStopSimulation" />

      <!-- 测试结果区域 - 独立的第三个显示区域 -->
      <ResultDisplay :active-tab="activeResultTab"
                     @update-tab="activeResultTab = $event" />
    </main>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive } from 'vue'
  import AppHeader from './components/AppHeader.vue'
  import ParameterSettings from './components/ParameterSettings.vue'
  import SceneSettings from './components/SceneSettings.vue'
  import ResultDisplay from './components/ResultDisplay.vue'

  // 响应式数据
  const activeParamTab = ref('uplink')
  const activeResultTab = ref('ber')

  const sceneSettings = reactive({
    interference: {
      type: 'none',
      intensity: -20
    },
    noise: {
      type: 'awgn',
      snr: 15
    },
    dynamic: {
      mode: 'static',
      velocity: 0
    }
  })

  // 事件处理函数
  const handleStartSimulation = () => {
    console.log('开始仿真...', sceneSettings)
    // TODO: 调用后端API
  }

  const handleResetSettings = () => {
    sceneSettings.interference.type = 'none'
    sceneSettings.interference.intensity = -20
    sceneSettings.noise.type = 'awgn'
    sceneSettings.noise.snr = 15
    sceneSettings.dynamic.mode = 'static'
    sceneSettings.dynamic.velocity = 0
  }

  const handleStopSimulation = () => {
    console.log('停止仿真...')
    // TODO: 调用后端API
  }
</script>

<style scoped>
  .app-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
  }

  .main-content {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 30px;
  }

  @media (max-width: 768px) {
    .app-container {
      padding: 10px;
    }

    .main-content {
      gap: 20px;
    }
  }
</style>
