# 安全设置配置

# Gemini 1.0 安全设置
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": 'HARM_CATEGORY_CIVIC_INTEGRITY',
        "threshold": 'BLOCK_NONE'
    }
]

# Gemini 2.0 安全设置
SAFETY_SETTINGS_G2 = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "OFF"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "OFF"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "OFF"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "OFF"
    },
    {
        "category": 'HARM_CATEGORY_CIVIC_INTEGRITY',
        "threshold": 'OFF'
    }
]