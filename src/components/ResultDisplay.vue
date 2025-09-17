<template>
  <section class="section">
    <div class="section-header">
      <i class="header-icon">📈</i>
      <h2>测试结果</h2>
      <div class="result-controls">
        <button class="export-btn" @click="exportResults">
          <i>📊</i>
          导出结果
        </button>
        <button class="refresh-btn" @click="refreshResults">
          <i>🔄</i>
          刷新数据
        </button>
      </div>
    </div>

    <div class="tab-container">
      <nav class="tab-nav">
        <button v-for="tab in resultTabs"
                :key="tab.id"
                :class="{ active: activeTab === tab.id }"
                @click="$emit('update-tab', tab.id)"
                class="tab-button">
          <i>{{ tab.icon }}</i>
          {{ tab.name }}
        </button>
      </nav>

      <div class="tab-content">
        <div v-for="tab in resultTabs"
             :key="tab.id"
             v-show="activeTab === tab.id"
             class="tab-panel">
          <div class="result-summary">
            <div class="summary-card">
              <div class="summary-title">总体状态</div>
              <div class="summary-value good">正常</div>
            </div>
            <div class="summary-card">
              <div class="summary-title">测试时长</div>
              <div class="summary-value">{{ testDuration }}s</div>
            </div>
            <div class="summary-card">
              <div class="summary-title">数据包数</div>
              <div class="summary-value">{{ totalPackets.toLocaleString() }}</div>
            </div>
            <div class="summary-card">
              <div class="summary-title">当前状态</div>
              <div class="summary-value">
                <span class="status-dot good"></span>
                {{ tab.name }}测试
              </div>
            </div>
          </div>

          <div class="result-sections">
            <!-- 误码率指标 -->
            <div v-if="tab.id === 'ber'" class="result-section">
              <div class="section-title">
                <i>🎯</i>
                <span>误码率指标</span>
              </div>
              <div class="result-grid">
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">实时误码率</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">1.2e-5</span>
                    </div>
                    <div class="description">当前实时误码率BER</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">平均误码率</div>
                    <div class="trend-indicator">📉</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">8.7e-6</span>
                    </div>
                    <div class="description">测试周期内平均误码率</div>
                  </div>
                </div>
                <div class="result-card warning">
                  <div class="card-header">
                    <div class="card-title">峰值误码率</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">3.4e-4</span>
                    </div>
                    <div class="description">测试周期内峰值误码率</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">错误比特数</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">1,247</span>
                      <span class="unit">bits</span>
                    </div>
                    <div class="description">累计检测到的错误比特数量</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">总比特数</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">143M</span>
                      <span class="unit">bits</span>
                    </div>
                    <div class="description">测试传输的总比特数量</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">失步次数</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">3</span>
                      <span class="unit">次</span>
                    </div>
                    <div class="description">同步信号丢失次数</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 测距指标 -->
            <div v-else-if="tab.id === 'ranging'" class="result-section">
              <div class="section-title">
                <i>📏</i>
                <span>测距精度</span>
              </div>
              <div class="result-grid">
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">测距精度RMS</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">0.85</span>
                      <span class="unit">m</span>
                    </div>
                    <div class="description">测距精度均方根误差</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">测距系统偏差</div>
                    <div class="trend-indicator">📉</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">-0.12</span>
                      <span class="unit">m</span>
                    </div>
                    <div class="description">测距系统的固有偏差</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">码相位误差</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">23.4</span>
                      <span class="unit">ns</span>
                    </div>
                    <div class="description">伪码相位测量误差</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">多普勒频移</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">142.6</span>
                      <span class="unit">Hz</span>
                    </div>
                    <div class="description">检测到的多普勒频移值</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">信号锁定时间</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">2.34</span>
                      <span class="unit">s</span>
                    </div>
                    <div class="description">测距信号首次锁定时间</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">跟踪环路信噪比</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">45.8</span>
                      <span class="unit">dB-Hz</span>
                    </div>
                    <div class="description">测距跟踪环路的信噪比</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 消息测试指标 -->
            <div v-else-if="tab.id === 'message'" class="result-section">
              <div class="section-title">
                <i>💬</i>
                <span>传输统计</span>
              </div>
              <div class="result-grid">
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">消息成功率</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">99.7</span>
                      <span class="unit">%</span>
                    </div>
                    <div class="description">消息传输成功率统计</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">消息总数</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">15,678</span>
                      <span class="unit">条</span>
                    </div>
                    <div class="description">测试期间传输的消息总数</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">平均消息延时</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">45.2</span>
                      <span class="unit">ms</span>
                    </div>
                    <div class="description">消息传输的平均延迟时间</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">消息吞吐量</div>
                    <div class="trend-indicator">➡️</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">1,024</span>
                      <span class="unit">msg/s</span>
                    </div>
                    <div class="description">每秒处理的消息数量</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">队列深度</div>
                    <div class="trend-indicator">📉</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">12</span>
                      <span class="unit">条</span>
                    </div>
                    <div class="description">消息队列当前深度</div>
                  </div>
                </div>
                <div class="result-card normal">
                  <div class="card-header">
                    <div class="card-title">带宽利用率</div>
                    <div class="trend-indicator">📈</div>
                  </div>
                  <div class="card-content">
                    <div class="value-display">
                      <span class="value">78.5</span>
                      <span class="unit">%</span>
                    </div>
                    <div class="description">消息传输的带宽利用率</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="chart-container">
            <div class="chart-header">
              <h4>{{ tab.name }}趋势图</h4>
              <select class="time-range-select">
                <option>最近1小时</option>
                <option>最近6小时</option>
                <option>最近24小时</option>
                <option>最近7天</option>
              </select>
            </div>
            <div class="chart-placeholder">
              <div class="chart-content">
                📊 {{ tab.name }}图表区域
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
  import { ref } from 'vue'

  defineProps(['activeTab'])
  defineEmits(['update-tab'])

  const testDuration = ref(120)
  const totalPackets = ref(15680)

  const resultTabs = [
    { id: 'ber', name: '误码率', icon: '🎯' },
    { id: 'ranging', name: '测距', icon: '📏' },
    { id: 'message', name: '消息测试', icon: '💬' }
  ]

  const exportResults = () => {
    console.log('导出测试结果...')
  }

  const refreshResults = () => {
    console.log('刷新测试数据...')
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
    border-bottom: 3px solid #17a2b8;
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
    flex: 1;
  }

  .result-controls {
    display: flex;
    gap: 10px;
  }

  .export-btn,
  .refresh-btn {
    padding: 8px 16px;
    border: 2px solid #17a2b8;
    background: white;
    color: #17a2b8;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.3s ease;
  }

    .export-btn:hover,
    .refresh-btn:hover {
      background: #17a2b8;
      color: white;
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

  .result-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
  }

  .summary-card {
    background: linear-gradient(135deg, #e3f2fd, #bbdefb);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    border: 2px solid #2196f3;
  }

  .summary-title {
    font-size: 14px;
    color: #1976d2;
    margin-bottom: 10px;
    font-weight: 500;
  }

  .summary-value {
    font-size: 24px;
    font-weight: bold;
    color: #0d47a1;
  }

    .summary-value.good {
      color: #2e7d32;
    }

  .status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
    animation: pulse 2s infinite;
  }

    .status-dot.good {
      background: #28a745;
    }

  .result-sections {
    display: flex;
    flex-direction: column;
    gap: 30px;
  }

  .result-section {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 25px;
    border: 2px solid #e9ecef;
    transition: all 0.3s ease;
  }

    .result-section:hover {
      border-color: #007bff;
      box-shadow: 0 8px 25px rgba(0, 123, 255, 0.1);
    }

  .section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 18px;
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e9ecef;
  }

  .result-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
  }

  .result-card {
    background: linear-gradient(135deg, #f8f9fa, #fff);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #007bff;
    transition: all 0.3s ease;
  }

    .result-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    }

    .result-card.normal {
      border-left-color: #28a745;
    }

    .result-card.warning {
      border-left-color: #ffc107;
    }

    .result-card.error {
      border-left-color: #dc3545;
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

  .value-display {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 12px;
  }

  .value {
    font-size: 28px;
    font-weight: bold;
    color: #2c3e50;
    font-family: 'Courier New', monospace;
  }

  .unit {
    font-size: 16px;
    color: #6c757d;
    font-weight: 500;
  }

  .description {
    font-size: 13px;
    color: #6c757d;
    line-height: 1.4;
  }

  .chart-container {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    border: 2px solid #e9ecef;
    margin-top: 30px;
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

    .chart-header h4 {
      margin: 0;
      color: #2c3e50;
      font-size: 18px;
    }

  .time-range-select {
    padding: 6px 12px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    background: white;
  }

  .chart-placeholder {
    height: 200px;
    background: white;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #dee2e6;
  }

  .chart-content {
    text-align: center;
    color: #6c757d;
    font-size: 16px;
  }

  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
      opacity: 1;
    }

    50% {
      transform: scale(1.05);
      opacity: 0.8;
    }
  }

  @media (max-width: 768px) {
    .result-summary,
    .result-grid {
      grid-template-columns: 1fr;
    }

    .result-controls {
      flex-direction: column;
    }

    .chart-header {
      flex-direction: column;
      gap: 10px;
    }
  }
</style>
