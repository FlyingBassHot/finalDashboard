"""插件体系错误类型。"""


class IntegrationError(Exception):
    """集成相关错误基类。"""


class IntegrationConfigError(IntegrationError):
    """集成清单 / 实例配置非法。"""


class UnknownIntegrationError(IntegrationError):
    """引用了未注册的集成。"""


class UnsupportedActionError(IntegrationError):
    """动作被能力白名单拒绝 —— 功能边界强制的核心异常。

    典型场景:对只读集成(未声明写能力)发起任何动作请求。
    调用方应将其映射为 4xx 而不是 5xx。
    """


class ActionExecutionError(IntegrationError):
    """动作执行失败,或目标实体不存在。"""
