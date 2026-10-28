# onvif — 摄像头 ONVIF 集成(P2 · 第一类 · 只读)

通过 **ONVIF Profile S** 标准协议读取网络摄像头信息。行业通用,零安装。

## 规划

- GetDeviceInformation / GetProfiles:型号、固件、能力
- 事件订阅(移动侦测等 ONVIF Event)→ 告警事件
- RTSP 流地址仅作展示/外链,不转发流媒体

## 边界

- 只读。**不控云台、不抓拍、不存储视频**。
