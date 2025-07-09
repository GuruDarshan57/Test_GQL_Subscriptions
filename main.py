import asyncio
from typing import AsyncGenerator
import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn


@strawberry.type
class Response:
    iteration: int
    completion_status: bool = False
    value: str | None = None

    def refresh(
        self, value: str = strawberry.UNSET, completion_status: bool = strawberry.UNSET
    ):
        self.iteration += 1
        self.value = self.value if value is strawberry.UNSET else value
        self.completion_status = (
            self.completion_status
            if completion_status is strawberry.UNSET
            else completion_status
        )
        return self


async def big_task():
    await asyncio.sleep(100)
    return "Big Task Completed."


@strawberry.type
class Query:
    @strawberry.field
    async def execute_big_task() -> str:
        return f"{await big_task()}"


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def exceute_big_task(self, token: str) -> AsyncGenerator[Response, None]:
        task = asyncio.create_task(big_task())
        status = Response(iteration=0)
        while not task.done():
            yield status.refresh()
            await asyncio.sleep(1)
        yield status.refresh(f"{await task} Auth token:{token}", True)


schema = strawberry.Schema(query=Query, subscription=Subscription)
router = GraphQLRouter(schema, path="/gql")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
uvicorn.run(app, host="0.0.0.0", port=8001)
