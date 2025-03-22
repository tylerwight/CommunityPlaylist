import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import uvicorn #uvicorn handled theading better than hypercorn
import json

app = FastAPI()

bot_instance = None

class GuildRequest(BaseModel):
    guild_id: int

@app.get("/guilds")
async def get_guilds():
    out = [guild.id for guild in bot_instance.guilds]
    return out

@app.post("/guild")
async def get_guild_info(data: GuildRequest):
    guild = bot_instance.get_guild(data.guild_id)
    if guild is None:
        return {"error": "Guild not found"}
    
    return {
        "name": str(guild),
        "id": str(guild.id),
        "prefix": "?"
    }

@app.post("/channels")
async def get_channels(data: GuildRequest):
    guild = bot_instance.get_guild(data.guild_id)
    if guild is None:
        return {"error": "Guild not found"}
    
    text_channels = [(channel.id, channel.name) for channel in guild.text_channels]
    return text_channels

@app.post("/update_guild")
async def update_guild_data(data: GuildRequest):
    await bot_instance.update_guild(data.guild_id)
    return {"status": "ok"}


def run_api():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [api] [%(levelname)s] %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": "INFO",
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    uvicorn.run("api:app", host="0.0.0.0", port=8090, log_config=logging_config)

