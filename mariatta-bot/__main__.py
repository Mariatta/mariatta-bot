import os
import aiohttp

from aiohttp import web

from gidgethub import routing, sansio
from gidgethub import aiohttp as gh_aiohttp

router = routing.Router()


@router.register("pull_request", action="closed")
async def pr_closed_event(event, gh, *args, **kwargs):
    """
    Whenever a PR is closed, delete the branch
    Only delete the branch if it's not from a forked repo
    """
    forked = event.data["pull_request"]["head"]["repo"]["fork"]
    merged = event.data["pull_request"]["merged"]

    if not forked and merged:
        branch_name = event.data["pull_request"]["head"]["ref"]
        repo = event.data["pull_request"]["repo"]["full_name"]
        await gh.delete(f"/repos/{repo}/git/refs/{branch_name}")


async def main(request):
    body = await request.read()

    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    event = sansio.Event.from_http(request.headers, body, secret=secret)
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "mariatta",
                                  oauth_token=oauth_token)
        await router.dispatch(event, gh)
    return web.Response(status=200)


if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/", main)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)