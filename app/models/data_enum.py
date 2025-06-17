"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: data_enum.py
@DateTime: 2025-06-17
@Docs: 网络自动化平台数据模型枚举类定义
"""

from enum import Enum


class DeviceTypeEnum(str, Enum):
    """设备类型枚举"""

    SWITCH = "switch"
    ROUTER = "router"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"
    WIRELESS_CONTROLLER = "wireless_controller"


class ConnectionTypeEnum(str, Enum):
    """连接类型枚举"""

    SSH = "ssh"
    TELNET = "telnet"
    SNMP = "snmp"


class DeviceStatusEnum(str, Enum):
    """设备状态枚举"""

    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class TemplateTypeEnum(str, Enum):
    """配置模板类型枚举"""

    INIT = "init"
    SECURITY = "security"
    VLAN = "vlan"
    ROUTING = "routing"
    QOS = "qos"
    BACKUP = "backup"
    MONITOR = "monitor"


class MetricTypeEnum(str, Enum):
    """监控指标类型枚举"""

    CPU = "cpu"
    MEMORY = "memory"
    INTERFACE = "interface"
    TEMPERATURE = "temperature"
    DISK = "disk"
    POWER = "power"
    FAN = "fan"


class MetricStatusEnum(str, Enum):
    """指标状态枚举"""

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertTypeEnum(str, Enum):
    """告警类型枚举"""

    THRESHOLD = "threshold"
    STATUS = "status"
    CONNECTION = "connection"
    CONFIGURATION = "configuration"
    SECURITY = "security"


class SeverityEnum(str, Enum):
    """告警级别枚举"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"


class AlertStatusEnum(str, Enum):
    """告警状态枚举"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class OperationResultEnum(str, Enum):
    """操作结果枚举"""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class LogLevelEnum(str, Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ResourceTypeEnum(str, Enum):
    """资源类型枚举"""

    DEVICE = "device"
    TEMPLATE = "template"
    ALERT = "alert"
    AREA = "area"
    BRAND = "brand"
    DEVICE_MODEL = "device_model"
    DEVICE_GROUP = "device_group"
    CONFIG = "config"
    MONITOR = "monitor"
    USER = "user"
    SYSTEM = "system"


class ActionEnum(str, Enum):
    """操作动作枚举"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    EXECUTE = "execute"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    BACKUP = "backup"
    RESTORE = "restore"
    RESTART = "restart"
    SHUTDOWN = "shutdown"
    LOGIN = "login"
    LOGOUT = "logout"
