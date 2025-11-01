"""
富途牛牛API配置文件

使用用户提供的真实API凭证
"""

# 富途API配置
FUTU_CONFIG = {
    'host': '127.0.0.1',
    'port': 11111,
    'market': 'HK',
    'websocket_port': 33333,
    'websocket_key': 'fc724f767796db1f',
    'user_id': '2860386'
}

# 权限说明
PERMISSION_INFO = {
    'hk_stock': {
        'level': 'LV1',
        'name': '港股行情',
        'enabled': True,
        'description': '可获取港股实时行情和历史数据',
        'trading_enabled': False,  # 需要LV3以上才能交易
        'required_level': 'LV3'
    },
    'hk_option': {
        'level': 'LV1',
        'name': '港股期权',
        'enabled': True,
        'description': '可获取港股期权行情数据',
        'trading_enabled': False,
        'required_level': 'LV3'
    },
    'hk_future': {
        'level': 'LV1',
        'name': '港股期货',
        'enabled': True,
        'description': '可获取港股期货行情数据',
        'trading_enabled': False,
        'required_level': 'LV3'
    },
    'hk_trading': {
        'level': '无权限',
        'name': '港股交易',
        'enabled': False,
        'description': '需要升级至LV3才能交易',
        'required_level': 'LV3'
    }
}

# 支持的港股代码
SUPPORTED_HK_SYMBOLS = {
    '00700.HK': '腾讯控股',
    '0388.HK': '香港交易所',
    '1398.HK': '中国工商银行',
    '0939.HK': '中国建设银行',
    '3988.HK': '中国银行',
    '1299.HK': '友邦保险',
    '2318.HK': '中国平安',
    '3690.HK': '美团',
    '0941.HK': '中国移动',
    '0883.HK': '中国海洋石油',
    '0011.HK': '恒生银行',
    '0386.HK': '中国石油化工股份',
    '0857.HK': '中国石油股份',
    '0883.HK': '中国海洋石油',
    '0762.HK': '中国联通',
    '2007.HK': '碧桂园',
    '1093.HK': '石药集团',
    '1171.HK': '兖州煤业股份',
    '1821.HK': 'ESR',
    '2020.HK': '安踏体育',
    '2382.HK': '舜宇光学科技',
    '2628.HK': '中国人寿',
    '3328.HK': '交通银行',
    '3800.HK': '保利协鑫能源',
    '6098.HK': '碧桂园服务',
    '9988.HK': '阿里巴巴-SW'
}

# 快速使用指南
QUICK_START = """
=== 富途API快速使用 ===

✅ 当前权限：港股LV1
   - 可获取实时行情
   - 可获取历史数据
   - 不可直接交易（需LV3）

📌 使用步骤：
1. 启动FutuOpenD客户端
2. 使用牛牛号2860386登录
3. 运行行情测试脚本

⚠️  如需交易功能：
   - 请在富途牛牛APP中升级权限
   - 升级至LV3或以上
   - 或联系富途客服
"""
