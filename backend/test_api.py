#!/usr/bin/env python3
"""
测试番茄小说API连通性
诊断 JSONDecodeError 问题
"""

import sys
import os
import json
import requests
from dotenv import load_dotenv

# 添加 backend 到 PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# 测试脚本默认直连，避免本机代理配置把诊断结果污染掉
for proxy_key in [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
]:
    os.environ.pop(proxy_key, None)
os.environ["NO_PROXY"] = "*"

# 从项目导入相关模块
try:
    from novel_downloader.novel_src.offical_tools.downloader import (
        FqReq,
        FqVariable,
        _ensure_fresh_iid,
        get_static_key
    )
    from novel_downloader.novel_src.offical_tools.get_version_code import GetVersionCode
    from config import get_downloader_config
    from novel_downloader.novel_src.base_system.context import GlobalContext
    
    print("[OK] 成功导入项目模块")
except ImportError as e:
    print(f"[ERROR] 导入失败: {e}")
    sys.exit(1)

# 测试章节ID（从你的日志中提取）
TEST_CHAPTER_ID = "7516217799669203518"  # 第681章

def test_1_static_key():
    """测试1: 验证静态密钥"""
    print("\n" + "="*60)
    print("测试1: 静态密钥")
    print("="*60)
    
    key = get_static_key()
    print(f"静态密钥: {key}")
    print(f"密钥长度: {len(key)} (期望: 32)")
    
    if len(key) == 32:
        print("[OK] 静态密钥正确")
        return True
    else:
        print("[ERROR] 静态密钥长度错误")
        return False

def test_2_config_init():
    """测试2: 初始化配置"""
    print("\n" + "="*60)
    print("测试2: 初始化 GlobalContext")
    print("="*60)
    
    try:
        config_data = get_downloader_config()
        print(f"配置项数量: {len(config_data)}")
        print(f"iid: {config_data.get('iid', '未设置')[:20]}..." if config_data.get('iid') else "iid: 未设置")
        
        GlobalContext.initialize(config_data=config_data)
        print("[OK] GlobalContext 初始化成功")
        return True
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")
        return False

