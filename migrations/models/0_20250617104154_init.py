from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "areas" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "code" VARCHAR(20) NOT NULL UNIQUE,
    "description" TEXT,
    "is_active" BOOL NOT NULL DEFAULT True,
    "parent_id" INT REFERENCES "areas" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_areas_created_7dfb2d" ON "areas" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_areas_is_dele_910666" ON "areas" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_areas_code_72953d" ON "areas" ("code");
CREATE INDEX IF NOT EXISTS "idx_areas_is_acti_81bb58" ON "areas" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_areas_parent__8c9113" ON "areas" ("parent_id", "name");
COMMENT ON COLUMN "areas"."id" IS '主键ID';
COMMENT ON COLUMN "areas"."created_at" IS '创建时间';
COMMENT ON COLUMN "areas"."updated_at" IS '更新时间';
COMMENT ON COLUMN "areas"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "areas"."name" IS '区域名称';
COMMENT ON COLUMN "areas"."code" IS '区域代码';
COMMENT ON COLUMN "areas"."description" IS '区域描述';
COMMENT ON COLUMN "areas"."is_active" IS '是否启用';
COMMENT ON COLUMN "areas"."parent_id" IS '父级区域';
COMMENT ON TABLE "areas" IS '区域表';
CREATE TABLE IF NOT EXISTS "brands" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "name" VARCHAR(50) NOT NULL UNIQUE,
    "code" VARCHAR(20) NOT NULL UNIQUE,
    "description" TEXT,
    "is_active" BOOL NOT NULL DEFAULT True
);
CREATE INDEX IF NOT EXISTS "idx_brands_created_fa838d" ON "brands" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_brands_is_dele_011e64" ON "brands" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_brands_code_e376fa" ON "brands" ("code");
CREATE INDEX IF NOT EXISTS "idx_brands_is_acti_df4a3c" ON "brands" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_brands_name_fdba21" ON "brands" ("name", "is_active");
COMMENT ON COLUMN "brands"."id" IS '主键ID';
COMMENT ON COLUMN "brands"."created_at" IS '创建时间';
COMMENT ON COLUMN "brands"."updated_at" IS '更新时间';
COMMENT ON COLUMN "brands"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "brands"."name" IS '品牌名称';
COMMENT ON COLUMN "brands"."code" IS '品牌代码';
COMMENT ON COLUMN "brands"."description" IS '品牌描述';
COMMENT ON COLUMN "brands"."is_active" IS '是否启用';
COMMENT ON TABLE "brands" IS '设备品牌表';
CREATE TABLE IF NOT EXISTS "config_templates" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "device_type" VARCHAR(19),
    "template_type" VARCHAR(8) NOT NULL,
    "content" TEXT NOT NULL,
    "variables" JSONB,
    "description" TEXT,
    "is_active" BOOL NOT NULL DEFAULT True,
    "brand_id" INT REFERENCES "brands" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_config_temp_created_44026c" ON "config_templates" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_config_temp_is_dele_fb1efb" ON "config_templates" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_config_temp_device__8cb1d3" ON "config_templates" ("device_type");
CREATE INDEX IF NOT EXISTS "idx_config_temp_templat_eb7d6c" ON "config_templates" ("template_type");
CREATE INDEX IF NOT EXISTS "idx_config_temp_is_acti_3c314b" ON "config_templates" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_config_temp_brand_i_0454bb" ON "config_templates" ("brand_id", "template_type");
COMMENT ON COLUMN "config_templates"."id" IS '主键ID';
COMMENT ON COLUMN "config_templates"."created_at" IS '创建时间';
COMMENT ON COLUMN "config_templates"."updated_at" IS '更新时间';
COMMENT ON COLUMN "config_templates"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "config_templates"."name" IS '模板名称';
COMMENT ON COLUMN "config_templates"."device_type" IS '适用设备类型';
COMMENT ON COLUMN "config_templates"."template_type" IS '模板类型';
COMMENT ON COLUMN "config_templates"."content" IS '模板内容';
COMMENT ON COLUMN "config_templates"."variables" IS '模板变量定义';
COMMENT ON COLUMN "config_templates"."description" IS '模板描述';
COMMENT ON COLUMN "config_templates"."is_active" IS '是否启用';
COMMENT ON COLUMN "config_templates"."brand_id" IS '适用品牌';
COMMENT ON TABLE "config_templates" IS '配置模板表';
CREATE TABLE IF NOT EXISTS "device_groups" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "name" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "is_active" BOOL NOT NULL DEFAULT True,
    "area_id" INT NOT NULL REFERENCES "areas" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_device_grou_created_56c9bd" ON "device_groups" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_device_grou_is_dele_647abc" ON "device_groups" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_device_grou_name_47c2d0" ON "device_groups" ("name");
