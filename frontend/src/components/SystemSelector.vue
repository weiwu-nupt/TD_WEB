<template>
  <div class="system-selector">
    <div class="container">
      <h1>选择系统类型</h1>

      <div class="cards">
        <div class="card" @click="selectSystem('ground')">
          <h3>🏗️ 地面检测系统</h3>
          <p>专业的地面通信测试平台</p>
        </div>

        <div class="card" @click="selectSystem('mixed')">
          <h3>🔮 虚实融合系统</h3>
          <p>虚拟现实集成测试平台</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  const emit = defineEmits(['system-selected'])

  const selectSystem = (type) => {
    console.log('选择系统:', type)
    emit('system-selected', type)
  }
</script>

<style scoped>
  .system-selector {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }

  .container {
    background: white;
    border-radius: 1rem;
    padding: 3rem;
    text-align: center;
    max-width: 800px;
  }

  h1 {
    color: #2c3e50;
    margin-bottom: 2rem;
    font-size: 2.5rem;
  }

  .cards {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }

  .card {
    background: #f8f9fa;
    border: 2px solid #e9ecef;
    border-radius: 1rem;
    padding: 2rem;
    cursor: pointer;
    transition: all 0.3s ease;
  }

    .card:hover {
      border-color: #007bff;
      transform: translateY(-5px);
      box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }

    .card h3 {
      color: #2c3e50;
      margin-bottom: 1rem;
      font-size: 1.5rem;
    }

    .card p {
      color: #666;
      margin: 0;
    }

  @media (max-width: 768px) {
    .cards {
      grid-template-columns: 1fr;
    }

    .container {
      padding: 2rem;
    }

    h1 {
      font-size: 2rem;
    }
  }
</style>
