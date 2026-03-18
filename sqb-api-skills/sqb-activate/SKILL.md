---
name: sqb-activate
description: "[后端项目使用]收钱吧终端激活接口技能。用于将设备注册为收钱吧终端，获取terminal_sn和terminal_key。当用户提到收钱吧激活、终端激活、activate terminal、激活码时触发。"
---

# 收钱吧终端激活接口

## 引导词

- 收钱吧激活
- 终端激活
- activate terminal
- 激活码
- 设备注册
- sqb-activate

## 概述

终端激活是接入收钱吧的第一步。通过激活码（code）将一个设备注册为收钱吧终端，获取后续交易所需的 `terminal_sn` 和 `terminal_key`。

## 前置条件

- 已获取服务商凭证：`vendor_sn` 和 `vendor_key`
- 已从收钱吧获取激活码（code），每个激活码绑定一个门店
- API 域名：`https://vsi-api.shouqianba.com`
- 收钱吧无官方 SDK，使用纯 HTTP API 对接，需引入 HTTP 客户端库和 JSON 库

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/terminal/activate` |
| 请求方法 | POST |
| Content-Type | `application/json; charset=utf-8` |
| API 域名 | `https://vsi-api.shouqianba.com` |

## 签名方式

激活接口使用 **vendor 级别签名**（与其他交易接口不同）：

```
Authorization: {vendor_sn} {MD5(request_body + vendor_key)}
```

> 注意：这是唯一使用 vendor_sn/vendor_key 签名的接口，其他接口均使用 terminal_sn/terminal_key。

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| app_id | string | Y | 应用 ID |
| code | string | Y | 激活码 |
| device_id | string | Y | 设备唯一标识，同门店不同设备需使用不同 device_id |
| client_sn | string | N | 客户端编号 |
| name | string | N | 终端名称 |
| os_info | string | N | 操作系统信息 |
| sdk_version | string | N | SDK 版本 |

## 请求示例

```json
{
    "app_id": "2019032019283301102",
    "code": "11000200",
    "device_id": "DEVICE_001",
    "name": "收银台1号",
    "os_info": "Windows 10"
}
```

## 响应参数

| 参数 | 说明 |
|---|---|
| terminal_sn | 终端序列号，后续交易签名使用 |
| terminal_key | 终端密钥，后续交易签名使用，**必须持久化存储** |
| terminal_name | 终端名称 |
| merchant_sn | 商户序列号 |
| store_sn | 门店序列号 |

## 响应示例

```json
{
    "result_code": "200",
    "biz_response": {
        "result_code": "ACTIVATE_SUCCESS",
        "data": {
            "terminal_sn": "10298371039",
            "terminal_key": "68d499beda5f72116592f5c527465656",
            "terminal_name": "收银台1号",
            "merchant_sn": "20190123456",
            "store_sn": "20190123456001"
        }
    }
}
```

## 陷阱与注意事项

### 1. 一个激活码只能激活一次
激活码使用后即失效，重复使用会报错。如需重新激活，需要申请新的激活码。

### 2. device_id 唯一性
同一门店下如有多台设备，每台设备必须使用不同的 `device_id`，否则会覆盖之前的终端。

### 3. terminal_key 必须持久化
`terminal_key` 是后续所有交易签名的核心密钥：
- 必须安全存储到数据库或配置文件
- 集群部署时需在多节点间同步
- 丢失后只能通过重新激活恢复

### 4. 无沙盒环境
激活后的终端对应真实商户和门店，所有交易都是真实的。

## 架构设计

```
项目结构
├── controller/
│   └── SqbTerminalController      # 终端管理控制器
├── service/
│   └── SqbTerminalService         # 终端激活/签到业务逻辑
├── model/
│   ├── ActivateRequest            # 激活请求 DTO
│   └── ActivateResponse           # 激活响应 DTO
└── util/
    └── SqbSignUtil                # 签名工具类（MD5）
```

## 实现步骤

1. 创建签名工具类 `SqbSignUtil`，实现 `MD5(body + key)` 签名逻辑
2. 创建激活请求 DTO `ActivateRequest`（app_id, code, device_id）
3. 实现激活服务 `SqbTerminalService.activate()`，包含签名计算和 HTTP 调用
4. 解析响应，提取 `terminal_sn` 和 `terminal_key`
5. 持久化存储 `terminal_key`（数据库或配置文件）
6. 创建控制器接口供管理后台调用

## 生成规则

当生成激活接口代码时，**必须**包含：
1. vendor 级别签名逻辑（MD5(body + vendor_key)）
2. 完整的请求参数构建
3. 响应解析，提取 terminal_sn 和 terminal_key
4. terminal_key 的持久化存储逻辑（至少提供存储接口/占位）
5. 错误处理（激活失败的重试或提示）

## 代码示例

见 `reference/` 目录：
- `ActivateExample.java` — Java 示例（OkHttp + Jackson）
- `activate_example.py` — Python 示例（requests）