CREATE INDEX IF NOT EXISTS "idx_device_grou_is_acti_1e01fe" ON "device_groups" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_device_grou_area_id_9f4221" ON "device_groups" ("area_id", "name");
COMMENT ON COLUMN "device_groups"."id" IS '主键ID';
COMMENT ON COLUMN "device_groups"."created_at" IS '创建时间';
COMMENT ON COLUMN "device_groups"."updated_at" IS '更新时间';
COMMENT ON COLUMN "device_groups"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "device_groups"."name" IS '分组名称';
COMMENT ON COLUMN "device_groups"."description" IS '分组描述';
COMMENT ON COLUMN "device_groups"."is_active" IS '是否启用';
COMMENT ON COLUMN "device_groups"."area_id" IS '所属区域';
COMMENT ON TABLE "device_groups" IS '设备分组表';
CREATE TABLE IF NOT EXISTS "device_models" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "name" VARCHAR(100) NOT NULL,
    "device_type" VARCHAR(19) NOT NULL,
    "description" TEXT,
    "is_active" BOOL NOT NULL DEFAULT True,
    "brand_id" INT NOT NULL REFERENCES "brands" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_device_mode_brand_i_922a94" UNIQUE ("brand_id", "name")
);
CREATE INDEX IF NOT EXISTS "idx_device_mode_created_28ed75" ON "device_models" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_device_mode_is_dele_f67ef2" ON "device_models" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_device_mode_name_a93a32" ON "device_models" ("name");
CREATE INDEX IF NOT EXISTS "idx_device_mode_device__18836e" ON "device_models" ("device_type");
CREATE INDEX IF NOT EXISTS "idx_device_mode_is_acti_f1319d" ON "device_models" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_device_mode_brand_i_1221dc" ON "device_models" ("brand_id", "device_type");
COMMENT ON COLUMN "device_models"."id" IS '主键ID';
COMMENT ON COLUMN "device_models"."created_at" IS '创建时间';
COMMENT ON COLUMN "device_models"."updated_at" IS '更新时间';
COMMENT ON COLUMN "device_models"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "device_models"."name" IS '型号名称';
COMMENT ON COLUMN "device_models"."device_type" IS '设备类型';
COMMENT ON COLUMN "device_models"."description" IS '型号描述';
COMMENT ON COLUMN "device_models"."is_active" IS '是否启用';
COMMENT ON COLUMN "device_models"."brand_id" IS '所属品牌';
COMMENT ON TABLE "device_models" IS '设备型号表';
CREATE TABLE IF NOT EXISTS "devices" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "name" VARCHAR(100) NOT NULL,
    "hostname" VARCHAR(100),
    "management_ip" VARCHAR(15) NOT NULL UNIQUE,
    "port" INT NOT NULL DEFAULT 22,
    "account" VARCHAR(50) NOT NULL,
    "password" VARCHAR(255) NOT NULL,
    "enable_password" VARCHAR(255),
    "connection_type" VARCHAR(6) NOT NULL DEFAULT 'ssh',
    "status" VARCHAR(11) NOT NULL DEFAULT 'unknown',
    "last_check_time" TIMESTAMPTZ,
    "version" VARCHAR(100),
    "serial_number" VARCHAR(100),
    "description" TEXT,
    "is_active" BOOL NOT NULL DEFAULT True,
    "area_id" INT NOT NULL REFERENCES "areas" ("id") ON DELETE CASCADE,
    "brand_id" INT NOT NULL REFERENCES "brands" ("id") ON DELETE CASCADE,
    "device_group_id" INT REFERENCES "device_groups" ("id") ON DELETE CASCADE,
    "device_model_id" INT REFERENCES "device_models" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_devices_created_9a1de1" ON "devices" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_devices_is_dele_3ea52b" ON "devices" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_devices_name_b84ed6" ON "devices" ("name");
