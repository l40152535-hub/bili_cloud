from pathlib import Path
import json
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from bilibili_api import video

try:
    from bilibili_api import select_client, request_settings
    select_client("curl_cffi")
    request_settings.set("impersonate", "chrome131")
except Exception:
    pass


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "bili_cloud_data.json"

app = FastAPI(title="Bili Monitor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本地测试可以用 *；正式部署建议改成你的域名
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def index():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/api/cloud-data")
async def get_cloud_data():
    if not DATA_FILE.exists():
        return JSONResponse(
            {
                "version": "empty",
                "exportTime": None,
                "videos": [],
                "nextId": 1
            },
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取 bili_cloud_data.json 失败：{e}")

    return JSONResponse(
        data,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/api/bili-video")
async def get_bili_video(bvid: str):
    bvid = bvid.strip()

    if not re.match(r"^BV[0-9A-Za-z]{8,20}$", bvid):
        raise HTTPException(status_code=400, detail="BV号格式不正确")

    try:
        v = video.Video(bvid=bvid)
        info = await v.get_info()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"B站数据获取失败：{e}")

    stat = info.get("stat", {})

    return {
        "code": 0,
        "data": {
            "bvid": info.get("bvid", bvid),
            "title": info.get("title", "无标题"),
            "stat": {
                "like": stat.get("like", 0),
                "coin": stat.get("coin", 0),
                "favorite": stat.get("favorite", 0),
                "view": stat.get("view", 0),
                "danmaku": stat.get("danmaku", 0),
                "reply": stat.get("reply", 0),
                "share": stat.get("share", 0)
            },
            "url": f"https://www.bilibili.com/video/{bvid}"
        }
    }
