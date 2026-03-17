from .dashboard_router import dashboard_router

@dashboard_router.get("")
async def get_all_dashboards():
    return "ok"