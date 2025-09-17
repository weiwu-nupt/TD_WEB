<template>
  <section class="section">
    <div class="section-header">
      <i class="header-icon">🎭</i>
      <h2>场景设置</h2>
    </div>

    <div class="scene-settings">
      <div class="scene-grid">
        <!-- 干扰设置 -->
        <div class="scene-card">
          <div class="card-header">
            <i class="card-icon">⚡</i>
            <h4>干扰设置</h4>
          </div>
          <div class="card-content">
            <div class="form-group">
              <label>干扰类型</label>
              <select v-model="settings.interference.type" class="select-field">
                <option value="none">无干扰</option>
                <option value="white">白噪声</option>
                <option value="narrow">窄带干扰</option>
                <option value="pulse">脉冲干扰</option>
                <option value="sweep">扫频干扰</option>
              </select>
            </div>
            <div class="slider-container">
              <label class="slider-label">
                干扰强度: <span class="value">{{ settings.interference.intensity }}dB</span>
              </label>
              <input type="range"
                     class="slider"
                     v-model="settings.interference.intensity"
                     min="-50"
                     max="10"
                     step="1">
              <div class="range-labels">
                <span>-50dB</span>
                <span>10dB</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 噪声设置 -->
        <div class="scene-card">
          <div class="card-header">
            <i class="card-icon">🌊</i>
            <h4>噪声设置</h4>
          </div>
          <div class="card-content">
            <div class="form-group">
              <label>噪声类型</label>
              <select v-model="settings.noise.type" class="select-field">
                <option value="awgn">高斯白噪声</option>
                <option value="colored">有色噪声</option>
                <option value="impulsive">冲击噪声</option>
                <option value="phase">相位噪声</option>
              </select>
            </div>
            <div class="slider-container">
              <label class="slider-label">
                信噪比: <span class="value">{{ settings.noise.snr }}dB</span>
              </label>
              <input type="range"
                     class="slider"
                     v-model="settings.noise.snr"
                     min="-10"
                     max="30"
                     step="0.5">
              <div class="range-labels">
                <span>-10dB</span>
                <span>30dB</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 动态设置 -->
        <div class="scene-card">
          <div class="card-header">
            <i class="card-icon">🚀</i>
            <h4>动态设置</h4>
          </div>
          <div class="card-content">
            <div class="form-group">
              <label>运动模式</label>
              <select v-model="settings.dynamic.mode" class="select-field">
                <option value="static">静态</option>
                <option value="linear">匀速运动</option>
                <option value="acceleration">加速运动</option>
                <option value="circular">圆周运动</option>
                <option value="orbit">轨道运动</option>
              </select>
            </div>
            <div class="slider-container">
              <label class="slider-label">
                速度: <span class="value">{{ settings.dynamic.velocity }}m/s</span>
              </label>
              <input type="range"
                     class="slider"
                     v-model="settings.dynamic.velocity"
                     min="0"
                     max="1000"
                     step="10">
              <div class="range-labels">
                <span>0m/s</span>
                <span>1000m/s</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 信道设置 -->
        <div class="scene-card">
          <div class="card-header">
            <i class="card-icon">📻</i>
            <h4>信道设置</h4>
          </div>
          <div class="card-content">
            <div class="form-group">
              <label>信道模型</label>
              <select v-model="channelModel" class="select-field">
                <option value="awgn">AWGN信道</option>
                <option value="rayleigh">瑞利衰落</option>
                <option value="rician">莱斯衰落</option>
                <option value="multipath">多径信道</option>
              </select>
            </div>
            <div class="slider-container">
              <label class="slider-label">
                多普勒频移: <span class="value">{{ dopplerShift }}Hz</span>
              </label>
              <input type="range"
                     class="slider"
                     v-model="dopplerShift"
                     min="-1000"
                     max="1000"
                     step="10">
              <div class="range-labels">
                <span>-1000Hz</span>
                <span>1000Hz</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="control-panel">
        <div class="control-buttons">
          <button class="btn btn-success" @click="$emit('start-simulation')">
            <i>▶️</i>
            开始仿真
          </button>
          <button class="btn btn-primary" @click="$emit('reset-settings')">
            <i>🔄</i>
            重置设置
          </button>
          <button class="btn btn-danger" @click="$emit('stop-simulation')">
            <i>⏹️</i>
            停止仿真
          </button>
        </div>

        <div class="simulation-status">
          <div class="status-indicator">
            <span class="status-dot" :class="simulationStatus"></span>
            <span>{{ getStatusText() }}</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
  import { ref } from 'vue'

  interface SceneSettings {
    interference: {
      type: string
      intensity: number
    }
    noise: {
      type: string
      snr: number
    }
    dynamic: {
      mode: string
      velocity: number
    }
  }

  defineProps<{
    settings: SceneSettings
  }>()

  defineEmits<{
    'start-simulation': []
    'reset-settings': []
    'stop-simulation': []
  }>()

  const channelModel = ref('awgn')
  const dopplerShift = ref(0)
  const simulationStatus = ref('stopped')

  const getStatusText = () => {
    switch (simulationStatus.value) {
      case 'running': return '仿真运行中'
      case 'stopped': return '仿真已停止'
      case 'paused': return '仿真暂停'
      default: return '未知状态'
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

  .scene-settings {
    padding: 30px;
    background: white;
  }

  .scene-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 25px;
    margin-bottom: 30px;
  }

  .scene-card {
    background: linear-gradient(135deg, #f8f9fa, #fff);
    border: 2px solid #e9ecef;
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.3s ease;
    position: relative;
  }

    .scene-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(135deg, #28a745, #20c997);
    }

    .scene-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
      border-color: #28a745;
    }

  .card-header {
    padding: 20px;
    border-bottom: 1px solid #e9ecef;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .card-icon {
    font-size: 20px;
  }

  .card-header h4 {
    color: #2c3e50;
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }

  .card-content {
    padding: 20px;
  }

  .form-group {
    margin-bottom: 20px;
  }

    .form-group label {
      display: block;
      font-weight: 600;
      color: #2c3e50;
      font-size: 14px;
      margin-bottom: 8px;
    }

  .select-field {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-size: 16px;
    transition: all 0.3s ease;
    background: white;
  }

    .select-field:focus {
      outline: none;
      border-color: #007bff;
      box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
    }

  .slider-container {
    margin: 15px 0;
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

  .control-panel {
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    border-radius: 12px;
    padding: 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 2px solid #e9ecef;
  }

  .control-buttons {
    display: flex;
    gap: 15px;
  }

  .btn {
    padding: 12px 30px;
    border: none;
    border-radius: 25px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .btn-primary {
    background: linear-gradient(135deg, #007bff, #0056b3);
    color: white;
  }

    .btn-primary:hover {
      background: linear-gradient(135deg, #0056b3, #004085);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0, 123, 255, 0.4);
    }

  .btn-success {
    background: linear-gradient(135deg, #28a745, #1e7e34);
    color: white;
  }

    .btn-success:hover {
      background: linear-gradient(135deg, #1e7e34, #155724);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
    }

  .btn-danger {
    background: linear-gradient(135deg, #dc3545, #bd2130);
    color: white;
  }

    .btn-danger:hover {
      background: linear-gradient(135deg, #bd2130, #a71e2a);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(220, 53, 69, 0.4);
    }

  .simulation-status {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
    color: #2c3e50;
  }

  .status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

    .status-dot.running {
      background: #28a745;
    }

    .status-dot.stopped {
      background: #6c757d;
    }

    .status-dot.paused {
      background: #ffc107;
    }

  @keyframes pulse {
    0% {
      transform: scale(1);
      opacity: 1;
    }

    50% {
      transform: scale(1.1);
      opacity: 0.7;
    }

    100% {
      transform: scale(1);
      opacity: 1;
    }
  }

  @media (max-width: 768px) {
    .scene-grid {
      grid-template-columns: 1fr;
    }

    .control-panel {
      flex-direction: column;
      gap: 20px;
    }

    .control-buttons {
      flex-direction: column;
      width: 100%;
    }

    .btn {
      width: 100%;
      justify-content: center;
    }
  }

 </style>
