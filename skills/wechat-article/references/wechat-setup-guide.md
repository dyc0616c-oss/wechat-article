# 微信开发者平台接入指南

## 用户需要准备
1. AppID
2. AppSecret
3. 当前运行机器的公网 IP
4. 将该 IP 加入微信开发者平台白名单

## 引导步骤
1. 让用户前往微信公众平台开发者设置页面
2. 获取 AppID / AppSecret
3. 查询当前出口 IP
4. 将该 IP 加入 API 白名单
5. 再测试 token 获取是否成功

## 常见报错
- `invalid ip not in whitelist`
  - 原因：IP 未加白或加错号
- `invalid appid`
  - 原因：AppID 填错
- `invalid credential`
  - 原因：Secret 错误或不匹配

## 验证目标
- 能成功获取 `access_token`
- 能成功上传一张测试图片
- 能成功创建一篇测试草稿