CREATE INDEX IF NOT EXISTS "idx_devices_status_45b5c1" ON "devices" ("status");
CREATE INDEX IF NOT EXISTS "idx_devices_last_ch_371d5e" ON "devices" ("last_check_time");
CREATE INDEX IF NOT EXISTS "idx_devices_is_acti_198813" ON "devices" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_devices_brand_i_41bf0a" ON "devices" ("brand_id", "status");
CREATE INDEX IF NOT EXISTS "idx_devices_area_id_aca5ae" ON "devices" ("area_id", "status");
CREATE INDEX IF NOT EXISTS "idx_devices_device__a15ecb" ON "devices" ("device_group_id", "status");
COMMENT ON COLUMN "devices"."id" IS '主键ID';
COMMENT ON COLUMN "devices"."created_at" IS '创建时间';
COMMENT ON COLUMN "devices"."updated_at" IS '更新时间';
COMMENT ON COLUMN "devices"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "devices"."name" IS '设备名称';
COMMENT ON COLUMN "devices"."hostname" IS '主机名';
COMMENT ON COLUMN "devices"."management_ip" IS '管理IP地址';
COMMENT ON COLUMN "devices"."port" IS '连接端口';
COMMENT ON COLUMN "devices"."account" IS '登录账号';
COMMENT ON COLUMN "devices"."password" IS '登录密码';
COMMENT ON COLUMN "devices"."enable_password" IS '特权模式密码';
COMMENT ON COLUMN "devices"."connection_type" IS '连接类型';
COMMENT ON COLUMN "devices"."status" IS '设备状态';
COMMENT ON COLUMN "devices"."last_check_time" IS '最后检查时间';
COMMENT ON COLUMN "devices"."version" IS '系统版本';
COMMENT ON COLUMN "devices"."serial_number" IS '序列号';
COMMENT ON COLUMN "devices"."description" IS '设备描述';
COMMENT ON COLUMN "devices"."is_active" IS '是否启用';
COMMENT ON COLUMN "devices"."area_id" IS '所属区域';
COMMENT ON COLUMN "devices"."brand_id" IS '设备品牌';
COMMENT ON COLUMN "devices"."device_group_id" IS '所属分组';
COMMENT ON COLUMN "devices"."device_model_id" IS '设备型号';
COMMENT ON TABLE "devices" IS '设备表';
CREATE TABLE IF NOT EXISTS "alerts" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "alert_type" VARCHAR(13) NOT NULL,
    "severity" VARCHAR(8) NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "message" TEXT NOT NULL,
    "metric_name" VARCHAR(100),
    "current_value" DOUBLE PRECISION,
    "threshold_value" DOUBLE PRECISION,
    "status" VARCHAR(12) NOT NULL DEFAULT 'active',
    "acknowledged_by" VARCHAR(50),
    "acknowledged_at" TIMESTAMPTZ,
    "resolved_at" TIMESTAMPTZ,
    "device_id" INT NOT NULL REFERENCES "devices" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_alerts_device__b3462b" UNIQUE ("device_id", "title", "created_at")
);
CREATE INDEX IF NOT EXISTS "idx_alerts_created_e55fa3" ON "alerts" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_alerts_is_dele_90e495" ON "alerts" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_alerts_alert_t_3f5ce7" ON "alerts" ("alert_type");
CREATE INDEX IF NOT EXISTS "idx_alerts_severit_97b068" ON "alerts" ("severity");
CREATE INDEX IF NOT EXISTS "idx_alerts_status_b1f33e" ON "alerts" ("status");
CREATE INDEX IF NOT EXISTS "idx_alerts_device__5f477b" ON "alerts" ("device_id", "status");
CREATE INDEX IF NOT EXISTS "idx_alerts_severit_c9b062" ON "alerts" ("severity", "status", "created_at");
COMMENT ON COLUMN "alerts"."id" IS '主键ID';
COMMENT ON COLUMN "alerts"."created_at" IS '创建时间';
COMMENT ON COLUMN "alerts"."updated_at" IS '更新时间';
COMMENT ON COLUMN "alerts"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "alerts"."alert_type" IS '告警类型';
COMMENT ON COLUMN "alerts"."severity" IS '告警级别';
COMMENT ON COLUMN "alerts"."title" IS '告警标题';
COMMENT ON COLUMN "alerts"."message" IS '告警消息';
COMMENT ON COLUMN "alerts"."metric_name" IS '相关指标名称';
COMMENT ON COLUMN "alerts"."current_value" IS '当前值';
COMMENT ON COLUMN "alerts"."threshold_value" IS '阈值';
COMMENT ON COLUMN "alerts"."status" IS '告警状态';
COMMENT ON COLUMN "alerts"."acknowledged_by" IS '确认人';
COMMENT ON COLUMN "alerts"."acknowledged_at" IS '确认时间';
COMMENT ON COLUMN "alerts"."resolved_at" IS '解决时间';
COMMENT ON COLUMN "alerts"."device_id" IS '关联设备';
COMMENT ON TABLE "alerts" IS '告警表';
CREATE TABLE IF NOT EXISTS "monitor_metrics" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "metric_type" VARCHAR(11) NOT NULL,
    "metric_name" VARCHAR(100) NOT NULL,
    "value" DOUBLE PRECISION NOT NULL,
    "unit" VARCHAR(20),
    "threshold_warning" DOUBLE PRECISION,
    "threshold_critical" DOUBLE PRECISION,
    "status" VARCHAR(8) NOT NULL DEFAULT 'normal',
    "collected_at" TIMESTAMPTZ NOT NULL,
    "device_id" INT NOT NULL REFERENCES "devices" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_monitor_met_created_cfb550" ON "monitor_metrics" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_monitor_met_is_dele_8ca6f0" ON "monitor_metrics" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_monitor_met_metric__539ac6" ON "monitor_metrics" ("metric_type");
