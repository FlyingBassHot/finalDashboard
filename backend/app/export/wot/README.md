# wot — WoT Thing Description 导出(决策 D2)

把底座实体**自动翻译**成 W3C WoT TD JSON,**仅作导出**,
不作为内部运行模型。

## 映射草案

- Entity → Thing(`@type` 按能力映射)
- readonly 能力 → properties affordance
- on_off / set_level / action 能力 → actions affordance
- 通过导出端点(如 `GET /api/export/wot`)按需生成,供第三方系统消费

## 边界

- 单向翻译,不消费外部 TD;内部语义以 HA 风格 Entity 为准。
