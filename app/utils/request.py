import asyncio
import time
from typing import Dict, Any
from app.utils.logging import log

class ActiveRequestsManager:
    """管理活跃API请求的类"""
    
    def __init__(self, requests_pool: Dict[str, asyncio.Task] = None):
        self.active_requests = requests_pool if requests_pool is not None else {}  # 存储活跃请求
    
    def add(self, key: str, task: asyncio.Task):
        """添加新的活跃请求任务"""
        task.creation_time = time.time()  # 添加创建时间属性
        self.active_requests[key] = task
    
    def get(self, key: str):
        """获取活跃请求任务"""
        return self.active_requests.get(key)
    
    def remove(self, key: str):
        """移除活跃请求任务"""
        if key in self.active_requests:
            del self.active_requests[key]
            return True
        return False
    
    def clean_completed(self):
        """清理所有已完成或已取消的任务"""
        
        for key, task in self.active_requests.items():
            if task.done() or task.cancelled():
                del self.active_requests[key]        
        
        # if keys_to_remove:
        #    log('info', f"清理已完成请求任务: {len(keys_to_remove)}个", cleanup='active_requests')
    
    def clean_long_running(self, max_age_seconds: int = 300):
        """清理长时间运行的任务"""
        now = time.time()
        long_running_keys = []
        
        for key, task in list(self.active_requests.items()):
            if (hasattr(task, 'creation_time') and
                task.creation_time < now - max_age_seconds and
                not task.done() and not task.cancelled()):
                
                long_running_keys.append(key)
                task.cancel()  # 取消长时间运行的任务
        
        if long_running_keys:
            log('warning', f"取消长时间运行的任务: {len(long_running_keys)}个", cleanup='long_running_tasks')
