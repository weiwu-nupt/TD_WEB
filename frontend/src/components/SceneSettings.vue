<template>
  <section class="section">
    <div class="section-header">
      <i class="header-icon">🎭</i>
      <h2>场景设置</h2>
    </div>

    <div class="scene-settings">
      <div class="scene-grid">
        <!-- 多普勒设置 -->
        <div class="scene-card">
          <div class="card-header">
            <i class="card-icon">🌊</i>
            <h4>多普勒设置</h4>
          </div>
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
            <div class="slider-container">
              <label class="slider-label">
                多普勒频移: <span class="value">{{ sceneSettings.doppler.frequency }}Hz</span>
              </label>
              <input type="range"
                     class="slider"
                     v-model="sceneSettings.doppler.frequency"
                     min="-1000"
                     max="1000"
                     step="10">
              <div class="range-labels">
                <span>-1000Hz</span>
                <span>1000Hz</span>
              </div>
            </div>
            <div class="slider-container">
              <label class="slider-label">
                变化率: <span class="value">{{ sceneSettings.doppler.rate }}Hz/s</span>
              </label>
              <input type="range"
                     class="slider"
                     v-model="sceneSettings.doppler.rate"
                     min="0"
                     max="100"
                     step="1">
              <div class="range-labels">
                <span>0Hz/s</span>
                <span>100Hz/s</span>
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

  // 创建一个本地的场景设置对象
  const sceneSettings = reactive({
    doppler: {
      type: 'none',
      frequency: 0,
      rate: 10
    }
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
    grid-template-columns: 1fr;
    gap: 25px;
    max-width: 600px;
    margin: 0 auto;
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

  @media (max-width: 768px) {
    .scene-grid {
      max-width: 100%;
    }

    .scene-settings {
      padding: 20px;
    }
  }
</style>
