import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

// 创建Vue应用实例
const app = createApp(App)

// 全局属性配置
app.config.globalProperties.$version = '1.0.0'

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('全局错误:', err)
  console.error('错误信息:', info)
  // 这里可以添加错误上报逻辑
}

// 挂载应用
app.mount('#app')
