import asyncio
import os
import sys

sys.path.insert(0, r"d:\SGC_AI\sgc-ai-agent\packages\shared\src")
sys.path.insert(0, r"d:\SGC_AI\sgc-ai-agent\packages\tools\src")

from sgc_tools.pikpart.pikpart_tools import FetchPikpartVehicleDetailsTool

async def main():
    tool = FetchPikpartVehicleDetailsTool()
    # pass mock session
    res = await tool.execute(None, vehicle_number="TEST1234")
    print("Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
