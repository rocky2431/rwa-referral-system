#!/usr/bin/env python3
"""
测试用户注册流程

测试步骤：
1. 检查未注册用户
2. 注册新用户
3. 验证注册成功
4. 测试重复注册（应返回409）
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
TEST_WALLET = "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_check_unregistered_user():
    """测试1：查询未注册用户"""
    print_section("测试1：查询未注册用户")

    url = f"{BASE_URL}/users/by-wallet/{TEST_WALLET}"
    response = requests.get(url)

    print(f"请求URL: {url}")
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    data = response.json()
    assert response.status_code == 200, "状态码应该是200"
    assert data["exists"] == False, "用户不应该存在"
    assert data["user_id"] is None, "user_id应该为null"

    print("✅ 测试通过：未注册用户正确返回exists=false")
    return True

def test_register_new_user():
    """测试2：注册新用户"""
    print_section("测试2：注册新用户")

    url = f"{BASE_URL}/users/register"
    payload = {
        "wallet_address": TEST_WALLET,
        "username": "TestNewUser",
        "avatar_url": "https://avatar.example.com/test.jpg"
    }

    response = requests.post(url, json=payload)

    print(f"请求URL: {url}")
    print(f"请求体: {json.dumps(payload, indent=2)}")
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    data = response.json()
    assert response.status_code == 201, "状态码应该是201"
    assert data["wallet_address"] == TEST_WALLET.lower(), "钱包地址应该匹配（小写）"
    assert data["username"] == "TestNewUser", "用户名应该匹配"
    assert data["id"] is not None, "应该返回user_id"

    print(f"✅ 测试通过：用户注册成功，user_id={data['id']}")
    return data["id"]

def test_check_registered_user(user_id):
    """测试3：验证注册成功"""
    print_section("测试3：验证用户已注册")

    url = f"{BASE_URL}/users/by-wallet/{TEST_WALLET}"
    response = requests.get(url)

    print(f"请求URL: {url}")
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    data = response.json()
    assert response.status_code == 200, "状态码应该是200"
    assert data["exists"] == True, "用户应该存在"
    assert data["user_id"] == user_id, f"user_id应该匹配: {user_id}"
    assert data["username"] == "TestNewUser", "用户名应该匹配"

    print("✅ 测试通过：已注册用户正确返回exists=true")
    return True

def test_duplicate_registration():
    """测试4：重复注册（应返回409）"""
    print_section("测试4：测试重复注册")

    url = f"{BASE_URL}/users/register"
    payload = {
        "wallet_address": TEST_WALLET,
        "username": "DuplicateUser"
    }

    response = requests.post(url, json=payload)

    print(f"请求URL: {url}")
    print(f"请求体: {json.dumps(payload, indent=2)}")
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    assert response.status_code == 409, "重复注册应该返回409"
    assert "已注册" in response.json()["detail"], "错误信息应该包含'已注册'"

    print("✅ 测试通过：重复注册正确返回409错误")
    return True

def main():
    print("\n" + "="*60)
    print("  用户注册API完整测试")
    print("="*60)

    try:
        # 测试1：检查未注册用户
        test_check_unregistered_user()

        # 测试2：注册新用户
        user_id = test_register_new_user()

        # 测试3：验证注册成功
        test_check_registered_user(user_id)

        # 测试4：测试重复注册
        test_duplicate_registration()

        print_section("🎉 所有测试通过！")
        print("✅ 用户注册流程完全正常")
        print(f"✅ 测试用户ID: {user_id}")
        print(f"✅ 钱包地址: {TEST_WALLET}")

        return True

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except requests.RequestException as e:
        print(f"\n❌ 网络请求失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
