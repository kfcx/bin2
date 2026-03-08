# -*- coding: utf-8 -*-
# @Time    : 2024/12/30
# @Author  : Naihe
# @File    : app.py
# @Software: PyCharm
import os
from pathlib import Path
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseSettings
from starlette.templating import Jinja2Templates


class Settings(BaseSettings):
    upload_dir: Path = Path("./upload")
    port: int = 6162
    address: str = "127.0.0.1"
    binary_upload_limit: int = 100  # in MiB
    client_desc: bool = False


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI()
# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")
# 设置模板目录
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_location = settings.upload_dir / file.filename
    # 限制文件大小
    content = await file.read()
    if len(content) > settings.binary_upload_limit * 1024 * 1024:
        return {"error": "File too large"}
    # 保存文件
    with open(file_location, "wb") as f:
        f.write(content)
    return {"filename": file.filename}


@app.post("/submit")
async def submit(content: str = Form(...)):
    # 为内容生成唯一 ID，例如使用哈希或计数器
    content_id = hash(content)
    file_location = settings.upload_dir / f"{content_id}.txt"
    with open(file_location, "w") as f:
        f.write(content)
    return RedirectResponse(url=f"/retrieve/{content_id}", status_code=303)


@app.get("/retrieve/{content_id}", response_class=HTMLResponse)
async def retrieve(request: Request, content_id: str):
    file_location = settings.upload_dir / f"{content_id}.txt"
    if not file_location.exists():
        return HTMLResponse(content="Content not found", status_code=404)
    with open(file_location, "r") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.get("/pretty/{content_id}", response_class=HTMLResponse)
async def pretty_retrieve(request: Request, content_id: str):
    file_location = settings.upload_dir / f"{content_id}.txt"
    if not file_location.exists():
        return HTMLResponse(content="Content not found", status_code=404)
    with open(file_location, "r") as f:
        content = f.read()
    return templates.TemplateResponse("pretty.html", {"request": request, "content": content})


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app)