CREATE INDEX IF NOT EXISTS "idx_monitor_met_status_4d3e2d" ON "monitor_metrics" ("status");
CREATE INDEX IF NOT EXISTS "idx_monitor_met_collect_d50813" ON "monitor_metrics" ("collected_at");
CREATE INDEX IF NOT EXISTS "idx_monitor_met_device__52ec73" ON "monitor_metrics" ("device_id", "metric_type", "collected_at");
CREATE INDEX IF NOT EXISTS "idx_monitor_met_status_b7d1f2" ON "monitor_metrics" ("status", "collected_at");
COMMENT ON COLUMN "monitor_metrics"."id" IS '主键ID';
COMMENT ON COLUMN "monitor_metrics"."created_at" IS '创建时间';
COMMENT ON COLUMN "monitor_metrics"."updated_at" IS '更新时间';
COMMENT ON COLUMN "monitor_metrics"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "monitor_metrics"."metric_type" IS '指标类型';
COMMENT ON COLUMN "monitor_metrics"."metric_name" IS '指标名称';
COMMENT ON COLUMN "monitor_metrics"."value" IS '指标值';
COMMENT ON COLUMN "monitor_metrics"."unit" IS '指标单位';
COMMENT ON COLUMN "monitor_metrics"."threshold_warning" IS '告警阈值';
COMMENT ON COLUMN "monitor_metrics"."threshold_critical" IS '严重告警阈值';
COMMENT ON COLUMN "monitor_metrics"."status" IS '指标状态';
COMMENT ON COLUMN "monitor_metrics"."collected_at" IS '采集时间';
COMMENT ON COLUMN "monitor_metrics"."device_id" IS '关联设备';
COMMENT ON TABLE "monitor_metrics" IS '监控指标表';
CREATE TABLE IF NOT EXISTS "operation_logs" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "user" VARCHAR(50),
    "action" VARCHAR(10) NOT NULL,
    "resource_type" VARCHAR(12) NOT NULL,
    "resource_id" VARCHAR(50),
    "resource_name" VARCHAR(200),
    "details" JSONB,
    "ip_address" VARCHAR(45),
    "result" VARCHAR(9) NOT NULL DEFAULT 'success',
    "error_message" TEXT,
    "execution_time" DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS "idx_operation_l_created_de1446" ON "operation_logs" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_operation_l_is_dele_4d9ae2" ON "operation_logs" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_operation_l_user_2390d3" ON "operation_logs" ("user");