def test_3_iid_generation():
    """测试3: 生成 install_id"""
    print("\n" + "="*60)
    print("测试3: 生成 install_id")
    print("="*60)
    
    try:
        _ensure_fresh_iid()
        cfg = GlobalContext.get_config()
        iid = cfg.iid
        
        if iid:
            print(f"install_id: {iid}")
            print(f"server_device_id: {int(iid) - 4096}")
            print(f"[OK] install_id 生成成功")
            return True, iid
        else:
            print("[ERROR] install_id 为空")
            return False, None
    except Exception as e:
        print(f"[ERROR] 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_4_version_code():
    """测试4: 获取版本号"""
    print("\n" + "="*60)
    print("测试4: 获取应用版本号")
    print("="*60)
    
    try:
        version = GetVersionCode.get()
        print(f"版本号: {version}")
        
        if version:
            print("[OK] 版本号获取成功")
            return True, version
        else:
            print("[WARN] 版本号为空，将使用备用值")
            return True, "66732"  # 备用版本号
    except Exception as e:
        print(f"[WARN] 获取失败: {e}")
        print("将使用备用版本号: 66732")
        return True, "66732"

def test_5_register_key(iid, version_code):
    """测试5: 注册密钥"""
    print("\n" + "="*60)
    print("测试5: 注册加密密钥")
    print("="*60)
    
    try:
        fq_var = FqVariable(
            install_id=iid,
            server_device_id=str(int(iid) - 4096),
            aid="1967",
            update_version_code=version_code
        )
        
        fq = FqReq(fq_var, timeout=15)
        print(f"[OK] FqReq 初始化成功")
        print(f"   key_version: {fq._key_version}")
        
        fq.close()
        return True, fq_var
    except Exception as e:
        print(f"[ERROR] 注册失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_6_single_chapter(fq_var):
    """测试6: 获取单个章节"""
    print("\n" + "="*60)
    print(f"测试6: 获取单个章节 ({TEST_CHAPTER_ID})")
    print("="*60)
    
    try:
        fq = FqReq(fq_var, timeout=15)
        
        # 发送请求
        print(f"正在请求章节 {TEST_CHAPTER_ID}...")
        raw_data = fq._batch_fetch(TEST_CHAPTER_ID)
        
        print(f"响应类型: {type(raw_data)}")
        print(f"响应键: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'N/A'}")
        
        # 检查是否有 data 字段
        if isinstance(raw_data, dict) and "data" in raw_data:
            data_keys = list(raw_data["data"].keys())
            print(f"data 键数量: {len(data_keys)}")
            
            if data_keys:
                first_key = data_keys[0]
                chapter_data = raw_data["data"][first_key]
                print(f"章节信息:")
                print(f"  - 是否有 content: {'content' in chapter_data}")
                print(f"  - 是否有 key_version: {'key_version' in chapter_data}")
                
                # 尝试解密
                decrypted = fq._decrypt_contents(raw_data)
                content = decrypted["data"][first_key].get("content", "")
                
                if content:
                    print(f"  - 内容长度: {len(content)} 字符")
                    print(f"  - 内容预览: {content[:100]}...")
                    print("[OK] 章节获取并解密成功")
                    fq.close()
                    return True
                else:
                    print("[ERROR] 解密后内容为空")
            else:
                print("[ERROR] data 中没有章节")
        else:
            print(f"[ERROR] 响应格式异常: {raw_data}")
        
        fq.close()
        return False
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON解析错误: {e}")
        print("   这表明API返回的不是JSON格式的数据")
        print("   可能原因:")
        print("   - API返回了HTML错误页面")
        print("   - 请求被拦截或限流")
        print("   - install_id 无效")
        return False
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_7_raw_api_call():
    """测试7: 直接调用API（不解密）"""
    print("\n" + "="*60)
    print("测试7: 直接HTTP请求（查看原始响应）")
    print("="*60)
    
    try:
        cfg = GlobalContext.get_config()
        iid = cfg.iid
        version_code = GetVersionCode.get() or "66732"
        
        url = "https://api5-normal-sinfonlineb.fqnovel.com/reading/reader/batch_full/v"
        params = {
            "item_ids": TEST_CHAPTER_ID,
            "update_version_code": version_code,
            "aid": "1967",
            "key_register_ts": "0"
        }
        headers = {
            "Cookie": f"install_id={iid}",
            "User-Agent": "Mozilla/5.0"
        }
        
        print(f"URL: {url}")
        print(f"参数: {params}")
        print(f"install_id: {iid[:20]}...")
        print("\n发送请求...")
        
        response = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
        
        print(f"HTTP 状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"响应长度: {len(response.content)} 字节")
        print(f"\n响应内容预览 (前500字符):")
        print("-" * 60)
        print(response.text[:500])
        print("-" * 60)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("\n[OK] 响应是有效的JSON")
                print(f"JSON键: {list(data.keys())}")
                return True
            except:
                print("\n[ERROR] 响应不是有效的JSON")
                print("这就是 JSONDecodeError 的原因！")
                return False
        else:
            print(f"\n[ERROR] HTTP状态码异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试流程"""
    print("[INFO] 番茄小说 API 诊断工具")
    print("="*60)
    
    results = {}
    
    # 测试1: 静态密钥
    results['static_key'] = test_1_static_key()
    
    # 测试2: 配置初始化
    results['config'] = test_2_config_init()
    if not results['config']:
        print("\n[ERROR] 配置初始化失败，无法继续测试")
        return
    
    # 测试3: 生成 IID
    success, iid = test_3_iid_generation()
    results['iid'] = success
    if not success or not iid:
        print("\n[ERROR] install_id 生成失败，无法继续测试")
        return
    
    # 测试4: 版本号
    success, version_code = test_4_version_code()
    results['version'] = success
    
    # 测试5: 注册密钥
    success, fq_var = test_5_register_key(iid, version_code)
    results['register'] = success
    if not success:
        print("\n[ERROR] 密钥注册失败，无法继续测试")
        return
    
    # 测试6: 获取章节
    results['chapter'] = test_6_single_chapter(fq_var)
    
    # 测试7: 原始API调用
    results['raw_api'] = test_7_raw_api_call()
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for test_name, result in results.items():
        status = "[OK] 通过" if result else "[ERROR] 失败"
        print(f"{test_name:15s}: {status}")
    
    # 诊断建议
    print("\n" + "="*60)
    print("诊断建议")
    print("="*60)
    
    if not results.get('raw_api'):
        print("[ISSUE] 问题: API返回非JSON响应")
        print("\n可能的解决方案:")
        print("1. install_id 可能无效")
        print("   - 尝试手动设置 NOVEL_IID 环境变量")
        print("   - 运行: docker-compose down && docker-compose up -d")
        print("\n2. 请求频率过高")
        print("   - 增加 NOVEL_MIN_WAIT_TIME (例如: 2000)")
        print("   - 增加 NOVEL_MAX_WAIT_TIME (例如: 5000)")
        print("\n3. IP被封禁")
        print("   - 等待一段时间后重试")
        print("   - 考虑使用代理")
        print("\n4. 番茄小说API可能已更新")
        print("   - 检查项目是否有更新")
        print("   - 查看 GitHub Issues")
    elif not results.get('chapter'):
        print("[WARN] 问题: API返回JSON但内容异常")
        print("\n可能原因:")
        print("- 加密密钥版本不匹配")
        print("- 章节ID不存在")
        print("- 需要更新加密算法")
    else:
        print("[OK] 所有测试通过！")
        print("API连接正常，问题可能在:")
        print("- 批量请求的章节数量过多")
        print("- 特定章节ID有问题")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARN] 测试被用户中断")
    except Exception as e:
        print(f"\n\n[FATAL] 测试过程中出现意外错误: {e}")
        import traceback
        traceback.print_exc()
()
