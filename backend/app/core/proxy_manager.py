"""代理池管理模块"""
import random
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from app.models.schemas import ProxyConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProxyManager:
    """代理池管理器类"""

    def __init__(self):
        """初始化代理池管理器"""
        self.proxies: List[ProxyConfig] = []
        self.failed_proxies: Dict[int, datetime] = {}  # 代理ID -> 失败时间
        self.cooldown_period = timedelta(minutes=5)  # 冷却期5分钟
        self._lock = asyncio.Lock()

    async def load_proxies(self, proxy_list: List[ProxyConfig]):
        """
        加载代理列表

        Args:
            proxy_list: 代理配置列表
        """
        self.proxies = proxy_list
        logger.info(f"加载了 {len(proxy_list)} 个代理")

    async def add_proxy(self, proxy: ProxyConfig):
        """
        添加代理

        Args:
            proxy: 代理配置
        """
        self.proxies.append(proxy)
        logger.info(f"添加代理: {proxy.host}:{proxy.port}")

    async def get_proxy(self, exclude: Optional[List[int]] = None) -> Optional[Dict[str, Any]]:
        """
        获取可用代理(负载均衡)

        Args:
            exclude: 排除的代理 ID 列表

        Returns:
            代理配置字典,如果无可用代理则返回 None
        """
        async with self._lock:
            exclude = exclude or []
            now = datetime.now()

            # 过滤可用代理
            available_proxies = [
                p for p in self.proxies
                if p.is_active
                and p.id not in exclude
                and (p.id not in self.failed_proxies or now - self.failed_proxies[p.id] > self.cooldown_period)
            ]

            if not available_proxies:
                logger.warning("没有可用代理")
                return None

            # 按失败率排序,优先使用成功率高的代理
            available_proxies.sort(
                key=lambda p: p.fail_count / (p.success_count + p.fail_count + 1)
            )

            # 选择代理(加权随机,从前3个中随机选择)
            proxy = random.choice(available_proxies[:min(3, len(available_proxies))])

            return {
                'id': proxy.id,
                'host': proxy.host,
                'port': proxy.port,
                'protocol': proxy.protocol,
                'username': proxy.username,
                'password': proxy.password
            }

    async def report_success(self, proxy_id: int):
        """
        报告代理成功

        Args:
            proxy_id: 代理 ID
        """
        async with self._lock:
            for proxy in self.proxies:
                if proxy.id == proxy_id:
                    proxy.success_count += 1
                    proxy.last_used = datetime.now()

                    # 从失败列表中移除
                    if proxy_id in self.failed_proxies:
                        del self.failed_proxies[proxy_id]

                    logger.info(
                        f"代理 {proxy_id} 成功计数: {proxy.success_count}, "
                        f"成功率: {proxy.success_count / (proxy.success_count + proxy.fail_count):.2%}"
                    )
                    break

    async def report_failure(self, proxy_id: int):
        """
        报告代理失败

        Args:
            proxy_id: 代理 ID
        """
        async with self._lock:
            for proxy in self.proxies:
                if proxy.id == proxy_id:
                    proxy.fail_count += 1
                    self.failed_proxies[proxy_id] = datetime.now()

                    # 如果失败率过高,暂时禁用
                    total_requests = proxy.success_count + proxy.fail_count
                    if total_requests > 5:
                        failure_rate = proxy.fail_count / total_requests
                        if failure_rate > 0.5:
                            proxy.is_active = False
                            logger.warning(
                                f"代理 {proxy_id} 失败率过高 ({failure_rate:.2%}), 已禁用"
                            )

                    logger.warning(
                        f"代理 {proxy_id} 失败计数: {proxy.fail_count}, "
                        f"成功率: {proxy.success_count / total_requests:.2% if total_requests > 0 else 0:.2%}"
                    )
                    break

    async def test_proxy(self, proxy: Dict[str, Any], timeout: int = 10) -> bool:
        """
        测试代理是否可用

        Args:
            proxy: 代理配置字典
            timeout: 超时时间(秒)

        Returns:
            是否可用
        """
        try:
            proxy_url = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"
            proxies = {
                'http://': proxy_url,
                'https://': proxy_url,
            }

            async with httpx.AsyncClient(timeout=timeout, proxies=proxies) as client:
                response = await client.get('https://httpbin.org/ip')
                return response.status_code == 200

        except Exception as e:
            logger.error(f"代理测试失败 {proxy['host']}:{proxy['port']}, 错误: {str(e)}")
            return False

    async def test_all_proxies(self):
        """测试所有代理的可用性"""
        tasks = []
        for proxy in self.proxies:
            task = self._test_and_update(proxy)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        active_count = sum(1 for r in results if r is True)
        logger.info(f"代理测试完成,可用: {active_count}/{len(self.proxies)}")

    async def _test_and_update(self, proxy: ProxyConfig) -> bool:
        """
        测试并更新代理状态

        Args:
            proxy: 代理配置对象

        Returns:
            是否可用
        """
        is_valid = await self.test_proxy({
            'host': proxy.host,
            'port': proxy.port,
            'protocol': proxy.protocol
        })

        proxy.is_active = is_valid
        return is_valid

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取代理池统计信息

        Returns:
            统计信息字典
        """
        active_proxies = [p for p in self.proxies if p.is_active]

        total_success = sum(p.success_count for p in self.proxies)
        total_failure = sum(p.fail_count for p in self.proxies)
        total_requests = total_success + total_failure

        return {
            'total_proxies': len(self.proxies),
            'active_proxies': len(active_proxies),
            'failed_proxies': len(self.failed_proxies),
            'total_requests': total_requests,
            'total_success': total_success,
            'total_failure': total_failure,
            'success_rate': total_success / total_requests if total_requests > 0 else 0,
            'cooldown_period_minutes': self.cooldown_period.total_seconds() / 60
        }

    async def reactivate_failed_proxies(self):
        """重新激活冷却期已过的失败代理"""
        async with self._lock:
            now = datetime.now()
            reactivated_count = 0

            for proxy in self.proxies:
                if not proxy.is_active and proxy.id in self.failed_proxies:
                    if now - self.failed_proxies[proxy.id] > self.cooldown_period:
                        proxy.is_active = True
                        del self.failed_proxies[proxy.id]
                        reactivated_count += 1

            if reactivated_count > 0:
                logger.info(f"重新激活了 {reactivated_count} 个代理")
