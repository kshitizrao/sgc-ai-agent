from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sgc_shared.types import ToolResult


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    async def execute(self, session: AsyncSession, **kwargs: Any) -> ToolResult:
        pass


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    async def invoke(
        self, name: str, session: AsyncSession, **kwargs: Any
    ) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(tool_name=name, success=False, error=f"Unknown tool: {name}")
        return await tool.execute(session, **kwargs)


def create_registry() -> ToolRegistry:
    from sgc_tools.catalog.parts_tools import (
        CheckPartFitmentTool,
        SearchPartsTool,
        SuggestAlternatesTool,
    )
    from sgc_tools.catalog.services_tools import (
        CompareServicePackagesTool,
        EstimateRepairCostTool,
        EstimateServiceCostTool,
        ListQuickServicesTool,
    )
    from sgc_tools.diagnostics.diagnostic_tools import (
        DiagnoseSymptomTool,
        GetPredictiveMaintenanceTool,
    )
    from sgc_tools.marketplace.garage_tools import RecommendGaragesTool
    from sgc_tools.operations.claims_tools import (
        ExplainClaimLiabilityTool,
        GetClaimStatusTool,
    )
    from sgc_tools.operations.rsa_tools import (
        DispatchResourceTool,
        LogEmergencyRequestTool,
        TriageEmergencyTool,
    )
    from sgc_tools.agent_meta.session_tools import CreateSessionNoteTool
    from sgc_tools.pikpart.pikpart_tools import (
        FetchPikpartServicesTool,
        FetchPikpartCustomersTool,
        FetchPikpartCustomerVehiclesTool,
        FetchPikpartVehicleServicesTool,
        FetchPikpartBookingServicesTool,
        FetchPikpartBookingsTool,
        FetchPikpartVehicleBrandsTool,
        FetchPikpartVehicleCategoriesTool,
    )

    registry = ToolRegistry()
    for tool_cls in [
        SearchPartsTool,
        CheckPartFitmentTool,
        SuggestAlternatesTool,
        CompareServicePackagesTool,
        EstimateServiceCostTool,
        EstimateRepairCostTool,
        ListQuickServicesTool,
        ExplainClaimLiabilityTool,
        GetClaimStatusTool,
        TriageEmergencyTool,
        DispatchResourceTool,
        LogEmergencyRequestTool,
        RecommendGaragesTool,
        DiagnoseSymptomTool,
        GetPredictiveMaintenanceTool,
        CreateSessionNoteTool,
        FetchPikpartServicesTool,
        FetchPikpartCustomersTool,
        FetchPikpartCustomerVehiclesTool,
        FetchPikpartVehicleServicesTool,
        FetchPikpartBookingServicesTool,
        FetchPikpartBookingsTool,
        FetchPikpartVehicleBrandsTool,
        FetchPikpartVehicleCategoriesTool,
    ]:
        registry.register(tool_cls())
    return registry
