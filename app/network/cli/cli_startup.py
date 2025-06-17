"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cli_startup.py
@DateTime: 2025-06-17
@Docs: CLI模块启动初始化脚本
"""

import asyncio

from app.network.cli.cli_manager import cli_manager
from app.utils.logger import logger


async def start_cli_service() -> None:
    """启动CLI服务"""
    try:
        await cli_manager.start()
        logger.info("CLI服务启动成功")
    except Exception as e:
        logger.error(f"CLI服务启动失败: {e}")
        raise


async def stop_cli_service() -> None:
    """停止CLI服务"""
    try:
        await cli_manager.stop()
        logger.info("CLI服务停止成功")
    except Exception as e:
        logger.error(f"CLI服务停止失败: {e}")


# 在应用启动时调用
async def startup_cli() -> None:
    """应用启动时初始化CLI服务"""
    await start_cli_service()


# 在应用关闭时调用
async def shutdown_cli() -> None:
    """应用关闭时清理CLI服务"""
    await stop_cli_service()


if __name__ == "__main__":
    # 测试CLI服务
    async def main():
        await start_cli_service()

        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭服务...")
            await stop_cli_service()

    asyncio.run(main())