CREATE INDEX IF NOT EXISTS "idx_operation_l_action_4da1e2" ON "operation_logs" ("action");
CREATE INDEX IF NOT EXISTS "idx_operation_l_resourc_a196f5" ON "operation_logs" ("resource_type");
CREATE INDEX IF NOT EXISTS "idx_operation_l_result_47d19a" ON "operation_logs" ("result");
CREATE INDEX IF NOT EXISTS "idx_operation_l_user_e5fe36" ON "operation_logs" ("user", "created_at");
CREATE INDEX IF NOT EXISTS "idx_operation_l_action_e3b9f5" ON "operation_logs" ("action", "result", "created_at");
COMMENT ON COLUMN "operation_logs"."id" IS '主键ID';
COMMENT ON COLUMN "operation_logs"."created_at" IS '创建时间';
COMMENT ON COLUMN "operation_logs"."updated_at" IS '更新时间';
COMMENT ON COLUMN "operation_logs"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "operation_logs"."user" IS '操作用户';
COMMENT ON COLUMN "operation_logs"."action" IS '操作动作';
COMMENT ON COLUMN "operation_logs"."resource_type" IS '资源类型';
COMMENT ON COLUMN "operation_logs"."resource_id" IS '资源ID';
COMMENT ON COLUMN "operation_logs"."resource_name" IS '资源名称';
COMMENT ON COLUMN "operation_logs"."details" IS '操作详情';
COMMENT ON COLUMN "operation_logs"."ip_address" IS '操作IP地址';
COMMENT ON COLUMN "operation_logs"."result" IS '操作结果';
COMMENT ON COLUMN "operation_logs"."error_message" IS '错误信息';
COMMENT ON COLUMN "operation_logs"."execution_time" IS '执行耗时(秒)';
COMMENT ON TABLE "operation_logs" IS '操作日志表';
CREATE TABLE IF NOT EXISTS "system_logs" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "level" VARCHAR(8) NOT NULL,
    "logger_name" VARCHAR(100) NOT NULL,
    "module" VARCHAR(100),
    "message" TEXT NOT NULL,
    "exception_info" TEXT,
    "extra_data" JSONB
);
CREATE INDEX IF NOT EXISTS "idx_system_logs_created_ec52ee" ON "system_logs" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_system_logs_is_dele_2dba6b" ON "system_logs" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_system_logs_level_607a60" ON "system_logs" ("level");
CREATE INDEX IF NOT EXISTS "idx_system_logs_module_943f90" ON "system_logs" ("module");
CREATE INDEX IF NOT EXISTS "idx_system_logs_level_4fd60f" ON "system_logs" ("level", "created_at");
CREATE INDEX IF NOT EXISTS "idx_system_logs_module_5fdb06" ON "system_logs" ("module", "level", "created_at");
COMMENT ON COLUMN "system_logs"."id" IS '主键ID';
COMMENT ON COLUMN "system_logs"."created_at" IS '创建时间';
COMMENT ON COLUMN "system_logs"."updated_at" IS '更新时间';
COMMENT ON COLUMN "system_logs"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "system_logs"."level" IS '日志级别';
COMMENT ON COLUMN "system_logs"."logger_name" IS '日志记录器名称';
COMMENT ON COLUMN "system_logs"."module" IS '模块名称';
COMMENT ON COLUMN "system_logs"."message" IS '日志消息内容';
COMMENT ON COLUMN "system_logs"."exception_info" IS '异常信息';
COMMENT ON COLUMN "system_logs"."extra_data" IS '额外数据';
COMMENT ON TABLE "system_logs" IS '系统日志表';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
