<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useDashboardStore } from '../../../stores/dashboard'
import * as echarts from 'echarts'

// 使用仪表盘存储
const dashboardStore = useDashboardStore()
// 图表DOM引用
const chartContainer = ref(null)
// 图表实例
let chart = null
// 数据
const chartData = ref({
  timestamps: [], // 时间点
  apiCalls: [],   // API调用数
  tokens: []      // Token使用量
})

// 最大显示点数
const MAX_POINTS = 30
// 更新间隔（毫秒）
const UPDATE_INTERVAL = 10000

// 定时器引用
let timer = null

// 初始化图表
function initChart() {
  if (!chartContainer.value) return
  
  // 创建图表实例
  chart = echarts.init(chartContainer.value)
  
  // 获取当前主题模式
  const isDark = dashboardStore.isDarkMode
  const textColor = isDark ? '#e0e0e0' : '#666'
  const axisLineColor = isDark ? '#555' : '#ccc'
  
  // 图表配置
  const option = {
    title: {
      text: 'API实时调用统计',
      left: 'center',
      textStyle: {
        color: textColor
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      }
    },
    legend: {
      data: ['API调用次数', 'Token使用量'],
      top: 30,
      textStyle: {
        color: textColor
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: chartData.value.timestamps,
      axisLabel: {
        rotate: 45,
        color: textColor
      },
      axisLine: {
        lineStyle: {
          color: axisLineColor
        }
      },
      splitLine: {
        lineStyle: {
          color: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        name: 'API调用次数',
        position: 'left',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#5470c6'
          }
        },
        axisLabel: {
          formatter: '{value}',
          color: textColor
        },
        splitLine: {
          lineStyle: {
            color: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
          }
        }
      },
      {
        type: 'value',
        name: 'Token使用量',
        position: 'right',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#91cc75'
          }
        },
        axisLabel: {
          formatter: '{value}',
          color: textColor
        },
        splitLine: {
          lineStyle: {
            color: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
          }
        }
      }
    ],
    series: [
      {
        name: 'API调用次数',
        type: 'line',
        smooth: true,
        data: chartData.value.apiCalls,
        itemStyle: {
          color: '#5470c6'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(84, 112, 198, 0.5)' },
            { offset: 1, color: 'rgba(84, 112, 198, 0.1)' }
          ])
        }
      },
      {
        name: 'Token使用量',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: chartData.value.tokens,
        itemStyle: {
          color: '#91cc75'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(145, 204, 117, 0.5)' },
            { offset: 1, color: 'rgba(145, 204, 117, 0.1)' }
          ])
        }
      }
    ]
  }
  
  // 应用配置
  chart.setOption(option)
  
  // 响应窗口大小变化
  window.addEventListener('resize', () => {
    chart && chart.resize()
  })
}

// 更新图表数据
function updateChartData() {
  // 清空之前的数据
  chartData.value.timestamps = []
  chartData.value.apiCalls = []
  chartData.value.tokens = []
  
  // 获取当前时间
  const now = new Date()
  const timeString = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  
  // 使用后端提供的时间序列数据
  if (dashboardStore.timeSeriesData.calls.length > 0 && dashboardStore.timeSeriesData.tokens.length > 0) {
    // 使用后端的时间序列数据
    chartData.value.timestamps = dashboardStore.timeSeriesData.calls.map(point => point.time)
    chartData.value.apiCalls = dashboardStore.timeSeriesData.calls.map(point => point.value)
    chartData.value.tokens = dashboardStore.timeSeriesData.tokens.map(point => point.value)
  } else {
    // 后备方案：使用最新的调用次数
    const apiCalls = dashboardStore.status.minuteCalls
    const tokenSum = calculateTokenSum()
    
    // 添加数据点
    chartData.value.timestamps.push(timeString)
    chartData.value.apiCalls.push(apiCalls)
    chartData.value.tokens.push(tokenSum)
  }
  
  // 限制显示点数
  if (chartData.value.timestamps.length > MAX_POINTS) {
    const toRemove = chartData.value.timestamps.length - MAX_POINTS
    chartData.value.timestamps.splice(0, toRemove)
    chartData.value.apiCalls.splice(0, toRemove)
    chartData.value.tokens.splice(0, toRemove)
  }
  
  // 更新图表
  if (chart) {
    chart.setOption({
      xAxis: {
        data: chartData.value.timestamps
      },
      series: [
        { data: chartData.value.apiCalls },
        { data: chartData.value.tokens }
      ]
    })
  }
}

// 计算最近一分钟内的Token总量
function calculateTokenSum() {
  let sum = 0
  
  if (dashboardStore.apiKeyStats.length > 0) {
    // 这里简化处理，显示最近的token总量变化
    // 实际项目中可能需要更精确的统计逻辑
    sum = dashboardStore.apiKeyStats.reduce((total, key) => {
      // 计算该密钥下所有模型的token总和
      const keyTokens = Object.values(key.model_stats || {}).reduce((sum, model) => {
        return sum + (model.tokens || 0)
      }, 0)
      return total + keyTokens / 100 // 缩放数值以便在图表中更好显示
    }, 0)
  }
  
  return Math.round(sum)
}

// 监听夜间模式变化
watch(() => dashboardStore.isDarkMode, (newValue) => {
  if (chart) {
    // 重新初始化图表以适应主题变化
    chart.dispose()
    nextTick(() => {
      initChart()
      // 重新填充数据
      if (chartData.value.timestamps.length > 0) {
        chart.setOption({
          xAxis: {
            data: chartData.value.timestamps
          },
          series: [
            { data: chartData.value.apiCalls },
            { data: chartData.value.tokens }
          ]
        })
      }
    })
  }
}, { immediate: false })

// 组件挂载时初始化
onMounted(() => {
  // 初始化图表
  initChart()
  
  // 第一次更新数据
  updateChartData()
  
  // 设置定时更新
  timer = setInterval(() => {
    // 刷新仪表盘数据
    dashboardStore.fetchDashboardData().then(() => {
      // 更新图表
      updateChartData()
    })
  }, UPDATE_INTERVAL)
})

// 组件卸载时清理
onUnmounted(() => {
  // 清除定时器
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  
  // 销毁图表实例
  if (chart) {
    chart.dispose()
    chart = null
  }
  
  // 移除事件监听
  window.removeEventListener('resize', () => {
    chart && chart.resize()
  })
})
</script>

<template>
  <div class="api-calls-chart-container">
    <div ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<style scoped>
.api-calls-chart-container {
  margin: 20px 0;
  border-radius: var(--radius-lg);
  background-color: var(--stats-item-bg);
  padding: 15px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--card-border);
  transition: all 0.3s ease;
}

.api-calls-chart-container:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--button-primary);
  transform: translateY(-3px);
}

.chart-title {
  margin-top: 0;
  margin-bottom: 15px;
  color: var(--color-heading);
  font-weight: 600;
  text-align: center;
}

.chart-container {
  width: 100%;
  height: 350px;
}

@media (max-width: 768px) {
  .chart-container {
    height: 300px;
  }
}

@media (max-width: 480px) {
  .chart-container {
    height: 250px;
  }
}
</style> 