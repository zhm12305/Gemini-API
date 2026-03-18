import requests
import httpx # 添加 httpx 导入
import logging
import asyncio
from fastapi import HTTPException, status
from app.utils.logging import format_log_message
from app.utils.logging import log

logger = logging.getLogger("my_logger")

def handle_gemini_error(error, current_api_key) -> str:
    # 同时检查 requests 和 httpx 的 HTTPError
    if isinstance(error, (requests.exceptions.HTTPError, httpx.HTTPStatusError)): 
        status_code = error.response.status_code
        if status_code == 400:
            try:
                error_data = error.response.json()
                if 'error' in error_data:
                    if error_data['error'].get('code') == "invalid_argument":
                        error_message = "无效的 API 密钥"
                        log('ERROR', f"{current_api_key[:8]} ... {current_api_key[-3:]} → 无效，可能已过期或被删除", 
                            extra={'key': current_api_key[:8], 'status_code': status_code, 'error_message': error_message})
                        # key_manager.blacklist_key(current_api_key)
                        
                        return error_message
                    error_message = error_data['error'].get('message', 'Bad Request')
                    
                    log('WARNING', f"400 错误请求: {error_message}", 
                        extra={'key': current_api_key[:8], 'status_code': status_code, 'error_message': error_message})
                    return f"400 错误请求: {error_message}"
            except ValueError:
                error_message = "400 错误请求：响应不是有效的JSON格式"
                extra_log_400_json = {'key': current_api_key[:8], 'status_code': status_code, 'error_message': error_message}
                log('WARNING', error_message, extra=extra_log_400_json)
                return error_message

        elif status_code == 403:
            error_message = f"权限被拒绝"
            log('ERROR', error_message, 
                extra={'key': current_api_key[:8], 'status_code': status_code})
            # key_manager.blacklist_key(current_api_key)
            
            return error_message
        
        elif status_code == 429:
            error_message = f"API 密钥配额已用尽或其他原因"
            log('WARNING', error_message, 
                extra={'key': current_api_key[:8], 'status_code': status_code})
            # key_manager.blacklist_key(current_api_key)
             
            return error_message
        
        if status_code == 500:
            error_message = f'Gemini API 内部错误' 
            log('WARNING', error_message, 
                extra={'key': current_api_key[:8], 'status_code': status_code})
            return error_message
  
        if status_code == 503:
            error_message = f"Gemini API 服务繁忙"
            log('WARNING', error_message, 
                extra={'key': current_api_key[:8], 'status_code': status_code})
            return error_message
        
        else:
            error_message = f"未知错误: {status_code}"
            log('WARNING', f"{status_code} 未知错误", 
                extra={'key': current_api_key[:8], 'status_code': status_code, 'error_message': error_message})
            
            return f"未知错误/模型不可用: {status_code}"

    elif isinstance(error, requests.exceptions.ConnectionError):
        error_message = "连接错误"
        log('WARNING', error_message, extra={'error_message': error_message})
        return error_message

    elif isinstance(error, requests.exceptions.Timeout):
        error_message = "请求超时"
        log('WARNING', error_message, extra={'error_message': error_message})
        return error_message
    else:
        error_message = f"发生未知错误: {error}"
        log('ERROR', error_message, extra={'error_message': error_message})
        return error_message

def translate_error(message: str) -> str:
    if "quota exceeded" in message.lower():
        return "API 密钥配额已用尽"
    if "invalid argument" in message.lower():
        return "无效参数"
    if "internal server error" in message.lower():
        return "服务器内部错误"
    if "service unavailable" in message.lower():
        return "服务不可用"
    return message

async def handle_api_error(e: Exception, api_key: str, key_manager, request_type: str, model: str, retry_count: int = 0):
    """统一处理API错误"""
    
    # 同时检查 requests 和 httpx 的 HTTPError
    if isinstance(e, (requests.exceptions.HTTPError, httpx.HTTPStatusError)):
        status_code = e.response.status_code
        # 对500和503错误实现自动重试机制, 最多重试3次
        if retry_count < 3 and (status_code == 500 or status_code == 503):
            error_message = 'Gemini API 内部错误' if (status_code == 500) else "Gemini API 服务目前不可用"
            
            # 等待时间 : MIN_RETRY_DELAY=1, MAX_RETRY_DELAY=16
            wait_time = min(1 * (2 ** retry_count), 16)  
            log('warning', f"{error_message}，将等待{wait_time}秒后重试 ({retry_count+1}/3)", 
                extra={'key': api_key[:8], 'request_type': request_type, 'model': model, 'status_code': int(status_code)})
            # 等待后返回重试信号
            await asyncio.sleep(wait_time)
            return {'remove_cache': False}        
        
        elif status_code == 429:
            error_message = "API 密钥配额已用尽或其他原因"
            log('WARNING', f"429 官方资源耗尽或其他原因", 
                extra={'key': api_key[:8], 'status_code': status_code, 'error_message': error_message})
            # key_manager.blacklist_key(api_key)
                     
            return {'remove_cache': False,'error': error_message, 'should_switch_key': True}             

        else:
            error_detail = handle_gemini_error(e, api_key)
            
            # # 重试次数用尽，在日志中输出错误状态码
            # log('error', f"Gemini 服务器错误({status_code})", 
            #     extra={'key': api_key[:8], 'request_type': request_type, 'model': model, 'status_code': int(status_code)})        
        
            # 不再切换密钥，直接向客户端抛出HTTP异常
            raise HTTPException(status_code=int(status_code),
                          detail=f"Gemini API 服务器错误({status_code})，请稍后重试")
    
    # 对于其他错误，返回切换密钥的信号，并输出错误信息到日志中
    error_detail = handle_gemini_error(e, api_key)
    return {'should_switch_key': True, 'error': error_detail, 'remove_cache': True}
