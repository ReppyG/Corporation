from datetime import datetime, UTC


class NotificationTool:
    def execute(self, channel: str, message: str):
        return {"channel": channel, "message": message, "timestamp": datetime.now(UTC).isoformat()}
