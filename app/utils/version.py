import requests
from app.utils.logging import log
import app.config.settings as settings
async def check_version():
    """
    检查应用程序版本更新
    
    从本地和远程获取版本信息，并比较版本号以确定是否有更新
    """
    # 导入全局变量
    try:
        # 读取本地版本
        with open("./version.txt", "r") as f:
            version_line = f.read().strip()
            settings.version['local_version'] = version_line.split("=")[1] if "=" in version_line else "0.0.0"
        
        # 获取远程版本
        github_url = "https://raw.githubusercontent.com/wyeeeee/hajimi/refs/heads/main/version.txt"
        response = requests.get(github_url, timeout=5)
        if response.status_code == 200:
            version_line = response.text.strip()
            settings.version['remote_version']= version_line.split("=")[1] if "=" in version_line else "0.0.0"
            # 比较版本号
            local_parts = [int(x) for x in settings.version['local_version'].split(".")]
            remote_parts = [int(x) for x in settings.version['remote_version'].split(".")]
            
            # 确保两个列表长度相同
            while len(local_parts) < len(remote_parts):
                local_parts.append(0)
            while len(remote_parts) < len(local_parts):
                remote_parts.append(0)
                
            # 比较版本号
            settings.version['has_update'] = False
            for i in range(len(local_parts)):
                if remote_parts[i] > local_parts[i]:
                    settings.version['has_update'] = True
                    break
                elif remote_parts[i] < local_parts[i]:
                    break
            
            log('info', f"版本检查: 本地版本 {settings.version['local_version']}, 远程版本 {settings.version['remote_version']}, 有更新: {settings.version['has_update']}")
        else:
            log('warning', f"无法获取远程版本信息，HTTP状态码: {response.status_code}")
    except Exception as e:
        log('error', f"版本检查失败: {str(e)}")
        
    return settings.version['has_update']