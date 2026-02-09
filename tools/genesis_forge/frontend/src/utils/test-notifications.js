// 测试通知系统的脚本
// 在浏览器控制台中运行这些命令

// 测试各种通知类型
function testNotifications() {
  console.log('测试通知系统...')
  
  // 测试成功通知
  window.notifySuccess('测试成功', '这是一个成功的通知消息')
  
  // 测试错误通知
  setTimeout(() => {
    window.notifyError('测试错误', '这是一个错误通知消息')
  }, 1000)
  
  // 测试警告通知
  setTimeout(() => {
    window.notifyWarning('测试警告', '这是一个警告通知消息')
  }, 2000)
  
  // 测试信息通知
  setTimeout(() => {
    window.notifyInfo('测试信息', '这是一个信息通知消息')
  }, 3000)
  
  // 测试带操作的通知
  setTimeout(() => {
    window.notify({
      title: '带操作的通知',
      message: '这个通知包含操作按钮',
      type: 'info',
      autoClose: false,
      actions: [
        {
          label: '取消',
          handler: () => console.log('取消点击'),
          type: 'secondary'
        },
        {
          label: '确认',
          handler: () => console.log('确认点击'),
          type: 'primary'
        }
      ]
    })
  }, 4000)
}

// 测试确认对话框
async function testConfirm() {
  console.log('测试确认对话框...')
  const result = await window.confirm({
    title: '确认测试',
    message: '您确定要执行此操作吗？',
    confirmText: '是的',
    cancelText: '取消'
  })
  console.log('确认结果:', result)
}

// 测试提示输入
async function testPrompt() {
  console.log('测试提示输入...')
  const result = await window.prompt({
    title: '输入测试',
    message: '请输入您的名字：',
    defaultValue: '张三',
    placeholder: '请输入姓名'
  })
  console.log('输入结果:', result)
}

// 将所有函数暴露到window
window.testNotifications = testNotifications
window.testConfirm = testConfirm
window.testPrompt = testPrompt

console.log('通知测试脚本已加载！')
console.log('可用命令：')
console.log('1. testNotifications() - 测试各种通知')
console.log('2. testConfirm() - 测试确认对话框')
console.log('3. testPrompt() - 测试提示输入')