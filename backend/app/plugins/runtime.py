"""运行期装配：目录、事件总线、持久化、状态表与实例运行器。"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.events import EventBus
from app.history.recorder import HistoryRecorder
from app.plugins.action_gateway import ActionGateway
from app.plugins.audit import DatabaseAuditSink
from app.plugins.catalog import EntityCatalog
from app.plugins.persistence import PersistenceSubscriber
from app.plugins.registry import IntegrationRegistry, default_registry
from app.plugins.runner import IntegrationRunner, SchedulerLike
from app.plugins.state_store import StateStore
from app.realtime import RealtimeHub
from app.topology.recorder import TopologyRecorder

SessionFactory = async_sessionmaker[AsyncSession]


class Runtime:
    def __init__(
        self,
        session_factory: SessionFactory,
        scheduler: SchedulerLike,
        registry: IntegrationRegistry | None = None,
    ) -> None:
        self.registry = registry or default_registry
        self.catalog = EntityCatalog()
        self.bus = EventBus()
        self.state_store = StateStore()

        self.realtime = RealtimeHub()
        self.realtime.register(self.bus)

        self.action_gateway = ActionGateway(
            self.catalog,
            audit=DatabaseAuditSink(session_factory),
        )

        self.persistence = PersistenceSubscriber(session_factory)
        self.persistence.register(self.bus)

        self.history = HistoryRecorder(session_factory)
        self.history.register(self.bus)

        self.topology = TopologyRecorder(session_factory)
        self.topology.register(self.bus)

        self.runner = IntegrationRunner(
            registry=self.registry,
            catalog=self.catalog,
            bus=self.bus,
            session_factory=session_factory,
            state_store=self.state_store,
            scheduler=scheduler,
        )

    async def startup(self) -> None:
        await self.persistence.load_into(self.catalog, self.state_store)
        await self.runner.start_enabled()

    async def shutdown(self) -> None:
        await self.runner.stop_all()
        self.persistence.close()
        self.history.close()
        self.topology.close()
        self.realtime.close()
